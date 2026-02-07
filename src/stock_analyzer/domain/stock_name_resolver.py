"""
股票名称解析服务

提供统一的股票名称获取逻辑，整合多种数据源：
1. 分析上下文（优先）
2. 实时行情数据
3. 静态映射表
4. 动态数据源
"""

import logging
from typing import Any

from stock_analyzer.domain.constants import STOCK_NAME_MAP
from stock_analyzer.domain.exceptions import handle_errors
from stock_analyzer.domain.repositories import IDataFetcher

logger = logging.getLogger(__name__)


class StockNameResolver:
    """股票名称解析器

    统一处理股票名称获取逻辑，支持多种数据源和缓存机制
    """

    def __init__(self, data_manager: IDataFetcher | None = None):
        """初始化解析器

        Args:
            data_manager: 数据获取管理器（可选，用于动态查询）
        """
        self._data_manager = data_manager
        self._local_cache: dict[str, str] = {}

    @classmethod
    def from_context(
        cls,
        stock_code: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """从上下文快速解析股票名称（类方法，无需实例化）

        获取优先级：
        1. 上下文中的 stock_name 字段
        2. 上下文中的 realtime.name 字段
        3. 静态映射表 STOCK_NAME_MAP
        4. 默认名称（股票{code}）

        Args:
            stock_code: 股票代码
            context: 分析上下文（可选）

        Returns:
            股票中文名称
        """
        # 1. 从上下文直接获取
        if context:
            # 优先从 stock_name 字段获取
            name = context.get("stock_name")
            if name and not name.startswith("股票"):
                return name

            # 其次从 realtime 数据获取
            realtime = context.get("realtime")
            if isinstance(realtime, dict):
                name = realtime.get("name")
                if name:
                    return name

        # 2. 从静态映射表获取
        if stock_code in STOCK_NAME_MAP:
            return STOCK_NAME_MAP[stock_code]

        # 3. 返回默认名称
        return f"股票{stock_code}"

    def resolve(
        self,
        stock_code: str,
        context: dict[str, Any] | None = None,
        use_cache: bool = True,
        update_global_cache: bool = True,
    ) -> str:
        """解析股票名称（完整版）

        获取优先级：
        1. 本地缓存
        2. 上下文数据
        3. 静态映射表
        4. 动态数据源
        5. 默认名称

        Args:
            stock_code: 股票代码
            context: 分析上下文（可选）
            use_cache: 是否使用缓存
            update_global_cache: 是否更新全局缓存

        Returns:
            股票中文名称
        """
        # 1. 检查本地缓存
        if use_cache and stock_code in self._local_cache:
            return self._local_cache[stock_code]

        # 2. 从上下文获取
        name = self._resolve_from_context(stock_code, context)
        if name and not name.startswith("股票"):
            if use_cache:
                self._local_cache[stock_code] = name
            return name

        # 3. 从静态映射表获取
        if stock_code in STOCK_NAME_MAP:
            name = STOCK_NAME_MAP[stock_code]
            if use_cache:
                self._local_cache[stock_code] = name
            return name

        # 4. 从动态数据源获取
        if self._data_manager:
            name = self._resolve_from_data_source(stock_code)
            if name:
                if use_cache:
                    self._local_cache[stock_code] = name
                if update_global_cache:
                    STOCK_NAME_MAP[stock_code] = name
                return name

        # 5. 返回默认名称
        default_name = f"股票{stock_code}"
        logger.debug(f"无法解析股票名称，使用默认值: {default_name}")
        return default_name

    def _resolve_from_context(
        self,
        stock_code: str,
        context: dict[str, Any] | None,
    ) -> str | None:
        """从上下文解析名称"""
        if not context:
            return None

        # 优先从 stock_name 字段获取
        name = context.get("stock_name")
        if name and not name.startswith("股票"):
            return name

        # 其次从 realtime 数据获取
        realtime = context.get("realtime")
        if isinstance(realtime, dict):
            name = realtime.get("name")
            if name:
                return name

        return None

    @handle_errors(
        "从数据源获取股票名称失败",
        default_return=None,
        log_level="debug",
    )
    def _resolve_from_data_source(self, stock_code: str) -> str | None:
        """从动态数据源解析名称"""
        if not self._data_manager:
            return None

        name = self._data_manager.get_stock_name(stock_code)
        if name:
            logger.debug(f"从数据源获取股票名称: {stock_code} -> {name}")
        return name

    def batch_resolve(
        self,
        stock_codes: list[str],
        use_cache: bool = True,
    ) -> dict[str, str]:
        """批量解析股票名称

        Args:
            stock_codes: 股票代码列表
            use_cache: 是否使用缓存

        Returns:
            {股票代码: 股票名称} 字典
        """
        result = {}
        missing_codes = []

        # 1. 从缓存获取
        if use_cache:
            for code in stock_codes:
                if code in self._local_cache:
                    result[code] = self._local_cache[code]
                elif code in STOCK_NAME_MAP:
                    result[code] = STOCK_NAME_MAP[code]
                    self._local_cache[code] = STOCK_NAME_MAP[code]
                else:
                    missing_codes.append(code)
        else:
            missing_codes = stock_codes

        # 2. 批量从数据源获取
        if missing_codes and self._data_manager:
            try:
                batch_result = self._data_manager.batch_get_stock_names(missing_codes)
                for code, name in batch_result.items():
                    if name:
                        result[code] = name
                        self._local_cache[code] = name
                        STOCK_NAME_MAP[code] = name

                # 记录未找到的代码
                for code in missing_codes:
                    if code not in result:
                        result[code] = f"股票{code}"
            except Exception as e:
                logger.warning(f"批量获取股票名称失败: {e}")
                for code in missing_codes:
                    result[code] = f"股票{code}"
        elif missing_codes:
            for code in missing_codes:
                result[code] = f"股票{code}"

        return result

    def clear_cache(self) -> None:
        """清空本地缓存"""
        self._local_cache.clear()
        logger.debug("股票名称本地缓存已清空")

    def register(self, code: str, name: str) -> None:
        """注册股票名称到本地缓存和全局映射表

        Args:
            code: 股票代码
            name: 股票名称
        """
        self._local_cache[code] = name
        STOCK_NAME_MAP[code] = name
        logger.debug(f"注册股票名称: {code} -> {name}")


# 便捷函数


def get_stock_name(
    stock_code: str,
    context: dict[str, Any] | None = None,
    data_manager: IDataFetcher | None = None,
) -> str:
    """获取股票名称（便捷函数）

    Args:
        stock_code: 股票代码
        context: 分析上下文（可选）
        data_manager: 数据获取管理器（可选）

    Returns:
        股票中文名称
    """
    resolver = StockNameResolver(data_manager)
    return resolver.resolve(stock_code, context)


def get_stock_name_from_context(stock_code: str, context: dict[str, Any] | None = None) -> str:
    """仅从上下文获取股票名称（快速版，无需实例化）

    Args:
        stock_code: 股票代码
        context: 分析上下文（可选）

    Returns:
        股票中文名称
    """
    return StockNameResolver.from_context(stock_code, context)
