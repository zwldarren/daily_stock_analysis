"""
股票数据仓储实现

实现 IStockRepository 接口，包装 DatabaseManager 提供数据访问。
"""

from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import asc, select

from stock_analyzer.domain.repositories import IStockRepository
from stock_analyzer.infrastructure.persistence.database import DatabaseManager
from stock_analyzer.infrastructure.persistence.models import StockDaily


class StockRepository(IStockRepository):
    """
    股票数据仓储实现

    职责：
    1. 实现 IStockRepository 接口
    2. 使用 DatabaseManager 进行实际的数据操作
    3. 作为基础设施层与领域层的桥梁

    使用示例：
        db = DatabaseManager.get_instance()
        repo = StockRepository(db)
        data = repo.get_daily_data("000001", days=30)
    """

    def __init__(self, db: DatabaseManager) -> None:
        """
        初始化仓储实现

        Args:
            db: 数据库管理器实例
        """
        self._db = db

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
            target_date: 目标日期（暂未使用，保持接口兼容）

        Returns:
            日线数据 DataFrame，失败返回 None
        """
        return self._db.get_daily_data(stock_code, days=days)

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
        return self._db.save_daily_data(df, stock_code, data_source=data_source)

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
        return self._db.get_latest_data(stock_code, days=days)

    def get_data_date_range(
        self,
        stock_code: str,
    ) -> tuple[date | None, date | None]:
        """
        获取数据日期范围

        Args:
            stock_code: 股票代码

        Returns:
            (最早日期, 最新日期)，无数据时返回 (None, None)
        """
        records = self._db.get_latest_data(stock_code, days=1)
        if not records:
            return None, None

        # 获取所有数据来确定最早日期
        with self._db.get_session() as session:
            earliest = session.execute(
                select(StockDaily.date).where(StockDaily.code == stock_code).order_by(asc(StockDaily.date)).limit(1)
            ).scalar_one_or_none()

            latest = session.execute(
                select(StockDaily.date).where(StockDaily.code == stock_code).order_by(StockDaily.date.desc()).limit(1)
            ).scalar_one_or_none()

            # 类型断言确保返回类型正确
            earliest_date: date | None = earliest if isinstance(earliest, date) else None
            latest_date: date | None = latest if isinstance(latest, date) else None
            return earliest_date, latest_date

        # 如果查询失败，至少返回最新的日期
        latest_record = records[0]
        return latest_record.date, latest_record.date

    def has_today_data(self, stock_code: str, target_date: date | None = None) -> bool:
        """
        检查是否已有指定日期的数据

        Args:
            stock_code: 股票代码
            target_date: 目标日期（默认今天）

        Returns:
            是否存在数据
        """
        return self._db.has_today_data(stock_code, target_date)

    def save_news_intel(
        self,
        stock_code: str,
        name: str,
        dimension: str,
        query: str,
        response: Any,
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
        return self._db.save_news_intel(
            code=stock_code,
            name=name,
            dimension=dimension,
            query=query,
            response=response,
            query_context=query_context,
        )

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
        return self._db.save_analysis_history(
            result=result,
            query_id=query_id,
            report_type=report_type,
            news_content=news_content,
            context_snapshot=context_snapshot,
            save_snapshot=save_snapshot,
        )

    def get_analysis_context(self, stock_code: str) -> dict[str, Any] | None:
        """
        获取分析上下文数据

        Args:
            stock_code: 股票代码

        Returns:
            包含历史数据的分析上下文字典
        """
        return self._db.get_analysis_context(stock_code)

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
        return self._db.get_analysis_history(code=stock_code, days=days, limit=limit)
