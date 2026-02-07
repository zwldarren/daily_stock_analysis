"""
Unit tests for domain models module (SearchResult, SearchResponse).

Tests cover:
- SearchResult creation and text conversion
- SearchResponse creation and context conversion
- Edge cases with missing data
"""

import pytest

from stock_analyzer.domain.models import SearchResponse, SearchResult


# =============================================================================
# SearchResult Tests
# =============================================================================
class TestSearchResult:
    """Test cases for SearchResult data class."""

    def test_basic_creation(self) -> None:
        """Test basic SearchResult creation."""
        result = SearchResult(
            title="Test Article",
            snippet="This is a test snippet",
            url="https://example.com/article",
            source="Example News",
        )

        assert result.title == "Test Article"
        assert result.snippet == "This is a test snippet"
        assert result.url == "https://example.com/article"
        assert result.source == "Example News"
        assert result.published_date is None

    def test_creation_with_date(self) -> None:
        """Test SearchResult creation with published date."""
        result = SearchResult(
            title="Test Article",
            snippet="This is a test snippet",
            url="https://example.com/article",
            source="Example News",
            published_date="2024-01-15",
        )

        assert result.published_date == "2024-01-15"

    def test_to_text_without_date(self) -> None:
        """Test text conversion without date."""
        result = SearchResult(
            title="Market Analysis",
            snippet="Stock market shows strong growth...",
            url="https://finance.com/news/123",
            source="Finance Daily",
        )

        text = result.to_text()

        assert "【Finance Daily】" in text
        assert "Market Analysis" in text
        assert "Stock market shows strong growth" in text
        assert "2024" not in text  # No date included

    def test_to_text_with_date(self) -> None:
        """Test text conversion with date."""
        result = SearchResult(
            title="Earnings Report",
            snippet="Q4 earnings exceeded expectations...",
            url="https://finance.com/earnings/456",
            source="Financial Times",
            published_date="2024-01-20",
        )

        text = result.to_text()

        assert "【Financial Times】" in text
        assert "Earnings Report" in text
        assert "(2024-01-20)" in text
        assert "Q4 earnings exceeded" in text

    def test_to_text_format(self) -> None:
        """Test text format is correct."""
        result = SearchResult(
            title="Title",
            snippet="Snippet",
            url="https://test.com",
            source="Source",
            published_date="2024-01-01",
        )

        text = result.to_text()

        # Expected format: 【Source】Title (date)\nSnippet
        expected = "【Source】Title (2024-01-01)\nSnippet"
        assert text == expected


# =============================================================================
# SearchResponse Tests
# =============================================================================
class TestSearchResponse:
    """Test cases for SearchResponse data class."""

    @pytest.fixture
    def sample_results(self) -> list[SearchResult]:
        """Create sample search results."""
        return [
            SearchResult(
                title="Article 1",
                snippet="Snippet 1",
                url="https://example.com/1",
                source="Source A",
                published_date="2024-01-01",
            ),
            SearchResult(
                title="Article 2",
                snippet="Snippet 2",
                url="https://example.com/2",
                source="Source B",
                published_date="2024-01-02",
            ),
            SearchResult(
                title="Article 3",
                snippet="Snippet 3",
                url="https://example.com/3",
                source="Source C",
            ),
        ]

    def test_basic_creation(self, sample_results: list[SearchResult]) -> None:
        """Test basic SearchResponse creation."""
        response = SearchResponse(
            query="stock analysis",
            results=sample_results,
            provider="google",
        )

        assert response.query == "stock analysis"
        assert len(response.results) == 3
        assert response.provider == "google"
        assert response.success is True
        assert response.error_message is None
        assert response.search_time == 0.0

    def test_creation_with_error(self) -> None:
        """Test SearchResponse creation with error."""
        response = SearchResponse(
            query="stock analysis",
            results=[],
            provider="google",
            success=False,
            error_message="API rate limit exceeded",
            search_time=2.5,
        )

        assert response.success is False
        assert response.error_message == "API rate limit exceeded"
        assert response.search_time == 2.5

    def test_to_context_success(self, sample_results: list[SearchResult]) -> None:
        """Test context conversion for successful search."""
        response = SearchResponse(
            query="贵州茅台",
            results=sample_results,
            provider="bing",
            search_time=1.2,
        )

        context = response.to_context()

        assert "贵州茅台 搜索结果" in context
        assert "来源：bing" in context
        assert "1." in context
        assert "2." in context
        assert "3." in context
        assert "Article 1" in context
        assert "Snippet 1" in context

    def test_to_context_limited_results(self, sample_results: list[SearchResult]) -> None:
        """Test context conversion with max_results limit."""
        response = SearchResponse(
            query="test",
            results=sample_results,
            provider="google",
        )

        context = response.to_context(max_results=2)

        # Should only include first 2 results
        assert "1." in context
        assert "2." in context
        assert "Article 3" not in context

    def test_to_context_no_results(self) -> None:
        """Test context conversion with no results."""
        response = SearchResponse(
            query="unknown stock",
            results=[],
            provider="google",
            success=True,
        )

        context = response.to_context()

        assert "未找到相关结果" in context
        assert "unknown stock" in context

    def test_to_context_failed_search(self) -> None:
        """Test context conversion for failed search."""
        response = SearchResponse(
            query="test query",
            results=[],
            provider="google",
            success=False,
            error_message="Network error",
        )

        context = response.to_context()

        assert "未找到相关结果" in context

    def test_to_context_format(self, sample_results: list[SearchResult]) -> None:
        """Test context format is correct."""
        response = SearchResponse(
            query="test",
            results=sample_results[:1],
            provider="test_provider",
        )

        context = response.to_context()

        lines = context.split("\n")
        assert lines[0] == "【test 搜索结果】（来源：test_provider）"
        assert lines[1] == ""  # Empty line before first result
        assert "1." in lines[2]


# =============================================================================
# Edge Cases
# =============================================================================
class TestEdgeCases:
    """Test edge cases."""

    def test_empty_snippet(self) -> None:
        """Test SearchResult with empty snippet."""
        result = SearchResult(
            title="Empty",
            snippet="",
            url="https://test.com",
            source="Test",
        )

        text = result.to_text()
        assert "Empty" in text
        assert text.endswith("\n")  # Ends with newline after empty snippet

    def test_very_long_snippet(self) -> None:
        """Test SearchResult with very long snippet."""
        long_snippet = "A" * 1000

        result = SearchResult(
            title="Long",
            snippet=long_snippet,
            url="https://test.com",
            source="Test",
        )

        text = result.to_text()
        assert long_snippet in text

    def test_unicode_content(self) -> None:
        """Test handling of unicode content."""
        result = SearchResult(
            title="中文标题",
            snippet="这是中文摘要内容",
            url="https://test.com",
            source="中文来源",
            published_date="2024-01-01",
        )

        text = result.to_text()
        assert "中文标题" in text
        assert "这是中文摘要" in text
        assert "中文来源" in text

    def test_special_characters_in_url(self) -> None:
        """Test handling of special characters in URL."""
        result = SearchResult(
            title="Test",
            snippet="Snippet",
            url="https://test.com/path?param=value&other=123",
            source="Test",
        )

        # URL is stored but not displayed in to_text
        text = result.to_text()
        assert "Test" in text
        assert "Snippet" in text
