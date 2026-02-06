"""Tests for domain exceptions."""

from stock_analyzer.domain.exceptions import (
    AnalysisError,
    ConfigurationError,
    DataFetchError,
    NotificationError,
    StockAnalyzerException,
    StorageError,
    ValidationError,
)


class TestStockAnalyzerException:
    """Test cases for StockAnalyzerException."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = StockAnalyzerException("Test error")
        assert str(error) == "Test error"

    def test_error_with_code(self):
        """Test error with code."""
        error = StockAnalyzerException("Test error", code="TEST_001")
        assert error.code == "TEST_001"
        assert str(error) == "[TEST_001] Test error"


class TestConfigurationError:
    """Test cases for ConfigurationError."""

    def test_is_subclass(self):
        """Test ConfigurationError is a subclass of StockAnalyzerException."""
        assert issubclass(ConfigurationError, StockAnalyzerException)

    def test_error_creation(self):
        """Test ConfigurationError creation."""
        error = ConfigurationError("Config missing")
        assert str(error) == "Config missing"


class TestDataFetchError:
    """Test cases for DataFetchError."""

    def test_is_subclass(self):
        """Test DataFetchError is a subclass of StockAnalyzerException."""
        assert issubclass(DataFetchError, StockAnalyzerException)

    def test_error_creation(self):
        """Test DataFetchError creation."""
        error = DataFetchError("Failed to fetch")
        assert str(error) == "Failed to fetch"


class TestStorageError:
    """Test cases for StorageError."""

    def test_is_subclass(self):
        """Test StorageError is a subclass of StockAnalyzerException."""
        assert issubclass(StorageError, StockAnalyzerException)

    def test_error_creation(self):
        """Test StorageError creation."""
        error = StorageError("Database error")
        assert str(error) == "Database error"


class TestValidationError:
    """Test cases for ValidationError."""

    def test_is_subclass(self):
        """Test ValidationError is a subclass of StockAnalyzerException."""
        assert issubclass(ValidationError, StockAnalyzerException)

    def test_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"


class TestAnalysisError:
    """Test cases for AnalysisError."""

    def test_is_subclass(self):
        """Test AnalysisError is a subclass of StockAnalyzerException."""
        assert issubclass(AnalysisError, StockAnalyzerException)

    def test_error_creation(self):
        """Test AnalysisError creation."""
        error = AnalysisError("Analysis failed")
        assert str(error) == "Analysis failed"


class TestNotificationError:
    """Test cases for NotificationError."""

    def test_is_subclass(self):
        """Test NotificationError is a subclass of StockAnalyzerException."""
        assert issubclass(NotificationError, StockAnalyzerException)

    def test_error_creation(self):
        """Test NotificationError creation."""
        error = NotificationError("Notification failed")
        assert str(error) == "Notification failed"
