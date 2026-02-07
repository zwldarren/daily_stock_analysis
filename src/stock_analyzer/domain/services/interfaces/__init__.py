"""
服务接口层

定义领域服务的抽象接口，遵循依赖倒置原则。
这些接口由应用层依赖，由基础设施层实现。
"""

from stock_analyzer.domain.services.interfaces.ai_analyzer import IAIAnalyzer
from stock_analyzer.domain.services.interfaces.search_service import ISearchService

__all__ = ["IAIAnalyzer", "ISearchService"]
