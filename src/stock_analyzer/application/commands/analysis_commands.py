"""
数据分析命令

职责：
1. 执行股票分析
2. 批量分析多只股票
3. 触发领域事件

返回CommandResult表示操作成功/失败。
"""

import logging
from typing import Any

from stock_analyzer.application.dto import CommandResult
from stock_analyzer.config import Config
from stock_analyzer.domain.entities import AnalysisResult
from stock_analyzer.domain.enums import ReportType
from stock_analyzer.domain.events import event_bus
from stock_analyzer.domain.events.stock_events import (
    StockAnalysisFailed,
    StockAnalyzed,
)

logger = logging.getLogger(__name__)


class AnalyzeStockCommand:
    """
    命令：分析单只股票

    职责：
    1. 协调数据获取、AI分析等步骤
    2. 发布领域事件
    3. 保存分析结果

    使用示例：
        cmd = AnalyzeStockCommand(config, data_service, analyzer)
        result = cmd.execute("000001", ReportType.SIMPLE)
    """

    def __init__(
        self,
        config: Config,
        data_service: Any,
        analyzer: Any,
        db: Any,
        trend_analyzer: Any | None = None,
        search_service: Any | None = None,
    ) -> None:
        self._config = config
        self._data_service = data_service
        self._analyzer = analyzer
        self._db = db
        self._trend_analyzer = trend_analyzer
        self._search_service = search_service

    def execute(
        self,
        stock_code: str,
        report_type: ReportType = ReportType.SIMPLE,
        skip_save: bool = False,
    ) -> CommandResult:
        """
        执行分析命令

        Args:
            stock_code: 股票代码
            report_type: 报告类型
            skip_save: 是否跳过保存结果

        Returns:
            CommandResult
        """
        try:
            # 构建完整的分析上下文
            context, news_context = self._build_analysis_context(stock_code)

            if not context.get("raw_data"):
                error_msg = f"无法获取 {stock_code} 的历史数据"
                logger.error(error_msg)
                event_bus.publish(StockAnalysisFailed(stock_code=stock_code, error=error_msg))
                return CommandResult(success=False, message=error_msg)

            # 执行AI分析
            result = self._analyzer.analyze(context, news_context=news_context)

            if result is None:
                error_msg = f"AI分析 {stock_code} 返回空结果"
                logger.error(error_msg)
                event_bus.publish(StockAnalysisFailed(stock_code=stock_code, error=error_msg))
                return CommandResult(success=False, message=error_msg)

            # 保存分析结果
            if not skip_save and result:
                self._db.save_analysis_history(
                    result=result,
                    query_id="",
                    report_type=report_type.value,
                    news_content=news_context,
                )

            # 发布分析完成事件
            event_bus.publish(StockAnalyzed(stock_code=stock_code, analysis_result=result))

            logger.info(
                f"[Command] 股票 {stock_code} 分析完成: 建议={result.operation_advice}, 评分={result.sentiment_score}"
            )

            return CommandResult(success=True, message=f"分析完成: {result.operation_advice}", data=result)

        except Exception as e:
            error_msg = f"分析 {stock_code} 时发生异常: {str(e)}"
            logger.exception(error_msg)
            event_bus.publish(StockAnalysisFailed(stock_code=stock_code, error=error_msg))
            return CommandResult(success=False, message=error_msg)

    def _build_analysis_context(self, stock_code: str) -> tuple[dict[str, Any], str | None]:
        """构建完整的分析上下文，包括数据、趋势分析、新闻等"""
        from stock_analyzer.domain import STOCK_NAME_MAP

        stock_name = STOCK_NAME_MAP.get(stock_code, "")

        # 1. 获取实时行情
        realtime_quote = self._data_service.get_realtime_quote(stock_code)
        if realtime_quote and getattr(realtime_quote, "name", None):
            stock_name = realtime_quote.name

        # 2. 获取历史数据
        daily_data, _ = self._data_service.get_daily_data(stock_code, days=30)

        if not stock_name:
            stock_name = f"股票{stock_code}"

        # 3. 获取筹码分布
        chip_data = None
        try:
            chip_data = self._data_service.get_chip_distribution(stock_code)
        except Exception as e:
            logger.debug(f"[{stock_code}] 获取筹码分布失败: {e}")

        # 4. 趋势分析
        trend_result = None
        if self._trend_analyzer and daily_data is not None and not daily_data.empty:
            try:
                trend_result = self._trend_analyzer.analyze(daily_data, stock_code)
            except Exception as e:
                logger.debug(f"[{stock_code}] 趋势分析失败: {e}")

        # 5. 新闻搜索
        news_context = None
        if self._search_service and self._search_service.is_available:
            try:
                intel_results = self._search_service.search_comprehensive_intel(
                    stock_code=stock_code, stock_name=stock_name, max_searches=5
                )
                if intel_results:
                    news_context = self._search_service.format_intel_report(intel_results, stock_name)
            except Exception as e:
                logger.debug(f"[{stock_code}] 新闻搜索失败: {e}")

        # 6. 构建上下文
        context: dict[str, Any] = {
            "code": stock_code,
            "stock_name": stock_name,
            "raw_data": daily_data.to_dict("records")
            if daily_data is not None and hasattr(daily_data, "to_dict")
            else [],
        }

        # 添加实时行情
        if realtime_quote:
            context["realtime"] = {
                "name": getattr(realtime_quote, "name", ""),
                "price": getattr(realtime_quote, "price", None),
                "volume_ratio": getattr(realtime_quote, "volume_ratio", None),
                "turnover_rate": getattr(realtime_quote, "turnover_rate", None),
                "pe_ratio": getattr(realtime_quote, "pe_ratio", None),
                "pb_ratio": getattr(realtime_quote, "pb_ratio", None),
            }

        # 添加筹码分布
        if chip_data:
            context["chip"] = {
                "profit_ratio": chip_data.profit_ratio,
                "avg_cost": chip_data.avg_cost,
                "concentration_90": chip_data.concentration_90,
                "concentration_70": chip_data.concentration_70,
            }

        # 添加趋势分析
        if trend_result:
            context["trend_analysis"] = {
                "trend_status": trend_result.trend_status.value,
                "ma_alignment": trend_result.ma_alignment,
                "trend_strength": trend_result.trend_strength,
                "buy_signal": trend_result.buy_signal.value,
                "signal_score": trend_result.signal_score,
                "signal_reasons": trend_result.signal_reasons,
                "risk_factors": trend_result.risk_factors,
            }

        return context, news_context


class BatchAnalyzeStocksCommand:
    """
    命令：批量分析多只股票

    使用AI Analyzer的batch_analyze方法进行批量分析，
    符合IAIAnalyzer接口定义。
    """

    def __init__(
        self,
        single_command: AnalyzeStockCommand,
        analyzer: Any,
        max_workers: int = 3,
    ) -> None:
        self._single_command = single_command
        self._analyzer = analyzer
        self._max_workers = max_workers

    def execute(
        self,
        stock_codes: list[str],
        report_type: ReportType = ReportType.SIMPLE,
    ) -> CommandResult:
        """
        执行批量分析

        流程：
        1. 为每只股票构建分析上下文
        2. 使用analyzer.batch_analyze进行批量AI分析
        3. 保存结果并发布事件

        Args:
            stock_codes: 股票代码列表
            report_type: 报告类型

        Returns:
            CommandResult（包含结果列表）
        """
        logger.info(f"[Command] 开始批量分析 {len(stock_codes)} 只股票")

        # 1. 构建所有股票的上下文
        contexts: list[dict[str, Any]] = []
        news_contexts: list[str | None] = []

        for code in stock_codes:
            try:
                context, news_context = self._single_command._build_analysis_context(code)
                if context.get("raw_data"):
                    contexts.append(context)
                    news_contexts.append(news_context)
                else:
                    logger.warning(f"[{code}] 无历史数据，跳过分析")
                    event_bus.publish(StockAnalysisFailed(stock_code=code, error="无历史数据"))
            except Exception as e:
                logger.error(f"[{code}] 构建上下文失败: {e}")
                event_bus.publish(StockAnalysisFailed(stock_code=code, error=str(e)))

        if not contexts:
            return CommandResult(success=False, message="没有有效的分析上下文")

        # 2. 使用AI Analyzer的batch_analyze方法进行批量分析
        try:
            # 调用analyzer.batch_analyze，符合IAIAnalyzer接口
            analysis_delay = self._single_command._config.schedule.analysis_delay
            results = self._analyzer.batch_analyze(contexts, delay_between=analysis_delay)

            # 3. 保存结果并发布事件
            valid_results: list[AnalysisResult] = []
            for i, result in enumerate(results):
                if result and result.success:
                    valid_results.append(result)
                    # 保存分析历史
                    try:
                        self._single_command._db.save_analysis_history(
                            result=result,
                            query_id="",
                            report_type=report_type.value,
                            news_content=news_contexts[i],
                        )
                    except Exception as e:
                        logger.warning(f"[{result.code}] 保存分析历史失败: {e}")

                    # 发布领域事件
                    event_bus.publish(StockAnalyzed(stock_code=result.code, analysis_result=result))
                else:
                    code = contexts[i].get("code", "unknown") if i < len(contexts) else "unknown"
                    logger.warning(f"[{code}] AI分析返回无效结果")
                    event_bus.publish(StockAnalysisFailed(stock_code=code, error="AI分析返回无效结果"))

            success_count = len(valid_results)
            fail_count = len(stock_codes) - success_count

            logger.info(f"[Command] 批量分析完成: 成功 {success_count}, 失败 {fail_count}")

            return CommandResult(
                success=success_count > 0,
                message=f"批量分析完成: 成功 {success_count}, 失败 {fail_count}",
                data=valid_results,
            )

        except Exception as e:
            error_msg = f"批量分析执行失败: {str(e)}"
            logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg)
