"""
Unit tests for technical indicator calculator module.

Tests cover:
- Moving average calculations (MA5, MA10, MA20, MA60)
- MACD indicator calculations
- RSI indicator calculations
"""

import numpy as np
import pandas as pd
import pytest

from stock_analyzer.technical.calculator import IndicatorCalculator


# =============================================================================
# Moving Average Tests
# =============================================================================
class TestMACalculations:
    """Test cases for moving average calculations."""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        np.random.seed(42)
        base_prices = 100 + np.cumsum(np.random.randn(30) * 0.5)

        return pd.DataFrame(
            {
                "date": dates,
                "open": base_prices - 0.5,
                "high": base_prices + 1.0,
                "low": base_prices - 1.0,
                "close": base_prices,
                "volume": np.random.randint(1000000, 5000000, 30),
            }
        )

    def test_calculate_mas_adds_ma_columns(self, sample_data: pd.DataFrame) -> None:
        """Test that calculate_mas adds MA columns to DataFrame."""
        result = IndicatorCalculator.calculate_mas(sample_data)

        assert "MA5" in result.columns
        assert "MA10" in result.columns
        assert "MA20" in result.columns
        assert "MA60" in result.columns

    def test_ma5_calculation(self, sample_data: pd.DataFrame) -> None:
        """Test MA5 calculation is correct."""
        result = IndicatorCalculator.calculate_mas(sample_data)

        # MA5 should be the rolling mean of last 5 close prices
        expected_ma5 = sample_data["close"].rolling(window=5).mean()
        expected_ma5.name = "MA5"
        pd.testing.assert_series_equal(result["MA5"], expected_ma5)

    def test_ma10_calculation(self, sample_data: pd.DataFrame) -> None:
        """Test MA10 calculation is correct."""
        result = IndicatorCalculator.calculate_mas(sample_data)

        expected_ma10 = sample_data["close"].rolling(window=10).mean()
        expected_ma10.name = "MA10"
        pd.testing.assert_series_equal(result["MA10"], expected_ma10)

    def test_ma20_calculation(self, sample_data: pd.DataFrame) -> None:
        """Test MA20 calculation is correct."""
        result = IndicatorCalculator.calculate_mas(sample_data)

        expected_ma20 = sample_data["close"].rolling(window=20).mean()
        expected_ma20.name = "MA20"
        pd.testing.assert_series_equal(result["MA20"], expected_ma20)

    def test_ma60_with_sufficient_data(self, sample_data: pd.DataFrame) -> None:
        """Test MA60 calculation with sufficient data."""
        # Extend data to 60+ days
        extended_dates = pd.date_range(start="2024-01-01", periods=70, freq="D")
        np.random.seed(42)
        extended_prices = 100 + np.cumsum(np.random.randn(70) * 0.5)

        extended_data = pd.DataFrame(
            {
                "date": extended_dates,
                "open": extended_prices - 0.5,
                "high": extended_prices + 1.0,
                "low": extended_prices - 1.0,
                "close": extended_prices,
                "volume": np.random.randint(1000000, 5000000, 70),
            }
        )

        result = IndicatorCalculator.calculate_mas(extended_data)

        expected_ma60 = extended_data["close"].rolling(window=60).mean()
        expected_ma60.name = "MA60"
        pd.testing.assert_series_equal(result["MA60"], expected_ma60)

    def test_ma60_fallback_with_insufficient_data(self) -> None:
        """Test MA60 falls back to MA20 when data is insufficient."""
        dates = pd.date_range(start="2024-01-01", periods=25, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": range(25),
                "volume": [1000000] * 25,
            }
        )

        result = IndicatorCalculator.calculate_mas(data)

        # With less than 60 data points, MA60 should equal MA20
        assert len(data) < 60
        # Compare values only, not names
        pd.testing.assert_series_equal(
            result["MA60"].reset_index(drop=True), result["MA20"].reset_index(drop=True), check_names=False
        )

    def test_calculate_mas_preserves_original_data(self, sample_data: pd.DataFrame) -> None:
        """Test that calculate_mas preserves original columns."""
        result = IndicatorCalculator.calculate_mas(sample_data)

        # Original columns should still exist
        assert "date" in result.columns
        assert "open" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns


# =============================================================================
# MACD Tests
# =============================================================================
class TestMACDCalculations:
    """Test cases for MACD indicator calculations."""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample data for MACD testing."""
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        # Create trending data
        prices = 100 + np.cumsum(np.random.randn(50) * 0.3)

        return pd.DataFrame(
            {
                "date": dates,
                "close": prices,
                "volume": np.random.randint(1000000, 5000000, 50),
            }
        )

    def test_calculate_macd_adds_macd_columns(self, sample_data: pd.DataFrame) -> None:
        """Test that calculate_macd adds MACD columns."""
        result = IndicatorCalculator.calculate_macd(sample_data)

        assert "MACD_DIF" in result.columns
        assert "MACD_DEA" in result.columns
        assert "MACD_BAR" in result.columns

    def test_macd_dif_calculation(self, sample_data: pd.DataFrame) -> None:
        """Test MACD DIF calculation."""
        result = IndicatorCalculator.calculate_macd(sample_data)

        # DIF = EMA(12) - EMA(26)
        ema_fast = sample_data["close"].ewm(span=12, adjust=False).mean()
        ema_slow = sample_data["close"].ewm(span=26, adjust=False).mean()
        expected_dif = ema_fast - ema_slow
        expected_dif.name = "MACD_DIF"

        pd.testing.assert_series_equal(result["MACD_DIF"], expected_dif)

    def test_macd_dea_calculation(self, sample_data: pd.DataFrame) -> None:
        """Test MACD DEA (signal line) calculation."""
        result = IndicatorCalculator.calculate_macd(sample_data)

        # DEA = EMA(DIF, 9)
        ema_fast = sample_data["close"].ewm(span=12, adjust=False).mean()
        ema_slow = sample_data["close"].ewm(span=26, adjust=False).mean()
        dif = ema_fast - ema_slow
        expected_dea = dif.ewm(span=9, adjust=False).mean()
        expected_dea.name = "MACD_DEA"

        pd.testing.assert_series_equal(result["MACD_DEA"], expected_dea)

    def test_macd_bar_calculation(self, sample_data: pd.DataFrame) -> None:
        """Test MACD histogram (BAR) calculation."""
        result = IndicatorCalculator.calculate_macd(sample_data)

        # MACD_BAR = (DIF - DEA) * 2
        expected_bar = (result["MACD_DIF"] - result["MACD_DEA"]) * 2
        expected_bar.name = "MACD_BAR"

        pd.testing.assert_series_equal(result["MACD_BAR"], expected_bar)

    def test_macd_parameters(self) -> None:
        """Test MACD parameters are set correctly."""
        assert IndicatorCalculator.MACD_FAST == 12
        assert IndicatorCalculator.MACD_SLOW == 26
        assert IndicatorCalculator.MACD_SIGNAL == 9


# =============================================================================
# RSI Tests
# =============================================================================
class TestRSICalculations:
    """Test cases for RSI indicator calculations."""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample data for RSI testing."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        # Create data with both up and down movements
        np.random.seed(42)
        changes = np.random.randn(30) * 2
        prices = 100 + np.cumsum(changes)

        return pd.DataFrame(
            {
                "date": dates,
                "close": prices,
                "volume": np.random.randint(1000000, 5000000, 30),
            }
        )

    def test_calculate_rsi_adds_rsi_columns(self, sample_data: pd.DataFrame) -> None:
        """Test that calculate_rsi adds RSI columns."""
        result = IndicatorCalculator.calculate_rsi(sample_data)

        assert "RSI_6" in result.columns
        assert "RSI_12" in result.columns
        assert "RSI_24" in result.columns

    def test_rsi_values_in_valid_range(self, sample_data: pd.DataFrame) -> None:
        """Test RSI values are within 0-100 range."""
        result = IndicatorCalculator.calculate_rsi(sample_data)

        # RSI should be between 0 and 100
        assert result["RSI_6"].min() >= 0
        assert result["RSI_6"].max() <= 100
        assert result["RSI_12"].min() >= 0
        assert result["RSI_12"].max() <= 100
        assert result["RSI_24"].min() >= 0
        assert result["RSI_24"].max() <= 100

    def test_rsi_calculation_formula(self) -> None:
        """Test RSI calculation follows standard formula."""
        # Create simple test data with known pattern
        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
        prices = [100, 101, 102, 101, 100, 99, 98, 99, 100, 101]

        data = pd.DataFrame(
            {
                "date": dates,
                "close": prices,
                "volume": [1000000] * 10,
            }
        )

        result = IndicatorCalculator.calculate_rsi(data)

        # Calculate expected RSI for period 6 manually
        delta = pd.Series(prices).diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=6).mean()
        avg_loss = loss.rolling(window=6).mean()
        rs = avg_gain / avg_loss
        expected_rsi = 100 - (100 / (1 + rs))
        expected_rsi = expected_rsi.fillna(50)
        expected_rsi.name = "RSI_6"

        # Compare with some tolerance for floating point
        pd.testing.assert_series_equal(
            result["RSI_6"].iloc[6:].reset_index(drop=True),
            expected_rsi.iloc[6:].reset_index(drop=True),
            check_exact=False,
            rtol=0.01,
            check_names=False,
        )

    def test_rsi_fills_nan_with_neutral(self) -> None:
        """Test RSI fills NaN values with neutral value (50)."""
        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "close": [100, 101, 102, 103, 104],
                "volume": [1000000] * 5,
            }
        )

        result = IndicatorCalculator.calculate_rsi(data)

        # Early values should be filled with 50 (neutral)
        assert result["RSI_6"].iloc[0] == 50

    def test_rsi_parameters(self) -> None:
        """Test RSI parameters are set correctly."""
        assert IndicatorCalculator.RSI_SHORT == 6
        assert IndicatorCalculator.RSI_MID == 12
        assert IndicatorCalculator.RSI_LONG == 24


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================
class TestCalculatorEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_empty_dataframe(self) -> None:
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame(columns=["date", "close", "volume"])

        # Should not raise exception
        result = IndicatorCalculator.calculate_mas(empty_df)
        assert result.empty

    def test_single_row_data(self) -> None:
        """Test handling of single row data."""
        data = pd.DataFrame(
            {
                "date": ["2024-01-01"],
                "close": [100.0],
                "volume": [1000000],
            }
        )

        result = IndicatorCalculator.calculate_mas(data)

        # MA values should be NaN for single row
        assert pd.isna(result["MA5"].iloc[0])

    def test_missing_close_column(self) -> None:
        """Test handling of missing close column."""
        data = pd.DataFrame(
            {
                "date": pd.date_range(start="2024-01-01", periods=10, freq="D"),
                "volume": [1000000] * 10,
            }
        )

        # Should raise KeyError when close column is missing
        with pytest.raises(KeyError):
            IndicatorCalculator.calculate_mas(data)

    def test_chained_calculations(self) -> None:
        """Test chaining multiple calculations."""
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(50) * 0.5)

        data = pd.DataFrame(
            {
                "date": dates,
                "close": prices,
                "volume": np.random.randint(1000000, 5000000, 50),
            }
        )

        # Chain all calculations
        result = IndicatorCalculator.calculate_mas(data)
        result = IndicatorCalculator.calculate_macd(result)
        result = IndicatorCalculator.calculate_rsi(result)

        # All expected columns should be present
        expected_columns = [
            "MA5",
            "MA10",
            "MA20",
            "MA60",
            "MACD_DIF",
            "MACD_DEA",
            "MACD_BAR",
            "RSI_6",
            "RSI_12",
            "RSI_24",
        ]
        for col in expected_columns:
            assert col in result.columns
