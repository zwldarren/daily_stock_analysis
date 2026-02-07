"""
数据获取器模块

提供各种外部数据源的获取器实现
"""

from stock_analyzer.infrastructure.external.data_sources.fetchers.base import (
    BaseFetcher,
    DataFetcherManager,
)

__all__ = ["BaseFetcher", "DataFetcherManager"]
