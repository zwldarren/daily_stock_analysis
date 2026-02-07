"""
Unit tests for AI response parser module.

Tests cover:
- JSON response parsing
- Text response parsing (fallback)
- JSON cleaning and fixing
- Error handling
"""

import json

from stock_analyzer.ai.response_parser import ResponseParser
from stock_analyzer.domain.entities.analysis_result import AnalysisResult


# =============================================================================
# JSON Parsing Tests
# =============================================================================
class TestJSONParsing:
    """Test cases for JSON response parsing."""

    def test_parse_valid_json(self) -> None:
        """Test parsing valid JSON response."""
        response_text = json.dumps(
            {
                "sentiment_score": 75,
                "trend_prediction": "看多",
                "operation_advice": "买入",
                "confidence_level": "高",
            }
        )

        result = ResponseParser.parse(response_text, "600519", "贵州茅台")

        assert isinstance(result, AnalysisResult)
        assert result.code == "600519"
        assert result.name == "贵州茅台"
        assert result.sentiment_score == 75
        assert result.trend_prediction == "看多"
        assert result.operation_advice == "买入"
        assert result.confidence_level == "高"

    def test_parse_json_with_markdown(self) -> None:
        """Test parsing JSON wrapped in markdown code blocks."""
        response_text = """```json
{
    "sentiment_score": 60,
    "trend_prediction": "震荡",
    "operation_advice": "持有"
}
```"""

        result = ResponseParser.parse(response_text, "600519", "贵州茅台")

        assert result.sentiment_score == 60
        assert result.trend_prediction == "震荡"

    def test_parse_json_with_dashboard(self) -> None:
        """Test parsing JSON with dashboard data."""
        response_text = json.dumps(
            {
                "sentiment_score": 80,
                "trend_prediction": "看多",
                "operation_advice": "强烈买入",
                "dashboard": {
                    "core_conclusion": {
                        "one_sentence": "业绩稳健，建议持有",
                    },
                },
            }
        )

        result = ResponseParser.parse(response_text, "600519", "贵州茅台")

        assert result.dashboard is not None
        assert result.dashboard["core_conclusion"]["one_sentence"] == "业绩稳健，建议持有"

    def test_parse_decision_type_from_operation(self) -> None:
        """Test decision_type is inferred from operation_advice."""
        test_cases = [
            ("买入", "buy"),
            ("加仓", "buy"),
            ("强烈买入", "buy"),
            ("卖出", "sell"),
            ("减仓", "sell"),
            ("强烈卖出", "sell"),
            ("持有", "hold"),
            ("观望", "hold"),
        ]

        for advice, expected_decision in test_cases:
            response_text = json.dumps(
                {
                    "operation_advice": advice,
                }
            )

            result = ResponseParser.parse(response_text, "600519", "贵州茅台")
            assert result.decision_type == expected_decision, f"Failed for {advice}"

    def test_parse_with_explicit_decision_type(self) -> None:
        """Test explicit decision_type is preserved."""
        response_text = json.dumps(
            {
                "operation_advice": "持有",
                "decision_type": "buy",  # Explicit decision type
            }
        )

        result = ResponseParser.parse(response_text, "600519", "贵州茅台")

        assert result.decision_type == "buy"


# =============================================================================
# JSON Cleaning Tests
# =============================================================================
class TestJSONCleaning:
    """Test cases for JSON cleaning functions."""

    def test_clean_response_removes_json_markers(self) -> None:
        """Test that markdown JSON markers are removed."""
        text = """```json
{"key": "value"}
```"""
        cleaned = ResponseParser._clean_response(text)

        assert "```json" not in cleaned
        assert "```" not in cleaned
        assert '{"key": "value"}' in cleaned

    def test_clean_response_removes_generic_code_blocks(self) -> None:
        """Test that generic code block markers are removed."""
        text = '```\n{"key": "value"}\n```'
        cleaned = ResponseParser._clean_response(text)

        assert "```" not in cleaned
        assert '{"key": "value"}' in cleaned

    def test_fix_json_removes_comments(self) -> None:
        """Test that comments are removed from JSON."""
        json_str = """{
            // This is a comment
            "key": "value"
        }"""
        fixed = ResponseParser._fix_json(json_str)

        assert "// This is a comment" not in fixed
        assert '"key": "value"' in fixed

    def test_fix_json_removes_block_comments(self) -> None:
        """Test that block comments are removed from JSON."""
        json_str = """{
            /* Multi-line
               comment */
            "key": "value"
        }"""
        fixed = ResponseParser._fix_json(json_str)

        assert "/*" not in fixed
        assert "*/" not in fixed
        assert '"key": "value"' in fixed

    def test_fix_json_removes_trailing_commas(self) -> None:
        """Test that trailing commas are removed from JSON."""
        json_str = '{"key": "value",}'
        fixed = ResponseParser._fix_json(json_str)

        assert '{"key": "value"}' in fixed

    def test_fix_json_removes_trailing_commas_in_arrays(self) -> None:
        """Test that trailing commas in arrays are removed."""
        json_str = '["item1", "item2",]'
        fixed = ResponseParser._fix_json(json_str)

        assert '["item1", "item2"]' in fixed

    def test_fix_json_converts_boolean_values(self) -> None:
        """Test that Python boolean values are converted to JSON."""
        json_str = '{"success": True, "failed": False}'
        fixed = ResponseParser._fix_json(json_str)

        assert '"success": true' in fixed
        assert '"failed": false' in fixed


# =============================================================================
# Text Parsing Tests (Fallback)
# =============================================================================
class TestTextParsing:
    """Test cases for text-based parsing fallback."""

    def test_parse_text_positive_sentiment(self) -> None:
        """Test parsing text with positive sentiment."""
        text = """
        该股票表现强势，建议买入。技术指标显示上涨趋势，
        突破关键阻力位，呈现利好态势。
        """

        result = ResponseParser._parse_text(text, "600519", "贵州茅台")

        assert result.sentiment_score > 50
        assert result.trend_prediction == "看多"
        assert result.operation_advice == "买入"
        assert result.decision_type == "buy"

    def test_parse_text_negative_sentiment(self) -> None:
        """Test parsing text with negative sentiment."""
        text = """
        该股票走势弱势，建议卖出。技术指标显示下跌趋势，
        跌破支撑位，呈现利空态势，建议减仓。
        """

        result = ResponseParser._parse_text(text, "600519", "贵州茅台")

        assert result.sentiment_score < 50
        assert result.trend_prediction == "看空"
        assert result.operation_advice == "卖出"
        assert result.decision_type == "sell"

    def test_parse_text_neutral_sentiment(self) -> None:
        """Test parsing text with neutral sentiment."""
        text = """
        该股票目前处于盘整状态，建议观望。
        技术指标没有明显方向，等待更好时机。
        """

        result = ResponseParser._parse_text(text, "600519", "贵州茅台")

        assert result.sentiment_score == 50
        assert result.trend_prediction == "震荡"
        assert result.operation_advice == "持有"
        assert result.decision_type == "hold"

    def test_parse_text_english_keywords(self) -> None:
        """Test parsing text with English keywords."""
        text = """
        The stock shows bullish signals. Recommendation: BUY.
        Technical indicators are positive, showing upward momentum.
        """

        result = ResponseParser._parse_text(text, "AAPL", "Apple")

        assert result.sentiment_score > 50
        assert result.trend_prediction == "看多"
        assert result.operation_advice == "买入"

    def test_parse_text_returns_raw_response(self) -> None:
        """Test that raw response is preserved."""
        text = "Some analysis text"

        result = ResponseParser._parse_text(text, "600519", "贵州茅台")

        assert result.raw_response == text
        assert result.success is True


# =============================================================================
# Error Handling Tests
# =============================================================================
class TestErrorHandling:
    """Test cases for error handling."""

    def test_parse_empty_response(self) -> None:
        """Test parsing empty response."""
        result = ResponseParser.parse("", "600519", "贵州茅台")

        assert isinstance(result, AnalysisResult)
        assert result.code == "600519"
        # Should fall back to text parsing

    def test_parse_no_json_found(self) -> None:
        """Test parsing response with no JSON."""
        text = "This is just plain text with no JSON structure."

        result = ResponseParser.parse(text, "600519", "贵州茅台")

        assert isinstance(result, AnalysisResult)
        assert result.success is True

    def test_parse_invalid_json(self) -> None:
        """Test parsing invalid JSON (should fallback to text)."""
        text = '{"invalid json: missing closing brace'

        result = ResponseParser.parse(text, "600519", "贵州茅台")

        assert isinstance(result, AnalysisResult)
        assert result.success is True

    def test_stock_name_from_ai(self) -> None:
        """Test that AI-provided stock name is used when available."""
        response_text = json.dumps(
            {
                "stock_name": "贵州茅台酒业",
                "sentiment_score": 75,
            }
        )

        result = ResponseParser.parse(response_text, "600519", "股票600519")

        assert result.name == "贵州茅台酒业"


# =============================================================================
# Build Result Tests
# =============================================================================
class TestBuildResult:
    """Test cases for _build_result method."""

    def test_build_result_with_all_fields(self) -> None:
        """Test building result with all available fields."""
        data = {
            "sentiment_score": 75,
            "trend_prediction": "看多",
            "operation_advice": "买入",
            "confidence_level": "高",
            "trend_analysis": "趋势向上",
            "technical_analysis": "技术指标良好",
            "fundamental_analysis": "基本面稳健",
            "analysis_summary": "建议买入",
            "risk_warning": "注意市场风险",
            "search_performed": True,
            "data_sources": "技术面+基本面",
        }

        result = ResponseParser._build_result(data, "600519", "贵州茅台", "raw")

        assert result.trend_analysis == "趋势向上"
        assert result.technical_analysis == "技术指标良好"
        assert result.fundamental_analysis == "基本面稳健"
        assert result.analysis_summary == "建议买入"
        assert result.risk_warning == "注意市场风险"
        assert result.search_performed is True
        assert result.data_sources == "技术面+基本面"

    def test_build_result_defaults(self) -> None:
        """Test building result with missing fields uses defaults."""
        data = {}

        result = ResponseParser._build_result(data, "600519", "贵州茅台", "raw")

        assert result.sentiment_score == 50  # Default
        assert result.trend_prediction == "震荡"  # Default
        assert result.operation_advice == "持有"  # Default
        assert result.confidence_level == "中"  # Default
        assert result.success is True
