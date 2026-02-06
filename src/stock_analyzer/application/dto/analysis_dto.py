"""
分析相关 DTO

定义分析请求和响应的数据结构
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class StockContextDTO:
    """股票上下文 DTO"""

    code: str
    name: str
    current_price: float | None = None
    price_change: float | None = None
    volume: float | None = None
    ma_status: str = ""


@dataclass
class AnalysisRequestDTO:
    """分析请求 DTO"""

    stock_code: str
    stock_name: str | None = None
    include_news: bool = True
    include_technical: bool = True
    query_id: str | None = None


@dataclass
class AnalysisResponseDTO:
    """分析响应 DTO"""

    success: bool
    stock_code: str
    stock_name: str
    sentiment_score: int | None = None
    operation_advice: str | None = None
    analysis_summary: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    raw_data: dict[str, Any] | None = None
