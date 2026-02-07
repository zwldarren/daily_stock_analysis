"""
趋势分析器

负责分析趋势状态、乖离率、量能等
"""

import logging

import pandas as pd

from stock_analyzer.technical.enums import TrendStatus, VolumeStatus
from stock_analyzer.technical.result import TrendAnalysisResult

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """趋势分析器"""

    BIAS_THRESHOLD = 5.0  # 乖离率阈值（%）
    VOLUME_SHRINK_RATIO = 0.7  # 缩量判断阈值
    VOLUME_HEAVY_RATIO = 1.5  # 放量判断阈值
    MA_SUPPORT_TOLERANCE = 0.02  # MA 支撑判断容忍度（2%）

    @staticmethod
    def get_ma_status(close: float, ma5: float, ma10: float, ma20: float) -> str:
        """
        获取均线状态描述

        Args:
            close: 当前价格
            ma5: MA5 值
            ma10: MA10 值
            ma20: MA20 值

        Returns:
            均线状态描述字符串
        """
        close = close or 0
        ma5 = ma5 or 0
        ma10 = ma10 or 0
        ma20 = ma20 or 0

        if close > ma5 > ma10 > ma20 > 0:
            return "多头排列 📈"
        elif close < ma5 < ma10 < ma20 and ma20 > 0:
            return "空头排列 📉"
        elif close > ma5 and ma5 > ma10:
            return "短期向好 🔼"
        elif close < ma5 and ma5 < ma10:
            return "短期走弱 🔽"
        else:
            return "震荡整理 ↔️"

    @staticmethod
    def analyze_trend(df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析趋势状态

        核心逻辑：判断均线排列和趋势强度
        """
        ma5, ma10, ma20 = result.ma5, result.ma10, result.ma20

        # 判断均线排列
        if ma5 > ma10 > ma20:
            # 检查间距是否在扩大（强势）
            prev = df.iloc[-5] if len(df) >= 5 else df.iloc[-1]
            prev_spread = (prev["MA5"] - prev["MA20"]) / prev["MA20"] * 100 if prev["MA20"] > 0 else 0
            curr_spread = (ma5 - ma20) / ma20 * 100 if ma20 > 0 else 0

            if curr_spread > prev_spread and curr_spread > 5:
                result.trend_status = TrendStatus.STRONG_BULL
                result.ma_alignment = "强势多头排列，均线发散上行"
                result.trend_strength = 90
            else:
                result.trend_status = TrendStatus.BULL
                result.ma_alignment = "多头排列 MA5>MA10>MA20"
                result.trend_strength = 75

        elif ma5 > ma10 and ma10 <= ma20:
            result.trend_status = TrendStatus.WEAK_BULL
            result.ma_alignment = "弱势多头，MA5>MA10 但 MA10≤MA20"
            result.trend_strength = 55

        elif ma5 < ma10 < ma20:
            prev = df.iloc[-5] if len(df) >= 5 else df.iloc[-1]
            prev_spread = (prev["MA20"] - prev["MA5"]) / prev["MA5"] * 100 if prev["MA5"] > 0 else 0
            curr_spread = (ma20 - ma5) / ma5 * 100 if ma5 > 0 else 0

            if curr_spread > prev_spread and curr_spread > 5:
                result.trend_status = TrendStatus.STRONG_BEAR
                result.ma_alignment = "强势空头排列，均线发散下行"
                result.trend_strength = 10
            else:
                result.trend_status = TrendStatus.BEAR
                result.ma_alignment = "空头排列 MA5<MA10<MA20"
                result.trend_strength = 25

        elif ma5 < ma10 and ma10 >= ma20:
            result.trend_status = TrendStatus.WEAK_BEAR
            result.ma_alignment = "弱势空头，MA5<MA10 但 MA10≥MA20"
            result.trend_strength = 40

        else:
            result.trend_status = TrendStatus.CONSOLIDATION
            result.ma_alignment = "均线缠绕，趋势不明"
            result.trend_strength = 50

    @staticmethod
    def calculate_bias(result: TrendAnalysisResult) -> None:
        """
        计算乖离率

        乖离率 = (现价 - 均线) / 均线 * 100%
        """
        price = result.current_price

        if result.ma5 > 0:
            result.bias_ma5 = (price - result.ma5) / result.ma5 * 100
        if result.ma10 > 0:
            result.bias_ma10 = (price - result.ma10) / result.ma10 * 100
        if result.ma20 > 0:
            result.bias_ma20 = (price - result.ma20) / result.ma20 * 100

    @staticmethod
    def analyze_volume(df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析量能

        偏好：缩量回调 > 放量上涨 > 缩量上涨 > 放量下跌
        """
        if len(df) < 5:
            return

        latest = df.iloc[-1]
        vol_5d_avg = df["volume"].iloc[-6:-1].mean()

        if vol_5d_avg > 0:
            result.volume_ratio_5d = float(latest["volume"]) / vol_5d_avg

        # 判断价格变化
        prev_close = df.iloc[-2]["close"]
        price_change = (latest["close"] - prev_close) / prev_close * 100

        # 量能状态判断
        if result.volume_ratio_5d >= TrendAnalyzer.VOLUME_HEAVY_RATIO:
            if price_change > 0:
                result.volume_status = VolumeStatus.HEAVY_VOLUME_UP
                result.volume_trend = "放量上涨，多头力量强劲"
            else:
                result.volume_status = VolumeStatus.HEAVY_VOLUME_DOWN
                result.volume_trend = "放量下跌，注意风险"
        elif result.volume_ratio_5d <= TrendAnalyzer.VOLUME_SHRINK_RATIO:
            if price_change > 0:
                result.volume_status = VolumeStatus.SHRINK_VOLUME_UP
                result.volume_trend = "缩量上涨，上攻动能不足"
            else:
                result.volume_status = VolumeStatus.SHRINK_VOLUME_DOWN
                result.volume_trend = "缩量回调，洗盘特征明显（好）"
        else:
            result.volume_status = VolumeStatus.NORMAL
            result.volume_trend = "量能正常"

    @staticmethod
    def analyze_support_resistance(df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """
        分析支撑压力位

        买点偏好：回踩 MA5/MA10 获得支撑
        """
        price = result.current_price

        # 检查是否在 MA5 附近获得支撑
        if result.ma5 > 0:
            ma5_distance = abs(price - result.ma5) / result.ma5
            if ma5_distance <= TrendAnalyzer.MA_SUPPORT_TOLERANCE and price >= result.ma5:
                result.support_ma5 = True
                result.support_levels.append(result.ma5)

        # 检查是否在 MA10 附近获得支撑
        if result.ma10 > 0:
            ma10_distance = abs(price - result.ma10) / result.ma10
            if ma10_distance <= TrendAnalyzer.MA_SUPPORT_TOLERANCE and price >= result.ma10:
                result.support_ma10 = True
                if result.ma10 not in result.support_levels:
                    result.support_levels.append(result.ma10)

        # MA20 作为重要支撑
        if result.ma20 > 0 and price >= result.ma20:
            result.support_levels.append(result.ma20)

        # 近期高点作为压力
        if len(df) >= 20:
            recent_high = df["high"].iloc[-20:].max()
            if recent_high > price:
                result.resistance_levels.append(recent_high)
