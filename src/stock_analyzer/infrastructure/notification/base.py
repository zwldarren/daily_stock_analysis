"""
通知渠道基类和枚举定义
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """通知渠道类型"""

    WECHAT = "wechat"  # 企业微信
    FEISHU = "feishu"  # 飞书
    TELEGRAM = "telegram"  # Telegram
    EMAIL = "email"  # 邮件
    PUSHOVER = "pushover"  # Pushover（手机/桌面推送）
    PUSHPLUS = "pushplus"  # PushPlus（国内推送服务）
    SERVERCHAN3 = "serverchan3"  # Server酱3（手机APP推送服务）
    CUSTOM = "custom"  # 自定义 Webhook
    DISCORD = "discord"  # Discord 机器人 (Bot)
    ASTRBOT = "astrbot"  # AstrBot
    UNKNOWN = "unknown"  # 未知


class ChannelDetector:
    """渠道检测器"""

    @staticmethod
    def get_channel_name(channel: NotificationChannel) -> str:
        """获取渠道中文名称"""
        names = {
            NotificationChannel.WECHAT: "企业微信",
            NotificationChannel.FEISHU: "飞书",
            NotificationChannel.TELEGRAM: "Telegram",
            NotificationChannel.EMAIL: "邮件",
            NotificationChannel.PUSHOVER: "Pushover",
            NotificationChannel.PUSHPLUS: "PushPlus",
            NotificationChannel.SERVERCHAN3: "Server酱3",
            NotificationChannel.CUSTOM: "自定义Webhook",
            NotificationChannel.DISCORD: "Discord Webhook",
            NotificationChannel.ASTRBOT: "AstrBot",
            NotificationChannel.UNKNOWN: "未知渠道",
        }
        return names.get(channel, "未知渠道")


class NotificationChannelBase(ABC):
    """
    通知渠道抽象基类

    所有具体通知渠道必须继承此类并实现 send 方法
    """

    def __init__(self, config: dict[str, Any]):
        """
        初始化通知渠道

        Args:
            config: 渠道配置字典
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置是否完整"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查渠道是否可用（配置完整）"""
        pass

    @abstractmethod
    def send(self, content: str, **kwargs: Any) -> bool:
        """
        发送消息

        Args:
            content: 消息内容
            **kwargs: 额外参数

        Returns:
            是否发送成功
        """
        pass

    @property
    @abstractmethod
    def channel_type(self) -> NotificationChannel:
        """返回渠道类型"""
        pass

    @property
    def name(self) -> str:
        """返回渠道名称"""
        return ChannelDetector.get_channel_name(self.channel_type)
