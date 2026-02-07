"""
Unit tests for TrendAnalysisResult data class.

Tests cover:
- Result creation with default values
- to_dict conversion
- Field validation
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


# =============================================================================
# Result Creation Tests
# =============================================================================
class TestResultCreation:
    """Test cases for TrendAnalysisResult creation."""

    def test_basic_creation(self) -> None:
        """Test basic result creation with code only."""
        result = TrendAnalysisResult(code="600519")

        assert result.code == "600519"

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        result = TrendAnalysisResult(code="600519")

        # Check default enum values
        assert result.trend_status == TrendStatus.CONSOLIDATION
        assert result.volume_status == VolumeStatus.NORMAL
        assert result.macd_status == MACDStatus.BULLISH
        assert result.rsi_status == RSIStatus.NEUTRAL
        assert result.buy_signal == BuySignal.WAIT

        # Check default numeric values
        assert result.trend_strength == 0.0
        assert result.ma5 == 0.0
        assert result.ma10 == 0.0
        assert result.ma20 == 0.0
        assert result.ma60 == 0.0
        assert result.current_price == 0.0
        assert result.bias_ma5 == 0.0
        assert result.bias_ma10 == 0.0
        assert result.bias_ma20 == 0.0
        assert result.volume_ratio_5d == 0.0
        assert result.macd_dif == 0.0
        assert result.macd_dea == 0.0
        assert result.macd_bar == 0.0
        assert result.rsi_6 == 0.0
        assert result.rsi_12 == 0.0
        assert result.rsi_24 == 0.0
        assert result.signal_score == 0

        # Check default boolean values
        assert result.support_ma5 is False
        assert result.support_ma10 is False

        # Check default list values
        assert result.resistance_levels == []
        assert result.support_levels == []
        assert result.signal_reasons == []
        assert result.risk_factors == []

    def test_custom_values(self) -> None:
        """Test result creation with custom values."""
        result = TrendAnalysisResult(
            code="600519",
            trend_status=TrendStatus.BULL,
            trend_strength=75.0,
            ma5=102.0,
            ma10=101.0,
            ma20=100.0,
            current_price=102.5,
            buy_signal=BuySignal.BUY,
            signal_score=68,
        )

        assert result.code == "600519"
        assert result.trend_status == TrendStatus.BULL
        assert result.trend_strength == 75.0
        assert result.ma5 == 102.0
        assert result.ma10 == 101.0
        assert result.ma20 == 100.0
        assert result.current_price == 102.5
        assert result.buy_signal == BuySignal.BUY
        assert result.signal_score == 68


# =============================================================================
# to_dict Tests
# =============================================================================
class TestToDict:
    """Test cases for to_dict method."""

    @pytest.fixture
    def sample_result(self) -> TrendAnalysisResult:
        """Create a sample result for testing."""
        result = TrendAnalysisResult(code="600519")
        result.trend_status = TrendStatus.BULL
        result.trend_strength = 75.0
        result.ma5 = 102.0
        result.ma10 = 101.0
        result.ma20 = 100.0
        result.current_price = 102.5
        result.bias_ma5 = 0.5
        result.volume_status = VolumeStatus.HEAVY_VOLUME_UP
        result.volume_ratio_5d = 1.8
        result.support_ma5 = True
        result.macd_dif = 0.5
        result.macd_dea = 0.3
        result.macd_bar = 0.4
        result.macd_status = MACDStatus.GOLDEN_CROSS
        result.rsi_6 = 65.0
        result.rsi_12 = 60.0
        result.rsi_24 = 55.0
        result.rsi_status = RSIStatus.STRONG_BUY
        result.buy_signal = BuySignal.BUY
        result.signal_score = 68
        result.signal_reasons = ["多头排列", "金叉"]
        result.risk_factors = ["乖离率略高"]
        return result

    def test_to_dict_returns_dict(self, sample_result: TrendAnalysisResult) -> None:
        """Test to_dict returns a dictionary."""
        result_dict = sample_result.to_dict()

        assert isinstance(result_dict, dict)

    def test_to_dict_contains_code(self, sample_result: TrendAnalysisResult) -> None:
        """Test to_dict contains stock code."""
        result_dict = sample_result.to_dict()

        assert result_dict["code"] == "600519"

    def test_to_dict_contains_enum_values(self, sample_result: TrendAnalysisResult) -> None:
        """Test to_dict converts enums to their values."""
        result_dict = sample_result.to_dict()

        # Enums should be converted to their string values
        assert result_dict["trend_status"] == "多头排列"
        assert result_dict["volume_status"] == "放量上涨"
        assert result_dict["macd_status"] == "金叉"
        assert result_dict["rsi_status"] == "强势买入"
        assert result_dict["buy_signal"] == "买入"

    def test_to_dict_contains_numeric_values(self, sample_result: TrendAnalysisResult) -> None:
        """Test to_dict contains numeric values."""
        result_dict = sample_result.to_dict()

        assert result_dict["ma5"] == 102.0
        assert result_dict["ma10"] == 101.0
        assert result_dict["ma20"] == 100.0
        assert result_dict["current_price"] == 102.5
        assert result_dict["trend_strength"] == 75.0
        assert result_dict["signal_score"] == 68

    def test_to_dict_contains_lists(self, sample_result: TrendAnalysisResult) -> None:
        """Test to_dict contains list values."""
        result_dict = sample_result.to_dict()

        assert result_dict["signal_reasons"] == ["多头排列", "金叉"]
        assert result_dict["risk_factors"] == ["乖离率略高"]

    def test_to_dict_all_fields_present(self, sample_result: TrendAnalysisResult) -> None:
        """Test to_dict contains all expected fields."""
        result_dict = sample_result.to_dict()

        expected_fields = [
            "code",
            "trend_status",
            "ma_alignment",
            "trend_strength",
            "ma5",
            "ma10",
            "ma20",
            "ma60",
            "current_price",
            "bias_ma5",
            "bias_ma10",
            "bias_ma20",
            "volume_status",
            "volume_ratio_5d",
            "volume_trend",
            "support_ma5",
            "support_ma10",
            "buy_signal",
            "signal_score",
            "signal_reasons",
            "risk_factors",
            "macd_dif",
            "macd_dea",
            "macd_bar",
            "macd_status",
            "macd_signal",
            "rsi_6",
            "rsi_12",
            "rsi_24",
            "rsi_status",
            "rsi_signal",
        ]

        for field in expected_fields:
            assert field in result_dict, f"Field {field} not found in dict"


# =============================================================================
# Field Mutation Tests
# =============================================================================
class TestFieldMutation:
    """Test cases for field mutation."""

    def test_field_mutation(self) -> None:
        """Test that fields can be mutated after creation."""
        result = TrendAnalysisResult(code="600519")

        # Mutate fields
        result.trend_status = TrendStatus.STRONG_BULL
        result.ma5 = 105.0
        result.signal_score = 85
        result.signal_reasons.append("强烈买入信号")

        assert result.trend_status == TrendStatus.STRONG_BULL
        assert result.ma5 == 105.0
        assert result.signal_score == 85
        assert "强烈买入信号" in result.signal_reasons

    def test_list_field_append(self) -> None:
        """Test appending to list fields."""
        result = TrendAnalysisResult(code="600519")

        result.signal_reasons.append("理由1")
        result.signal_reasons.append("理由2")
        result.risk_factors.append("风险1")

        assert len(result.signal_reasons) == 2
        assert len(result.risk_factors) == 1

    def test_list_field_extend(self) -> None:
        """Test extending list fields."""
        result = TrendAnalysisResult(code="600519")

        result.signal_reasons.extend(["理由1", "理由2", "理由3"])

        assert len(result.signal_reasons) == 3


# =============================================================================
# Edge Cases
# =============================================================================
class TestEdgeCases:
    """Test edge cases."""

    def test_empty_code(self) -> None:
        """Test result with empty code."""
        result = TrendAnalysisResult(code="")

        assert result.code == ""

    def test_very_long_code(self) -> None:
        """Test result with very long code."""
        long_code = "A" * 1000
        result = TrendAnalysisResult(code=long_code)

        assert result.code == long_code

    def test_negative_values(self) -> None:
        """Test result with negative numeric values."""
        result = TrendAnalysisResult(code="600519")
        result.bias_ma5 = -5.0
        result.macd_dif = -0.5

        assert result.bias_ma5 == -5.0
        assert result.macd_dif == -0.5

    def test_zero_values(self) -> None:
        """Test result with zero values."""
        result = TrendAnalysisResult(code="600519")
        result.ma5 = 0.0
        result.signal_score = 0

        assert result.ma5 == 0.0
        assert result.signal_score == 0
