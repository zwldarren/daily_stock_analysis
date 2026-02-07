"""DataService domain data service with TTL caching."""

import fnmatch
import logging
from datetime import date
from typing import Any

import pandas as pd
from cachetools import TTLCache

from stock_analyzer.config import Config
from stock_analyzer.domain.repositories import IDataFetcher, IStockRepository
from stock_analyzer.infrastructure.external.data_sources.fetchers.realtime_types import (
    ChipDistribution,
    UnifiedRealtimeQuote,
)

logger = logging.getLogger(__name__)


class DataService:
    """DataService provide unified data access for stock analysis, with caching and multiple data sources."""

    def __init__(
        self,
        stock_repo: IStockRepository | None = None,
        fetcher_manager: IDataFetcher | None = None,
        config: Config | None = None,
    ):
        """Init DataService with optional repository and fetcher manager"""
        self._stock_repo = stock_repo
        self._fetcher_manager = fetcher_manager
        self._config = config

        # Initialize TTL cache for real-time data and stock names
        # Default TTL will be set based on config when needed
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=1000, ttl=600)
        # Track cache entry expiration times for custom TTL support
        self._cache_expiry: dict[str, float] = {}

        logger.info("DataService initialized")

    def get_daily_data(
        self,
        stock_code: str,
        days: int = 30,
        target_date: date | None = None,
        use_cache: bool = True,
    ) -> tuple[pd.DataFrame | None, str]:
        """
        Fetch daily stock data with caching strategy

        Strategy:
        1. If use_cache=True, try to get from local DB first
        2. If local data is insufficient or expired, fetch from external API
        3. Save new data to local DB
        """
        if target_date is None:
            target_date = date.today()

        # 1. 尝试从本地数据库获取
        if use_cache and self._stock_repo is not None:
            local_data = self._stock_repo.get_daily_data(stock_code, days=days)
            if local_data is not None and not local_data.empty:
                # 检查是否包含目标日期数据
                latest_date = pd.to_datetime(local_data["date"].iloc[-1]).date()
                if latest_date >= target_date:
                    logger.info(f"[DataService] 从本地数据库获取 {stock_code} 数据，共 {len(local_data)} 条")
                    return local_data, "database"

        # 2. 从外部数据源获取
        if self._fetcher_manager is not None:
            try:
                df, source = self._fetcher_manager.get_daily_data(stock_code, days=days)

                if df is not None and not df.empty:
                    # 3. 保存到本地数据库
                    if self._stock_repo is not None:
                        self._stock_repo.save_daily_data(df, stock_code, data_source=source)
                    logger.info(f"[DataService] 从 {source} 获取 {stock_code} 数据并缓存，共 {len(df)} 条")
                    return df, source

            except Exception as e:
                logger.error(f"[DataService] 获取 {stock_code} 日线数据失败: {e}")
        else:
            logger.warning(f"[DataService] 数据获取器未配置，无法获取 {stock_code} 的外部数据")

        return None, ""

    def get_realtime_quote(self, stock_code: str) -> UnifiedRealtimeQuote | None:
        """Fetch real-time stock quote with caching strategy"""
        if self._fetcher_manager is None:
            logger.warning(f"[DataService] 数据获取器未配置，无法获取 {stock_code} 的实时行情")
            return None

        cache_key = f"realtime:{stock_code}"

        # 检查缓存
        if self._is_cache_valid(cache_key):
            logger.debug(f"[DataService] 实时行情缓存命中: {stock_code}")
            return self._cache.get(cache_key)

        # 从数据源获取
        quote = self._fetcher_manager.get_realtime_quote(stock_code)

        if quote is not None and self._config is not None:
            # Update cache with configured TTL
            ttl = self._config.realtime_quote.realtime_cache_ttl
            self._set_cache(cache_key, quote, ttl)

        return quote

    def get_chip_distribution(self, stock_code: str) -> ChipDistribution | None:
        """Fetch chip distribution data for a stock, no caching implemented"""
        if self._fetcher_manager is None:
            logger.warning(f"[DataService] 数据获取器未配置，无法获取 {stock_code} 的筹码分布")
            return None
        return self._fetcher_manager.get_chip_distribution(stock_code)

    def get_stock_name(self, stock_code: str) -> str | None:
        """Get Chinese stock name by code, with caching strategy"""
        cache_key = f"stock_name:{stock_code}"

        # 1. 检查内存缓存
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 2. 尝试从实时行情获取
        quote = self.get_realtime_quote(stock_code)
        if quote and hasattr(quote, "name") and quote.name:
            self._cache[cache_key] = quote.name
            return quote.name

        # 3. 从数据源获取
        if self._fetcher_manager is None:
            logger.warning(f"[DataService] 数据获取器未配置，无法获取 {stock_code} 的股票名称")
            return None

        name = self._fetcher_manager.get_stock_name(stock_code)
        if name:
            self._cache[cache_key] = name

        return name

    def batch_get_stock_names(self, stock_codes: list[str]) -> dict[str, str]:
        """Get stock names for a list of stock codes, with caching strategy"""
        result = {}
        missing_codes = []

        # 1. 先检查内存缓存
        for code in stock_codes:
            cache_key = f"stock_name:{code}"
            if cache_key in self._cache:
                result[code] = self._cache[cache_key]
            else:
                missing_codes.append(code)

        if not missing_codes:
            return result

        # 2. 批量获取剩余的股票名称
        if self._fetcher_manager is None:
            logger.warning("[DataService] 数据获取器未配置，无法批量获取股票名称")
            return result

        names = self._fetcher_manager.batch_get_stock_names(missing_codes)
        result.update(names)

        # 3. 更新缓存
        for code, name in names.items():
            self._cache[f"stock_name:{code}"] = name

        return result

    def get_analysis_context(self, stock_code: str, target_date: date | None = None) -> dict[str, Any] | None:
        """Get analysis context for a stock, including today's and yesterday's data, and technical indicators"""
        if target_date is None:
            target_date = date.today()

        # 从数据库获取最近2天数据
        if self._stock_repo is None:
            logger.warning(f"[DataService] 仓储未配置，无法获取 {stock_code} 的数据")
            return None

        recent_data = self._stock_repo.get_latest_data(stock_code, days=2)

        if not recent_data:
            logger.warning(f"[DataService] 未找到 {stock_code} 的数据")
            return None

        today_data = recent_data[0]
        yesterday_data = recent_data[1] if len(recent_data) > 1 else None

        context = {
            "code": stock_code,
            "date": today_data.date.isoformat(),
            "today": today_data.to_dict(),
        }

        if yesterday_data:
            context["yesterday"] = yesterday_data.to_dict()

            # 计算相比昨日的变化
            if yesterday_data.volume and yesterday_data.volume > 0:
                context["volume_change_ratio"] = round(today_data.volume / yesterday_data.volume, 2)

            if yesterday_data.close and yesterday_data.close > 0:
                context["price_change_ratio"] = round(
                    (today_data.close - yesterday_data.close) / yesterday_data.close * 100, 2
                )

            # 均线形态判断 (使用 technical 模块的 TrendAnalyzer)
            from stock_analyzer.technical.trend import TrendAnalyzer

            context["ma_status"] = TrendAnalyzer.get_ma_status(
                today_data.close, today_data.ma5, today_data.ma10, today_data.ma20
            )

        return context

    def get_main_indices(self) -> list[dict[str, Any]]:
        """Get main stock indices data"""
        if self._fetcher_manager is None:
            logger.warning("[DataService] 数据获取器未配置，无法获取主要指数")
            return []
        return self._fetcher_manager.get_main_indices()

    def get_market_stats(self) -> dict[str, Any]:
        """Get overall market statistics, such as涨跌家数, 成交额, etc."""
        if self._fetcher_manager is None:
            logger.warning("[DataService] 数据获取器未配置，无法获取市场统计")
            return {}
        return self._fetcher_manager.get_market_stats()

    def get_sector_rankings(self, n: int = 5) -> tuple[list[dict], list[dict]]:
        """Get sector rankings"""
        if self._fetcher_manager is None:
            logger.warning("[DataService] 数据获取器未配置，无法获取板块排名")
            return [], []
        return self._fetcher_manager.get_sector_rankings(n)

    def invalidate_cache(self, pattern: str | None = None) -> None:
        """Invalidate cache entries matching the pattern. If pattern is None, clear all cache."""
        if pattern is None:
            self._cache.clear()
            self._cache_expiry.clear()
            logger.info("[DataService] All cache cleared")
        else:
            keys_to_remove = [k for k in self._cache if fnmatch.fnmatch(k, pattern)]
            for key in keys_to_remove:
                del self._cache[key]
                self._cache_expiry.pop(key, None)
            logger.info(f"[DataService] Cache cleared: {pattern} ({len(keys_to_remove)} entries)")

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is valid (exists and not expired)."""
        if key not in self._cache:
            return False
        # Check custom expiry if set
        if key in self._cache_expiry:
            import time

            if time.time() > self._cache_expiry[key]:
                # Expired, remove from cache
                del self._cache[key]
                del self._cache_expiry[key]
                return False
        return True

    def _set_cache(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set cache entry with TTL (time-to-live) in seconds."""
        import time

        self._cache[key] = value
        # Store custom expiry time for this entry
        self._cache_expiry[key] = time.time() + ttl_seconds
