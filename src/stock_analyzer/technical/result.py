"""
趋势分析结果数据类
"""

from dataclasses import dataclass, field
from typing import Any

from stock_analyzer.technical.enums import (
    BuySignal,
    MACDStatus,
    RSIStatus,
    TrendStatus,
    VolumeStatus,
)


@dataclass
class TrendAnalysisResult:
    """趋势分析结果"""

    code: str

    # 趋势判断
    trend_status: TrendStatus = TrendStatus.CONSOLIDATION
    ma_alignment: str = ""  # 均线排列描述
    trend_strength: float = 0.0  # 趋势强度 0-100

    # 均线数据
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    current_price: float = 0.0

    # 乖离率（与 MA5 的偏离度）
    bias_ma5: float = 0.0  # (Close - MA5) / MA5 * 100
    bias_ma10: float = 0.0
    bias_ma20: float = 0.0

    # 量能分析
    volume_status: VolumeStatus = VolumeStatus.NORMAL
    volume_ratio_5d: float = 0.0  # 当日成交量/5日均量
    volume_trend: str = ""  # 量能趋势描述

    # 支撑压力
    support_ma5: bool = False  # MA5 是否构成支撑
    support_ma10: bool = False  # MA10 是否构成支撑
    resistance_levels: list[float] = field(default_factory=list)
    support_levels: list[float] = field(default_factory=list)

    # MACD 指标
    macd_dif: float = 0.0  # DIF 快线
    macd_dea: float = 0.0  # DEA 慢线
    macd_bar: float = 0.0  # MACD 柱状图
    macd_status: MACDStatus = MACDStatus.BULLISH
    macd_signal: str = ""  # MACD 信号描述

    # RSI 指标
    rsi_6: float = 0.0  # RSI(6) 短期
    rsi_12: float = 0.0  # RSI(12) 中期
    rsi_24: float = 0.0  # RSI(24) 长期
    rsi_status: RSIStatus = RSIStatus.NEUTRAL
    rsi_signal: str = ""  # RSI 信号描述

    # 买入信号
    buy_signal: BuySignal = BuySignal.WAIT
    signal_score: int = 0  # 综合评分 0-100
    signal_reasons: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "trend_status": self.trend_status.value,
            "ma_alignment": self.ma_alignment,
            "trend_strength": self.trend_strength,
            "ma5": self.ma5,
            "ma10": self.ma10,
            "ma20": self.ma20,
            "ma60": self.ma60,
            "current_price": self.current_price,
            "bias_ma5": self.bias_ma5,
            "bias_ma10": self.bias_ma10,
            "bias_ma20": self.bias_ma20,
            "volume_status": self.volume_status.value,
            "volume_ratio_5d": self.volume_ratio_5d,
            "volume_trend": self.volume_trend,
            "support_ma5": self.support_ma5,
            "support_ma10": self.support_ma10,
            "buy_signal": self.buy_signal.value,
            "signal_score": self.signal_score,
            "signal_reasons": self.signal_reasons,
            "risk_factors": self.risk_factors,
            "macd_dif": self.macd_dif,
            "macd_dea": self.macd_dea,
            "macd_bar": self.macd_bar,
            "macd_status": self.macd_status.value,
            "macd_signal": self.macd_signal,
            "rsi_6": self.rsi_6,
            "rsi_12": self.rsi_12,
            "rsi_24": self.rsi_24,
            "rsi_status": self.rsi_status.value,
            "rsi_signal": self.rsi_signal,
        }
