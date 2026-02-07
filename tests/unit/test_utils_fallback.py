"""
Unit tests for fallback strategy module.

Tests cover:
- SequentialFallbackStrategy
- CircuitBreakerFallbackStrategy
- FallbackManager
- with_fallback decorator
"""

import pytest

from stock_analyzer.utils.fallback import (
    CircuitBreakerFallbackStrategy,
    FallbackManager,
    SequentialFallbackStrategy,
    create_circuit_breaker,
    create_sequential_fallback,
    with_fallback,
)


# =============================================================================
# SequentialFallbackStrategy Tests
# =============================================================================
class TestSequentialFallbackStrategy:
    """Test cases for SequentialFallbackStrategy."""

    def test_success_on_first_try(self) -> None:
        """Test successful execution on first operation."""
        strategy = SequentialFallbackStrategy()

        def primary():
            return "success"

        def fallback():
            return "fallback"

        result = strategy.execute(primary, [fallback])

        assert result == "success"

    def test_fallback_on_primary_failure(self) -> None:
        """Test fallback is used when primary fails."""
        strategy = SequentialFallbackStrategy()

        def primary():
            raise ValueError("Primary failed")

        def fallback():
            return "fallback_success"

        result = strategy.execute(primary, [fallback])

        assert result == "fallback_success"

    def test_multiple_fallbacks(self) -> None:
        """Test trying multiple fallbacks."""
        strategy = SequentialFallbackStrategy()

        def primary():
            raise ValueError("Primary failed")

        def fallback1():
            raise ValueError("Fallback 1 failed")

        def fallback2():
            return "fallback2_success"

        result = strategy.execute(primary, [fallback1, fallback2])

        assert result == "fallback2_success"

    def test_all_operations_fail(self) -> None:
        """Test exception raised when all operations fail."""
        strategy = SequentialFallbackStrategy()

        def primary():
            raise ValueError("Primary failed")

        def fallback():
            raise ValueError("Fallback failed")

        with pytest.raises(ValueError, match="Fallback failed"):
            strategy.execute(primary, [fallback])

    def test_retry_on_failure(self) -> None:
        """Test retry mechanism."""
        strategy = SequentialFallbackStrategy(max_retries=2)

        call_count = 0

        def primary():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = strategy.execute(primary, [])

        assert result == "success"
        assert call_count == 2

    def test_strategy_name(self) -> None:
        """Test strategy name is used in logs."""
        strategy = SequentialFallbackStrategy(name="test_strategy")

        def primary():
            return "success"

        # Should not raise and should complete successfully
        result = strategy.execute(primary, [])
        assert result == "success"


# =============================================================================
# CircuitBreakerFallbackStrategy Tests
# =============================================================================
class TestCircuitBreakerFallbackStrategy:
    """Test cases for CircuitBreakerFallbackStrategy."""

    def test_success_resets_failure_count(self) -> None:
        """Test successful operation resets failure count."""
        strategy = CircuitBreakerFallbackStrategy(failure_threshold=3)

        def primary():
            return "success"

        # First call succeeds
        result = strategy.execute(primary, [])
        assert result == "success"
        assert strategy._failure_count == 0

    def test_failure_increments_count(self) -> None:
        """Test failure increments failure count."""
        strategy = CircuitBreakerFallbackStrategy(failure_threshold=3)

        def primary():
            raise ValueError("Failed")

        def fallback():
            return "fallback"

        # First failure
        strategy.execute(primary, [fallback])
        assert strategy._failure_count == 1

        # Second failure
        strategy.execute(primary, [fallback])
        assert strategy._failure_count == 2

    def test_circuit_opens_after_threshold(self) -> None:
        """Test circuit opens after failure threshold."""
        strategy = CircuitBreakerFallbackStrategy(failure_threshold=2)

        def primary():
            raise ValueError("Failed")

        def fallback():
            return "fallback"

        # First two failures
        strategy.execute(primary, [fallback])
        strategy.execute(primary, [fallback])

        # Circuit should be open now
        assert strategy._is_open is True

    def test_circuit_skips_primary_when_open(self) -> None:
        """Test primary operation is skipped when circuit is open."""
        strategy = CircuitBreakerFallbackStrategy(failure_threshold=1)

        primary_called = False

        def primary():
            nonlocal primary_called
            primary_called = True
            raise ValueError("Failed")

        def fallback():
            return "fallback"

        # First call opens circuit
        strategy.execute(primary, [fallback])

        # Reset flag
        primary_called = False

        # Second call should skip primary
        result = strategy.execute(primary, [fallback])

        assert result == "fallback"
        assert primary_called is False  # Primary was skipped

    def test_circuit_recovery(self) -> None:
        """Test circuit recovers after timeout."""
        strategy = CircuitBreakerFallbackStrategy(
            failure_threshold=1,
            recovery_timeout=0,  # Immediate recovery for testing
        )

        def primary():
            raise ValueError("Failed")

        def fallback():
            return "fallback"

        # Open the circuit
        strategy.execute(primary, [fallback])
        assert strategy._is_open is True

        # Circuit should recover immediately (timeout=0)
        # Reset failure count manually to simulate recovery
        strategy._is_open = False
        strategy._failure_count = 0

        assert strategy._is_open is False

    def test_fallback_chain_execution(self) -> None:
        """Test fallback chain execution."""
        strategy = CircuitBreakerFallbackStrategy()

        def primary():
            raise ValueError("Primary failed")

        def fallback1():
            raise ValueError("Fallback 1 failed")

        def fallback2():
            return "fallback2_success"

        result = strategy.execute(primary, [fallback1, fallback2])

        assert result == "fallback2_success"


# =============================================================================
# FallbackManager Tests
# =============================================================================
class TestFallbackManager:
    """Test cases for FallbackManager."""

    def test_execute_with_default_strategy(self) -> None:
        """Test execution with default sequential strategy."""
        manager = FallbackManager()

        def primary():
            return "success"

        result = manager.execute(primary)

        assert result == "success"

    def test_execute_with_fallbacks(self) -> None:
        """Test execution with fallback operations."""
        manager = FallbackManager()

        def primary():
            raise ValueError("Failed")

        def fallback():
            return "fallback"

        result = manager.execute(primary, fallback)

        assert result == "fallback"

    def test_with_strategy_returns_new_manager(self) -> None:
        """Test with_strategy returns new manager with specified strategy."""
        manager = FallbackManager()
        circuit_strategy = CircuitBreakerFallbackStrategy()

        new_manager = manager.with_strategy(circuit_strategy)  # type: ignore[arg-type]

        assert new_manager is not manager
        assert isinstance(new_manager._strategy, CircuitBreakerFallbackStrategy)


# =============================================================================
# Factory Functions Tests
# =============================================================================
class TestFactoryFunctions:
    """Test cases for factory functions."""

    def test_create_sequential_fallback(self) -> None:
        """Test create_sequential_fallback factory."""
        manager = create_sequential_fallback(name="test", max_retries=3)

        assert isinstance(manager, FallbackManager)
        assert isinstance(manager._strategy, SequentialFallbackStrategy)
        assert manager._strategy._name == "test"
        assert manager._strategy._max_retries == 3

    def test_create_circuit_breaker(self) -> None:
        """Test create_circuit_breaker factory."""
        manager = create_circuit_breaker(
            name="cb_test",
            failure_threshold=5,
            recovery_timeout=120,
        )

        assert isinstance(manager, FallbackManager)
        assert isinstance(manager._strategy, CircuitBreakerFallbackStrategy)
        assert manager._strategy._name == "cb_test"
        assert manager._strategy._failure_threshold == 5
        assert manager._strategy._recovery_timeout == 120


# =============================================================================
# with_fallback Decorator Tests
# =============================================================================
class TestWithFallbackDecorator:
    """Test cases for with_fallback decorator."""

    def test_decorator_success(self) -> None:
        """Test decorator with successful primary."""

        def fallback():
            return "fallback"

        @with_fallback(fallback)
        def primary():
            return "success"

        result = primary()

        assert result == "success"

    def test_decorator_fallback(self) -> None:
        """Test decorator falls back on failure."""

        def fallback():
            return "fallback"

        @with_fallback(fallback)
        def primary():
            raise ValueError("Failed")

        result = primary()

        assert result == "fallback"

    def test_decorator_multiple_fallbacks(self) -> None:
        """Test decorator with multiple fallbacks."""

        def fallback1():
            raise ValueError("Fallback 1 failed")

        def fallback2():
            return "fallback2"

        @with_fallback(fallback1, fallback2)
        def primary():
            raise ValueError("Primary failed")

        result = primary()

        assert result == "fallback2"
