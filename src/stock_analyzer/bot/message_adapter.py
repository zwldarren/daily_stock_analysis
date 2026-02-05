"""
BotMessage 适配器模块

将 BotMessage 适配为 MessageContext，实现通知服务的解耦。
"""

from stock_analyzer.bot.models import BotMessage
from stock_analyzer.notification.context import MessageContext


def adapt_bot_message(message: BotMessage | None) -> MessageContext | None:
    """将 BotMessage 适配为 MessageContext

    这个适配器函数用于解耦 NotificationService 与 BotMessage 的直接依赖。
    NotificationService 只需要 MessageContext，不需要关心消息来源。

    Args:
        message: BotMessage 实例或 None

    Returns:
        MessageContext 实例或 None

    Example:
        >>> from stock_analyzer.bot.models import BotMessage
        >>> bot_msg = BotMessage(
        ...     platform="feishu",
        ...     message_id="123",
        ...     user_id="user_001",
        ...     user_name="张三",
        ...     chat_id="chat_001",
        ...     chat_type="group",
        ...     content="分析 600519"
        ... )
        >>> context = adapt_bot_message(bot_msg)
        >>> context.platform
        'feishu'
    """
    if message is None:
        return None

    return MessageContext(
        platform=message.platform,
        user_id=message.user_id,
        user_name=message.user_name,
        chat_id=message.chat_id,
        message_id=message.message_id,
        content=message.content,
    )
