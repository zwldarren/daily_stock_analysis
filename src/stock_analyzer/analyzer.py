"""兼容层：请使用 stock_analyzer.ai.analyzer"""

import warnings

from stock_analyzer.ai.analyzer import GeminiAnalyzer, get_analyzer
from stock_analyzer.ai.models import AnalysisResult
from stock_analyzer.ai.stock_names import STOCK_NAME_MAP, get_stock_name_multi_source

warnings.warn(
    "stock_analyzer.analyzer is deprecated. Use stock_analyzer.ai.analyzer instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "GeminiAnalyzer",
    "get_analyzer",
    "AnalysisResult",
    "get_stock_name_multi_source",
    "STOCK_NAME_MAP",
]
