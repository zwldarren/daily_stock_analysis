"""
Search engine providers module.

Provides base classes, configurations, and implementations for all search engine providers.
"""

from stock_analyzer.infrastructure.external.search.providers.base import (
    ApiKeyProviderConfig,
    ApiKeySearchProvider,
    BaseSearchProvider,
    ProviderConfig,
    SearxngProviderConfig,
)
from stock_analyzer.infrastructure.external.search.providers.impl import (
    BochaSearchProvider,
    BraveSearchProvider,
    SearxngSearchProvider,
    SerpAPISearchProvider,
    TavilySearchProvider,
)
from stock_analyzer.infrastructure.external.search.providers.registry import (
    ProviderRegistry,
    register_builtin_providers,
)

# Auto-register built-in providers on module import
register_builtin_providers()

__all__ = [
    # Configuration classes
    "ProviderConfig",
    "ApiKeyProviderConfig",
    "SearxngProviderConfig",
    # Base classes
    "BaseSearchProvider",
    "ApiKeySearchProvider",
    # Provider implementations
    "TavilySearchProvider",
    "SerpAPISearchProvider",
    "BraveSearchProvider",
    "BochaSearchProvider",
    "SearxngSearchProvider",
    # Registry
    "ProviderRegistry",
    "register_builtin_providers",
]
