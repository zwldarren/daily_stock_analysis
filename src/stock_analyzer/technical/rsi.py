"""
RSI分析器
"""

import pandas as pd

from stock_analyzer.technical.calculator import IndicatorCalculator
from stock_analyzer.technical.enums import RSIStatus
from stock_analyzer.technical.result import TrendAnalysisResult


class RSIAnalyzer:
    """RSI分析器"""

    # RSI 参数从 IndicatorCalculator 导入，避免重复定义
    RSI_SHORT = IndicatorCalculator.RSI_SHORT  # 短期RSI周期
    RSI_MID = IndicatorCalculator.RSI_MID  # 中期RSI周期
    RSI_LONG = IndicatorCalculator.RSI_LONG  # 长期RSI周期
    RSI_OVERBOUGHT = 70  # 超买阈值
    RSI_OVERSOLD = 30  # 超卖阈值

    @staticmethod
    def analyze(df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析 RSI 指标

        核心判断：
        - RSI > 70：超买，谨慎追高
        - RSI < 30：超卖，关注反弹
        - 40-60：中性区域
        """
        if len(df) < RSIAnalyzer.RSI_LONG:
            result.rsi_signal = "数据不足"
            return

        latest = df.iloc[-1]

        # 获取 RSI 数据
        result.rsi_6 = float(latest[f"RSI_{RSIAnalyzer.RSI_SHORT}"])
        result.rsi_12 = float(latest[f"RSI_{RSIAnalyzer.RSI_MID}"])
        result.rsi_24 = float(latest[f"RSI_{RSIAnalyzer.RSI_LONG}"])

        # 以中期 RSI(12) 为主进行判断
        rsi_mid = result.rsi_12

        # 判断 RSI 状态
        if rsi_mid > RSIAnalyzer.RSI_OVERBOUGHT:
            result.rsi_status = RSIStatus.OVERBOUGHT
            result.rsi_signal = f"⚠️ RSI超买({rsi_mid:.1f}>70)，短期回调风险高"
        elif rsi_mid > 60:
            result.rsi_status = RSIStatus.STRONG_BUY
            result.rsi_signal = f"✅ RSI强势({rsi_mid:.1f})，多头力量充足"
        elif rsi_mid >= 40:
            result.rsi_status = RSIStatus.NEUTRAL
            result.rsi_signal = f" RSI中性({rsi_mid:.1f})，震荡整理中"
        elif rsi_mid >= RSIAnalyzer.RSI_OVERSOLD:
            result.rsi_status = RSIStatus.WEAK
            result.rsi_signal = f"⚡ RSI弱势({rsi_mid:.1f})，关注反弹"
        else:
            result.rsi_status = RSIStatus.OVERSOLD
            result.rsi_signal = f"⭐ RSI超卖({rsi_mid:.1f}<30)，反弹机会大"
