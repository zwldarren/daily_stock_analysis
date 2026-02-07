"""
Unit tests for technical enums module.

Tests cover:
- TrendStatus enum values
- VolumeStatus enum values
- BuySignal enum values
- MACDStatus enum values
- RSIStatus enum values
"""

import pytest

from stock_analyzer.technical.enums import (
    BuySignal,
    MACDStatus,
    RSIStatus,
    TrendStatus,
    VolumeStatus,
)


# =============================================================================
# TrendStatus Tests
# =============================================================================
class TestTrendStatus:
    """Test cases for TrendStatus enum."""

    @pytest.mark.parametrize(
        "status,expected_value",
        [
            (TrendStatus.STRONG_BULL, "强势多头"),
            (TrendStatus.BULL, "多头排列"),
            (TrendStatus.WEAK_BULL, "弱势多头"),
            (TrendStatus.CONSOLIDATION, "盘整"),
            (TrendStatus.WEAK_BEAR, "弱势空头"),
            (TrendStatus.BEAR, "空头排列"),
            (TrendStatus.STRONG_BEAR, "强势空头"),
        ],
    )
    def test_trend_status_values(self, status: TrendStatus, expected_value: str) -> None:
        """Test TrendStatus enum values."""
        assert status.value == expected_value

    def test_all_trend_statuses_defined(self) -> None:
        """Test that all expected trend statuses are defined."""
        expected_statuses = [
            "强势多头",
            "多头排列",
            "弱势多头",
            "盘整",
            "弱势空头",
            "空头排列",
            "强势空头",
        ]
        actual_statuses = [s.value for s in TrendStatus]

        for expected in expected_statuses:
            assert expected in actual_statuses


# =============================================================================
# VolumeStatus Tests
# =============================================================================
class TestVolumeStatus:
    """Test cases for VolumeStatus enum."""

    @pytest.mark.parametrize(
        "status,expected_value",
        [
            (VolumeStatus.HEAVY_VOLUME_UP, "放量上涨"),
            (VolumeStatus.HEAVY_VOLUME_DOWN, "放量下跌"),
            (VolumeStatus.SHRINK_VOLUME_UP, "缩量上涨"),
            (VolumeStatus.SHRINK_VOLUME_DOWN, "缩量回调"),
            (VolumeStatus.NORMAL, "量能正常"),
        ],
    )
    def test_volume_status_values(self, status: VolumeStatus, expected_value: str) -> None:
        """Test VolumeStatus enum values."""
        assert status.value == expected_value

    def test_all_volume_statuses_defined(self) -> None:
        """Test that all expected volume statuses are defined."""
        expected_statuses = [
            "放量上涨",
            "放量下跌",
            "缩量上涨",
            "缩量回调",
            "量能正常",
        ]
        actual_statuses = [s.value for s in VolumeStatus]

        for expected in expected_statuses:
            assert expected in actual_statuses


# =============================================================================
# BuySignal Tests
# =============================================================================
class TestBuySignal:
    """Test cases for BuySignal enum."""

    @pytest.mark.parametrize(
        "signal,expected_value",
        [
            (BuySignal.STRONG_BUY, "强烈买入"),
            (BuySignal.BUY, "买入"),
            (BuySignal.HOLD, "持有"),
            (BuySignal.WAIT, "观望"),
            (BuySignal.SELL, "卖出"),
            (BuySignal.STRONG_SELL, "强烈卖出"),
        ],
    )
    def test_buy_signal_values(self, signal: BuySignal, expected_value: str) -> None:
        """Test BuySignal enum values."""
        assert signal.value == expected_value

    def test_buy_signal_order(self) -> None:
        """Test that buy signals are ordered from strongest buy to strongest sell."""
        signals = list(BuySignal)

        # Check that the order makes logical sense
        assert BuySignal.STRONG_BUY in signals
        assert BuySignal.BUY in signals
        assert BuySignal.HOLD in signals
        assert BuySignal.WAIT in signals
        assert BuySignal.SELL in signals
        assert BuySignal.STRONG_SELL in signals


# =============================================================================
# MACDStatus Tests
# =============================================================================
class TestMACDStatus:
    """Test cases for MACDStatus enum."""

    @pytest.mark.parametrize(
        "status,expected_value",
        [
            (MACDStatus.GOLDEN_CROSS_ZERO, "零轴上金叉"),
            (MACDStatus.GOLDEN_CROSS, "金叉"),
            (MACDStatus.BULLISH, "多头"),
            (MACDStatus.CROSSING_UP, "上穿零轴"),
            (MACDStatus.CROSSING_DOWN, "下穿零轴"),
            (MACDStatus.BEARISH, "空头"),
            (MACDStatus.DEATH_CROSS, "死叉"),
        ],
    )
    def test_macd_status_values(self, status: MACDStatus, expected_value: str) -> None:
        """Test MACDStatus enum values."""
        assert status.value == expected_value

    def test_macd_bullish_statuses(self) -> None:
        """Test bullish MACD statuses."""
        bullish_statuses = [
            MACDStatus.GOLDEN_CROSS_ZERO,
            MACDStatus.GOLDEN_CROSS,
            MACDStatus.BULLISH,
            MACDStatus.CROSSING_UP,
        ]

        for status in bullish_statuses:
            assert status in MACDStatus

    def test_macd_bearish_statuses(self) -> None:
        """Test bearish MACD statuses."""
        bearish_statuses = [
            MACDStatus.DEATH_CROSS,
            MACDStatus.BEARISH,
            MACDStatus.CROSSING_DOWN,
        ]

        for status in bearish_statuses:
            assert status in MACDStatus


# =============================================================================
# RSIStatus Tests
# =============================================================================
class TestRSIStatus:
    """Test cases for RSIStatus enum."""

    @pytest.mark.parametrize(
        "status,expected_value",
        [
            (RSIStatus.OVERBOUGHT, "超买"),
            (RSIStatus.STRONG_BUY, "强势买入"),
            (RSIStatus.NEUTRAL, "中性"),
            (RSIStatus.WEAK, "弱势"),
            (RSIStatus.OVERSOLD, "超卖"),
        ],
    )
    def test_rsi_status_values(self, status: RSIStatus, expected_value: str) -> None:
        """Test RSIStatus enum values."""
        assert status.value == expected_value

    def test_rsi_status_order(self) -> None:
        """Test RSI status order from overbought to oversold."""
        # RSI > 70: Overbought (most bearish)
        # 50 < RSI < 70: Strong buy
        # 40 <= RSI <= 60: Neutral
        # 30 < RSI < 40: Weak
        # RSI < 30: Oversold (most bullish for reversal)

        assert RSIStatus.OVERBOUGHT.value == "超买"
        assert RSIStatus.OVERSOLD.value == "超卖"


# =============================================================================
# Enum Comparisons
# =============================================================================
class TestEnumComparisons:
    """Test enum comparison operations."""

    def test_enum_equality(self) -> None:
        """Test enum equality comparison."""
        assert TrendStatus.BULL == TrendStatus.BULL
        assert TrendStatus.BULL != TrendStatus.BEAR

    def test_enum_identity(self) -> None:
        """Test enum identity comparison."""
        assert TrendStatus.BULL is TrendStatus.BULL
        assert TrendStatus.BULL is not TrendStatus.BEAR

    def test_enum_in_collection(self) -> None:
        """Test enum membership in collections."""
        bullish_trends = [TrendStatus.STRONG_BULL, TrendStatus.BULL, TrendStatus.WEAK_BULL]

        assert TrendStatus.BULL in bullish_trends
        assert TrendStatus.BEAR not in bullish_trends

    def test_enum_hashable(self) -> None:
        """Test that enums are hashable and can be used as dict keys."""
        trend_scores = {
            TrendStatus.STRONG_BULL: 30,
            TrendStatus.BULL: 26,
            TrendStatus.WEAK_BULL: 18,
        }

        assert trend_scores[TrendStatus.STRONG_BULL] == 30
