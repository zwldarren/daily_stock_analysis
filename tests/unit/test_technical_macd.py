"""
Unit tests for MACD analyzer module.

Tests cover:
- Golden cross and death cross detection
- Zero line crossing detection
- MACD status classification
- Signal generation
"""

import pandas as pd
import pytest

from stock_analyzer.technical.enums import MACDStatus
from stock_analyzer.technical.macd import MACDAnalyzer
from stock_analyzer.technical.result import TrendAnalysisResult


# =============================================================================
# MACD Analysis Tests
# =============================================================================
class TestMACDAnalyzer:
    """Test cases for MACD analyzer."""

    @pytest.fixture
    def base_data(self) -> pd.DataFrame:
        """Create base DataFrame with required columns."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        return pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": [0.0] * 30,
                "MACD_DEA": [0.0] * 30,
                "MACD_BAR": [0.0] * 30,
            }
        )

    @pytest.fixture
    def result(self) -> TrendAnalysisResult:
        """Create a fresh TrendAnalysisResult."""
        return TrendAnalysisResult(code="600519")

    def test_analyze_with_insufficient_data(self, result: TrendAnalysisResult) -> None:
        """Test analysis with insufficient data (< 26 days)."""
        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 10,
                "MACD_DIF": [0.0] * 10,
                "MACD_DEA": [0.0] * 10,
                "MACD_BAR": [0.0] * 10,
            }
        )

        MACDAnalyzer.analyze(data, result)

        assert result.macd_signal == "数据不足"

    def test_golden_cross_detection(self, result: TrendAnalysisResult) -> None:
        """Test golden cross detection (DIF crosses above DEA)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        # Previous: DIF < DEA, Current: DIF > DEA (both negative, crossing below zero)
        dif_values = [0.0] * 28 + [-0.5, -0.1]  # Cross from below to above DEA, but still negative
        dea_values = [0.0] * 28 + [-0.3, -0.3]  # DEA stays negative
        bar_values = [0.0] * 30

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        assert result.macd_status == MACDStatus.GOLDEN_CROSS
        assert "金叉" in result.macd_signal

    def test_death_cross_detection(self, result: TrendAnalysisResult) -> None:
        """Test death cross detection (DIF crosses below DEA)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        # Previous: DIF > DEA, Current: DIF < DEA
        dif_values = [0.0] * 28 + [0.5, -0.5]  # Cross from positive to negative
        dea_values = [0.0] * 28 + [0.0, 0.0]
        bar_values = [0.0] * 30

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        assert result.macd_status == MACDStatus.DEATH_CROSS
        assert "死叉" in result.macd_signal

    def test_golden_cross_above_zero(self, result: TrendAnalysisResult) -> None:
        """Test golden cross above zero line (strongest buy signal)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        # Golden cross above zero: DIF crosses from below DEA to above DEA, both positive
        dif_values = [0.0] * 28 + [0.3, 0.8]  # Cross above zero
        dea_values = [0.0] * 28 + [0.5, 0.5]
        bar_values = [0.0] * 30

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        assert result.macd_status == MACDStatus.GOLDEN_CROSS_ZERO
        assert "零轴上金叉" in result.macd_signal
        assert "强烈买入" in result.macd_signal

    def test_crossing_up_zero_line(self, result: TrendAnalysisResult) -> None:
        """Test crossing up through zero line (without golden cross)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        # DIF crosses from negative to positive, but already above DEA (no golden cross)
        dif_values = [0.0] * 28 + [-0.5, 0.5]
        dea_values = [0.0] * 28 + [-0.8, -0.8]  # DIF was already above DEA
        bar_values = [0.0] * 30

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        assert result.macd_status == MACDStatus.CROSSING_UP
        assert "上穿零轴" in result.macd_signal

    def test_crossing_down_zero_line(self, result: TrendAnalysisResult) -> None:
        """Test crossing down through zero line (without death cross)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        # DIF crosses from positive to negative, but already below DEA (no death cross)
        dif_values = [0.0] * 28 + [0.5, -0.5]
        dea_values = [0.0] * 28 + [0.8, 0.8]  # DIF was already below DEA
        bar_values = [0.0] * 30

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        assert result.macd_status == MACDStatus.CROSSING_DOWN
        assert "下穿零轴" in result.macd_signal

    def test_bullish_status(self, result: TrendAnalysisResult) -> None:
        """Test bullish status (DIF > DEA > 0)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        # Both DIF and DEA positive, DIF > DEA
        dif_values = [0.0] * 28 + [0.8, 0.8]
        dea_values = [0.0] * 28 + [0.5, 0.5]
        bar_values = [0.0] * 30

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        assert result.macd_status == MACDStatus.BULLISH
        assert "多头" in result.macd_signal

    def test_bearish_status(self, result: TrendAnalysisResult) -> None:
        """Test bearish status (DIF < DEA < 0)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        # Both DIF and DEA negative, DIF < DEA
        dif_values = [0.0] * 28 + [-0.8, -0.8]
        dea_values = [0.0] * 28 + [-0.5, -0.5]
        bar_values = [0.0] * 30

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        assert result.macd_status == MACDStatus.BEARISH
        assert "空头" in result.macd_signal

    def test_macd_values_set_correctly(self, result: TrendAnalysisResult) -> None:
        """Test that MACD values are correctly set in result."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        dif_values = list(range(30))  # 0, 1, 2, ..., 29
        dea_values = [v * 0.5 for v in dif_values]
        bar_values = [(dif_values[i] - dea_values[i]) * 2 for i in range(30)]

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        # Latest values should be set
        assert result.macd_dif == 29.0
        assert result.macd_dea == 14.5
        assert result.macd_bar == 29.0


# =============================================================================
# Edge Cases
# =============================================================================
class TestMACDEdgeCases:
    """Test edge cases for MACD analyzer."""

    @pytest.fixture
    def result(self) -> TrendAnalysisResult:
        """Create a fresh TrendAnalysisResult."""
        return TrendAnalysisResult(code="600519")

    def test_exactly_on_zero(self, result: TrendAnalysisResult) -> None:
        """Test when DIF is exactly on zero line."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        # DIF exactly at zero, no cross
        dif_values = [0.0] * 28 + [0.0, 0.0]
        dea_values = [0.0] * 28 + [-0.1, -0.1]
        bar_values = [0.0] * 30

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        # Should be bullish since DIF > DEA and DIF >= 0
        assert result.macd_status == MACDStatus.BULLISH

    def test_no_cross_just_above(self, result: TrendAnalysisResult) -> None:
        """Test when DIF stays just above DEA without crossing."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        dif_values = [0.0] * 28 + [0.6, 0.6]  # Consistently above
        dea_values = [0.0] * 28 + [0.5, 0.5]
        bar_values = [0.0] * 30

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        # No cross, just bullish
        assert result.macd_status == MACDStatus.BULLISH

    def test_no_cross_just_below(self, result: TrendAnalysisResult) -> None:
        """Test when DIF stays just below DEA without crossing."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        dif_values = [0.0] * 28 + [0.4, 0.4]  # Consistently below
        dea_values = [0.0] * 28 + [0.5, 0.5]
        bar_values = [0.0] * 30

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "MACD_DIF": dif_values,
                "MACD_DEA": dea_values,
                "MACD_BAR": bar_values,
            }
        )

        MACDAnalyzer.analyze(data, result)

        # No cross, but since both are positive and DIF < DEA, it's bullish (neutral zone)
        # Actually in the current implementation, this falls through to BULLISH
        assert result.macd_status == MACDStatus.BULLISH
