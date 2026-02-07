"""
市场快照构建模块

负责构建股票行情快照数据
"""

from typing import Any

from stock_analyzer.technical.formatter import ResultFormatter


class MarketSnapshotBuilder:
    """市场快照构建器"""

    @staticmethod
    def build(context: dict[str, Any]) -> dict[str, Any]:
        """构建当日行情快照"""
        today = context.get("today", {}) or {}
        realtime = context.get("realtime", {}) or {}
        yesterday = context.get("yesterday", {}) or {}

        prev_close = yesterday.get("close")
        close = today.get("close")
        high = today.get("high")
        low = today.get("low")

        amplitude = None
        change_amount = None
        if prev_close not in (None, 0) and high is not None and low is not None:
            try:
                amplitude = (float(high) - float(low)) / float(prev_close) * 100
            except TypeError, ValueError, ZeroDivisionError:
                amplitude = None
        if prev_close is not None and close is not None:
            try:
                change_amount = float(close) - float(prev_close)
            except TypeError, ValueError:
                change_amount = None

        snapshot = {
            "date": context.get("date", "未知"),
            "close": MarketSnapshotBuilder._format_price(close),
            "open": MarketSnapshotBuilder._format_price(today.get("open")),
            "high": MarketSnapshotBuilder._format_price(high),
            "low": MarketSnapshotBuilder._format_price(low),
            "prev_close": MarketSnapshotBuilder._format_price(prev_close),
            "pct_chg": MarketSnapshotBuilder._format_percent(today.get("pct_chg")),
            "change_amount": MarketSnapshotBuilder._format_price(change_amount),
            "amplitude": MarketSnapshotBuilder._format_percent(amplitude),
            "volume": ResultFormatter.format_volume(today.get("volume")),
            "amount": ResultFormatter.format_amount(today.get("amount")),
        }

        if realtime:
            snapshot.update(
                {
                    "price": MarketSnapshotBuilder._format_price(realtime.get("price")),
                    "volume_ratio": realtime.get("volume_ratio", "N/A"),
                    "turnover_rate": MarketSnapshotBuilder._format_percent(realtime.get("turnover_rate")),
                    "source": getattr(realtime.get("source"), "value", realtime.get("source", "N/A")),
                }
            )

        return snapshot

    @staticmethod
    def _format_price(value: float | None) -> str:
        """格式化价格显示"""
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.2f}"
        except TypeError, ValueError:
            return "N/A"

    @staticmethod
    def _format_percent(value: float | None) -> str:
        """格式化百分比显示"""
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.2f}%"
        except TypeError, ValueError:
            return "N/A"
