"""
===================================
A股自选股智能分析系统 - 主调度程序
===================================

职责：
1. 协调各模块完成股票分析流程
2. 实现低并发的线程池调度
3. 全局异常处理，确保单股失败不影响整体
4. 提供命令行入口

使用方式：
    python -m stock_analyzer              # 正常运行
    python -m stock_analyzer --debug      # 调试模式
    python -m stock_analyzer --dry-run    # 仅获取数据不分析

交易理念（已融入分析）：
- 严进策略：不追高，乖离率 > 5% 不买入
- 趋势交易：只做 MA5>MA10>MA20 多头排列
- 效率优先：关注筹码集中度好的股票
- 买点偏好：缩量回踩 MA5/MA10 支撑
"""

import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

import click
from loguru import logger

from stock_analyzer.infrastructure.external.feishu.doc_manager import FeishuDocManager

from .application import register_event_handlers
from .application.market_review import run_market_review
from .application.services.stock_analysis_orchestrator import StockAnalysisOrchestrator
from .config import Config, get_config
from .infrastructure.external.search import SearchService
from .infrastructure.notification import NotificationService
from .utils.logging_config import setup_logging


@click.command()
@click.option("--debug", is_flag=True, help="启用调试模式，输出详细日志")
@click.option("--dry-run", is_flag=True, help="仅获取数据，不进行 AI 分析")
@click.option("--stocks", type=str, help="指定要分析的股票代码，逗号分隔（覆盖配置文件）")
@click.option("--no-notify", is_flag=True, help="不发送推送通知")
@click.option(
    "--single-notify",
    is_flag=True,
    help="启用单股推送模式：每分析完一只股票立即推送，而不是汇总推送",
)
@click.option("--workers", type=int, default=None, help="并发线程数（默认使用配置值）")
@click.option("--schedule", is_flag=True, help="启用定时任务模式，每日定时执行")
@click.option("--market-review", is_flag=True, help="仅运行大盘复盘分析")
@click.option("--no-market-review", is_flag=True, help="跳过大盘复盘分析")
@click.option("--no-context-snapshot", is_flag=True, help="不保存分析上下文快照")
def main(
    debug: bool,
    dry_run: bool,
    stocks: str | None,
    no_notify: bool,
    single_notify: bool,
    workers: int | None,
    schedule: bool,
    market_review: bool,
    no_market_review: bool,
    no_context_snapshot: bool,
) -> int:
    """A股自选股智能分析系统

    Examples:

        \b
        stock-analyzer                    # 正常运行
        stock-analyzer --debug            # 调试模式
        stock-analyzer --dry-run          # 仅获取数据，不进行 AI 分析
        stock-analyzer --stocks 600519,000001  # 指定分析特定股票
        stock-analyzer --no-notify        # 不发送推送通知
        stock-analyzer --single-notify    # 启用单股推送模式
        stock-analyzer --schedule         # 启用定时任务模式
        stock-analyzer --market-review    # 仅运行大盘复盘
    """
    # 加载配置（在设置日志前加载，以获取日志目录）
    config = get_config()

    # 应用系统配置：代理设置
    # GitHub Actions 环境自动跳过代理配置
    if os.getenv("GITHUB_ACTIONS") != "true":
        if config.system.http_proxy:
            os.environ["http_proxy"] = config.system.http_proxy
            logger.debug(f"已设置 http_proxy: {config.system.http_proxy}")
        if config.system.https_proxy:
            os.environ["https_proxy"] = config.system.https_proxy
            logger.debug(f"已设置 https_proxy: {config.system.https_proxy}")

    # 配置日志（输出到控制台和文件）
    # 命令行 --debug 参数优先，其次使用配置文件中的 debug 设置
    effective_debug = debug or config.system.debug
    setup_logging(debug=effective_debug, log_dir=config.logging.log_dir)

    logger.info("=" * 60)
    logger.info("A股自选股智能分析系统 启动")
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 注册事件处理器（激活DDD事件系统）
    register_event_handlers()

    # 验证配置
    warnings = config.validate_config()
    for warning in warnings:
        logger.warning(warning)

    # 解析股票列表
    stock_codes = None
    if stocks:
        stock_codes = [code.strip() for code in stocks.split(",") if code.strip()]
        logger.info(f"使用命令行指定的股票列表: {stock_codes}")

    try:
        # 模式1: 仅大盘复盘
        if market_review:
            logger.info("模式: 仅大盘复盘")
            notifier = NotificationService()

            # 初始化搜索服务和分析器（如果有配置）
            search_service = None
            analyzer = None

            if config.search.bocha_api_keys or config.search.tavily_api_keys or config.search.serpapi_keys:
                search_service = SearchService(
                    bocha_keys=config.search.bocha_api_keys,
                    tavily_keys=config.search.tavily_api_keys,
                    serpapi_keys=config.search.serpapi_keys,
                )

            if config.ai.llm_api_key:
                from stock_analyzer.ai.analyzer import AIAnalyzer

                analyzer = AIAnalyzer()
                if not analyzer.is_available():
                    logger.warning("AI 分析器初始化后不可用，请检查 API Key 配置")
                    analyzer = None
            else:
                logger.warning("未检测到 LLM_API_KEY，将仅使用模板生成报告")

            run_market_review(
                notifier=notifier,
                analyzer=analyzer,
                search_service=search_service,
                send_notification=not no_notify,
            )
            return 0

        # 模式2: 定时任务模式
        if schedule or config.schedule.schedule_enabled:
            logger.info("模式: 定时任务")
            logger.info(f"每日执行时间: {config.schedule.schedule_time}")

            from stock_analyzer.application.scheduler import run_with_schedule

            def scheduled_task():
                run_full_analysis(
                    config,
                    stock_codes,
                    dry_run,
                    no_notify,
                    single_notify,
                    workers,
                    no_market_review,
                    no_context_snapshot,
                )

            run_with_schedule(
                task=scheduled_task,
                schedule_time=config.schedule.schedule_time,
                run_immediately=True,  # 启动时先执行一次
            )
            return 0

        # 模式3: 正常单次运行
        run_full_analysis(
            config, stock_codes, dry_run, no_notify, single_notify, workers, no_market_review, no_context_snapshot
        )

        logger.info("\n程序执行完成")

        return 0

    except KeyboardInterrupt:
        logger.info("\n用户中断，程序退出")
        return 130

    except Exception as e:
        logger.exception(f"程序执行失败: {e}")
        return 1


def run_full_analysis(
    config: Config,
    stock_codes: list[str] | None,
    dry_run: bool,
    no_notify: bool,
    single_notify: bool,
    workers: int | None,
    no_market_review: bool,
    no_context_snapshot: bool = False,
):
    """
    执行完整的分析流程（个股 + 大盘复盘）

    这是定时任务调用的主函数
    """
    try:
        # 命令行参数 --single-notify 覆盖配置（#55）
        if single_notify:
            config.notification_message.single_stock_notify = True

        # 创建编排器
        query_id = uuid.uuid4().hex
        # 确定是否保存上下文快照：命令行参数优先，否则使用配置
        save_context_snapshot = not no_context_snapshot and config.database.save_context_snapshot
        orchestrator = StockAnalysisOrchestrator(
            config=config,
            max_workers=workers,
            query_id=query_id,
            query_source="cli",
            save_context_snapshot=save_context_snapshot,
        )

        # 1. 运行个股分析
        results = orchestrator.run(stock_codes=stock_codes, dry_run=dry_run, send_notification=not no_notify)

        # Issue #128: 分析间隔 - 在个股分析和大盘分析之间添加延迟
        analysis_delay = config.schedule.analysis_delay
        if analysis_delay > 0 and config.schedule.market_review_enabled and not no_market_review:
            logger.info(f"等待 {analysis_delay} 秒后执行大盘复盘（避免API限流）...")
            time.sleep(analysis_delay)

        # 2. 运行大盘复盘（如果启用且不是仅个股模式）
        market_report = ""
        if config.schedule.market_review_enabled and not no_market_review:
            # 从容器获取AI分析器和搜索服务
            from stock_analyzer.container import get_container

            container = get_container()
            analyzer = container.ai_analyzer()
            search_service = container.search_service()

            # 只调用一次，并获取结果
            review_result = run_market_review(
                notifier=orchestrator.notifier,
                analyzer=analyzer,
                search_service=search_service,
                send_notification=not no_notify,
            )
            # 如果有结果，赋值给 market_report 用于后续飞书文档生成
            if review_result:
                market_report = review_result

        # 输出摘要
        if results:
            logger.info("\n===== 分析结果摘要 =====")
            for r in sorted(results, key=lambda x: x.sentiment_score, reverse=True):
                emoji = r.get_emoji()
                logger.info(
                    f"{emoji} {r.name}({r.code}): {r.operation_advice} | "
                    f"评分 {r.sentiment_score} | {r.trend_prediction}"
                )

        logger.info("\n任务执行完成")

        # === 新增：生成飞书云文档 ===
        try:
            feishu_doc = FeishuDocManager()
            if feishu_doc.is_configured() and (results or market_report):
                logger.info("正在创建飞书云文档...")

                # 1. 准备标题 "01-01 13:01大盘复盘"
                tz_cn = timezone(timedelta(hours=8))
                now = datetime.now(tz_cn)
                doc_title = f"{now.strftime('%Y-%m-%d %H:%M')} 大盘复盘"

                # 2. 准备内容 (拼接个股分析和大盘复盘)
                full_content = ""

                # 添加大盘复盘内容（如果有）
                if market_report:
                    full_content += f"# 📈 大盘复盘\n\n{market_report}\n\n---\n\n"

                # 添加个股决策仪表盘（使用 NotificationService 生成）
                if results:
                    dashboard_content = orchestrator.notifier.generate_dashboard_report(results)
                    full_content += f"# 🚀 个股决策仪表盘\n\n{dashboard_content}"

                # 3. 创建文档
                doc_url = feishu_doc.create_daily_doc(doc_title, full_content)
                if doc_url:
                    logger.info(f"飞书云文档创建成功: {doc_url}")
                    # 可选：将文档链接也推送到群里
                    if not no_notify:
                        orchestrator.notifier.send(f"[{now.strftime('%Y-%m-%d %H:%M')}] 复盘文档创建成功: {doc_url}")

        except Exception as e:
            logger.error(f"飞书文档生成失败: {e}")

    except Exception as e:
        logger.exception(f"分析流程执行失败: {e}")


if __name__ == "__main__":
    sys.exit(main())
