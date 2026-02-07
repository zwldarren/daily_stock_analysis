"""
股票分析编排器（应用服务层）

职责：
1. 协调命令层完成股票分析流程（CQRS）
2. 管理通知和报告生成
3. 处理大盘复盘功能

设计原则：
- 不直接处理业务逻辑，通过Command层委托
- 专注于流程编排和横切关注点（通知、日志等）
- 支持依赖注入，便于测试
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from stock_analyzer.application.commands import (
    AnalyzeStockCommand,
    BatchAnalyzeStocksCommand,
    FetchStockDataCommand,
)
from stock_analyzer.application.dto import CommandResult
from stock_analyzer.config import Config, get_config
from stock_analyzer.container import get_container
from stock_analyzer.domain.entities.analysis_result import AnalysisResult
from stock_analyzer.domain.enums import ReportType
from stock_analyzer.domain.events import event_bus
from stock_analyzer.domain.events.stock_events import StockAnalysisFailed
from stock_analyzer.infrastructure.bot.message_adapter import adapt_bot_message
from stock_analyzer.infrastructure.bot.models import BotMessage

logger = logging.getLogger(__name__)


class StockAnalysisOrchestrator:
    """
    股票分析编排器

    作为应用层的入口点，协调命令层完成分析流程，
    处理通知和报告生成等横切关注点。
    """

    def __init__(
        self,
        config: Config | None = None,
        max_workers: int | None = None,
        source_message: BotMessage | None = None,
        query_id: str | None = None,
        query_source: str | None = None,
        batch_command: BatchAnalyzeStocksCommand | None = None,
        fetch_command: FetchStockDataCommand | None = None,
        analyze_command: AnalyzeStockCommand | None = None,
    ):
        """
        初始化编排器

        Args:
            config: 配置对象（可选，默认使用全局配置）
            max_workers: 最大并发线程数（可选，默认从配置读取）
            source_message: 来源消息（用于上下文回复）
            query_id: 查询ID
            query_source: 查询来源
            batch_command: 批量分析命令（可选，默认从容器获取）
            fetch_command: 数据获取命令（可选，默认从容器获取）
            analyze_command: 单股分析命令（可选，默认从容器获取）
        """
        self.config = config or get_config()
        self.max_workers = max_workers or self.config.system.max_workers
        self.source_message = source_message
        self.query_id = query_id
        self.query_source = self._resolve_query_source(query_source)

        # 从容器获取依赖或直接使用注入的依赖
        container = get_container()

        # 命令层依赖（支持注入便于测试）
        self._batch_command = batch_command or container.batch_analyze_stocks_command()
        self._fetch_command = fetch_command or container.fetch_stock_data_command()
        self._analyze_command = analyze_command or container.analyze_stock_command()

        # 数据库和通知服务
        self.db = container.db()
        message_context = adapt_bot_message(source_message)
        self.notifier = container.notification_service(context=message_context)

        logger.info(f"编排器初始化完成，最大并发数: {self.max_workers}")

    def run(
        self,
        stock_codes: list[str] | None = None,
        dry_run: bool = False,
        send_notification: bool = True,
    ) -> list[AnalysisResult]:
        """
        运行完整的分析流程

        流程：
        1. 获取待分析的股票列表
        2. 使用Command层执行分析（CQRS）
        3. 收集分析结果
        4. 发送通知

        Args:
            stock_codes: 股票代码列表（可选，默认使用配置中的自选股）
            dry_run: 是否仅获取数据不分析
            send_notification: 是否发送推送通知

        Returns:
            分析结果列表
        """
        start_time = time.time()

        # 使用配置中的股票列表
        if stock_codes is None:
            self.config.refresh_stock_list()
            stock_codes = self.config.stock_list

        if not stock_codes:
            logger.error("未配置自选股列表，请在 .env 文件中设置 STOCK_LIST")
            return []

        logger.info(f"===== 开始分析 {len(stock_codes)} 只股票 =====")
        logger.info(f"股票列表: {', '.join(stock_codes)}")
        logger.info(f"并发数: {self.max_workers}, 模式: {'仅获取数据' if dry_run else '完整分析'}")

        # 批量预取实时行情（优化性能）
        self._prefetch_realtime_quotes(stock_codes)

        results: list[AnalysisResult] = []

        if dry_run:
            # dry_run模式：仅获取数据，使用线程池并发
            results = self._run_dry_mode(stock_codes)
        else:
            # 正常分析模式：使用CQRS Command层
            results = self._run_analysis_mode(stock_codes, send_notification)

        # 统计
        elapsed_time = time.time() - start_time
        logger.info("===== 分析完成 =====")
        if dry_run:
            logger.info(
                f"数据获取完成: {len(stock_codes)} 只股票, 耗时: {elapsed_time:.2f} 秒 (dry-run 模式跳过 AI 分析)"
            )
        else:
            failed_count = len(stock_codes) - len(results)
            logger.info(f"成功: {len(results)}, 失败: {failed_count}, 耗时: {elapsed_time:.2f} 秒")

        return results

    def _prefetch_realtime_quotes(self, stock_codes: list[str]) -> None:
        """批量预取实时行情数据以优化性能"""
        if len(stock_codes) >= 5:
            try:
                container = get_container()
                data_service = container.data_service()
                if hasattr(data_service, "_fetcher_manager") and data_service._fetcher_manager is not None:
                    prefetch_count = data_service._fetcher_manager.prefetch_realtime_quotes(stock_codes)
                    if prefetch_count > 0:
                        logger.info(f"已启用批量预取架构：一次拉取全市场数据，{len(stock_codes)} 只股票共享缓存")
            except Exception as e:
                logger.debug(f"批量预取实时行情失败: {e}")

    def _run_dry_mode(self, stock_codes: list[str]) -> list[AnalysisResult]:
        """dry_run模式：仅获取数据，不进行分析"""
        logger.info("Dry-run模式：仅获取数据")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_code = {
                executor.submit(self._fetch_command.execute, code, 30, False): code for code in stock_codes
            }

            for future in as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    result: CommandResult = future.result()
                    if not result.success:
                        logger.warning(f"[{code}] 数据获取失败: {result.message}")
                except Exception as e:
                    logger.error(f"[{code}] 任务执行失败: {e}")
                    event_bus.publish(StockAnalysisFailed(stock_code=code, error=str(e)))

        # dry_run模式下返回空列表（没有分析结果）
        return []

    def _run_analysis_mode(self, stock_codes: list[str], send_notification: bool) -> list[AnalysisResult]:
        """正常分析模式：使用CQRS Command层执行批量分析"""
        logger.info("使用CQRS Command层执行批量分析")

        # 获取报告类型配置
        report_type_str = self.config.notification_message.report_type.lower()
        report_type = ReportType.FULL if report_type_str == "full" else ReportType.SIMPLE
        single_stock_notify = self.config.notification_message.single_stock_notify

        if single_stock_notify:
            logger.info(f"已启用单股推送模式（报告类型: {report_type_str}）")
            return self._run_single_stock_mode(stock_codes, report_type, send_notification)

        # 批量分析模式
        command_result = self._batch_command.execute(stock_codes, report_type)

        if not command_result.success or not command_result.data:
            logger.error(f"批量分析失败: {command_result.message}")
            return []

        results: list[AnalysisResult] = command_result.data

        # 发送汇总通知
        if results and send_notification:
            self._send_notifications(results)

        return results

    def _run_single_stock_mode(
        self, stock_codes: list[str], report_type: ReportType, send_notification: bool
    ) -> list[AnalysisResult]:
        """单股推送模式：逐只股票分析并立即推送"""
        results: list[AnalysisResult] = []

        for code in stock_codes:
            try:
                # 使用单股分析命令
                result = self._analyze_command.execute(code, report_type)

                if result.success and result.data:
                    results.append(result.data)
                    logger.info(f"[{code}] 分析完成: {result.data.operation_advice}")

                    # 立即推送
                    if send_notification and self.notifier.is_available():
                        self._send_single_stock_notification(result.data, report_type)
                else:
                    logger.warning(f"[{code}] 分析失败: {result.message}")

            except Exception as e:
                logger.error(f"[{code}] 执行异常: {e}")
                event_bus.publish(StockAnalysisFailed(stock_code=code, error=str(e)))

        # 单股推送模式下，汇总通知仅保存到本地
        if results and send_notification:
            self._send_notifications(results, skip_push=True)

        return results

    def _send_single_stock_notification(self, result: AnalysisResult, report_type: ReportType) -> None:
        """发送单只股票的分析通知"""
        try:
            if report_type == ReportType.FULL:
                report_content = self.notifier.generate_dashboard_report([result])
            else:
                report_content = self.notifier.generate_single_stock_report(result)

            if self.notifier.send(report_content):
                logger.info(f"[{result.code}] 单股推送成功")
            else:
                logger.warning(f"[{result.code}] 单股推送失败")
        except Exception as e:
            logger.error(f"[{result.code}] 单股推送异常: {e}")

    def _send_notifications(self, results: list[AnalysisResult], skip_push: bool = False) -> None:
        """发送分析结果通知"""
        try:
            logger.info("生成决策仪表盘日报...")
            report = self.notifier.generate_dashboard_report(results)
            filepath = self.notifier.save_report_to_file(report)
            logger.info(f"决策仪表盘日报已保存: {filepath}")

            if skip_push:
                return

            if not self.notifier.is_available():
                logger.info("通知渠道未配置，跳过推送")
                return

            # 发送通知到各个渠道
            self._send_to_channels(report, results)

        except Exception as e:
            logger.error(f"发送通知失败: {e}")

    def _send_to_channels(self, report: str, results: list[AnalysisResult]) -> None:
        """发送报告到各个通知渠道"""
        from stock_analyzer.infrastructure.notification import NotificationChannel

        channels = self.notifier.get_available_channels()
        context_success = self.notifier.send_to_context(report)

        # 企业微信：只发精简版
        wechat_success = False
        if NotificationChannel.WECHAT in channels:
            dashboard_content = self.notifier.generate_wechat_dashboard(results)
            logger.info(f"企业微信仪表盘长度: {len(dashboard_content)} 字符")
            wechat_success = self.notifier.send_to_wechat(dashboard_content)

        # 其他渠道：发完整报告
        non_wechat_success = False
        for channel in channels:
            if channel == NotificationChannel.WECHAT:
                continue
            try:
                if channel == NotificationChannel.FEISHU:
                    non_wechat_success = self.notifier.send_to_feishu(report) or non_wechat_success
                elif channel == NotificationChannel.TELEGRAM:
                    non_wechat_success = self.notifier.send_to_telegram(report) or non_wechat_success
                elif channel == NotificationChannel.EMAIL:
                    non_wechat_success = self.notifier.send_to_email(report) or non_wechat_success
                elif channel == NotificationChannel.CUSTOM:
                    non_wechat_success = self.notifier.send_to_custom(report) or non_wechat_success
                elif channel == NotificationChannel.PUSHPLUS:
                    non_wechat_success = self.notifier.send_to_pushplus(report) or non_wechat_success
                elif channel == NotificationChannel.DISCORD:
                    non_wechat_success = self.notifier.send_to_discord(report) or non_wechat_success
                elif channel == NotificationChannel.PUSHOVER:
                    non_wechat_success = self.notifier.send_to_pushover(report) or non_wechat_success
                elif channel == NotificationChannel.ASTRBOT:
                    non_wechat_success = self.notifier.send_to_astrbot(report) or non_wechat_success
            except Exception as e:
                logger.warning(f"发送到渠道 {channel} 失败: {e}")

        success = wechat_success or non_wechat_success or context_success
        if success:
            logger.info("决策仪表盘推送成功")
        else:
            logger.warning("决策仪表盘推送失败")

    def _resolve_query_source(self, query_source: str | None) -> str:
        """解析请求来源"""
        if query_source:
            return query_source
        if self.source_message:
            return "bot"
        if self.query_id:
            return "web"
        return "system"

    def fetch_and_save_stock_data(self, code: str, force_refresh: bool = False) -> tuple[bool, str | None]:
        """
        获取并保存单只股票数据（便捷方法）

        实际通过FetchStockDataCommand执行。
        """
        result = self._fetch_command.execute(code, days=30, force_refresh=force_refresh)
        return result.success, None if result.success else result.message

    def analyze_single_stock(self, code: str, report_type: ReportType = ReportType.SIMPLE) -> AnalysisResult | None:
        """
        分析单只股票（便捷方法）

        实际通过AnalyzeStockCommand执行。
        """
        result = self._analyze_command.execute(code, report_type)
        return result.data if result.success else None
