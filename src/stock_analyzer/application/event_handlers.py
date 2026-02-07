"""
应用层事件处理器

订阅领域事件并执行相应的应用逻辑。
这是DDD架构中连接领域层和应用层的桥梁。
"""

import logging

from stock_analyzer.domain.entities import AnalysisResult
from stock_analyzer.domain.events import event_bus
from stock_analyzer.domain.events.stock_events import (
    MarketReviewCompleted,
    StockAnalysisFailed,
    StockAnalyzed,
)

logger = logging.getLogger(__name__)


def on_stock_analyzed(event: StockAnalyzed) -> None:
    """
    处理股票分析完成事件

    职责：
    1. 记录分析成功日志
    2. 更新统计信息（如需要）
    3. 触发后续工作流
    """
    result = event.analysis_result
    if isinstance(result, AnalysisResult):
        logger.info(
            f"[Event] 股票 {event.stock_code} ({result.name}) 分析完成: "
            f"建议={result.operation_advice}, 评分={result.sentiment_score}"
        )
    else:
        logger.info(f"[Event] 股票 {event.stock_code} 分析完成")


def on_stock_analysis_failed(event: StockAnalysisFailed) -> None:
    """
    处理股票分析失败事件

    职责：
    1. 记录错误日志
    2. 发送告警通知（如需要）
    3. 保存失败记录用于后续排查
    """
    logger.error(f"[Event] 股票 {event.stock_code} 分析失败: {event.error}")

    # 可选：保存失败记录到数据库
    # try:
    #     db = get_db()
    #     # 这里可以扩展保存失败记录的逻辑
    #     logger.debug(f"已记录 {event.stock_code} 的分析失败")
    # except Exception as e:
    #     logger.warning(f"记录分析失败时出错: {e}")


def on_market_review_completed(event: MarketReviewCompleted) -> None:
    """
    处理市场复盘完成事件

    职责：
    1. 记录复盘完成
    2. 保存市场数据快照
    """
    market_data = event.market_data
    logger.info(
        f"[Event] 市场复盘完成: "
        f"上证指数={market_data.get('sh_index', 'N/A')}, "
        f"涨跌比={market_data.get('up_down_ratio', 'N/A')}"
    )


def register_event_handlers() -> None:
    """
    注册所有事件处理器

    在应用启动时调用，建立事件订阅关系。
    """
    # 订阅股票分析完成事件
    event_bus.subscribe("stock_analyzed", on_stock_analyzed)
    logger.debug("已注册 StockAnalyzed 事件处理器")

    # 订阅股票分析失败事件
    event_bus.subscribe("stock_analysis_failed", on_stock_analysis_failed)
    logger.debug("已注册 StockAnalysisFailed 事件处理器")

    # 订阅市场复盘完成事件
    event_bus.subscribe("market_review_completed", on_market_review_completed)
    logger.debug("已注册 MarketReviewCompleted 事件处理器")

    logger.debug("所有事件处理器注册完成")


def unregister_event_handlers() -> None:
    """
    注销所有事件处理器

    在应用关闭或测试清理时调用。
    """
    event_bus.clear_handlers()
    logger.debug("所有事件处理器已注销")
