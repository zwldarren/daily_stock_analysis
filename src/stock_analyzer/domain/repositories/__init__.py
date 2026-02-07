"""
仓储接口层

定义领域层的仓储接口，遵循依赖倒置原则。
基础设施层将实现这些接口。
"""

from stock_analyzer.domain.repositories.data_fetcher import IDataFetcher
from stock_analyzer.domain.repositories.stock_repository import IStockRepository

__all__ = ["IStockRepository", "IDataFetcher"]
