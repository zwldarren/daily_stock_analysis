"""
命令层（Command Layer）

职责：
1. 处理业务操作（写操作）
2. 触发领域事件
3. 保证业务规则执行

CQRS原则：命令改变状态，返回操作结果而非数据。
"""

from stock_analyzer.application.commands.analysis_commands import (
    AnalyzeStockCommand,
    BatchAnalyzeStocksCommand,
)
from stock_analyzer.application.commands.data_commands import (
    FetchStockDataCommand,
    RefreshStockDataCommand,
)

__all__ = [
    "AnalyzeStockCommand",
    "BatchAnalyzeStocksCommand",
    "FetchStockDataCommand",
    "RefreshStockDataCommand",
]
