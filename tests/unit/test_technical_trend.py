"""
Unit tests for trend analyzer module.

Tests cover:
- Trend status classification (bull, bear, consolidation)
- Bias (deviation) calculations
- Volume analysis
- Support and resistance detection
"""

import numpy as np
import pandas as pd
import pytest

from stock_analyzer.technical.enums import TrendStatus, VolumeStatus
from stock_analyzer.technical.result import TrendAnalysisResult
from stock_analyzer.technical.trend import TrendAnalyzer


# =============================================================================
# Trend Analysis Tests
# =============================================================================
class TestTrendAnalyzer:
    """Test cases for trend analyzer."""

    @pytest.fixture
    def base_result(self) -> TrendAnalysisResult:
        """Create a base result for testing."""
        result = TrendAnalysisResult(code="600519")
        result.current_price = 100.0
        return result

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample OHLCV data."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(30) * 0.5)

        return pd.DataFrame(
            {
                "date": dates,
                "open": prices - 0.5,
                "high": prices + 1.0,
                "low": prices - 1.0,
                "close": prices,
                "volume": np.random.randint(1000000, 5000000, 30),
                "MA5": prices,
                "MA10": prices * 0.98,
                "MA20": prices * 0.96,
            }
        )

    def test_strong_bull_detection(self, base_result: TrendAnalysisResult) -> None:
        """Test strong bull trend detection."""
        # MA5 > MA10 > MA20 with expanding spread
        base_result.ma5 = 105.0
        base_result.ma10 = 102.0
        base_result.ma20 = 98.0

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "volume": [1000000] * 30,
                "MA5": [100.0] * 25 + [103.0] * 5,  # Expanding spread
                "MA10": [100.0] * 25 + [101.0] * 5,
                "MA20": [100.0] * 30,
            }
        )

        TrendAnalyzer.analyze_trend(data, base_result)

        assert base_result.trend_status == TrendStatus.STRONG_BULL
        assert base_result.trend_strength == 90

    def test_bull_detection(self, base_result: TrendAnalysisResult) -> None:
        """Test bull trend detection."""
        # MA5 > MA10 > MA20
        base_result.ma5 = 102.0
        base_result.ma10 = 101.0
        base_result.ma20 = 100.0

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "volume": [1000000] * 30,
                "MA5": [100.0] * 30,
                "MA10": [100.0] * 30,
                "MA20": [100.0] * 30,
            }
        )

        TrendAnalyzer.analyze_trend(data, base_result)

        assert base_result.trend_status == TrendStatus.BULL
        assert base_result.trend_strength == 75

    def test_weak_bull_detection(self, base_result: TrendAnalysisResult) -> None:
        """Test weak bull trend detection."""
        # MA5 > MA10 but MA10 <= MA20
        base_result.ma5 = 102.0
        base_result.ma10 = 101.0
        base_result.ma20 = 101.0

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "volume": [1000000] * 30,
                "MA5": [100.0] * 30,
                "MA10": [100.0] * 30,
                "MA20": [100.0] * 30,
            }
        )

        TrendAnalyzer.analyze_trend(data, base_result)

        assert base_result.trend_status == TrendStatus.WEAK_BULL
        assert base_result.trend_strength == 55

    def test_bear_detection(self, base_result: TrendAnalysisResult) -> None:
        """Test bear trend detection."""
        # MA5 < MA10 < MA20
        base_result.ma5 = 98.0
        base_result.ma10 = 99.0
        base_result.ma20 = 100.0

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "volume": [1000000] * 30,
                "MA5": [100.0] * 30,
                "MA10": [100.0] * 30,
                "MA20": [100.0] * 30,
            }
        )

        TrendAnalyzer.analyze_trend(data, base_result)

        assert base_result.trend_status == TrendStatus.BEAR
        assert base_result.trend_strength == 25

    def test_strong_bear_detection(self, base_result: TrendAnalysisResult) -> None:
        """Test strong bear trend detection."""
        # MA5 < MA10 < MA20 with expanding spread
        base_result.ma5 = 95.0
        base_result.ma10 = 98.0
        base_result.ma20 = 102.0

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "volume": [1000000] * 30,
                "MA5": [100.0] * 25 + [97.0] * 5,  # Expanding spread downward
                "MA10": [100.0] * 25 + [99.0] * 5,
                "MA20": [100.0] * 30,
            }
        )

        TrendAnalyzer.analyze_trend(data, base_result)

        assert base_result.trend_status == TrendStatus.STRONG_BEAR
        assert base_result.trend_strength == 10

    def test_consolidation_detection(self, base_result: TrendAnalysisResult) -> None:
        """Test consolidation (sideways) detection."""
        # Mixed MA alignment - all equal means consolidation
        base_result.ma5 = 100.0
        base_result.ma10 = 100.0
        base_result.ma20 = 100.0

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "volume": [1000000] * 30,
                "MA5": [100.0] * 30,
                "MA10": [100.0] * 30,
                "MA20": [100.0] * 30,
            }
        )

        TrendAnalyzer.analyze_trend(data, base_result)

        assert base_result.trend_status == TrendStatus.CONSOLIDATION
        assert base_result.trend_strength == 50


# =============================================================================
# Bias Calculation Tests
# =============================================================================
class TestBiasCalculations:
    """Test cases for bias (deviation) calculations."""

    @pytest.fixture
    def base_result(self) -> TrendAnalysisResult:
        """Create a base result for testing."""
        result = TrendAnalysisResult(code="600519")
        result.current_price = 100.0
        result.ma5 = 100.0
        result.ma10 = 98.0
        result.ma20 = 96.0
        return result

    def test_bias_ma5_calculation(self, base_result: TrendAnalysisResult) -> None:
        """Test MA5 bias calculation."""
        TrendAnalyzer.calculate_bias(base_result)

        # Bias = (Price - MA) / MA * 100
        expected_bias = (100.0 - 100.0) / 100.0 * 100
        assert base_result.bias_ma5 == pytest.approx(expected_bias, 0.01)

    def test_bias_positive(self, base_result: TrendAnalysisResult) -> None:
        """Test positive bias calculation."""
        base_result.current_price = 105.0
        base_result.ma5 = 100.0

        TrendAnalyzer.calculate_bias(base_result)

        expected_bias = (105.0 - 100.0) / 100.0 * 100  # 5%
        assert base_result.bias_ma5 == pytest.approx(expected_bias, 0.01)

    def test_bias_negative(self, base_result: TrendAnalysisResult) -> None:
        """Test negative bias calculation."""
        base_result.current_price = 95.0
        base_result.ma5 = 100.0

        TrendAnalyzer.calculate_bias(base_result)

        expected_bias = (95.0 - 100.0) / 100.0 * 100  # -5%
        assert base_result.bias_ma5 == pytest.approx(expected_bias, 0.01)

    def test_bias_with_zero_ma(self, base_result: TrendAnalysisResult) -> None:
        """Test bias calculation when MA is zero."""
        base_result.ma5 = 0.0

        TrendAnalyzer.calculate_bias(base_result)

        # Should not crash, bias should remain 0
        assert base_result.bias_ma5 == 0.0


# =============================================================================
# Volume Analysis Tests
# =============================================================================
class TestVolumeAnalysis:
    """Test cases for volume analysis."""

    @pytest.fixture
    def base_result(self) -> TrendAnalysisResult:
        """Create a base result for testing."""
        return TrendAnalysisResult(code="600519")

    def test_heavy_volume_up(self, base_result: TrendAnalysisResult) -> None:
        """Test heavy volume up detection."""
        # Need at least 6 days: 5 days for average + 1 current day
        dates = pd.date_range(start="2024-01-01", periods=6, freq="D")
        volumes = [1000000] * 5 + [2000000]  # First 5 days normal, last day heavy
        prices = [100.0] * 5 + [101.0]  # Rising price on last day

        data = pd.DataFrame(
            {
                "date": dates,
                "close": prices,
                "volume": volumes,
            }
        )

        TrendAnalyzer.analyze_volume(data, base_result)

        assert base_result.volume_status == VolumeStatus.HEAVY_VOLUME_UP
        assert "放量上涨" in base_result.volume_trend

    def test_heavy_volume_down(self, base_result: TrendAnalysisResult) -> None:
        """Test heavy volume down detection."""
        # Need at least 6 days: 5 days for average + 1 current day
        dates = pd.date_range(start="2024-01-01", periods=6, freq="D")
        volumes = [1000000] * 5 + [2000000]  # First 5 days normal, last day heavy
        prices = [100.0] * 5 + [99.0]  # Falling price on last day

        data = pd.DataFrame(
            {
                "date": dates,
                "close": prices,
                "volume": volumes,
            }
        )

        TrendAnalyzer.analyze_volume(data, base_result)

        assert base_result.volume_status == VolumeStatus.HEAVY_VOLUME_DOWN
        assert "放量下跌" in base_result.volume_trend

    def test_shrink_volume_up(self, base_result: TrendAnalysisResult) -> None:
        """Test shrink volume up detection."""
        # Need at least 6 days: 5 days for average + 1 current day
        dates = pd.date_range(start="2024-01-01", periods=6, freq="D")
        volumes = [1000000] * 5 + [500000]  # First 5 days normal, last day low volume
        prices = [100.0] * 5 + [101.0]  # Rising price on last day

        data = pd.DataFrame(
            {
                "date": dates,
                "close": prices,
                "volume": volumes,
            }
        )

        TrendAnalyzer.analyze_volume(data, base_result)

        assert base_result.volume_status == VolumeStatus.SHRINK_VOLUME_UP
        assert "缩量上涨" in base_result.volume_trend

    def test_shrink_volume_down(self, base_result: TrendAnalysisResult) -> None:
        """Test shrink volume down detection."""
        # Need at least 6 days: 5 days for average + 1 current day
        dates = pd.date_range(start="2024-01-01", periods=6, freq="D")
        volumes = [1000000] * 5 + [500000]  # First 5 days normal, last day low volume
        prices = [100.0] * 5 + [99.0]  # Falling price on last day

        data = pd.DataFrame(
            {
                "date": dates,
                "close": prices,
                "volume": volumes,
            }
        )

        TrendAnalyzer.analyze_volume(data, base_result)

        assert base_result.volume_status == VolumeStatus.SHRINK_VOLUME_DOWN
        assert "缩量回调" in base_result.volume_trend

    def test_normal_volume(self, base_result: TrendAnalysisResult) -> None:
        """Test normal volume detection."""
        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
        volumes = [1000000] * 10  # Consistent volume
        prices = [100.0] * 10

        data = pd.DataFrame(
            {
                "date": dates,
                "close": prices,
                "volume": volumes,
            }
        )

        TrendAnalyzer.analyze_volume(data, base_result)

        assert base_result.volume_status == VolumeStatus.NORMAL

    def test_volume_with_insufficient_data(self, base_result: TrendAnalysisResult) -> None:
        """Test volume analysis with insufficient data."""
        dates = pd.date_range(start="2024-01-01", periods=3, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 3,
                "volume": [1000000] * 3,
            }
        )

        # Should not crash with < 5 days of data
        TrendAnalyzer.analyze_volume(data, base_result)


# =============================================================================
# Support and Resistance Tests
# =============================================================================
class TestSupportResistance:
    """Test cases for support and resistance analysis."""

    @pytest.fixture
    def base_result(self) -> TrendAnalysisResult:
        """Create a base result for testing."""
        result = TrendAnalysisResult(code="600519")
        result.current_price = 100.0
        result.ma5 = 100.0
        result.ma10 = 98.0
        result.ma20 = 96.0
        return result

    def test_ma5_support_detection(self, base_result: TrendAnalysisResult) -> None:
        """Test MA5 support detection."""
        # Price at MA5 with small tolerance
        base_result.current_price = 100.0
        base_result.ma5 = 100.0

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "high": [101.0] * 30,
                "volume": [1000000] * 30,
            }
        )

        TrendAnalyzer.analyze_support_resistance(data, base_result)

        assert base_result.support_ma5 is True
        assert base_result.ma5 in base_result.support_levels

    def test_ma10_support_detection(self, base_result: TrendAnalysisResult) -> None:
        """Test MA10 support detection."""
        base_result.current_price = 98.0
        base_result.ma10 = 98.0

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "high": [101.0] * 30,
                "volume": [1000000] * 30,
            }
        )

        TrendAnalyzer.analyze_support_resistance(data, base_result)

        assert base_result.support_ma10 is True
        assert base_result.ma10 in base_result.support_levels

    def test_resistance_from_recent_high(self, base_result: TrendAnalysisResult) -> None:
        """Test resistance detection from recent high."""
        base_result.current_price = 100.0

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        highs = [100.0] * 10 + [110.0] * 10 + [100.0] * 10  # Recent high at 110

        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "high": highs,
                "volume": [1000000] * 30,
            }
        )

        TrendAnalyzer.analyze_support_resistance(data, base_result)

        assert 110.0 in base_result.resistance_levels

    def test_ma20_as_support(self, base_result: TrendAnalysisResult) -> None:
        """Test MA20 always added as support when price >= MA20."""
        base_result.current_price = 100.0
        base_result.ma20 = 96.0

        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100.0] * 30,
                "high": [101.0] * 30,
                "volume": [1000000] * 30,
            }
        )

        TrendAnalyzer.analyze_support_resistance(data, base_result)

        assert base_result.ma20 in base_result.support_levels


# =============================================================================
# MA Status Description Tests
# =============================================================================
class TestMAStatusDescription:
    """Test cases for MA status description."""

    def test_bullish_alignment_description(self) -> None:
        """Test description for bullish alignment."""
        desc = TrendAnalyzer.get_ma_status(105.0, 104.0, 103.0, 102.0)
        assert "多头" in desc

    def test_bearish_alignment_description(self) -> None:
        """Test description for bearish alignment."""
        desc = TrendAnalyzer.get_ma_status(95.0, 96.0, 97.0, 98.0)
        assert "空头" in desc

    def test_short_term_bullish_description(self) -> None:
        """Test description for short-term bullish."""
        # close > ma5 and ma5 > ma10, but ma10 <= ma20 (not full bullish alignment)
        desc = TrendAnalyzer.get_ma_status(102.0, 101.0, 100.0, 101.0)
        # When close > ma5 and ma5 > ma10, should show short-term bullish
        assert "向好" in desc or "短期" in desc or "🔼" in desc

    def test_consolidation_description(self) -> None:
        """Test description for consolidation."""
        desc = TrendAnalyzer.get_ma_status(100.0, 102.0, 98.0, 100.0)
        assert "震荡" in desc or "整理" in desc
