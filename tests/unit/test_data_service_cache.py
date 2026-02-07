"""
单元测试 - DataService 缓存功能

测试范围:
- DataService 缓存逻辑
- 缓存命中和失效
- TTL 缓存行为
"""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pandas as pd
import pytest
from cachetools import TTLCache

from stock_analyzer.domain.services.data_service import DataService
from stock_analyzer.infrastructure.external.data_sources.fetchers.realtime_types import (
    RealtimeSource,
    UnifiedRealtimeQuote,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_stock_repo():
    """创建模拟的股票仓库"""
    repo = MagicMock()
    return repo


@pytest.fixture
def mock_fetcher_manager():
    """创建模拟的数据获取管理器"""
    fetcher = MagicMock()
    return fetcher


@pytest.fixture
def mock_config():
    """创建模拟的配置"""
    config = MagicMock()
    config.realtime_quote.realtime_cache_ttl = 300  # 5分钟
    return config


@pytest.fixture
def data_service(mock_stock_repo, mock_fetcher_manager, mock_config):
    """创建 DataService 实例"""
    return DataService(
        stock_repo=mock_stock_repo,
        fetcher_manager=mock_fetcher_manager,
        config=mock_config,
    )


@pytest.fixture
def sample_daily_data():
    """创建示例日线数据"""
    return pd.DataFrame(
        {
            "code": ["600519"] * 5,
            "date": pd.date_range(end=date.today(), periods=5),
            "open": [1700.0, 1710.0, 1720.0, 1730.0, 1740.0],
            "high": [1750.0, 1760.0, 1770.0, 1780.0, 1790.0],
            "low": [1690.0, 1700.0, 1710.0, 1720.0, 1730.0],
            "close": [1740.0, 1750.0, 1760.0, 1770.0, 1780.0],
            "volume": [10000, 11000, 12000, 13000, 14000],
            "amount": [17400000.0, 19250000.0, 21120000.0, 23010000.0, 24920000.0],
            "pct_chg": [0.5, 0.6, 0.7, 0.8, 0.9],
        }
    )


@pytest.fixture
def sample_realtime_quote():
    """创建示例实时行情"""
    return UnifiedRealtimeQuote(
        code="600519",
        name="贵州茅台",
        source=RealtimeSource.EFINANCE,
        price=1780.0,
        change_pct=0.5,
        volume=15000,
    )


# =============================================================================
# DataService Cache Tests
# =============================================================================


class TestDataServiceCache:
    """测试 DataService 缓存功能"""

    def test_cache_initialization(self, data_service):
        """测试缓存初始化"""
        assert isinstance(data_service._cache, TTLCache)
        assert data_service._cache.maxsize == 1000

    def test_get_daily_data_from_cache(self, data_service, mock_stock_repo, sample_daily_data):
        """测试从本地数据库缓存获取日线数据"""
        stock_code = "600519"
        mock_stock_repo.get_daily_data.return_value = sample_daily_data

        df, source = data_service.get_daily_data(stock_code, days=5, use_cache=True)

        assert df is not None
        assert source == "database"
        mock_stock_repo.get_daily_data.assert_called_once_with(stock_code, days=5)

    def test_get_daily_data_from_fetcher(self, data_service, mock_stock_repo, mock_fetcher_manager, sample_daily_data):
        """测试从外部数据源获取日线数据并缓存"""
        stock_code = "600519"
        mock_stock_repo.get_daily_data.return_value = None  # 本地无数据
        mock_fetcher_manager.get_daily_data.return_value = (sample_daily_data, "EfinanceFetcher")

        df, source = data_service.get_daily_data(stock_code, days=5, use_cache=True)

        assert df is not None
        assert source == "EfinanceFetcher"
        mock_fetcher_manager.get_daily_data.assert_called_once()
        mock_stock_repo.save_daily_data.assert_called_once()

    def test_get_daily_data_no_cache(self, data_service, mock_stock_repo, mock_fetcher_manager, sample_daily_data):
        """测试不使用缓存时直接获取外部数据"""
        stock_code = "600519"
        mock_fetcher_manager.get_daily_data.return_value = (sample_daily_data, "AkshareFetcher")

        df, source = data_service.get_daily_data(stock_code, days=5, use_cache=False)

        assert df is not None
        assert source == "AkshareFetcher"
        # 不使用缓存时不应该查询本地数据库
        mock_stock_repo.get_daily_data.assert_not_called()

    def test_get_daily_data_stale_cache(self, data_service, mock_stock_repo, mock_fetcher_manager, sample_daily_data):
        """测试本地缓存数据过期时重新获取"""
        stock_code = "600519"
        # 创建过期的数据（3天前的数据）
        stale_data = sample_daily_data.copy()
        stale_data["date"] = pd.date_range(end=date.today() - timedelta(days=3), periods=5)

        mock_stock_repo.get_daily_data.return_value = stale_data
        mock_fetcher_manager.get_daily_data.return_value = (sample_daily_data, "EfinanceFetcher")

        df, source = data_service.get_daily_data(stock_code, days=5, target_date=date.today())

        # 因为本地数据过期，应该从外部获取
        assert source == "EfinanceFetcher"

    def test_get_realtime_quote_cache_hit(self, data_service, mock_fetcher_manager, sample_realtime_quote):
        """测试实时行情缓存命中"""
        stock_code = "600519"
        cache_key = f"realtime:{stock_code}"

        # 预先设置缓存
        data_service._cache[cache_key] = sample_realtime_quote

        quote = data_service.get_realtime_quote(stock_code)

        assert quote is not None
        assert quote.code == stock_code
        assert quote.price == 1780.0
        # 缓存命中时不应该调用 fetcher
        mock_fetcher_manager.get_realtime_quote.assert_not_called()

    def test_get_realtime_quote_cache_miss(self, data_service, mock_fetcher_manager, sample_realtime_quote):
        """测试实时行情缓存未命中"""
        stock_code = "600519"
        mock_fetcher_manager.get_realtime_quote.return_value = sample_realtime_quote

        quote = data_service.get_realtime_quote(stock_code)

        assert quote is not None
        assert quote.code == stock_code
        mock_fetcher_manager.get_realtime_quote.assert_called_once_with(stock_code)
        # 验证缓存已更新
        cache_key = f"realtime:{stock_code}"
        assert cache_key in data_service._cache

    def test_get_realtime_quote_no_fetcher(self, data_service, mock_fetcher_manager):
        """测试没有 fetcher 时返回 None"""
        data_service._fetcher_manager = None

        quote = data_service.get_realtime_quote("600519")

        assert quote is None

    def test_get_stock_name_from_cache(self, data_service):
        """测试从缓存获取股票名称"""
        stock_code = "600519"
        cache_key = f"stock_name:{stock_code}"
        data_service._cache[cache_key] = "贵州茅台"

        name = data_service.get_stock_name(stock_code)

        assert name == "贵州茅台"

    def test_get_stock_name_from_quote(self, data_service, mock_fetcher_manager, sample_realtime_quote):
        """测试从实时行情获取股票名称并缓存"""
        stock_code = "600519"
        mock_fetcher_manager.get_realtime_quote.return_value = sample_realtime_quote

        name = data_service.get_stock_name(stock_code)

        assert name == "贵州茅台"
        # 验证已缓存
        cache_key = f"stock_name:{stock_code}"
        assert data_service._cache[cache_key] == "贵州茅台"

    def test_get_stock_name_from_fetcher(self, data_service, mock_fetcher_manager):
        """测试从 fetcher 获取股票名称"""
        stock_code = "600519"
        mock_fetcher_manager.get_realtime_quote.return_value = None
        mock_fetcher_manager.get_stock_name.return_value = "贵州茅台"

        name = data_service.get_stock_name(stock_code)

        assert name == "贵州茅台"
        mock_fetcher_manager.get_stock_name.assert_called_once_with(stock_code)

    def test_batch_get_stock_names_with_cache(self, data_service):
        """测试批量获取股票名称（部分缓存命中）"""
        # 预设缓存
        data_service._cache["stock_name:600519"] = "贵州茅台"

        mock_fetcher_manager = data_service._fetcher_manager
        mock_fetcher_manager.batch_get_stock_names.return_value = {"000001": "平安银行"}

        codes = ["600519", "000001", "000002"]
        names = data_service.batch_get_stock_names(codes)

        # 600519 应该从缓存获取
        assert names["600519"] == "贵州茅台"
        # 000001 应该从 fetcher 获取
        assert names["000001"] == "平安银行"
        # 只请求未缓存的代码
        mock_fetcher_manager.batch_get_stock_names.assert_called_once_with(["000001", "000002"])

    def test_batch_get_stock_names_all_cached(self, data_service):
        """测试批量获取股票名称（全部缓存命中）"""
        # 预设所有缓存
        data_service._cache["stock_name:600519"] = "贵州茅台"
        data_service._cache["stock_name:000001"] = "平安银行"

        mock_fetcher_manager = data_service._fetcher_manager

        codes = ["600519", "000001"]
        names = data_service.batch_get_stock_names(codes)

        assert len(names) == 2
        # 全部缓存命中，不应该调用 fetcher
        mock_fetcher_manager.batch_get_stock_names.assert_not_called()


class TestDataServiceCacheManagement:
    """测试 DataService 缓存管理"""

    def test_invalidate_cache_all(self, data_service):
        """测试清除所有缓存"""
        # 填充缓存
        data_service._cache["key1"] = "value1"
        data_service._cache["key2"] = "value2"

        data_service.invalidate_cache()

        assert len(data_service._cache) == 0

    def test_invalidate_cache_with_pattern(self, data_service):
        """测试按模式清除缓存"""
        # 填充缓存
        data_service._cache["stock_name:600519"] = "贵州茅台"
        data_service._cache["stock_name:000001"] = "平安银行"
        data_service._cache["realtime:600519"] = MagicMock()
        data_service._cache["other_key"] = "other_value"

        data_service.invalidate_cache("stock_name:*")

        # stock_name 缓存应该被清除
        assert "stock_name:600519" not in data_service._cache
        assert "stock_name:000001" not in data_service._cache
        # 其他缓存应该保留
        assert "realtime:600519" in data_service._cache
        assert "other_key" in data_service._cache

    def test_is_cache_valid(self, data_service):
        """测试缓存有效性检查"""
        data_service._cache["valid_key"] = "value"

        assert data_service._is_cache_valid("valid_key") is True
        assert data_service._is_cache_valid("invalid_key") is False

    def test_set_cache(self, data_service):
        """测试设置缓存"""
        data_service._set_cache("test_key", "test_value", 300)

        assert "test_key" in data_service._cache
        assert data_service._cache["test_key"] == "test_value"


class TestDataServiceNoDependencies:
    """测试 DataService 无依赖时的行为"""

    def test_get_daily_data_no_repo_no_fetcher(self):
        """测试没有仓库和 fetcher 时获取日线数据"""
        service = DataService(stock_repo=None, fetcher_manager=None)

        df, source = service.get_daily_data("600519", days=5)

        assert df is None
        assert source == ""

    def test_get_realtime_quote_no_fetcher(self):
        """测试没有 fetcher 时获取实时行情"""
        service = DataService(stock_repo=None, fetcher_manager=None)

        quote = service.get_realtime_quote("600519")

        assert quote is None

    def test_get_chip_distribution_no_fetcher(self):
        """测试没有 fetcher 时获取筹码分布"""
        service = DataService(stock_repo=None, fetcher_manager=None)

        chip = service.get_chip_distribution("600519")

        assert chip is None

    def test_get_stock_name_no_fetcher(self):
        """测试没有 fetcher 时获取股票名称"""
        service = DataService(stock_repo=None, fetcher_manager=None)

        name = service.get_stock_name("600519")

        assert name is None

    def test_batch_get_stock_names_no_fetcher(self):
        """测试没有 fetcher 时批量获取股票名称"""
        service = DataService(stock_repo=None, fetcher_manager=None)

        names = service.batch_get_stock_names(["600519", "000001"])

        assert isinstance(names, dict)
        assert len(names) == 0

    def test_get_main_indices_no_fetcher(self):
        """测试没有 fetcher 时获取主要指数"""
        service = DataService(stock_repo=None, fetcher_manager=None)

        indices = service.get_main_indices()

        assert isinstance(indices, list)
        assert len(indices) == 0

    def test_get_market_stats_no_fetcher(self):
        """测试没有 fetcher 时获取市场统计"""
        service = DataService(stock_repo=None, fetcher_manager=None)

        stats = service.get_market_stats()

        assert isinstance(stats, dict)
        assert len(stats) == 0

    def test_get_sector_rankings_no_fetcher(self):
        """测试没有 fetcher 时获取板块排名"""
        service = DataService(stock_repo=None, fetcher_manager=None)

        top, bottom = service.get_sector_rankings()

        assert isinstance(top, list)
        assert isinstance(bottom, list)


class TestDataServiceWithMockData:
    """使用模拟数据测试 DataService"""

    def test_get_analysis_context(self):
        """测试获取分析上下文"""
        mock_repo = MagicMock()
        # 模拟返回最近2天的数据
        from stock_analyzer.infrastructure.persistence.models import StockDaily

        today = StockDaily(
            code="600519",
            date=date.today(),
            open=1700.0,
            close=1780.0,
            high=1790.0,
            low=1690.0,
            volume=15000,
            amount=26700000.0,
            ma5=1760.0,
            ma10=1750.0,
            ma20=1740.0,
        )
        yesterday = StockDaily(
            code="600519",
            date=date.today() - timedelta(days=1),
            open=1690.0,
            close=1770.0,
            high=1780.0,
            low=1680.0,
            volume=14000,
            amount=24780000.0,
            ma5=1755.0,
            ma10=1745.0,
            ma20=1735.0,
        )
        mock_repo.get_latest_data.return_value = [today, yesterday]

        service = DataService(stock_repo=mock_repo, fetcher_manager=None)
        context = service.get_analysis_context("600519")

        assert context is not None
        assert context["code"] == "600519"
        assert "today" in context
        assert "yesterday" in context
        assert "volume_change_ratio" in context
        assert "price_change_ratio" in context

    def test_get_analysis_context_no_data(self):
        """测试没有数据时获取分析上下文"""
        mock_repo = MagicMock()
        mock_repo.get_latest_data.return_value = []

        service = DataService(stock_repo=mock_repo, fetcher_manager=None)
        context = service.get_analysis_context("600519")

        assert context is None

    def test_get_analysis_context_no_repo(self):
        """测试没有仓库时获取分析上下文"""
        service = DataService(stock_repo=None, fetcher_manager=None)
        context = service.get_analysis_context("600519")

        assert context is None
