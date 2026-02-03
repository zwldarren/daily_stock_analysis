"""
===================================
命令处理器模块
===================================

包含所有机器人命令的实现。
"""

from stock_analyzer.bot.commands.analyze import AnalyzeCommand
from stock_analyzer.bot.commands.base import BotCommand
from stock_analyzer.bot.commands.batch import BatchCommand
from stock_analyzer.bot.commands.help import HelpCommand
from stock_analyzer.bot.commands.market import MarketCommand
from stock_analyzer.bot.commands.status import StatusCommand

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
