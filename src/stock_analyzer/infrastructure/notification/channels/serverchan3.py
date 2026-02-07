"""
Server酱3 通知渠道

国内推送服务，支持多家国产系统推送通道，可无后台推送
"""

import logging
import re
from datetime import datetime
from typing import Any

import requests

from stock_analyzer.infrastructure.notification.base import NotificationChannel, NotificationChannelBase

logger = logging.getLogger(__name__)


class Serverchan3Channel(NotificationChannelBase):
    """Server酱3 推送渠道"""

    def __init__(self, config: dict[str, Any]):
        self.sendkey: str | None = None
        super().__init__(config)

    def _validate_config(self) -> None:
        """验证配置"""
        self.sendkey = self.config.get("sendkey")

    def is_available(self) -> bool:
        """检查配置是否完整"""
        return bool(self.sendkey)

    @property
    def channel_type(self) -> NotificationChannel:
        return NotificationChannel.SERVERCHAN3

    def send(self, content: str, **kwargs: Any) -> bool:
        """
        推送消息到 Server酱3

        Server酱3 API 格式：
        POST https://sctapi.ftqq.com/{sendkey}.send
        或
        POST https://{num}.push.ft07.com/send/{sendkey}.send
        {
            "title": "消息标题",
            "desp": "消息内容",
            "options": {}
        }

        Args:
            content: 消息内容（Markdown 格式）
            **kwargs: 可包含 title 参数指定主题

        Returns:
            是否发送成功
        """
        if not self.sendkey:
            logger.warning("Server酱3 SendKey 未配置，跳过推送")
            return False

        # 处理消息标题
        title = kwargs.get("title")
        if title is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            title = f"📈 股票分析报告 - {date_str}"

        try:
            # 根据 sendkey 格式构造 URL
            sendkey = self.sendkey
            if sendkey.startswith("sctp"):
                match = re.match(r"sctp(\d+)t", sendkey)
                if match:
                    num = match.group(1)
                    url = f"https://{num}.push.ft07.com/send/{sendkey}.send"
                else:
                    logger.error("Invalid sendkey format for sctp")
                    return False
            else:
                url = f"https://sctapi.ftqq.com/{sendkey}.send"

            # 构建请求参数
            params = {
                "title": title,
                "desp": content,
                "options": {},
            }

            # 发送请求
            headers = {"Content-Type": "application/json;charset=utf-8"}
            response = requests.post(url, json=params, headers=headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Server酱3 消息发送成功: {result}")
                return True
            else:
                logger.error(f"Server酱3 请求失败: HTTP {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False

        except Exception as e:
            logger.error(f"发送 Server酱3 消息失败: {e}")
            return False
