"""
===================================
平台适配器模块
===================================

包含各平台的 Webhook 处理和消息解析逻辑。

支持两种接入模式：
1. Webhook 模式：需要公网 IP，配置回调 URL
2. Stream 模式：无需公网 IP，通过 WebSocket 长连接（钉钉、飞书支持）
"""

from .base import BotPlatform
from .dingtalk import DingtalkPlatform

# 所有可用平台（Webhook 模式）
ALL_PLATFORMS = {
    "dingtalk": DingtalkPlatform,
}

# 钉钉 Stream 模式（可选）
try:
    from .dingtalk_stream import (
        DINGTALK_STREAM_AVAILABLE,
        DingtalkStreamClient,
        DingtalkStreamHandler,
        get_dingtalk_stream_client,
        start_dingtalk_stream_background,
    )
except ImportError:
    DINGTALK_STREAM_AVAILABLE = False
    DingtalkStreamClient = None  # type: ignore[misc,assignment]
    DingtalkStreamHandler = None  # type: ignore[misc,assignment]

    def get_dingtalk_stream_client():
        return None

    def start_dingtalk_stream_background():
        return False


# 飞书 Stream 模式（可选）
try:
    from .feishu_stream import (
        FEISHU_SDK_AVAILABLE,
        FeishuReplyClient,
        FeishuStreamClient,
        FeishuStreamHandler,
        get_feishu_stream_client,
        start_feishu_stream_background,
    )
except ImportError:
    FEISHU_SDK_AVAILABLE = False
    FeishuStreamClient = None  # type: ignore[misc,assignment]
    FeishuStreamHandler = None  # type: ignore[misc,assignment]
    FeishuReplyClient = None  # type: ignore[misc,assignment]

    def get_feishu_stream_client():
        return None

    def start_feishu_stream_background():
        return False


__all__ = [
    "BotPlatform",
    "DingtalkPlatform",
    "ALL_PLATFORMS",
    # 钉钉 Stream 模式
    "DingtalkStreamClient",
    "DingtalkStreamHandler",
    "get_dingtalk_stream_client",
    "start_dingtalk_stream_background",
    "DINGTALK_STREAM_AVAILABLE",
    # 飞书 Stream 模式
    "FeishuStreamClient",
    "FeishuStreamHandler",
    "FeishuReplyClient",
    "get_feishu_stream_client",
    "start_feishu_stream_background",
    "FEISHU_SDK_AVAILABLE",
]
