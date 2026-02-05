"""
依赖注入容器

提供应用级别的依赖管理和依赖注入支持，实现模块解耦和可测试性。
"""

from dependency_injector import containers, providers

from stock_analyzer.ai.analyzer import GeminiAnalyzer
from stock_analyzer.config import get_config
from stock_analyzer.data_provider import DataFetcherManager
from stock_analyzer.notification import NotificationService
from stock_analyzer.search_service import SearchService
from stock_analyzer.stock_analyzer import StockTrendAnalyzer
from stock_analyzer.storage import get_db


class Container(containers.DeclarativeContainer):
    """应用依赖容器"""

    # 配置
    config = providers.Singleton(get_config)

    # 基础设施 - 数据库
    db = providers.Singleton(get_db)

    # 数据层
    fetcher_manager = providers.Singleton(DataFetcherManager)

    # 分析层
    trend_analyzer = providers.Singleton(StockTrendAnalyzer)
    ai_analyzer = providers.Singleton(GeminiAnalyzer)
    search_service = providers.Singleton(
        SearchService,
        bocha_keys=config.provided.bocha_api_keys,
        tavily_keys=config.provided.tavily_api_keys,
        serpapi_keys=config.provided.serpapi_keys,
    )

    # 通知层 - 使用Factory因为可能需要不同的上下文
    notification_service = providers.Factory(NotificationService)


# 全局容器实例
_container: Container | None = None


def get_container() -> Container:
    """获取容器实例（单例模式）"""
    global _container
    if _container is None:
        _container = Container()
    return _container


def init_container() -> Container:
    """
    初始化容器（用于测试时重置或首次初始化）

    Returns:
        新创建的容器实例
    """
    global _container
    _container = Container()
    return _container


def reset_container() -> None:
    """重置容器（主要用于测试）"""
    global _container
    _container = None
