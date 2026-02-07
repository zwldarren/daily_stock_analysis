"""
单元测试 - 通知服务基础模块

测试范围:
- NotificationChannel 枚举
- ChannelDetector 渠道检测器
- NotificationChannelBase 抽象基类
"""

from abc import ABC
from typing import Any
from unittest.mock import MagicMock

import pytest

from stock_analyzer.infrastructure.notification.base import (
    ChannelDetector,
    NotificationChannel,
    NotificationChannelBase,
)


# =============================================================================
# NotificationChannel 枚举测试
# =============================================================================
class TestNotificationChannel:
    """测试通知渠道枚举"""

    @pytest.mark.parametrize(
        "channel, value",
        [
            (NotificationChannel.WECHAT, "wechat"),
            (NotificationChannel.FEISHU, "feishu"),
            (NotificationChannel.TELEGRAM, "telegram"),
            (NotificationChannel.EMAIL, "email"),
            (NotificationChannel.PUSHOVER, "pushover"),
            (NotificationChannel.PUSHPLUS, "pushplus"),
            (NotificationChannel.SERVERCHAN3, "serverchan3"),
            (NotificationChannel.CUSTOM, "custom"),
            (NotificationChannel.DISCORD, "discord"),
            (NotificationChannel.ASTRBOT, "astrbot"),
            (NotificationChannel.UNKNOWN, "unknown"),
        ],
    )
    def test_channel_values(self, channel: NotificationChannel, value: str) -> None:
        """测试各渠道枚举值"""
        assert channel.value == value

    def test_all_channels(self) -> None:
        """测试所有定义的渠道"""
        expected_channels = [
            "wechat",
            "feishu",
            "telegram",
            "email",
            "pushover",
            "pushplus",
            "serverchan3",
            "custom",
            "discord",
            "astrbot",
            "unknown",
        ]
        actual_channels = [c.value for c in NotificationChannel]

        for expected in expected_channels:
            assert expected in actual_channels, f"Missing channel: {expected}"


# =============================================================================
# ChannelDetector 测试
# =============================================================================
class TestChannelDetector:
    """测试渠道检测器"""

    @pytest.mark.parametrize(
        "channel, expected_name",
        [
            (NotificationChannel.WECHAT, "企业微信"),
            (NotificationChannel.FEISHU, "飞书"),
            (NotificationChannel.TELEGRAM, "Telegram"),
            (NotificationChannel.EMAIL, "邮件"),
            (NotificationChannel.PUSHOVER, "Pushover"),
            (NotificationChannel.PUSHPLUS, "PushPlus"),
            (NotificationChannel.SERVERCHAN3, "Server酱3"),
            (NotificationChannel.CUSTOM, "自定义Webhook"),
            (NotificationChannel.DISCORD, "Discord Webhook"),
            (NotificationChannel.ASTRBOT, "AstrBot"),
            (NotificationChannel.UNKNOWN, "未知渠道"),
        ],
    )
    def test_get_channel_name(self, channel: NotificationChannel, expected_name: str) -> None:
        """测试获取渠道中文名称"""
        assert ChannelDetector.get_channel_name(channel) == expected_name

    def test_get_channel_name_unknown(self) -> None:
        """测试获取未知渠道的默认名称"""
        # 使用不存在的渠道值
        unknown_channel = MagicMock()
        unknown_channel.value = "nonexistent"

        # 当渠道不在映射中时应该返回 "未知渠道"
        assert ChannelDetector.get_channel_name(unknown_channel) == "未知渠道"  # type: ignore[arg-type]


# =============================================================================
# NotificationChannelBase 抽象基类测试
# =============================================================================
class ConcreteChannel(NotificationChannelBase):
    """用于测试的具体渠道实现"""

    def _validate_config(self) -> None:
        """验证配置"""
        if not self.config:
            raise ValueError("配置不能为空")

    def is_available(self) -> bool:
        """检查是否可用"""
        return bool(self.config.get("enabled", False))

    def send(self, content: str, **kwargs: Any) -> bool:
        """发送消息"""
        return self.is_available()

    @property
    def channel_type(self) -> NotificationChannel:
        """渠道类型"""
        return NotificationChannel.CUSTOM


class TestNotificationChannelBase:
    """测试通知渠道抽象基类"""

    def test_base_is_abstract(self) -> None:
        """测试基类是抽象的，不能直接实例化"""
        with pytest.raises(TypeError):
            NotificationChannelBase({})

    def test_concrete_channel_init(self) -> None:
        """测试具体渠道初始化"""
        config = {"enabled": True, "api_key": "test123"}
        channel = ConcreteChannel(config)

        assert channel.config == config
        assert channel.name == "自定义Webhook"

    def test_concrete_channel_validation(self) -> None:
        """测试配置验证"""
        # 空配置应该抛出异常
        with pytest.raises(ValueError, match="配置不能为空"):
            ConcreteChannel({})

    def test_is_available(self) -> None:
        """测试可用性检查"""
        enabled_channel = ConcreteChannel({"enabled": True})
        assert enabled_channel.is_available() is True

        disabled_channel = ConcreteChannel({"enabled": False})
        assert disabled_channel.is_available() is False
        # 配置非空通过验证，enabled默认为False，所以不可用

        # 注意：配置为空会抛出异常（见 test_concrete_channel_validation）
        # 所以不需要测试默认值为空的情况

    def test_send_success(self) -> None:
        """测试发送成功"""
        channel = ConcreteChannel({"enabled": True})

        result = channel.send("测试消息")
        assert result is True

    def test_send_when_unavailable(self) -> None:
        """测试渠道不可用时发送失败"""
        channel = ConcreteChannel({"enabled": False})

        result = channel.send("测试消息")
        assert result is False

    def test_channel_type_property(self) -> None:
        """测试渠道类型属性"""
        channel = ConcreteChannel({"enabled": True})

        assert channel.channel_type == NotificationChannel.CUSTOM

    def test_name_property(self) -> None:
        """测试名称属性"""
        # 测试不同渠道类型返回正确的名称
        channel = ConcreteChannel({"enabled": True})
        assert channel.name == "自定义Webhook"


# =============================================================================
# ABC 继承验证测试
# =============================================================================
class TestNotificationChannelABC:
    """验证抽象基类的正确性"""

    def test_notification_channel_base_is_abc(self) -> None:
        """验证 NotificationChannelBase 是抽象基类"""
        assert issubclass(NotificationChannelBase, ABC)

    def test_concrete_class_implements_all_abstract(self) -> None:
        """验证 ConcreteChannel 实现了所有抽象方法"""
        # 应该能够成功实例化
        channel = ConcreteChannel({"enabled": True})

        # 验证实现了所有必需的方法
        assert hasattr(channel, "_validate_config")
        assert hasattr(channel, "is_available")
        assert hasattr(channel, "send")
        assert hasattr(channel, "channel_type")
