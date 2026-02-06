"""
Infrastructure External Layer

外部服务基础设施层，提供第三方服务集成。
"""

from stock_analyzer.infrastructure.external.search.service import SearchService, get_search_service

__all__ = ["SearchService", "get_search_service"]
