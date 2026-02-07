"""
飞书(Feishu)集成模块

提供飞书云文档管理、消息格式化等功能
"""

from stock_analyzer.infrastructure.external.feishu.doc_manager import FeishuDocManager
from stock_analyzer.infrastructure.external.feishu.formatters import (
    chunk_feishu_content,
    format_feishu_markdown,
)

__all__ = [
    "FeishuDocManager",
    "format_feishu_markdown",
    "chunk_feishu_content",
]
