"""
===================================
命令处理器模块
===================================

包含所有机器人命令的实现。
"""

from .analyze import AnalyzeCommand
from .base import BotCommand
from .batch import BatchCommand
from .help import HelpCommand
from .market import MarketCommand
from .status import StatusCommand

# 所有可用命令（用于自动注册）
ALL_COMMANDS = [
    HelpCommand,
    StatusCommand,
    AnalyzeCommand,
    MarketCommand,
    BatchCommand,
]

__all__ = [
    "BotCommand",
    "HelpCommand",
    "StatusCommand",
    "AnalyzeCommand",
    "MarketCommand",
    "BatchCommand",
    "ALL_COMMANDS",
]
