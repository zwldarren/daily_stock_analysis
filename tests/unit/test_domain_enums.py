"""
Unit tests for domain enums module (ReportType).

Tests cover:
- ReportType enum values
- from_str conversion method
- display_name property
"""

from stock_analyzer.domain.enums import ReportType


# =============================================================================
# ReportType Tests
# =============================================================================
class TestReportType:
    """Test cases for ReportType enum."""

    def test_simple_value(self) -> None:
        """Test SIMPLE report type value."""
        assert ReportType.SIMPLE.value == "simple"

    def test_full_value(self) -> None:
        """Test FULL report type value."""
        assert ReportType.FULL.value == "full"

    def test_str_enum_behavior(self) -> None:
        """Test that ReportType behaves like a string."""
        # Can be compared with strings
        assert ReportType.SIMPLE == "simple"
        assert ReportType.FULL == "full"

        # Can be used in string contexts
        assert str(ReportType.SIMPLE) == "simple"

    def test_all_report_types(self) -> None:
        """Test that all expected report types are defined."""
        expected_types = ["simple", "full"]
        actual_types = [rt.value for rt in ReportType]

        for expected in expected_types:
            assert expected in actual_types


# =============================================================================
# from_str Tests
# =============================================================================
class TestFromStr:
    """Test cases for from_str method."""

    def test_from_str_simple(self) -> None:
        """Test from_str with 'simple'."""
        result = ReportType.from_str("simple")
        assert result == ReportType.SIMPLE

    def test_from_str_full(self) -> None:
        """Test from_str with 'full'."""
        result = ReportType.from_str("full")
        assert result == ReportType.FULL

    def test_from_str_case_insensitive(self) -> None:
        """Test from_str is case insensitive."""
        assert ReportType.from_str("SIMPLE") == ReportType.SIMPLE
        assert ReportType.from_str("Simple") == ReportType.SIMPLE
        assert ReportType.from_str("FULL") == ReportType.FULL
        assert ReportType.from_str("Full") == ReportType.FULL

    def test_from_str_with_whitespace(self) -> None:
        """Test from_str handles whitespace."""
        assert ReportType.from_str("  simple  ") == ReportType.SIMPLE
        assert ReportType.from_str("full ") == ReportType.FULL

    def test_from_str_invalid_returns_simple(self) -> None:
        """Test from_str returns SIMPLE for invalid input."""
        result = ReportType.from_str("invalid")
        assert result == ReportType.SIMPLE

    def test_from_str_empty_returns_simple(self) -> None:
        """Test from_str returns SIMPLE for empty string."""
        result = ReportType.from_str("")
        assert result == ReportType.SIMPLE

    def test_from_str_none_returns_simple(self) -> None:
        """Test from_str returns SIMPLE for None input."""
        result = ReportType.from_str(None)  # type: ignore[arg-type]
        assert result == ReportType.SIMPLE


# =============================================================================
# display_name Tests
# =============================================================================
class TestDisplayName:
    """Test cases for display_name property."""

    def test_simple_display_name(self) -> None:
        """Test display name for SIMPLE."""
        assert ReportType.SIMPLE.display_name == "精简报告"

    def test_full_display_name(self) -> None:
        """Test display name for FULL."""
        assert ReportType.FULL.display_name == "完整报告"

    def test_display_name_chinese(self) -> None:
        """Test that display names are in Chinese."""
        for rt in ReportType:
            assert len(rt.display_name) > 0
            # Should contain Chinese characters
            assert any("\u4e00" <= char <= "\u9fff" for char in rt.display_name)


# =============================================================================
# Edge Cases
# =============================================================================
class TestEdgeCases:
    """Test edge cases."""

    def test_enum_comparison(self) -> None:
        """Test enum comparison operations."""
        assert ReportType.SIMPLE == ReportType.SIMPLE
        assert ReportType.SIMPLE != ReportType.FULL
        assert ReportType.SIMPLE is ReportType.SIMPLE

    def test_enum_in_collection(self) -> None:
        """Test enum membership in collections."""
        report_types = [ReportType.SIMPLE, ReportType.FULL]

        assert ReportType.SIMPLE in report_types
        assert ReportType.FULL in report_types

    def test_enum_hashable(self) -> None:
        """Test that enums are hashable and can be used as dict keys."""
        report_config = {
            ReportType.SIMPLE: {"max_length": 1000},
            ReportType.FULL: {"max_length": 5000},
        }

        assert report_config[ReportType.SIMPLE]["max_length"] == 1000
        assert report_config[ReportType.FULL]["max_length"] == 5000
