"""
股票数据查询服务

查询职责：
1. 获取日线数据
2. 获取历史分析记录
3. 获取股票列表

注意：查询只返回数据，不修改状态。
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd

from stock_analyzer.domain.repositories import IStockRepository


@dataclass
class StockDailyDataDTO:
    """日线数据DTO"""

    code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    pct_chg: float | None = None
    ma5: float | None = None
    ma10: float | None = None
    ma20: float | None = None


@dataclass
class AnalysisHistoryDTO:
    """分析历史记录DTO"""

    query_id: str
    code: str
    name: str
    report_type: str
    sentiment_score: int
    operation_advice: str
    trend_prediction: str
    created_at: str


class GetStockDailyDataQuery:
    """
    查询：获取股票日线数据

    使用示例：
        query = GetStockDailyDataQuery(stock_repo)
        data = query.execute("000001", days=30)
    """

    def __init__(self, stock_repo: IStockRepository) -> None:
        self._repo = stock_repo

    def execute(self, stock_code: str, days: int = 30) -> list[StockDailyDataDTO]:
        """
        执行查询

        Args:
            stock_code: 股票代码
            days: 查询天数

        Returns:
            日线数据列表
        """
        df = self._repo.get_daily_data(stock_code, days=days)

        if df is None or df.empty:
            return []

        # 转换为DTO列表
        result = []
        for _, row in df.iterrows():
            dto = StockDailyDataDTO(
                code=stock_code,
                date=str(row.get("date", "")),
                open=float(row.get("open", 0)),
                high=float(row.get("high", 0)),
                low=float(row.get("low", 0)),
                close=float(row.get("close", 0)),
                volume=float(row.get("volume", 0)),
                pct_chg=float(row.get("pct_chg")) if pd.notna(row.get("pct_chg")) else None,
                ma5=float(row.get("ma5")) if pd.notna(row.get("ma5")) else None,
                ma10=float(row.get("ma10")) if pd.notna(row.get("ma10")) else None,
                ma20=float(row.get("ma20")) if pd.notna(row.get("ma20")) else None,
            )
            result.append(dto)

        return result


class GetStockAnalysisHistoryQuery:
    """
    查询：获取股票分析历史

    通过仓储接口获取历史分析记录，遵循 CQRS 原则。
    """

    def __init__(self, stock_repo: IStockRepository) -> None:
        self._repo = stock_repo

    def execute(self, stock_code: str | None = None, days: int = 30, limit: int = 50) -> list[AnalysisHistoryDTO]:
        """
        执行查询

        Args:
            stock_code: 股票代码（可选）
            days: 查询最近N天
            limit: 最大返回条数

        Returns:
            分析历史记录列表
        """
        records = self._repo.get_analysis_history(stock_code=stock_code, days=days, limit=limit)

        return [
            AnalysisHistoryDTO(
                query_id=r.query_id,
                code=r.code,
                name=r.name,
                report_type=r.report_type,
                sentiment_score=r.sentiment_score,
                operation_advice=r.operation_advice,
                trend_prediction=r.trend_prediction,
                created_at=r.created_at.isoformat() if r.created_at else "",
            )
            for r in records
        ]


class GetStockListQuery:
    """
    查询：获取股票列表

    从配置或数据库获取自选股列表。
    """

    def __init__(self, config: Any) -> None:
        self._config = config

    def execute(self) -> list[str]:
        """
        执行查询

        Returns:
            股票代码列表
        """
        # 刷新股票列表（从配置或缓存）
        self._config.refresh_stock_list()
        return self._config.stock_list
