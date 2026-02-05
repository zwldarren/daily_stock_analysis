"""
流水线具体阶段实现

实现股票分析流程的各个阶段，每个阶段都是一个独立的 PipelineStage。
所有阶段都遵循 PipelineStage[StageContext, StageContext] 的签名。
"""

import logging
from datetime import date
from typing import Any

import pandas as pd

from stock_analyzer.ai.analyzer import STOCK_NAME_MAP, GeminiAnalyzer
from stock_analyzer.ai.models import AnalysisResult
from stock_analyzer.core.stage import PipelineStage, StageContext, StageExecutionError
from stock_analyzer.data_provider import DataFetcherManager
from stock_analyzer.data_provider.realtime_types import ChipDistribution, UnifiedRealtimeQuote
from stock_analyzer.enums import ReportType
from stock_analyzer.search_service import SearchService
from stock_analyzer.stock_analyzer import StockTrendAnalyzer, TrendAnalysisResult
from stock_analyzer.storage import DatabaseManager

logger = logging.getLogger(__name__)


class DataCollectionStage(PipelineStage[StageContext, StageContext]):
    """数据收集阶段

    从数据源获取股票历史数据并保存到数据库。
    """

    def __init__(self, fetcher_manager: DataFetcherManager, db: DatabaseManager):
        self.fetcher_manager = fetcher_manager
        self.db = db

    def execute(self, context: StageContext) -> StageContext:  # type: ignore[override]
        """执行数据收集

        Args:
            context: 包含 stock_code 的上下文

        Returns:
            添加了 raw_data 和 data_source 的上下文
        """
        stock_code = context.get("stock_code")
        if not stock_code:
            raise StageExecutionError("DataCollectionStage", "缺少 stock_code")

        context.set_metadata("stage", "data_collection")

        try:
            today = date.today()

            # 断点续传检查
            if self.db.has_today_data(stock_code, today):
                logger.info(f"[{stock_code}] 今日数据已存在，使用缓存数据")
                # 从数据库获取已有数据
                df_data = self.db.get_daily_data(stock_code, days=30)
                if df_data is not None and not df_data.empty:
                    context.set("raw_data", df_data)
                    context.set("data_source", "cache")
                    return context

            # 从数据源获取数据
            logger.info(f"[{stock_code}] 开始从数据源获取数据...")
            df, source_name = self.fetcher_manager.get_daily_data(stock_code, days=30)

            if df is None or df.empty:
                raise StageExecutionError("DataCollectionStage", f"获取数据为空: {stock_code}")

            # 保存到数据库
            saved_count = self.db.save_daily_data(df, stock_code, source_name)
            logger.info(f"[{stock_code}] 数据保存成功（来源: {source_name}，新增 {saved_count} 条）")

            context.set("raw_data", df)
            context.set("data_source", source_name)

        except Exception as e:
            logger.error(f"[{stock_code}] 数据收集失败: {e}")
            raise StageExecutionError("DataCollectionStage", str(e), e) from e

        return context

    def rollback(self, context: StageContext) -> None:  # type: ignore[override]
        """回滚：删除今日保存的数据"""
        stock_code = context.get("stock_code")
        if not stock_code:
            return

        try:
            today = date.today()
            if self.db.has_today_data(stock_code, today):
                logger.warning(f"[{stock_code}] 回滚：删除今日数据")
        except Exception as e:
            logger.error(f"[{stock_code}] 回滚失败: {e}")


class RealtimeQuoteStage(PipelineStage[StageContext, StageContext]):
    """实时行情获取阶段

    获取股票的实时行情数据（价格、量比、换手率等）。
    """

    def __init__(self, fetcher_manager: DataFetcherManager):
        self.fetcher_manager = fetcher_manager

    def execute(self, context: StageContext) -> StageContext:  # type: ignore[override]
        """执行实时行情获取

        Args:
            context: 包含 stock_code 的上下文

        Returns:
            添加了 realtime_quote 的上下文
        """
        stock_code = context.get("stock_code")
        if not stock_code:
            raise StageExecutionError("RealtimeQuoteStage", "缺少 stock_code")

        context.set_metadata("stage", "realtime_quote")

        try:
            realtime_quote = self.fetcher_manager.get_realtime_quote(stock_code)

            if realtime_quote:
                # 更新股票名称
                if realtime_quote.name:
                    context.set("stock_name", realtime_quote.name)

                volume_ratio = getattr(realtime_quote, "volume_ratio", None)
                turnover_rate = getattr(realtime_quote, "turnover_rate", None)

                logger.info(
                    f"[{stock_code}] 实时行情: 价格={realtime_quote.price}, "
                    f"量比={volume_ratio}, 换手率={turnover_rate}%"
                )

                context.set("realtime_quote", realtime_quote)
            else:
                logger.info(f"[{stock_code}] 实时行情获取失败或已禁用")

        except Exception as e:
            logger.warning(f"[{stock_code}] 获取实时行情失败: {e}")

        return context


class ChipAnalysisStage(PipelineStage[StageContext, StageContext]):
    """筹码分析阶段

    获取股票的筹码分布数据。
    """

    def __init__(self, fetcher_manager: DataFetcherManager):
        self.fetcher_manager = fetcher_manager

    def execute(self, context: StageContext) -> StageContext:  # type: ignore[override]
        """执行筹码分析

        Args:
            context: 包含 stock_code 的上下文

        Returns:
            添加了 chip_data 的上下文
        """
        stock_code = context.get("stock_code")
        if not stock_code:
            raise StageExecutionError("ChipAnalysisStage", "缺少 stock_code")

        context.set_metadata("stage", "chip_analysis")

        try:
            chip_data = self.fetcher_manager.get_chip_distribution(stock_code)

            if chip_data:
                logger.info(
                    f"[{stock_code}] 筹码分布: 获利比例={chip_data.profit_ratio:.1%}, "
                    f"90%集中度={chip_data.concentration_90:.2%}"
                )
                context.set("chip_data", chip_data)
            else:
                logger.debug(f"[{stock_code}] 筹码分布获取失败或已禁用")

        except Exception as e:
            logger.warning(f"[{stock_code}] 获取筹码分布失败: {e}")

        return context


class TrendAnalysisStage(PipelineStage[StageContext, StageContext]):
    """趋势分析阶段

    基于历史数据进行技术指标和趋势分析。
    """

    def __init__(self, trend_analyzer: StockTrendAnalyzer, db: DatabaseManager):
        self.trend_analyzer = trend_analyzer
        self.db = db

    def execute(self, context: StageContext) -> StageContext:  # type: ignore[override]
        """执行趋势分析

        Args:
            context: 包含 stock_code 的上下文

        Returns:
            添加了 trend_result 的上下文
        """
        stock_code = context.get("stock_code")
        if not stock_code:
            raise StageExecutionError("TrendAnalysisStage", "缺少 stock_code")

        context.set_metadata("stage", "trend_analysis")

        try:
            # 从数据库获取历史数据
            raw_data = self.db.get_daily_data(stock_code, days=60)

            if raw_data is not None and len(raw_data) > 0:
                df = pd.DataFrame(raw_data) if isinstance(raw_data, list) else raw_data
                trend_result = self.trend_analyzer.analyze(df, stock_code)

                logger.info(
                    f"[{stock_code}] 趋势分析: {trend_result.trend_status.value}, "
                    f"买入信号={trend_result.buy_signal.value}, 评分={trend_result.signal_score}"
                )

                context.set("trend_result", trend_result)
            else:
                logger.warning(f"[{stock_code}] 历史数据不足，跳过趋势分析")

        except Exception as e:
            logger.warning(f"[{stock_code}] 趋势分析失败: {e}")

        return context


class NewsSearchStage(PipelineStage[StageContext, StageContext]):
    """新闻搜索阶段

    搜索股票相关的新闻和情报。
    """

    def __init__(self, search_service: SearchService):
        self.search_service = search_service

    def execute(self, context: StageContext) -> StageContext:  # type: ignore[override]
        """执行新闻搜索

        Args:
            context: 包含 stock_code 和可选 stock_name 的上下文

        Returns:
            添加了 news_context 的上下文
        """
        stock_code = context.get("stock_code")
        if not stock_code:
            raise StageExecutionError("NewsSearchStage", "缺少 stock_code")

        context.set_metadata("stage", "news_search")

        if not self.search_service.is_available:
            logger.info(f"[{stock_code}] 搜索服务不可用，跳过情报搜索")
            return context

        try:
            stock_name = context.get("stock_name") or STOCK_NAME_MAP.get(stock_code, stock_code)

            logger.info(f"[{stock_code}] 开始多维度情报搜索...")

            # 使用多维度搜索
            intel_results = self.search_service.search_comprehensive_intel(
                stock_code=stock_code, stock_name=stock_name, max_searches=5
            )

            if intel_results:
                news_context = self.search_service.format_intel_report(intel_results, stock_name)
                total_results = sum(len(r.results) for r in intel_results.values() if r.success)

                logger.info(f"[{stock_code}] 情报搜索完成: 共 {total_results} 条结果")
                context.set("news_context", news_context)
                context.set("intel_results", intel_results)
            else:
                logger.info(f"[{stock_code}] 情报搜索无结果")

        except Exception as e:
            logger.warning(f"[{stock_code}] 情报搜索失败: {e}")

        return context


class AIAnalysisStage(PipelineStage[StageContext, StageContext]):
    """AI分析阶段

    调用大语言模型进行综合分析。
    """

    def __init__(self, ai_analyzer: GeminiAnalyzer):
        self.ai_analyzer = ai_analyzer

    def _build_analysis_context(self, context: StageContext) -> dict[str, Any]:
        """构建AI分析的上下文数据

        Args:
            context: 流水线上下文

        Returns:
            增强的上下文字典
        """
        stock_code = context.get("stock_code", "")
        stock_name = context.get("stock_name") or STOCK_NAME_MAP.get(stock_code, f"股票{stock_code}")

        # 基础上下文
        enhanced = {
            "code": stock_code,
            "stock_name": stock_name,
            "date": date.today().isoformat(),
        }

        # 添加实时行情
        realtime_quote: UnifiedRealtimeQuote | None = context.get("realtime_quote")
        if realtime_quote:
            volume_ratio = getattr(realtime_quote, "volume_ratio", None)
            enhanced["realtime"] = {
                "name": getattr(realtime_quote, "name", ""),
                "price": getattr(realtime_quote, "price", None),
                "volume_ratio": volume_ratio,
                "turnover_rate": getattr(realtime_quote, "turnover_rate", None),
                "pe_ratio": getattr(realtime_quote, "pe_ratio", None),
                "pb_ratio": getattr(realtime_quote, "pb_ratio", None),
            }
            # 移除 None 值
            enhanced["realtime"] = {k: v for k, v in enhanced["realtime"].items() if v is not None}

        # 添加筹码分布
        chip_data: ChipDistribution | None = context.get("chip_data")
        if chip_data:
            current_price = getattr(realtime_quote, "price", 0) if realtime_quote else 0
            enhanced["chip"] = {
                "profit_ratio": chip_data.profit_ratio,
                "avg_cost": chip_data.avg_cost,
                "concentration_90": chip_data.concentration_90,
                "concentration_70": chip_data.concentration_70,
                "chip_status": chip_data.get_chip_status(current_price or 0),
            }

        # 添加趋势分析
        trend_result: TrendAnalysisResult | None = context.get("trend_result")
        if trend_result:
            enhanced["trend_analysis"] = {
                "trend_status": trend_result.trend_status.value,
                "ma_alignment": trend_result.ma_alignment,
                "trend_strength": trend_result.trend_strength,
                "bias_ma5": trend_result.bias_ma5,
                "bias_ma10": trend_result.bias_ma10,
                "volume_status": trend_result.volume_status.value,
                "buy_signal": trend_result.buy_signal.value,
                "signal_score": trend_result.signal_score,
                "signal_reasons": trend_result.signal_reasons,
                "risk_factors": trend_result.risk_factors,
            }

        # 添加历史数据（如果有）
        raw_data = context.get("raw_data")
        if raw_data is not None:
            if isinstance(raw_data, pd.DataFrame):
                # 取最近5天数据
                recent_data = raw_data.tail(5).to_dict("records")
                enhanced["recent_data"] = recent_data
            elif isinstance(raw_data, list) and len(raw_data) > 0:
                enhanced["recent_data"] = raw_data[-5:]

        return enhanced

    def execute(self, context: StageContext) -> StageContext:  # type: ignore[override]
        """执行AI分析

        Args:
            context: 包含所有前置阶段数据的上下文

        Returns:
            添加了 analysis_result 的上下文
        """
        stock_code = context.get("stock_code")
        if not stock_code:
            raise StageExecutionError("AIAnalysisStage", "缺少 stock_code")

        context.set_metadata("stage", "ai_analysis")

        try:
            # 构建分析上下文
            analysis_context = self._build_analysis_context(context)

            # 获取新闻上下文
            news_context = context.get("news_context")

            # 调用AI分析
            result = self.ai_analyzer.analyze(analysis_context, news_context=news_context)

            if result:
                logger.info(f"[{stock_code}] AI分析完成: {result.operation_advice}, 评分={result.sentiment_score}")
                context.set("analysis_result", result)
            else:
                raise StageExecutionError("AIAnalysisStage", "AI分析返回空结果")

        except Exception as e:
            logger.error(f"[{stock_code}] AI分析失败: {e}")
            raise StageExecutionError("AIAnalysisStage", str(e), e) from e

        return context


class PersistenceStage(PipelineStage[StageContext, StageContext]):
    """持久化阶段

    将分析结果保存到数据库。
    """

    def __init__(
        self,
        db: DatabaseManager,
        query_id: str | None = None,
        report_type: ReportType = ReportType.SIMPLE,
        save_context_snapshot: bool = True,
    ):
        self.db = db
        self.query_id = query_id
        self.report_type = report_type
        self.save_context_snapshot = save_context_snapshot

    def _build_context_snapshot(self, context: StageContext) -> dict[str, Any]:
        """构建上下文快照"""
        snapshot = {
            "enhanced_context": context.get("raw_data"),
            "news_content": context.get("news_context"),
        }

        # 安全转换对象
        def safe_to_dict(value: Any) -> dict[str, Any] | None:
            if value is None:
                return None
            if hasattr(value, "to_dict"):
                try:
                    return value.to_dict()
                except Exception:
                    return None
            if hasattr(value, "__dict__"):
                try:
                    return dict(value.__dict__)
                except Exception:
                    return None
            return None

        snapshot["realtime_quote_raw"] = safe_to_dict(context.get("realtime_quote"))
        snapshot["chip_distribution_raw"] = safe_to_dict(context.get("chip_data"))

        return snapshot

    def execute(self, context: StageContext) -> StageContext:  # type: ignore[override]
        """执行持久化

        Args:
            context: 包含 analysis_result 的上下文

        Returns:
            上下文（不变）
        """
        stock_code = context.get("stock_code")
        result: AnalysisResult | None = context.get("analysis_result")

        if not result:
            logger.warning(f"[{stock_code}] 没有分析结果，跳过持久化")
            return context

        context.set_metadata("stage", "persistence")

        try:
            context_snapshot = None
            if self.save_context_snapshot:
                context_snapshot = self._build_context_snapshot(context)

            self.db.save_analysis_history(
                result=result,
                query_id=self.query_id or "",
                report_type=self.report_type.value,
                news_content=context.get("news_context"),
                context_snapshot=context_snapshot,
                save_snapshot=self.save_context_snapshot,
            )

            logger.info(f"[{stock_code}] 分析结果已保存到数据库")

        except Exception as e:
            logger.warning(f"[{stock_code}] 保存分析历史失败: {e}")

        return context
