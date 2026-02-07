"""
股票分析相关领域事件
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from stock_analyzer.domain.events import DomainEvent


@dataclass(frozen=True)
class StockAnalyzed(DomainEvent):
    """
    股票分析完成事件

    当股票分析流程完成后触发。

    属性：
    - stock_code: 股票代码
    - analysis_result: 分析结果对象
    - timestamp: 事件发生时间
    """

    stock_code: str
    analysis_result: Any  # AnalysisResult 类型，避免循环导入
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def event_type(self) -> str:
        return "stock_analyzed"


@dataclass(frozen=True)
class StockAnalysisFailed(DomainEvent):
    """
    股票分析失败事件

    当股票分析流程失败时触发。

    属性：
    - stock_code: 股票代码
    - error: 错误信息
    - timestamp: 事件发生时间
    """

    stock_code: str
    error: str
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def event_type(self) -> str:
        return "stock_analysis_failed"


@dataclass(frozen=True)
class MarketReviewCompleted(DomainEvent):
    """
    市场复盘完成事件

    当市场复盘分析完成后触发。

    属性：
    - market_data: 市场数据汇总
    - timestamp: 事件发生时间
    """

    market_data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def event_type(self) -> str:
        return "market_review_completed"
