"""
股票分析 AI 模块

该模块提供基于大语言模型的股票分析功能。

主要组件:
    - GeminiAnalyzer: Google Gemini API 封装
    - AnalysisResult: 分析结果数据类
    - SYSTEM_PROMPT: 系统提示词模板
    - get_stock_name_multi_source: 多来源获取股票名称
    - STOCK_NAME_MAP: 常见股票名称映射

使用示例:
    >>> from stock_analyzer.ai.analyzer import GeminiAnalyzer
    >>> from stock_analyzer.domain.entities.analysis_result import AnalysisResult
    >>> analyzer = GeminiAnalyzer()
    >>> result = analyzer.analyze(context)

依赖:
    - google-generativeai >= 0.8.0
    - openai >= 2.0.0
"""

from stock_analyzer.domain.entities.analysis_result import AnalysisResult

from .analyzer import GeminiAnalyzer, get_analyzer
from .stock_names import STOCK_NAME_MAP, get_stock_name_multi_source

__all__ = [
    "GeminiAnalyzer",
    "get_analyzer",
    "AnalysisResult",
    "STOCK_NAME_MAP",
    "get_stock_name_multi_source",
]
