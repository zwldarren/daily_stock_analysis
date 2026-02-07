"""
基础设施层 - 技术实现细节

该模块包含：
- 外部服务集成 (external)
- 通知渠道 (notification)
- 数据持久化 (persistence)
- 机器人平台 (bot)
- 缓存 (cache)
"""

from stock_analyzer.infrastructure.external.feishu import FeishuDocManager
from stock_analyzer.infrastructure.external.search import SearchService
from stock_analyzer.infrastructure.notification import NotificationService
from stock_analyzer.infrastructure.persistence import get_db

__all__ = [
    "FeishuDocManager",
    "NotificationService",
    "SearchService",
    "get_db",
]
