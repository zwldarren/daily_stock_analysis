"""
容器模块

按功能模块拆分容器配置，避免单一文件过于臃肿。
"""

from dependency_injector import containers, providers

from stock_analyzer.config import get_config
from stock_analyzer.infrastructure.persistence import get_db


class InfrastructureContainer(containers.DeclarativeContainer):
    """基础设施层容器"""

    # 配置
    config = providers.Singleton(get_config)

    # 数据库
    db = providers.Singleton(get_db)


class RepositoryContainer(containers.DeclarativeContainer):
    """仓储层容器"""

    infrastructure = providers.DependenciesContainer()

    # 导入并配置仓储
    from stock_analyzer.infrastructure.persistence.repositories.stock_repository import (
        StockRepository,
    )

    stock_repository = providers.Singleton(
        StockRepository,
        db=infrastructure.db,
    )


class DataContainer(containers.DeclarativeContainer):
    """数据层容器"""

    infrastructure = providers.DependenciesContainer()
    repositories = providers.DependenciesContainer()

    # 导入数据获取器管理器
    from stock_analyzer.infrastructure.external.data_sources import DataFetcherManager

    fetcher_manager = providers.Singleton(DataFetcherManager)


class AIContainer(containers.DeclarativeContainer):
    """AI 层容器"""

    infrastructure = providers.DependenciesContainer()

    from stock_analyzer.ai.analyzer import GeminiAnalyzer

    analyzer = providers.Singleton(GeminiAnalyzer)


class ServiceContainer(containers.DeclarativeContainer):
    """领域服务层容器"""

    infrastructure = providers.DependenciesContainer()
    repositories = providers.DependenciesContainer()
    data = providers.DependenciesContainer()
    ai = providers.DependenciesContainer()

    from stock_analyzer.domain.services import DataService
    from stock_analyzer.infrastructure.external.search import SearchService
    from stock_analyzer.technical import StockTrendAnalyzer

    # 趋势分析器
    trend_analyzer = providers.Singleton(StockTrendAnalyzer)

    # 数据服务
    data_service = providers.Singleton(
        DataService,
        stock_repo=repositories.stock_repository,
        fetcher_manager=data.fetcher_manager,
        config=infrastructure.config,
    )

    # 搜索服务
    search_service = providers.Singleton(
        SearchService,
        bocha_keys=infrastructure.config.provided.search.bocha_api_keys,
        tavily_keys=infrastructure.config.provided.search.tavily_api_keys,
        serpapi_keys=infrastructure.config.provided.search.serpapi_keys,
    )


class QueryContainer(containers.DeclarativeContainer):
    """CQRS 查询层容器"""

    infrastructure = providers.DependenciesContainer()
    repositories = providers.DependenciesContainer()

    from stock_analyzer.application.queries.stock_queries import (
        GetStockAnalysisHistoryQuery,
        GetStockDailyDataQuery,
        GetStockListQuery,
    )

    # 查询：日线数据
    get_stock_daily_data_query = providers.Singleton(
        GetStockDailyDataQuery,
        stock_repo=repositories.stock_repository,
    )

    # 查询：分析历史
    get_stock_analysis_history_query = providers.Singleton(
        GetStockAnalysisHistoryQuery,
        stock_repo=repositories.stock_repository,
    )

    # 查询：股票列表
    get_stock_list_query = providers.Singleton(
        GetStockListQuery,
        config=infrastructure.config,
    )


class CommandContainer(containers.DeclarativeContainer):
    """CQRS 命令层容器"""

    infrastructure = providers.DependenciesContainer()
    repositories = providers.DependenciesContainer()
    data = providers.DependenciesContainer()
    ai = providers.DependenciesContainer()
    services = providers.DependenciesContainer()
    queries = providers.DependenciesContainer()

    from stock_analyzer.application.commands.analysis_commands import (
        AnalyzeStockCommand,
        BatchAnalyzeStocksCommand,
    )
    from stock_analyzer.application.commands.data_commands import (
        FetchStockDataCommand,
        RefreshStockDataCommand,
    )

    # 命令：获取股票数据
    fetch_stock_data_command = providers.Singleton(
        FetchStockDataCommand,
        data_service=services.data_service,
        stock_repo=repositories.stock_repository,
    )

    # 命令：刷新股票数据
    refresh_stock_data_command = providers.Singleton(
        RefreshStockDataCommand,
        fetch_command=fetch_stock_data_command,
    )

    # 命令：分析单只股票
    analyze_stock_command = providers.Singleton(
        AnalyzeStockCommand,
        config=infrastructure.config,
        data_service=services.data_service,
        analyzer=ai.analyzer,
        db=infrastructure.db,
        trend_analyzer=services.trend_analyzer,
        search_service=services.search_service,
    )

    # 命令：批量分析股票
    batch_analyze_stocks_command = providers.Singleton(
        BatchAnalyzeStocksCommand,
        single_command=analyze_stock_command,
        analyzer=ai.analyzer,
        max_workers=infrastructure.config.provided.system.max_workers,
    )


class NotificationContainer(containers.DeclarativeContainer):
    """通知层容器"""

    from stock_analyzer.infrastructure.notification import NotificationService

    notification_service = providers.Factory(NotificationService)


class ApplicationContainer(containers.DeclarativeContainer):
    """
    主应用容器

    组合所有子容器，提供统一的依赖管理。
    """

    # 子容器
    infrastructure = providers.Container(InfrastructureContainer)
    repositories = providers.Container(RepositoryContainer, infrastructure=infrastructure)
    data = providers.Container(DataContainer, infrastructure=infrastructure, repositories=repositories)
    ai = providers.Container(AIContainer, infrastructure=infrastructure)
    services = providers.Container(
        ServiceContainer,
        infrastructure=infrastructure,
        repositories=repositories,
        data=data,
        ai=ai,
    )
    queries = providers.Container(
        QueryContainer,
        infrastructure=infrastructure,
        repositories=repositories,
    )
    commands = providers.Container(
        CommandContainer,
        infrastructure=infrastructure,
        repositories=repositories,
        data=data,
        ai=ai,
        services=services,
        queries=queries,
    )
    notification = providers.Container(NotificationContainer)

    # 导出常用组件的快捷访问
    config = infrastructure.config
    db = infrastructure.db
    stock_repository = repositories.stock_repository
    fetcher_manager = data.fetcher_manager
    ai_analyzer = ai.analyzer
    data_service = services.data_service
    search_service = services.search_service
    trend_analyzer = services.trend_analyzer
    notification_service = notification.notification_service

    # CQRS 查询快捷访问
    get_stock_daily_data_query = queries.get_stock_daily_data_query
    get_stock_analysis_history_query = queries.get_stock_analysis_history_query
    get_stock_list_query = queries.get_stock_list_query

    # CQRS 命令快捷访问
    analyze_stock_command = commands.analyze_stock_command
    batch_analyze_stocks_command = commands.batch_analyze_stocks_command
    fetch_stock_data_command = commands.fetch_stock_data_command
    refresh_stock_data_command = commands.refresh_stock_data_command


# 全局容器实例
_container: ApplicationContainer | None = None


def get_container() -> ApplicationContainer:
    """获取容器实例（单例模式）"""
    global _container
    if _container is None:
        _container = ApplicationContainer()
    return _container


def init_container() -> ApplicationContainer:
    """
    初始化容器（用于测试时重置或首次初始化）

    Returns:
        新创建的容器实例
    """
    global _container
    _container = ApplicationContainer()
    return _container


def reset_container() -> None:
    """重置容器（主要用于测试）"""
    global _container
    _container = None
