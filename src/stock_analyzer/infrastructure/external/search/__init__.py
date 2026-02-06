"""
搜索服务模块

提供统一的新闻搜索接口，支持多个搜索引擎。
"""

from stock_analyzer.infrastructure.external.search.models import SearchResponse, SearchResult
from stock_analyzer.infrastructure.external.search.providers import (
    BaseSearchProvider,
    BochaSearchProvider,
    SerpAPISearchProvider,
    TavilySearchProvider,
)
from stock_analyzer.infrastructure.external.search.service import SearchService, get_search_service

__all__ = [
    "SearchResult",
    "SearchResponse",
    "BaseSearchProvider",
    "TavilySearchProvider",
    "SerpAPISearchProvider",
    "BochaSearchProvider",
    "SearchService",
    "get_search_service",
]
