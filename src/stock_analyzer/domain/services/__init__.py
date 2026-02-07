"""
股票分析领域服务

职责：
1. 提供核心业务逻辑和数据协调服务

注意：
- 股票分析的核心逻辑已迁移到CQRS Command层（AnalyzeStockCommand）
- 交易策略评估已集成到技术分析模块
"""

from stock_analyzer.domain.services.data_service import DataService

__all__ = [
    "DataService",
]
