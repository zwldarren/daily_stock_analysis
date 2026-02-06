"""
领域层 - 核心业务逻辑和常量

该模块包含：
- 业务常量 (constants)
- 领域实体 (entities)
- 自定义异常 (exceptions)
- 枚举定义 (enums)
"""

from stock_analyzer.domain.constants import STOCK_NAME_MAP
from stock_analyzer.domain.entities import AnalysisResult
from stock_analyzer.domain.enums import ReportType
from stock_analyzer.domain.exceptions import (
    AnalysisError,
    DataFetchError,
    NotificationError,
    StockAnalyzerException,
    StorageError,
    ValidationError,
)

__all__ = [
    # Constants
    "STOCK_NAME_MAP",
    # Entities
    "AnalysisResult",
    # Enums
    "ReportType",
    # Exceptions
    "StockAnalyzerException",
    "DataFetchError",
    "StorageError",
    "ValidationError",
    "AnalysisError",
    "NotificationError",
]
