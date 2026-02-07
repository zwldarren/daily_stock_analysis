"""
趋势分析枚举定义
"""

from enum import Enum


class TrendStatus(Enum):
    """趋势状态枚举"""

    STRONG_BULL = "强势多头"  # MA5 > MA10 > MA20，且间距扩大
    BULL = "多头排列"  # MA5 > MA10 > MA20
    WEAK_BULL = "弱势多头"  # MA5 > MA10，但 MA10 < MA20
    CONSOLIDATION = "盘整"  # 均线缠绕
    WEAK_BEAR = "弱势空头"  # MA5 < MA10，但 MA10 > MA20
    BEAR = "空头排列"  # MA5 < MA10 < MA20
    STRONG_BEAR = "强势空头"  # MA5 < MA10 < MA20，且间距扩大


class VolumeStatus(Enum):
    """量能状态枚举"""

    HEAVY_VOLUME_UP = "放量上涨"  # 量价齐升
    HEAVY_VOLUME_DOWN = "放量下跌"  # 放量杀跌
    SHRINK_VOLUME_UP = "缩量上涨"  # 无量上涨
    SHRINK_VOLUME_DOWN = "缩量回调"  # 缩量回调（好）
    NORMAL = "量能正常"


class BuySignal(Enum):
    """买入信号枚举"""

    STRONG_BUY = "强烈买入"  # 多条件满足
    BUY = "买入"  # 基本条件满足
    HOLD = "持有"  # 已持有可继续
    WAIT = "观望"  # 等待更好时机
    SELL = "卖出"  # 趋势转弱
    STRONG_SELL = "强烈卖出"  # 趋势破坏


class MACDStatus(Enum):
    """MACD状态枚举"""

    GOLDEN_CROSS_ZERO = "零轴上金叉"  # DIF上穿DEA，且在零轴上方
    GOLDEN_CROSS = "金叉"  # DIF上穿DEA
    BULLISH = "多头"  # DIF>DEA>0
    CROSSING_UP = "上穿零轴"  # DIF上穿零轴
    CROSSING_DOWN = "下穿零轴"  # DIF下穿零轴
    BEARISH = "空头"  # DIF<DEA<0
    DEATH_CROSS = "死叉"  # DIF下穿DEA


class RSIStatus(Enum):
    """RSI状态枚举"""

    OVERBOUGHT = "超买"  # RSI > 70
    STRONG_BUY = "强势买入"  # 50 < RSI < 70
    NEUTRAL = "中性"  # 40 <= RSI <= 60
    WEAK = "弱势"  # 30 < RSI < 40
    OVERSOLD = "超卖"  # RSI < 30
