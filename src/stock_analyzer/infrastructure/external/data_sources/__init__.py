"""External data sources for stock analysis."""

from stock_analyzer.infrastructure.external.data_sources.fetchers.akshare_fetcher import AkshareFetcher
from stock_analyzer.infrastructure.external.data_sources.fetchers.baostock_fetcher import BaostockFetcher
from stock_analyzer.infrastructure.external.data_sources.fetchers.base import BaseFetcher, DataFetcherManager
from stock_analyzer.infrastructure.external.data_sources.fetchers.efinance_fetcher import EfinanceFetcher
from stock_analyzer.infrastructure.external.data_sources.fetchers.pytdx_fetcher import PytdxFetcher
from stock_analyzer.infrastructure.external.data_sources.fetchers.tushare_fetcher import TushareFetcher
from stock_analyzer.infrastructure.external.data_sources.fetchers.yfinance_fetcher import YfinanceFetcher

__all__ = [
    "BaseFetcher",
    "DataFetcherManager",
    "EfinanceFetcher",
    "AkshareFetcher",
    "TushareFetcher",
    "PytdxFetcher",
    "BaostockFetcher",
    "YfinanceFetcher",
]
