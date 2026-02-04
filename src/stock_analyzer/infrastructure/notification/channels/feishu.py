"""
飞书通知渠道
"""

import logging
import time
from typing import Any

import requests

from stock_analyzer.formatters import format_feishu_markdown

from ..base import NotificationChannel, NotificationChannelBase

logger = logging.getLogger(__name__)


class FeishuChannel(NotificationChannelBase):
    """飞书 Webhook 通知渠道"""

    def __init__(self, config: dict[str, Any]):
        self.webhook_url: str | None = None
        self.max_bytes: int = 20000
        super().__init__(config)

    def _validate_config(self) -> None:
        """验证配置"""
        self.webhook_url = self.config.get("webhook_url")
        self.max_bytes = self.config.get("max_bytes", 20000)

    def is_available(self) -> bool:
        """检查配置是否完整"""
        return bool(self.webhook_url)

    @property
    def channel_type(self) -> NotificationChannel:
        return NotificationChannel.FEISHU

    def send(self, content: str, **kwargs: Any) -> bool:
        """
        发送消息到飞书

        Args:
            content: Markdown 格式的消息内容

        Returns:
            是否发送成功
        """
        if not self.webhook_url:
            logger.warning("飞书 Webhook 未配置，跳过推送")
            return False

        # 飞书 lark_md 支持有限，先做格式转换
        formatted_content = format_feishu_markdown(content)

        # 检查字节长度，超长则分批发送
        content_bytes = len(formatted_content.encode("utf-8"))
        if content_bytes > self.max_bytes:
            logger.info(f"飞书消息内容超长({content_bytes}字节/{len(content)}字符)，将分批发送")
            return self._send_chunked(formatted_content)

        try:
            return self._send_message(formatted_content)
        except Exception as e:
            logger.error(f"发送飞书消息失败: {e}")
            return False

    def _send_chunked(self, content: str) -> bool:
        """分批发送长消息"""

        def get_bytes(s: str) -> int:
            return len(s.encode("utf-8"))

        # 智能分割
        if "\n---\n" in content:
            sections = content.split("\n---\n")
            separator = "\n---\n"
        elif "\n### " in content:
            parts = content.split("\n### ")
            sections = [parts[0]] + [f"### {p}" for p in parts[1:]]
            separator = "\n"
        else:
            return self._send_force_chunked(content)

        chunks = []
        current_chunk = []
        current_bytes = 0
        separator_bytes = get_bytes(separator)

        for section in sections:
            section_bytes = get_bytes(section) + separator_bytes

            if section_bytes > self.max_bytes:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_bytes = 0

                truncated = self._truncate_to_bytes(section, self.max_bytes - 200)
                truncated += "\n\n...(本段内容过长已截断)"
                chunks.append(truncated)
                continue

            if current_bytes + section_bytes > self.max_bytes:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                current_chunk = [section]
                current_bytes = section_bytes
            else:
                current_chunk.append(section)
                current_bytes += section_bytes

        if current_chunk:
            chunks.append(separator.join(current_chunk))

        # 分批发送
        total_chunks = len(chunks)
        success_count = 0

        logger.info(f"飞书分批发送：共 {total_chunks} 批")

        for i, chunk in enumerate(chunks):
            if total_chunks > 1:
                page_marker = f"\n\n📄 ({i + 1}/{total_chunks})"
                chunk_with_marker = chunk + page_marker
            else:
                chunk_with_marker = chunk

            try:
                if self._send_message(chunk_with_marker):
                    success_count += 1
                    logger.info(f"飞书第 {i + 1}/{total_chunks} 批发送成功")
                else:
                    logger.error(f"飞书第 {i + 1}/{total_chunks} 批发送失败")
            except Exception as e:
                logger.error(f"飞书第 {i + 1}/{total_chunks} 批发送异常: {e}")

            if i < total_chunks - 1:
                time.sleep(1)

        return success_count == total_chunks

    def _send_force_chunked(self, content: str) -> bool:
        """强制按字节分割发送"""
        chunks = []
        current_chunk = ""
        lines = content.split("\n")

        for line in lines:
            test_chunk = current_chunk + ("\n" if current_chunk else "") + line
            if len(test_chunk.encode("utf-8")) > self.max_bytes - 100:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk = test_chunk

        if current_chunk:
            chunks.append(current_chunk)

        total_chunks = len(chunks)
        success_count = 0

        logger.info(f"飞书强制分批发送：共 {total_chunks} 批")

        for i, chunk in enumerate(chunks):
            page_marker = f"\n\n📄 ({i + 1}/{total_chunks})" if total_chunks > 1 else ""

            try:
                if self._send_message(chunk + page_marker):
                    success_count += 1
            except Exception as e:
                logger.error(f"飞书第 {i + 1}/{total_chunks} 批发送异常: {e}")

            if i < total_chunks - 1:
                time.sleep(1)

        return success_count == total_chunks

    def _truncate_to_bytes(self, text: str, max_bytes: int) -> str:
        """按字节数截断字符串"""
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text

        truncated = encoded[:max_bytes]
        while truncated:
            try:
                return truncated.decode("utf-8")
            except UnicodeDecodeError:
                truncated = truncated[:-1]
        return ""

    def _send_message(self, content: str) -> bool:
        """发送单条飞书消息"""

        def _post_payload(payload: dict[str, Any]) -> bool:
            logger.debug(f"飞书请求 payload 长度: {len(content)} 字符")

            response = requests.post(self.webhook_url, json=payload, timeout=30)

            logger.debug(f"飞书响应状态码: {response.status_code}")
            logger.debug(f"飞书响应内容: {response.text}")

            if response.status_code == 200:
                result = response.json()
                code = result.get("code") if "code" in result else result.get("StatusCode")
                if code == 0:
                    logger.info("飞书消息发送成功")
                    return True
                else:
                    error_msg = result.get("msg") or result.get("StatusMessage", "未知错误")
                    error_code = result.get("code") or result.get("StatusCode", "N/A")
                    logger.error(f"飞书返回错误 [code={error_code}]: {error_msg}")
                    return False
            else:
                logger.error(f"飞书请求失败: HTTP {response.status_code}")
                return False

        # 优先使用交互卡片
        card_payload = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {"title": {"tag": "plain_text", "content": "A股智能分析报告"}},
                "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": content}}],
            },
        }

        if _post_payload(card_payload):
            return True

        # 回退为普通文本消息
        text_payload = {"msg_type": "text", "content": {"text": content}}
        return _post_payload(text_payload)
