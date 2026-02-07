"""
股票数据仓储接口

定义股票数据访问的抽象接口，基础设施层将提供具体实现。
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import pandas as pd

from stock_analyzer.domain.models import SearchResponse


class IStockRepository(ABC):
    """
    股票数据仓储接口

    职责：
    1. 抽象股票数据的持久化访问
    2. 支持日线数据的存取
    3. 支持最新数据的查询
    4. 支持新闻情报和分析历史的存取

    实现类：
    - StockRepository（基础设施层）
    """

    @abstractmethod
    def get_daily_data(
        self,
        stock_code: str,
        days: int = 30,
        target_date: date | None = None,
    ) -> pd.DataFrame | None:
        """
        获取日线数据

        Args:
            stock_code: 股票代码
            days: 获取天数
            target_date: 目标日期（默认今天）

        Returns:
            日线数据 DataFrame，失败返回 None
        """
        pass

    @abstractmethod
    def save_daily_data(
        self,
        df: pd.DataFrame,
        stock_code: str,
        data_source: str = "unknown",
    ) -> int:
        """
        保存日线数据

        Args:
            df: 日线数据 DataFrame
            stock_code: 股票代码
            data_source: 数据来源标识

        Returns:
            保存的记录数
        """
        pass

    @abstractmethod
    def get_latest_data(
        self,
        stock_code: str,
        days: int = 1,
    ) -> list[Any]:
        """
        获取最近的日线数据记录

        Args:
            stock_code: 股票代码
            days: 获取天数

        Returns:
            StockDaily 对象列表
        """
        pass

    @abstractmethod
    def get_data_date_range(
        self,
        stock_code: str,
    ) -> tuple[date | None, date | None]:
        """
        获取数据日期范围

        Args:
            stock_code: 股票代码

        Returns:
            (最早日期, 最新日期)
        """
        pass

    @abstractmethod
    def has_today_data(self, stock_code: str, target_date: date | None = None) -> bool:
        """
        检查是否已有指定日期的数据

        Args:
            stock_code: 股票代码
            target_date: 目标日期（默认今天）

        Returns:
            是否存在数据
        """
        pass

    @abstractmethod
    def save_news_intel(
        self,
        stock_code: str,
        name: str,
        dimension: str,
        query: str,
        response: SearchResponse,
        query_context: dict[str, str] | None = None,
    ) -> int:
        """
        保存新闻情报到数据库

        Args:
            stock_code: 股票代码
            name: 股票名称
            dimension: 搜索维度
            query: 搜索查询
            response: 搜索响应
            query_context: 查询上下文

        Returns:
            保存的记录数
        """
        pass

    @abstractmethod
    def save_analysis_history(
        self,
        result: Any,
        query_id: str,
        report_type: str,
        news_content: str | None,
        context_snapshot: dict[str, Any] | None = None,
        save_snapshot: bool = True,
    ) -> int:
        """
        保存分析结果历史记录

        Args:
            result: 分析结果对象
            query_id: 查询ID
            report_type: 报告类型
            news_content: 新闻内容
            context_snapshot: 上下文快照
            save_snapshot: 是否保存快照

        Returns:
            保存的记录数
        """
        pass

    @abstractmethod
    def get_analysis_context(self, stock_code: str) -> dict[str, Any] | None:
        """
        获取分析上下文数据

        Args:
            stock_code: 股票代码

        Returns:
            包含历史数据的分析上下文字典
        """
        pass

    @abstractmethod
    def get_analysis_history(
        self,
        stock_code: str | None = None,
        days: int = 30,
        limit: int = 50,
    ) -> list[Any]:
        """
        获取分析历史记录

        Args:
            stock_code: 股票代码（可选）
            days: 查询最近N天
            limit: 最大返回条数

        Returns:
            分析历史记录列表
        """
        pass
