"""
通知服务基础设施模块

提供多渠道消息推送能力，支持：
- 企业微信
- 飞书
- Telegram
- 邮件
- Discord
- Pushover
- PushPlus
- 自定义 Webhook
"""

from .base import ChannelDetector, NotificationChannel, NotificationChannelBase
from .builder import NotificationBuilder
from .report_generator import ReportGenerator
from .service import NotificationService

__all__ = [
    "NotificationChannel",
    "ChannelDetector",
    "NotificationChannelBase",
    "NotificationService",
    "NotificationBuilder",
    "ReportGenerator",
]
