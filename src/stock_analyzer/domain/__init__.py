"""
领域层 - 核心业务逻辑和常量

该模块包含：
- 业务常量 (constants)
- 领域实体 (entities)
- 自定义异常 (exceptions)
- 枚举定义 (enums)
- 股票名称解析 (stock_name_resolver)
- 值对象 (value_objects)
- 领域服务 (services)
- 业务策略 (policies)
- 领域事件 (events)
- 仓储接口 (repositories)
"""

from stock_analyzer.domain.constants import STOCK_NAME_MAP
from stock_analyzer.domain.entities import AnalysisResult
from stock_analyzer.domain.enums import ReportType
from stock_analyzer.domain.events import DomainEvent, EventBus, event_bus
from stock_analyzer.domain.events.stock_events import (
    MarketReviewCompleted,
    StockAnalysisFailed,
    StockAnalyzed,
)
from stock_analyzer.domain.exceptions import (
    AnalysisError,
    ConfigurationError,
    DataFetchError,
    DataSourceUnavailableError,
    NotificationError,
    RateLimitError,
    StockAnalyzerException,
    StockNameResolutionError,
    StorageError,
    ValidationError,
    handle_errors,
    safe_execute,
)
from stock_analyzer.domain.policies import (
    BullishAlignmentRule,
    ChipConcentratedRule,
    HighProfitRule,
    NotTooHighRule,
    RuleResult,
    TradingRule,
    create_strict_entry_strategy,
    create_trend_following_strategy,
)
from stock_analyzer.domain.repositories import IStockRepository
from stock_analyzer.domain.services import DataService
from stock_analyzer.domain.stock_name_resolver import (
    StockNameResolver,
    get_stock_name,
    get_stock_name_from_context,
)
from stock_analyzer.domain.value_objects import (
    BiasRate,
    ChipDistribution,
    DateRange,
    MovingAverage,
    Percentage,
    Price,
    StockCode,
    TurnoverRate,
    Volume,
)

__all__ = [
    "STOCK_NAME_MAP",
    "AnalysisResult",
    "ReportType",
    "StockAnalyzerException",
    "DataFetchError",
    "RateLimitError",
    "DataSourceUnavailableError",
    "StorageError",
    "ValidationError",
    "AnalysisError",
    "NotificationError",
    "ConfigurationError",
    "StockNameResolutionError",
    "handle_errors",
    "safe_execute",
    # Stock Name Resolver
    "StockNameResolver",
    "get_stock_name",
    "get_stock_name_from_context",
    "StockCode",
    "Price",
    "Volume",
    "Percentage",
    "DateRange",
    "MovingAverage",
    "BiasRate",
    "ChipDistribution",
    "TurnoverRate",
    "DataService",
    "TradingRule",
    "RuleResult",
    "BullishAlignmentRule",
    "NotTooHighRule",
    "ChipConcentratedRule",
    "HighProfitRule",
    "create_strict_entry_strategy",
    "create_trend_following_strategy",
    "DomainEvent",
    "EventBus",
    "event_bus",
    "StockAnalyzed",
    "StockAnalysisFailed",
    "MarketReviewCompleted",
    "IStockRepository",
]
