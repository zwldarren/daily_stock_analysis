"""
===================================
Discord 平台适配器
===================================

负责：
1. 验证 Discord Webhook 请求
2. 解析 Discord 消息为统一格式
3. 将响应转换为 Discord 格式
"""

import contextlib
import logging
from datetime import datetime
from typing import Any

from ..models import BotMessage, ChatType, WebhookResponse
from .base import BotPlatform

logger = logging.getLogger(__name__)


class DiscordPlatform(BotPlatform):
    """Discord 平台适配器"""

    @property
    def platform_name(self) -> str:
        """平台标识名称"""
        return "discord"

    def verify_request(self, headers: dict[str, str], body: bytes) -> bool:
        """验证 Discord Webhook 请求签名

        Discord Webhook 签名验证：
        1. 从请求头获取 X-Signature-Ed25519 和 X-Signature-Timestamp
        2. 使用公钥验证签名

        Args:
            headers: HTTP 请求头
            body: 请求体原始字节

        Returns:
            签名是否有效
        """
        # TODO: 实现 Discord Webhook 签名验证
        # 当前暂时返回 True，后续需要完善
        return True

    def parse_message(self, data: dict[str, Any]) -> BotMessage | None:
        """解析 Discord 消息为统一格式

        Args:
            data: 解析后的 JSON 数据

        Returns:
            BotMessage 对象，或 None（不需要处理）
        """
        # 检查是否是消息事件
        if data.get("type") != 1 and data.get("type") != 2:
            return None

        # 提取消息内容
        content = data.get("content", "").strip()
        if not content:
            return None

        # 提取用户信息
        author = data.get("author", {})
        user_id = author.get("id", "")
        user_name = author.get("username", "unknown")

        # 提取频道信息
        channel_id = data.get("channel_id", "")
        guild_id = data.get("guild_id", "")

        # 提取消息 ID
        message_id = data.get("id", "")

        # 提取附件信息（如果有）
        attachments = data.get("attachments", [])

        # 解析时间戳
        timestamp_str = data.get("timestamp")
        timestamp = datetime.now()
        if timestamp_str:
            with contextlib.suppress(ValueError):
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        # 提取 mentions 为用户ID列表
        mentions_data = data.get("mentions", [])
        mention_ids = [m.get("id", "") for m in mentions_data if isinstance(m, dict)]

        # 构建 BotMessage 对象
        message = BotMessage(
            platform="discord",
            message_id=message_id,
            user_id=user_id,
            user_name=user_name,
            chat_id=channel_id or guild_id or "",
            chat_type=ChatType.GROUP if guild_id else ChatType.PRIVATE,
            content=content,
            raw_content=content,
            mentioned=data.get("mention_everyone", False),
            mentions=mention_ids,
            timestamp=timestamp,
            # 添加 Discord 特定的原始数据
            raw_data={
                "message_id": message_id,
                "channel_id": channel_id,
                "guild_id": guild_id,
                "author": author,
                "content": content,
                "timestamp": data.get("timestamp"),
                "attachments": attachments,
                "mentions": data.get("mentions", []),
                "mention_roles": data.get("mention_roles", []),
                "mention_everyone": data.get("mention_everyone", False),
                "type": data.get("type"),
            },
        )

        return message

    def format_response(self, response: Any, message: BotMessage) -> WebhookResponse:
        """将统一响应转换为 Discord 格式

        Args:
            response: 统一响应对象
            message: 原始消息对象

        Returns:
            WebhookResponse 对象
        """
        # 构建 Discord 响应格式
        discord_response = {
            "content": response.text if hasattr(response, "text") else str(response),
            "tts": False,
            "embeds": [],
            "allowed_mentions": {"parse": ["users", "roles", "everyone"]},
        }

        return WebhookResponse.success(discord_response)

    def handle_challenge(self, data: dict[str, Any]) -> WebhookResponse | None:
        """处理 Discord 验证请求

        Discord 在配置 Webhook 时会发送验证请求

        Args:
            data: 请求数据

        Returns:
            验证响应，或 None（不是验证请求）
        """
        # Discord Webhook 验证请求类型是 1
        if data.get("type") == 1:
            return WebhookResponse.success({"type": 1})

        # Discord 命令交互验证
        if "challenge" in data:
            return WebhookResponse.success({"challenge": data["challenge"]})

        return None
