"""
查询层（Query Layer）

职责：
1. 处理数据查询请求（只读操作）
2. 返回DTO而非领域实体
3. 支持复杂的查询优化（如缓存、批量查询）

CQRS原则：查询和命令分离，查询不涉及业务状态变更。
"""

from stock_analyzer.application.queries.stock_queries import (
    GetStockAnalysisHistoryQuery,
    GetStockDailyDataQuery,
    GetStockListQuery,
)

__all__ = [
    "GetStockDailyDataQuery",
    "GetStockAnalysisHistoryQuery",
    "GetStockListQuery",
]
