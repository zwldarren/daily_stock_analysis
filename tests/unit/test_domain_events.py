"""
Unit tests for domain events module.

Tests cover:
- DomainEvent base class
- EventBus functionality
- StockAnalyzed event
- StockAnalysisFailed event
- MarketReviewCompleted event
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from stock_analyzer.domain.events import DomainEvent, EventBus, event_bus
from stock_analyzer.domain.events.stock_events import (
    MarketReviewCompleted,
    StockAnalysisFailed,
    StockAnalyzed,
)


# =============================================================================
# DomainEvent Tests
# =============================================================================
class TestDomainEvent:
    """Test cases for DomainEvent base class."""

    def test_domain_event_is_abstract(self) -> None:
        """Test that DomainEvent is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            DomainEvent()

    def test_concrete_event_creation(self) -> None:
        """Test creating concrete event instances."""
        # Create a mock analysis result
        mock_result = MagicMock()

        event = StockAnalyzed(
            stock_code="600519",
            analysis_result=mock_result,
        )

        assert event.stock_code == "600519"
        assert event.analysis_result == mock_result
        assert event.event_type == "stock_analyzed"
        assert isinstance(event.timestamp, datetime)


# =============================================================================
# StockAnalyzed Event Tests
# =============================================================================
class TestStockAnalyzed:
    """Test cases for StockAnalyzed event."""

    def test_event_creation(self) -> None:
        """Test StockAnalyzed event creation."""
        mock_result = {"code": "600519", "score": 75}

        event = StockAnalyzed(
            stock_code="600519",
            analysis_result=mock_result,
        )

        assert event.stock_code == "600519"
        assert event.analysis_result == mock_result
        assert event.event_type == "stock_analyzed"

    def test_event_timestamp(self) -> None:
        """Test that event has timestamp."""
        mock_result = MagicMock()

        before = datetime.now()
        event = StockAnalyzed(
            stock_code="600519",
            analysis_result=mock_result,
        )
        after = datetime.now()

        assert before <= event.timestamp <= after

    def test_event_is_frozen(self) -> None:
        """Test that event is immutable (frozen dataclass)."""
        # Verify it's a frozen dataclass by checking the class attribute
        assert StockAnalyzed.__dataclass_params__.frozen is True


# =============================================================================
# StockAnalysisFailed Event Tests
# =============================================================================
class TestStockAnalysisFailed:
    """Test cases for StockAnalysisFailed event."""

    def test_event_creation(self) -> None:
        """Test StockAnalysisFailed event creation."""
        event = StockAnalysisFailed(
            stock_code="600519",
            error="API timeout",
        )

        assert event.stock_code == "600519"
        assert event.error == "API timeout"
        assert event.event_type == "stock_analysis_failed"

    def test_event_with_exception(self) -> None:
        """Test event creation with exception error."""
        error_msg = "Connection failed after 3 retries"

        event = StockAnalysisFailed(
            stock_code="600519",
            error=error_msg,
        )

        assert event.error == error_msg


# =============================================================================
# MarketReviewCompleted Event Tests
# =============================================================================
class TestMarketReviewCompleted:
    """Test cases for MarketReviewCompleted event."""

    def test_event_creation(self) -> None:
        """Test MarketReviewCompleted event creation."""
        market_data = {
            "index": "上证指数",
            "change": 1.5,
            "volume": 1000000000,
        }

        event = MarketReviewCompleted(
            market_data=market_data,
        )

        assert event.market_data == market_data
        assert event.event_type == "market_review_completed"

    def test_event_with_complex_data(self) -> None:
        """Test event with complex market data."""
        market_data = {
            "indices": {
                "sh": {"close": 3000.0, "change": 0.5},
                "sz": {"close": 10000.0, "change": -0.3},
            },
            "leaders": ["600519", "000001"],
            "laggards": ["300001", "002001"],
        }

        event = MarketReviewCompleted(market_data=market_data)

        assert event.market_data["indices"]["sh"]["close"] == 3000.0
        assert "600519" in event.market_data["leaders"]


# =============================================================================
# EventBus Tests
# =============================================================================
class TestEventBus:
    """Test cases for EventBus."""

    @pytest.fixture
    def fresh_bus(self) -> EventBus:
        """Create a fresh event bus for testing."""
        return EventBus()

    def test_event_bus_initialization(self, fresh_bus: EventBus) -> None:
        """Test event bus initialization."""
        assert fresh_bus._handlers == {}

    def test_subscribe_handler(self, fresh_bus: EventBus) -> None:
        """Test subscribing a handler to an event type."""
        handler_called = False

        def handler(event: StockAnalyzed) -> None:
            nonlocal handler_called
            handler_called = True

        fresh_bus.subscribe("stock_analyzed", handler)

        assert "stock_analyzed" in fresh_bus._handlers
        assert handler in fresh_bus._handlers["stock_analyzed"]

    def test_unsubscribe_handler(self, fresh_bus: EventBus) -> None:
        """Test unsubscribing a handler."""

        def handler(event: StockAnalyzed) -> None:
            pass

        fresh_bus.subscribe("stock_analyzed", handler)
        fresh_bus.unsubscribe("stock_analyzed", handler)

        assert handler not in fresh_bus._handlers["stock_analyzed"]

    def test_publish_event(self, fresh_bus: EventBus) -> None:
        """Test publishing an event."""
        received_events = []

        def handler(event: StockAnalyzed) -> None:
            received_events.append(event)

        fresh_bus.subscribe("stock_analyzed", handler)

        mock_result = MagicMock()
        event = StockAnalyzed(
            stock_code="600519",
            analysis_result=mock_result,
        )

        fresh_bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].stock_code == "600519"

    def test_publish_no_handlers(self, fresh_bus: EventBus) -> None:
        """Test publishing when no handlers are registered."""
        # Should not raise exception
        mock_result = MagicMock()
        event = StockAnalyzed(
            stock_code="600519",
            analysis_result=mock_result,
        )

        fresh_bus.publish(event)  # Should not raise

    def test_multiple_handlers(self, fresh_bus: EventBus) -> None:
        """Test multiple handlers for same event type."""
        handler1_called = False
        handler2_called = False

        def handler1(event: StockAnalyzed) -> None:
            nonlocal handler1_called
            handler1_called = True

        def handler2(event: StockAnalyzed) -> None:
            nonlocal handler2_called
            handler2_called = True

        fresh_bus.subscribe("stock_analyzed", handler1)
        fresh_bus.subscribe("stock_analyzed", handler2)

        mock_result = MagicMock()
        event = StockAnalyzed(
            stock_code="600519",
            analysis_result=mock_result,
        )

        fresh_bus.publish(event)

        assert handler1_called
        assert handler2_called

    def test_handler_exception_isolated(self, fresh_bus: EventBus) -> None:
        """Test that handler exceptions don't affect other handlers."""
        handler1_called = False
        handler2_called = False

        def handler1(event: StockAnalyzed) -> None:
            nonlocal handler1_called
            handler1_called = True
            raise ValueError("Handler 1 error")

        def handler2(event: StockAnalyzed) -> None:
            nonlocal handler2_called
            handler2_called = True

        fresh_bus.subscribe("stock_analyzed", handler1)
        fresh_bus.subscribe("stock_analyzed", handler2)

        mock_result = MagicMock()
        event = StockAnalyzed(
            stock_code="600519",
            analysis_result=mock_result,
        )

        # Should not raise exception
        fresh_bus.publish(event)

        # Both handlers should have been called
        assert handler1_called
        assert handler2_called

    def test_clear_all_handlers(self, fresh_bus: EventBus) -> None:
        """Test clearing all handlers."""

        def handler(event: StockAnalyzed) -> None:
            pass

        fresh_bus.subscribe("stock_analyzed", handler)
        fresh_bus.subscribe("stock_analysis_failed", handler)

        fresh_bus.clear_handlers()

        assert fresh_bus._handlers == {}

    def test_clear_specific_handlers(self, fresh_bus: EventBus) -> None:
        """Test clearing handlers for specific event type."""

        def handler(event: StockAnalyzed) -> None:
            pass

        fresh_bus.subscribe("stock_analyzed", handler)
        fresh_bus.subscribe("stock_analysis_failed", handler)

        fresh_bus.clear_handlers("stock_analyzed")

        assert "stock_analyzed" not in fresh_bus._handlers
        assert "stock_analysis_failed" in fresh_bus._handlers


# =============================================================================
# Global EventBus Tests
# =============================================================================
class TestGlobalEventBus:
    """Test cases for global event_bus instance."""

    def test_global_event_bus_exists(self) -> None:
        """Test that global event_bus exists."""
        assert event_bus is not None
        assert isinstance(event_bus, EventBus)

    def test_global_event_bus_is_singleton(self) -> None:
        """Test that global event_bus is a singleton."""
        from stock_analyzer.domain.events import event_bus as event_bus2

        assert event_bus is event_bus2
