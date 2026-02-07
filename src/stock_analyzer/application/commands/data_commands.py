"""
数据操作命令

职责：
1. 获取股票数据
2. 刷新数据
3. 数据同步

不涉及AI分析，纯数据操作。
"""

import logging
from typing import Any

from stock_analyzer.application.dto import CommandResult
from stock_analyzer.domain.repositories import IStockRepository

logger = logging.getLogger(__name__)


class FetchStockDataCommand:
    """
    命令：获取并保存股票数据

    职责：
    1. 从数据源获取日线数据
    2. 保存到本地数据库
    3. 实现断点续传逻辑

    使用示例：
        cmd = FetchStockDataCommand(data_service, stock_repo)
        result = cmd.execute("000001", force_refresh=False)
    """

    def __init__(
        self,
        data_service: Any,
        stock_repo: IStockRepository,
    ) -> None:
        self._data_service = data_service
        self._stock_repo = stock_repo

    def execute(
        self,
        stock_code: str,
        days: int = 30,
        force_refresh: bool = False,
    ) -> CommandResult:
        """
        执行数据获取命令

        Args:
            stock_code: 股票代码
            days: 获取天数
            force_refresh: 是否强制刷新（忽略本地缓存）

        Returns:
            CommandResult
        """
        try:
            # 断点续传检查
            if not force_refresh:
                # 检查数据库是否已有今日数据
                # 这里简化处理，实际可以通过repo查询最新日期
                pass

            # 从数据源获取
            df, source = self._data_service.get_daily_data(stock_code, days=days, use_cache=not force_refresh)

            if df is None or df.empty:
                return CommandResult(success=False, message=f"获取 {stock_code} 数据为空")

            # 保存到本地
            saved_count = self._stock_repo.save_daily_data(df=df, stock_code=stock_code, data_source=source)

            logger.info(f"[Command] {stock_code} 数据获取完成: 来源={source}, 保存={saved_count}条")

            return CommandResult(
                success=True,
                message=f"数据获取成功，保存 {saved_count} 条",
                data={"source": source, "count": saved_count},
            )

        except Exception as e:
            error_msg = f"获取 {stock_code} 数据失败: {str(e)}"
            logger.exception(error_msg)
            return CommandResult(success=False, message=error_msg)


class RefreshStockDataCommand:
    """
    命令：刷新股票数据

    强制从外部数据源刷新，忽略本地缓存。
    """

    def __init__(self, fetch_command: FetchStockDataCommand) -> None:
        self._fetch_command = fetch_command

    def execute(
        self,
        stock_code: str,
        days: int = 30,
    ) -> CommandResult:
        """
        执行刷新命令

        Args:
            stock_code: 股票代码
            days: 获取天数

        Returns:
            CommandResult
        """
        logger.info(f"[Command] 强制刷新 {stock_code} 数据")

        return self._fetch_command.execute(stock_code=stock_code, days=days, force_refresh=True)
