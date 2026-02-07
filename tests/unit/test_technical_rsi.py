"""
Unit tests for RSI analyzer module.

Tests cover:
- RSI status classification (overbought, oversold, neutral, etc.)
- RSI value extraction
- Signal generation based on RSI levels
"""

import pandas as pd
import pytest

from stock_analyzer.technical.enums import RSIStatus
from stock_analyzer.technical.result import TrendAnalysisResult
from stock_analyzer.technical.rsi import RSIAnalyzer


# =============================================================================
# RSI Analysis Tests
# =============================================================================
class TestRSIAnalyzer:
    """Test cases for RSI analyzer."""

    @pytest.fixture
    def result(self) -> TrendAnalysisResult:
        """Create a fresh TrendAnalysisResult."""
        return TrendAnalysisResult(code="600519")

    def test_analyze_with_insufficient_data(self, result: TrendAnalysisResult) -> None:
        """Test analysis with insufficient data (< 24 days)."""
        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 10,
                "RSI_6": [50.0] * 10,
                "RSI_12": [50.0] * 10,
                "RSI_24": [50.0] * 10,
            }
        )

        RSIAnalyzer.analyze(data, result)

        assert result.rsi_signal == "数据不足"

    def test_overbought_detection(self, result: TrendAnalysisResult) -> None:
        """Test overbought detection (RSI > 70)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "RSI_6": [75.0] * 30,
                "RSI_12": [75.0] * 30,  # RSI(12) > 70, should trigger overbought
                "RSI_24": [70.0] * 30,
            }
        )

        RSIAnalyzer.analyze(data, result)

        assert result.rsi_status == RSIStatus.OVERBOUGHT
        assert "超买" in result.rsi_signal
        assert "回调风险" in result.rsi_signal

    def test_oversold_detection(self, result: TrendAnalysisResult) -> None:
        """Test oversold detection (RSI < 30)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "RSI_6": [25.0] * 30,
                "RSI_12": [25.0] * 30,  # RSI(12) < 30, should trigger oversold
                "RSI_24": [30.0] * 30,
            }
        )

        RSIAnalyzer.analyze(data, result)

        assert result.rsi_status == RSIStatus.OVERSOLD
        assert "超卖" in result.rsi_signal
        assert "反弹" in result.rsi_signal

    def test_strong_buy_zone(self, result: TrendAnalysisResult) -> None:
        """Test strong buy zone detection (60 < RSI <= 70)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "RSI_6": [65.0] * 30,
                "RSI_12": [65.0] * 30,  # 60 < RSI(12) <= 70
                "RSI_24": [60.0] * 30,
            }
        )

        RSIAnalyzer.analyze(data, result)

        assert result.rsi_status == RSIStatus.STRONG_BUY
        assert "强势" in result.rsi_signal

    def test_neutral_zone(self, result: TrendAnalysisResult) -> None:
        """Test neutral zone detection (40 <= RSI <= 60)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "RSI_6": [50.0] * 30,
                "RSI_12": [50.0] * 30,  # 40 <= RSI(12) <= 60
                "RSI_24": [50.0] * 30,
            }
        )

        RSIAnalyzer.analyze(data, result)

        assert result.rsi_status == RSIStatus.NEUTRAL
        assert "中性" in result.rsi_signal

    def test_weak_zone(self, result: TrendAnalysisResult) -> None:
        """Test weak zone detection (30 <= RSI < 40)."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "RSI_6": [35.0] * 30,
                "RSI_12": [35.0] * 30,  # 30 <= RSI(12) < 40
                "RSI_24": [35.0] * 30,
            }
        )

        RSIAnalyzer.analyze(data, result)

        assert result.rsi_status == RSIStatus.WEAK
        assert "弱势" in result.rsi_signal

    def test_rsi_values_extracted_correctly(self, result: TrendAnalysisResult) -> None:
        """Test that RSI values are correctly extracted from data."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        rsi_6_values = list(range(30))  # 0, 1, 2, ..., 29
        rsi_12_values = [v + 10 for v in rsi_6_values]  # 10, 11, 12, ..., 39
        rsi_24_values = [v + 20 for v in rsi_6_values]  # 20, 21, 22, ..., 49

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "RSI_6": rsi_6_values,
                "RSI_12": rsi_12_values,
                "RSI_24": rsi_24_values,
            }
        )

        RSIAnalyzer.analyze(data, result)

        # Latest values should be extracted
        assert result.rsi_6 == 29.0
        assert result.rsi_12 == 39.0
        assert result.rsi_24 == 49.0

    def test_boundary_at_70(self, result: TrendAnalysisResult) -> None:
        """Test boundary condition at RSI = 70."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "RSI_6": [70.0] * 30,
                "RSI_12": [70.0] * 30,  # Exactly at 70
                "RSI_24": [70.0] * 30,
            }
        )

        RSIAnalyzer.analyze(data, result)

        # RSI = 70 should be strong buy (60 < RSI <= 70)
        assert result.rsi_status == RSIStatus.STRONG_BUY

    def test_boundary_at_30(self, result: TrendAnalysisResult) -> None:
        """Test boundary condition at RSI = 30."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "RSI_6": [30.0] * 30,
                "RSI_12": [30.0] * 30,  # Exactly at 30
                "RSI_24": [30.0] * 30,
            }
        )

        RSIAnalyzer.analyze(data, result)

        # RSI = 30 should be weak (not oversold)
        assert result.rsi_status == RSIStatus.WEAK

    def test_boundary_at_60(self, result: TrendAnalysisResult) -> None:
        """Test boundary condition at RSI = 60."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "RSI_6": [60.0] * 30,
                "RSI_12": [60.0] * 30,  # Exactly at 60
                "RSI_24": [60.0] * 30,
            }
        )

        RSIAnalyzer.analyze(data, result)

        # RSI = 60 should be neutral
        assert result.rsi_status == RSIStatus.NEUTRAL

    def test_boundary_at_40(self, result: TrendAnalysisResult) -> None:
        """Test boundary condition at RSI = 40."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "RSI_6": [40.0] * 30,
                "RSI_12": [40.0] * 30,  # Exactly at 40
                "RSI_24": [40.0] * 30,
            }
        )

        RSIAnalyzer.analyze(data, result)

        # RSI = 40 should be neutral
        assert result.rsi_status == RSIStatus.NEUTRAL


# =============================================================================
# RSI Parameters Tests
# =============================================================================
class TestRSIParameters:
    """Test RSI analyzer parameters."""

    def test_rsi_period_constants(self) -> None:
        """Test RSI period constants are correct."""
        assert RSIAnalyzer.RSI_SHORT == 6
        assert RSIAnalyzer.RSI_MID == 12
        assert RSIAnalyzer.RSI_LONG == 24

    def test_rsi_threshold_constants(self) -> None:
        """Test RSI threshold constants are correct."""
        assert RSIAnalyzer.RSI_OVERBOUGHT == 70
        assert RSIAnalyzer.RSI_OVERSOLD == 30
