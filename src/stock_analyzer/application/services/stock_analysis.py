"""
股票分析应用服务

应用服务层，协调领域层和基础设施层完成分析用例。

注意：本模块提供便捷函数，实际逻辑委托给StockAnalysisOrchestrator和Command层。
"""

import uuid

from stock_analyzer.application.market_review import run_market_review
from stock_analyzer.application.services.stock_analysis_orchestrator import StockAnalysisOrchestrator
from stock_analyzer.config import Config, get_config
from stock_analyzer.container import get_container
from stock_analyzer.domain import AnalysisResult, ReportType
from stock_analyzer.infrastructure.notification import NotificationService


def analyze_stock(
    stock_code: str,
    config: Config | None = None,
    full_report: bool = False,
    notifier: NotificationService | None = None,
) -> AnalysisResult | None:
    """
    分析单只股票

    Args:
        stock_code: 股票代码
        config: 配置对象（可选，默认使用单例）
        full_report: 是否生成完整报告
        notifier: 通知服务（可选）

    Returns:
        分析结果对象
    """
    if config is None:
        config = get_config()

    # 创建分析编排器
    orchestrator = StockAnalysisOrchestrator(config=config, query_id=uuid.uuid4().hex, query_source="cli")

    # 使用通知服务（如果提供）
    if notifier:
        orchestrator.notifier = notifier

    # 运行单只股票分析
    result = orchestrator.analyze_single_stock(
        code=stock_code, report_type=ReportType.FULL if full_report else ReportType.SIMPLE
    )

    return result


def analyze_stocks(
    stock_codes: list[str],
    config: Config | None = None,
    full_report: bool = False,
    notifier: NotificationService | None = None,
) -> list[AnalysisResult]:
    """
    分析多只股票

    Args:
        stock_codes: 股票代码列表
        config: 配置对象（可选，默认使用单例）
        full_report: 是否生成完整报告
        notifier: 通知服务（可选）

    Returns:
        分析结果列表
    """
    if config is None:
        config = get_config()

    # 创建分析编排器
    orchestrator = StockAnalysisOrchestrator(config=config, query_id=uuid.uuid4().hex, query_source="cli")

    # 使用通知服务（如果提供）
    if notifier:
        orchestrator.notifier = notifier

    # 运行批量分析
    results = orchestrator.run(stock_codes=stock_codes, dry_run=False, send_notification=notifier is not None)

    return results


def perform_market_review(config: Config | None = None, notifier: NotificationService | None = None) -> str | None:
    """
    执行大盘复盘

    Args:
        config: 配置对象（可选，默认使用单例）
        notifier: 通知服务（可选）

    Returns:
        复盘报告内容
    """
    if config is None:
        config = get_config()

    # 从容器获取依赖
    container = get_container()
    analyzer = container.ai_analyzer()
    search_service = container.search_service()

    # 创建通知服务（如果没有提供）
    if notifier is None:
        orchestrator = StockAnalysisOrchestrator(config=config, query_id=uuid.uuid4().hex, query_source="cli")
        notifier = orchestrator.notifier

    # 调用大盘复盘函数
    return run_market_review(notifier=notifier, analyzer=analyzer, search_service=search_service)
