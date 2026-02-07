"""
Unit tests for AI prompt builder module.

Tests cover:
- Analysis prompt building
- Context data integration
- Realtime data integration
- Chip distribution data integration
"""

from unittest.mock import patch

from stock_analyzer.ai.prompt_builder import PromptBuilder


# =============================================================================
# Basic Prompt Building Tests
# =============================================================================
class TestBasicPromptBuilding:
    """Test cases for basic prompt building."""

    def test_build_prompt_contains_stock_code(self) -> None:
        """Test that prompt contains stock code."""
        context = {"code": "600519"}

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "600519" in prompt

    def test_build_prompt_contains_stock_name(self) -> None:
        """Test that prompt contains stock name."""
        context = {"code": "600519"}

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "贵州茅台" in prompt

    def test_build_prompt_contains_technical_sections(self) -> None:
        """Test that prompt contains technical analysis sections."""
        context = {"code": "600519"}

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "技术面数据" in prompt or "Technical" in prompt
        assert "均线" in prompt or "MA" in prompt

    def test_build_prompt_contains_output_requirements(self) -> None:
        """Test that prompt contains output requirements."""
        context = {"code": "600519"}

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "JSON" in prompt
        assert "决策仪表盘" in prompt


# =============================================================================
# Context Data Integration Tests
# =============================================================================
class TestContextDataIntegration:
    """Test cases for context data integration."""

    def test_build_prompt_with_price_data(self) -> None:
        """Test prompt includes price data from context."""
        context = {
            "code": "600519",
            "today": {
                "close": 1800.0,
                "open": 1780.0,
                "high": 1810.0,
                "low": 1770.0,
                "pct_chg": 1.5,
                "volume": 1000000,
                "amount": 1800000000,
            },
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "1800.0" in prompt or "1800" in prompt
        assert "1780.0" in prompt or "1780" in prompt

    def test_build_prompt_with_ma_data(self) -> None:
        """Test prompt includes MA data from context."""
        context = {
            "code": "600519",
            "today": {
                "ma5": 1790.0,
                "ma10": 1780.0,
                "ma20": 1770.0,
            },
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "1790" in prompt
        assert "1780" in prompt
        assert "1770" in prompt

    def test_build_prompt_with_ma_status(self) -> None:
        """Test prompt includes MA status from context."""
        context = {
            "code": "600519",
            "ma_status": "多头排列",
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "多头排列" in prompt


# =============================================================================
# Realtime Data Integration Tests
# =============================================================================
class TestRealtimeDataIntegration:
    """Test cases for realtime data integration."""

    def test_build_prompt_with_realtime_data(self) -> None:
        """Test prompt includes realtime data when available."""
        context = {
            "code": "600519",
            "realtime": {
                "price": 1805.0,
                "change_percent": 1.8,
                "volume_ratio": 1.5,
                "turnover_rate": 0.8,
                "pe_ratio": 25.0,
                "pb_ratio": 8.0,
            },
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "1805" in prompt
        assert "1.8" in prompt or "1.80" in prompt
        assert "量比" in prompt or "volume_ratio" in prompt.lower()

    def test_realtime_price_overrides_close(self) -> None:
        """Test that realtime price overrides historical close price."""
        context = {
            "code": "600519",
            "today": {
                "close": 1800.0,
            },
            "realtime": {
                "price": 1805.0,
            },
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        # Realtime price should be in the prompt
        assert "1805" in prompt

    def test_realtime_change_overrides_pct_chg(self) -> None:
        """Test that realtime change overrides historical pct_chg."""
        context = {
            "code": "600519",
            "today": {
                "pct_chg": 1.5,
            },
            "realtime": {
                "change_percent": 1.8,
            },
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        # Realtime change should be reflected
        assert "1.8" in prompt or "1.80" in prompt


# =============================================================================
# Chip Distribution Tests
# =============================================================================
class TestChipDistribution:
    """Test cases for chip distribution data integration."""

    def test_build_prompt_with_chip_data(self) -> None:
        """Test prompt includes chip distribution data."""
        context = {
            "code": "600519",
            "chip": {
                "profit_ratio": 0.75,
                "avg_cost": 1750.0,
                "concentration_90": 0.12,
                "concentration_70": 0.08,
                "chip_status": "集中",
            },
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "筹码" in prompt or "chip" in prompt.lower()
        assert "75" in prompt or "0.75" in prompt  # Profit ratio
        assert "1750" in prompt  # Average cost

    def test_chip_data_formatting(self) -> None:
        """Test chip data is properly formatted in prompt."""
        context = {
            "code": "600519",
            "chip": {
                "profit_ratio": 0.85,
                "avg_cost": 1700.0,
                "concentration_90": 0.10,
            },
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        # Should be formatted as percentage
        assert "85" in prompt or "85.0" in prompt


# =============================================================================
# Trend Analysis Integration Tests
# =============================================================================
class TestTrendAnalysisIntegration:
    """Test cases for trend analysis data integration."""

    def test_build_prompt_with_trend_analysis(self) -> None:
        """Test prompt includes trend analysis data."""
        context = {
            "code": "600519",
            "trend_analysis": {
                "trend_status": "多头排列",
                "ma_alignment": "MA5>MA10>MA20",
                "trend_strength": 80,
                "bias_ma5": 2.5,
                "bias_ma10": 3.0,
                "volume_status": "放量上涨",
                "volume_trend": "多头力量强劲",
                "buy_signal": "买入",
                "signal_score": 75,
                "signal_reasons": ["多头排列", "放量突破"],
                "risk_factors": ["乖离率略高"],
            },
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "多头排列" in prompt
        assert "80" in prompt or "80/100" in prompt
        assert "2.5" in prompt or "2.50" in prompt


# =============================================================================
# News Context Tests
# =============================================================================
class TestNewsContext:
    """Test cases for news context integration."""

    def test_build_prompt_with_news(self) -> None:
        """Test prompt includes news context when provided."""
        context = {"code": "600519"}
        news = """
        1. 贵州茅台发布业绩预告，Q4净利润同比增长20%
        2. 白酒行业整体向好，茅台渠道库存下降
        """

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台", news)

        assert "舆情情报" in prompt or "News" in prompt
        assert "贵州茅台" in prompt
        assert "Q4净利润" in prompt or "业绩预告" in prompt

    def test_build_prompt_without_news(self) -> None:
        """Test prompt handles missing news gracefully."""
        context = {"code": "600519"}

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台", None)

        assert "未搜索" in prompt or "no news" in prompt.lower()


# =============================================================================
# Data Missing Warning Tests
# =============================================================================
class TestDataMissingWarning:
    """Test cases for data missing warning."""

    def test_data_missing_warning_included(self) -> None:
        """Test that data missing warning is included when flag is set."""
        context = {
            "code": "600519",
            "data_missing": True,
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "数据缺失" in prompt or "data missing" in prompt.lower()
        assert "N/A" in prompt or "无法获取" in prompt

    def test_no_warning_when_data_complete(self) -> None:
        """Test that no warning when data is complete."""
        context = {
            "code": "600519",
            "data_missing": False,
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        # Should not contain data missing warning
        assert "数据缺失警告" not in prompt


# =============================================================================
# Stock Name Resolution Tests
# =============================================================================
class TestStockNameResolution:
    """Test cases for stock name resolution."""

    def test_stock_name_from_context(self) -> None:
        """Test stock name is taken from context when available."""
        context = {
            "code": "600519",
            "stock_name": "贵州茅台酒股份有限公司",
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "贵州茅台")

        assert "贵州茅台酒股份有限公司" in prompt

    @patch("stock_analyzer.ai.prompt_builder.get_stock_name_from_context")
    def test_stock_name_fallback(self, mock_get_name) -> None:
        """Test stock name fallback when context name is generic."""
        mock_get_name.return_value = "贵州茅台酒业"

        context = {
            "code": "600519",
            "stock_name": "股票600519",  # Generic name
        }

        prompt = PromptBuilder.build_analysis_prompt(context, "股票600519")

        # Should use the resolved name
        assert "贵州茅台酒业" in prompt
