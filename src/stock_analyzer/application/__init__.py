"""
Application Layer

应用服务层，协调领域层和基础设施层，实现业务用例。
包含：应用服务、DTO、事件处理器、Commands和Queries。
"""

# DTO
# CQRS: Commands
from stock_analyzer.application.commands.analysis_commands import (
    AnalyzeStockCommand,
    BatchAnalyzeStocksCommand,
    CommandResult,
)
from stock_analyzer.application.commands.data_commands import (
    FetchStockDataCommand,
    RefreshStockDataCommand,
)
from stock_analyzer.application.dto.analysis_dto import (
    AnalysisRequestDTO,
    AnalysisResponseDTO,
    StockContextDTO,
)

# 事件处理器
from stock_analyzer.application.event_handlers import (
    on_market_review_completed,
    on_stock_analysis_failed,
    on_stock_analyzed,
    register_event_handlers,
    unregister_event_handlers,
)

# 应用服务
from stock_analyzer.application.market_review import run_market_review

# CQRS: Queries
from stock_analyzer.application.queries.stock_queries import (
    GetStockAnalysisHistoryQuery,
    GetStockDailyDataQuery,
    GetStockListQuery,
)
from stock_analyzer.application.services.stock_analysis import (
    analyze_stock,
    analyze_stocks,
    perform_market_review,
)

__all__ = [
    # DTO
    "AnalysisRequestDTO",
    "AnalysisResponseDTO",
    "StockContextDTO",
    # 应用服务
    "analyze_stock",
    "analyze_stocks",
    "perform_market_review",
    "run_market_review",
    # 事件处理器
    "register_event_handlers",
    "unregister_event_handlers",
    "on_stock_analyzed",
    "on_stock_analysis_failed",
    "on_market_review_completed",
    # Commands
    "AnalyzeStockCommand",
    "BatchAnalyzeStocksCommand",
    "FetchStockDataCommand",
    "RefreshStockDataCommand",
    "CommandResult",
    # Queries
    "GetStockDailyDataQuery",
    "GetStockAnalysisHistoryQuery",
    "GetStockListQuery",
]
