"""
Unit tests for result formatter module.

Tests cover:
- Volume formatting
- Amount formatting
- Full result formatting
"""

import pytest

from stock_analyzer.technical.enums import (
    BuySignal,
    MACDStatus,
    RSIStatus,
    TrendStatus,
    VolumeStatus,
)
from stock_analyzer.technical.formatter import ResultFormatter
from stock_analyzer.technical.result import TrendAnalysisResult


# =============================================================================
# Volume Formatting Tests
# =============================================================================
class TestVolumeFormatting:
    """Test cases for volume formatting."""

    def test_format_volume_none(self) -> None:
        """Test formatting None volume."""
        result = ResultFormatter.format_volume(None)
        assert result == "N/A"

    def test_format_volume_billions(self) -> None:
        """Test formatting volume in billions (亿股)."""
        result = ResultFormatter.format_volume(150000000)  # 1.5 billion
        assert "亿股" in result
        assert "1.50" in result

    def test_format_volume_millions(self) -> None:
        """Test formatting volume in millions (万股)."""
        result = ResultFormatter.format_volume(1500000)  # 1.5 million
        assert "万股" in result
        assert "150.00" in result

    def test_format_volume_small(self) -> None:
        """Test formatting small volume."""
        result = ResultFormatter.format_volume(1500)  # 1,500 shares
        assert "股" in result
        assert "1500" in result

    def test_format_volume_zero(self) -> None:
        """Test formatting zero volume."""
        result = ResultFormatter.format_volume(0)
        assert "0" in result


# =============================================================================
# Amount Formatting Tests
# =============================================================================
class TestAmountFormatting:
    """Test cases for amount formatting."""

    def test_format_amount_none(self) -> None:
        """Test formatting None amount."""
        result = ResultFormatter.format_amount(None)
        assert result == "N/A"

    def test_format_amount_billions(self) -> None:
        """Test formatting amount in billions (亿元)."""
        result = ResultFormatter.format_amount(150000000)  # 1.5 billion
        assert "亿元" in result
        assert "1.50" in result

    def test_format_amount_millions(self) -> None:
        """Test formatting amount in millions (万元)."""
        result = ResultFormatter.format_amount(1500000)  # 1.5 million
        assert "万元" in result
        assert "150.00" in result

    def test_format_amount_small(self) -> None:
        """Test formatting small amount."""
        result = ResultFormatter.format_amount(1500)  # 1,500 yuan
        assert "元" in result
        assert "1500" in result


# =============================================================================
# Full Result Formatting Tests
# =============================================================================
class TestResultFormatting:
    """Test cases for full result formatting."""

    @pytest.fixture
    def sample_result(self) -> TrendAnalysisResult:
        """Create a sample result for testing."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.BULL
        result.ma_alignment = "多头排列 MA5>MA10>MA20"
        result.trend_strength = 75.0
        result.ma5 = 102.0
        result.ma10 = 101.0
        result.ma20 = 100.0
        result.ma60 = 98.0
        result.current_price = 102.5
        result.bias_ma5 = 0.5
        result.bias_ma10 = 1.5
        result.bias_ma20 = 2.5
        result.volume_status = VolumeStatus.HEAVY_VOLUME_UP
        result.volume_ratio_5d = 1.8
        result.volume_trend = "放量上涨，多头力量强劲"
        result.macd_dif = 0.5
        result.macd_dea = 0.3
        result.macd_bar = 0.4
        result.macd_status = MACDStatus.GOLDEN_CROSS
        result.macd_signal = "金叉，趋势向上"
        result.rsi_6 = 65.0
        result.rsi_12 = 60.0
        result.rsi_24 = 55.0
        result.rsi_status = RSIStatus.STRONG_BUY
        result.rsi_signal = "RSI强势，多头力量充足"
        result.buy_signal = BuySignal.BUY
        result.signal_score = 68
        result.signal_reasons = [
            "多头排列，顺势做多",
            "价格贴近MA5，介入好时机",
        ]
        result.risk_factors = [
            "乖离率略高，注意风险",
        ]
        return result

    def test_format_contains_stock_code(self, sample_result: TrendAnalysisResult) -> None:
        """Test formatted output contains stock code."""
        formatted = ResultFormatter.format(sample_result)
        assert "600519" in formatted

    def test_format_contains_trend_info(self, sample_result: TrendAnalysisResult) -> None:
        """Test formatted output contains trend information."""
        formatted = ResultFormatter.format(sample_result)
        assert "多头排列" in formatted
        assert "75" in formatted  # trend strength

    def test_format_contains_ma_data(self, sample_result: TrendAnalysisResult) -> None:
        """Test formatted output contains MA data."""
        formatted = ResultFormatter.format(sample_result)
        assert "MA5" in formatted
        assert "MA10" in formatted
        assert "MA20" in formatted
        assert "102.00" in formatted or "102.0" in formatted

    def test_format_contains_volume_info(self, sample_result: TrendAnalysisResult) -> None:
        """Test formatted output contains volume information."""
        formatted = ResultFormatter.format(sample_result)
        assert "放量上涨" in formatted
        assert "1.80" in formatted or "1.8" in formatted

    def test_format_contains_macd_info(self, sample_result: TrendAnalysisResult) -> None:
        """Test formatted output contains MACD information."""
        formatted = ResultFormatter.format(sample_result)
        assert "MACD" in formatted
        assert "金叉" in formatted
        assert "0.5000" in formatted or "0.5" in formatted

    def test_format_contains_rsi_info(self, sample_result: TrendAnalysisResult) -> None:
        """Test formatted output contains RSI information."""
        formatted = ResultFormatter.format(sample_result)
        assert "RSI" in formatted
        assert "65.0" in formatted or "65" in formatted

    def test_format_contains_signal(self, sample_result: TrendAnalysisResult) -> None:
        """Test formatted output contains buy signal."""
        formatted = ResultFormatter.format(sample_result)
        assert "买入" in formatted
        assert "68" in formatted  # signal score

    def test_format_contains_reasons(self, sample_result: TrendAnalysisResult) -> None:
        """Test formatted output contains signal reasons."""
        formatted = ResultFormatter.format(sample_result)
        assert "买入理由" in formatted
        assert "多头排列" in formatted

    def test_format_contains_risks(self, sample_result: TrendAnalysisResult) -> None:
        """Test formatted output contains risk factors."""
        formatted = ResultFormatter.format(sample_result)
        assert "风险因素" in formatted
        assert "乖离率" in formatted

    def test_format_structure(self, sample_result: TrendAnalysisResult) -> None:
        """Test formatted output has proper structure with sections."""
        formatted = ResultFormatter.format(sample_result)

        # Should have section headers
        assert "===" in formatted  # Section separator
        assert "趋势判断" in formatted
        assert "均线数据" in formatted
        assert "量能分析" in formatted


# =============================================================================
# Edge Cases
# =============================================================================
class TestFormattingEdgeCases:
    """Test edge cases for formatting."""

    def test_format_empty_reasons(self) -> None:
        """Test formatting with empty reasons list."""
        result = TrendAnalysisResult(code="600519")
        result.signal_reasons = []
        result.risk_factors = []

        formatted = ResultFormatter.format(result)

        # Should not crash and should not have reasons section
        assert "600519" in formatted

    def test_format_zero_values(self) -> None:
        """Test formatting with zero values."""
        result = TrendAnalysisResult(code="600519")
        result.ma5 = 0.0
        result.ma10 = 0.0
        result.ma20 = 0.0
        result.current_price = 0.0

        formatted = ResultFormatter.format(result)

        # Should not crash
        assert "600519" in formatted

    def test_format_very_large_values(self) -> None:
        """Test formatting with very large values."""
        result = TrendAnalysisResult(code="600519")
        result.current_price = 999999.99
        result.ma5 = 999999.99
        result.volume_ratio_5d = 999.99

        formatted = ResultFormatter.format(result)

        # Should format large numbers correctly
        assert "999999" in formatted or "1000000" in formatted
