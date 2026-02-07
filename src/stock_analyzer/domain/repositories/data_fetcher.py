"""
数据获取服务接口

定义领域层需要的数据获取能力，基础设施层提供具体实现。
这是防腐层的一部分，确保领域层不依赖具体的数据源实现。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd


class IDataFetcher(ABC):
    """
    数据获取服务接口

    职责：
    1. 抽象股票数据获取能力
    2. 支持日线数据、实时行情、筹码分布等
    3. 作为领域层与基础设施层的桥梁

    实现类：
    - DataFetcherManager (基础设施层)
    """

    @abstractmethod
    def get_daily_data(
        self,
        stock_code: str,
        days: int = 30,
    ) -> tuple[pd.DataFrame | None, str]:
        """
        获取日线数据

        Args:
            stock_code: 股票代码
            days: 获取天数

        Returns:
            (DataFrame, 数据源名称)
        """
        pass

    @abstractmethod
    def get_realtime_quote(self, stock_code: str) -> Any:
        """
        获取实时行情

        Args:
            stock_code: 股票代码

        Returns:
            实时行情对象或 None
        """
        pass

    @abstractmethod
    def get_chip_distribution(self, stock_code: str) -> Any:
        """
        获取筹码分布数据

        Args:
            stock_code: 股票代码

        Returns:
            筹码分布对象或 None
        """
        pass

    @abstractmethod
    def get_stock_name(self, stock_code: str) -> str | None:
        """
        获取股票名称

        Args:
            stock_code: 股票代码

        Returns:
            股票中文名称或 None
        """
        pass

    @abstractmethod
    def batch_get_stock_names(self, stock_codes: list[str]) -> dict[str, str]:
        """
        批量获取股票名称

        Args:
            stock_codes: 股票代码列表

        Returns:
            {代码: 名称} 字典
        """
        pass

    @abstractmethod
    def get_main_indices(self) -> list[dict[str, Any]]:
        """
        获取主要指数数据

        Returns:
            指数数据列表
        """
        pass

    @abstractmethod
    def get_market_stats(self) -> dict[str, Any]:
        """
        获取市场统计数据

        Returns:
            市场统计数据
        """
        pass

    @abstractmethod
    def get_sector_rankings(self, n: int = 5) -> tuple[list[dict], list[dict]]:
        """
        获取板块排名

        Args:
            n: 返回前几名

        Returns:
            (领涨板块, 领跌板块)
        """
        pass

    @abstractmethod
    def prefetch_realtime_quotes(self, stock_codes: list[str]) -> int:
        """
        批量预取实时行情

        Args:
            stock_codes: 股票代码列表

        Returns:
            成功预取的数量
        """
        pass
