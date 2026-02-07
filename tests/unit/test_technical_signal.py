"""
Unit tests for signal generator module.

Tests cover:
- Buy signal generation based on trend, bias, volume, MACD, and RSI
- Signal scoring system
- Risk factor identification
"""

import pytest

from stock_analyzer.technical.enums import (
    BuySignal,
    MACDStatus,
    RSIStatus,
    TrendStatus,
    VolumeStatus,
)
from stock_analyzer.technical.result import TrendAnalysisResult
from stock_analyzer.technical.signal import SignalGenerator


# =============================================================================
# Signal Generation Tests
# =============================================================================
class TestSignalGenerator:
    """Test cases for signal generator."""

    @pytest.fixture
    def base_result(self) -> TrendAnalysisResult:
        """Create a base result with neutral values."""
        result = TrendAnalysisResult(code="600519")
        result.current_price = 100.0
        result.ma5 = 100.0
        result.ma10 = 99.0
        result.ma20 = 98.0
        result.trend_status = TrendStatus.CONSOLIDATION
        result.ma_alignment = "均线缠绕"
        result.trend_strength = 50.0
        result.bias_ma5 = 0.0
        result.bias_ma10 = 1.0
        result.bias_ma20 = 2.0
        result.volume_status = VolumeStatus.NORMAL
        result.volume_ratio_5d = 1.0
        result.volume_trend = "量能正常"
        result.support_ma5 = False
        result.support_ma10 = False
        result.macd_status = MACDStatus.BULLISH
        result.macd_signal = "多头"
        result.rsi_status = RSIStatus.NEUTRAL
        result.rsi_signal = "RSI中性"
        return result

    def test_strong_bull_trend_score(self, base_result: TrendAnalysisResult) -> None:
        """Test trend scoring for strong bull."""
        base_result.trend_status = TrendStatus.STRONG_BULL
        SignalGenerator.generate(base_result)

        # Strong bull should get 30 points for trend
        assert base_result.signal_score >= 30
        assert "强势多头" in base_result.signal_reasons[0]

    def test_bear_trend_risk(self, base_result: TrendAnalysisResult) -> None:
        """Test risk detection for bear trend."""
        base_result.trend_status = TrendStatus.BEAR
        SignalGenerator.generate(base_result)

        # Bear trend should add risk factor
        assert any("空头排列" in risk for risk in base_result.risk_factors)

    def test_bias_negative_close_to_ma5(self, base_result: TrendAnalysisResult) -> None:
        """Test bias scoring when price is slightly below MA5."""
        base_result.bias_ma5 = -1.0  # Slightly below MA5
        SignalGenerator.generate(base_result)

        # Should get high score for being close to MA5
        assert any("回踩买点" in reason for reason in base_result.signal_reasons)

    def test_bias_positive_close_to_ma5(self, base_result: TrendAnalysisResult) -> None:
        """Test bias scoring when price is slightly above MA5."""
        base_result.bias_ma5 = 1.0  # Slightly above MA5
        SignalGenerator.generate(base_result)

        # Should recognize good entry point
        assert any("贴近MA5" in reason for reason in base_result.signal_reasons)

    def test_bias_high_risk(self, base_result: TrendAnalysisResult) -> None:
        """Test risk detection for high bias (> 5%)."""
        base_result.bias_ma5 = 6.0  # More than 5% above MA5
        SignalGenerator.generate(base_result)

        # Should warn about chasing high prices
        assert any("乖离率过高" in risk for risk in base_result.risk_factors)
        assert any("严禁追高" in risk for risk in base_result.risk_factors)

    def test_shrink_volume_down_best(self, base_result: TrendAnalysisResult) -> None:
        """Test volume scoring for shrink volume down (best case)."""
        base_result.volume_status = VolumeStatus.SHRINK_VOLUME_DOWN
        SignalGenerator.generate(base_result)

        # Should recognize as good sign
        assert any("缩量回调" in reason for reason in base_result.signal_reasons)

    def test_heavy_volume_down_risk(self, base_result: TrendAnalysisResult) -> None:
        """Test risk detection for heavy volume down."""
        base_result.volume_status = VolumeStatus.HEAVY_VOLUME_DOWN
        SignalGenerator.generate(base_result)

        # Should warn about heavy volume decline
        assert any("放量下跌" in risk for risk in base_result.risk_factors)

    def test_ma5_support(self, base_result: TrendAnalysisResult) -> None:
        """Test support scoring for MA5."""
        base_result.support_ma5 = True
        SignalGenerator.generate(base_result)

        # Should recognize MA5 support
        assert any("MA5支撑有效" in reason for reason in base_result.signal_reasons)

    def test_ma10_support(self, base_result: TrendAnalysisResult) -> None:
        """Test support scoring for MA10."""
        base_result.support_ma10 = True
        SignalGenerator.generate(base_result)

        # Should recognize MA10 support
        assert any("MA10支撑有效" in reason for reason in base_result.signal_reasons)

    def test_macd_golden_cross_zero(self, base_result: TrendAnalysisResult) -> None:
        """Test MACD scoring for golden cross above zero."""
        base_result.macd_status = MACDStatus.GOLDEN_CROSS_ZERO
        base_result.macd_signal = "零轴上金叉"
        SignalGenerator.generate(base_result)

        # Should recognize as strong signal with checkmark prefix
        assert any("零轴上金叉" in reason for reason in base_result.signal_reasons)

    def test_macd_death_cross_risk(self, base_result: TrendAnalysisResult) -> None:
        """Test risk detection for MACD death cross."""
        base_result.macd_status = MACDStatus.DEATH_CROSS
        base_result.macd_signal = "死叉"
        SignalGenerator.generate(base_result)

        # Should warn about death cross
        assert any("死叉" in risk for risk in base_result.risk_factors)

    def test_rsi_oversold(self, base_result: TrendAnalysisResult) -> None:
        """Test RSI scoring for oversold condition."""
        base_result.rsi_status = RSIStatus.OVERSOLD
        base_result.rsi_signal = "RSI超卖"
        SignalGenerator.generate(base_result)

        # Should recognize oversold as opportunity
        assert any("RSI超卖" in reason for reason in base_result.signal_reasons)

    def test_rsi_overbought_risk(self, base_result: TrendAnalysisResult) -> None:
        """Test risk detection for RSI overbought."""
        base_result.rsi_status = RSIStatus.OVERBOUGHT
        base_result.rsi_signal = "RSI超买"
        SignalGenerator.generate(base_result)

        # Should warn about overbought condition
        assert any("RSI超买" in risk for risk in base_result.risk_factors)


# =============================================================================
# Buy Signal Classification Tests
# =============================================================================
class TestBuySignalClassification:
    """Test cases for buy signal classification."""

    @pytest.fixture
    def strong_buy_result(self) -> TrendAnalysisResult:
        """Create a result that should trigger strong buy."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.STRONG_BULL
        result.bias_ma5 = -1.0
        result.volume_status = VolumeStatus.SHRINK_VOLUME_DOWN
        result.support_ma5 = True
        result.support_ma10 = True
        result.macd_status = MACDStatus.GOLDEN_CROSS_ZERO
        result.macd_signal = "零轴上金叉"
        result.rsi_status = RSIStatus.OVERSOLD
        result.rsi_signal = "RSI超卖"
        return result

    def test_strong_buy_signal(self, strong_buy_result: TrendAnalysisResult) -> None:
        """Test strong buy signal generation."""
        SignalGenerator.generate(strong_buy_result)

        # With perfect conditions, should get strong buy
        assert strong_buy_result.buy_signal == BuySignal.STRONG_BUY
        assert strong_buy_result.signal_score >= 75

    def test_buy_signal(self) -> None:
        """Test buy signal generation."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.BULL
        result.bias_ma5 = 1.0
        result.volume_status = VolumeStatus.HEAVY_VOLUME_UP
        result.macd_status = MACDStatus.GOLDEN_CROSS
        result.macd_signal = "金叉"
        result.rsi_status = RSIStatus.STRONG_BUY
        result.rsi_signal = "RSI强势"

        SignalGenerator.generate(result)

        # Good conditions - should get at least BUY (may get STRONG_BUY depending on score)
        assert result.buy_signal in [BuySignal.BUY, BuySignal.STRONG_BUY]
        assert result.signal_score >= 60

    def test_hold_signal(self) -> None:
        """Test hold signal generation."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.WEAK_BULL
        result.bias_ma5 = 3.0
        result.volume_status = VolumeStatus.NORMAL
        result.macd_status = MACDStatus.BULLISH
        result.macd_signal = "多头"
        result.rsi_status = RSIStatus.NEUTRAL
        result.rsi_signal = "RSI中性"

        SignalGenerator.generate(result)

        # Moderate conditions
        assert result.buy_signal == BuySignal.HOLD
        assert 45 <= result.signal_score < 60

    def test_wait_signal(self) -> None:
        """Test wait signal generation."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.CONSOLIDATION
        result.bias_ma5 = 4.0
        result.volume_status = VolumeStatus.SHRINK_VOLUME_UP
        result.macd_status = MACDStatus.BEARISH
        result.macd_signal = "空头"
        result.rsi_status = RSIStatus.WEAK
        result.rsi_signal = "RSI弱势"

        SignalGenerator.generate(result)

        # Weak conditions
        assert result.buy_signal == BuySignal.WAIT
        assert 30 <= result.signal_score < 45

    def test_sell_signal(self) -> None:
        """Test sell signal generation."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.BEAR
        result.bias_ma5 = 6.0
        result.volume_status = VolumeStatus.HEAVY_VOLUME_DOWN
        result.macd_status = MACDStatus.DEATH_CROSS
        result.macd_signal = "死叉"
        result.rsi_status = RSIStatus.OVERBOUGHT
        result.rsi_signal = "RSI超买"

        SignalGenerator.generate(result)

        # Poor conditions with bear trend - should get STRONG_SELL
        assert result.buy_signal == BuySignal.STRONG_SELL

    def test_strong_sell_signal(self) -> None:
        """Test strong sell signal generation."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.STRONG_BEAR
        result.bias_ma5 = -6.0
        result.volume_status = VolumeStatus.HEAVY_VOLUME_DOWN
        result.macd_status = MACDStatus.CROSSING_DOWN
        result.macd_signal = "下穿零轴"
        result.rsi_status = RSIStatus.OVERBOUGHT
        result.rsi_signal = "RSI超买"

        SignalGenerator.generate(result)

        # Worst conditions
        assert result.buy_signal == BuySignal.STRONG_SELL


# =============================================================================
# Score Range Tests
# =============================================================================
class TestScoreRanges:
    """Test cases for score range validation."""

    def test_score_never_negative(self) -> None:
        """Test that score is never negative."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.STRONG_BEAR
        result.bias_ma5 = 10.0
        result.volume_status = VolumeStatus.HEAVY_VOLUME_DOWN
        result.macd_status = MACDStatus.DEATH_CROSS
        result.rsi_status = RSIStatus.OVERBOUGHT

        SignalGenerator.generate(result)

        assert result.signal_score >= 0

    def test_score_never_exceeds_100(self) -> None:
        """Test that score never exceeds 100."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.STRONG_BULL
        result.bias_ma5 = -2.0
        result.volume_status = VolumeStatus.SHRINK_VOLUME_DOWN
        result.support_ma5 = True
        result.support_ma10 = True
        result.macd_status = MACDStatus.GOLDEN_CROSS_ZERO
        result.rsi_status = RSIStatus.OVERSOLD

        SignalGenerator.generate(result)

        assert result.signal_score <= 100

    def test_score_components_sum(self) -> None:
        """Test that score components sum correctly."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.STRONG_BULL  # 30 points
        result.bias_ma5 = -1.0  # 20 points
        result.volume_status = VolumeStatus.SHRINK_VOLUME_DOWN  # 15 points
        result.support_ma5 = True  # 5 points
        result.support_ma10 = True  # 5 points
        result.macd_status = MACDStatus.GOLDEN_CROSS_ZERO  # 15 points
        result.rsi_status = RSIStatus.OVERSOLD  # 10 points

        SignalGenerator.generate(result)

        # Maximum possible score
        assert result.signal_score == 100
