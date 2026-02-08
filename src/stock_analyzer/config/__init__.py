"""
Configuration management module.

Provides type-safe, validated configuration management following DDD principles.
The config module is kept pure without infrastructure dependencies.
Database storage is handled separately in infrastructure.config.
"""

from stock_analyzer.config.config import (
    AIConfig,
    BotConfig,
    Config,
    DatabaseConfig,
    DingtalkBotConfig,
    FeishuBotConfig,
    FeishuDocConfig,
    LoggingConfig,
    NotificationChannelConfig,
    NotificationMessageConfig,
    RealtimeQuoteConfig,
    ScheduleConfig,
    SearchConfig,
    SystemConfig,
    check_config_valid,
    get_config,
    get_config_safe,
    get_project_root,
)
from stock_analyzer.config.interfaces import IConfigStorage
from stock_analyzer.config.storage import (
    ConfigConverter,
    ConfigStorage,
    load_merged_config,
)

__all__ = [
    # Main config
    "Config",
    "get_config",
    "get_config_safe",
    "check_config_valid",
    "get_project_root",
    # File-based storage
    "ConfigStorage",
    "ConfigConverter",
    "load_merged_config",
    # Interface
    "IConfigStorage",
    # Nested configs
    "AIConfig",
    "SearchConfig",
    "NotificationChannelConfig",
    "NotificationMessageConfig",
    "DatabaseConfig",
    "LoggingConfig",
    "SystemConfig",
    "ScheduleConfig",
    "RealtimeQuoteConfig",
    "BotConfig",
    "FeishuBotConfig",
    "DingtalkBotConfig",
    "FeishuDocConfig",
]
