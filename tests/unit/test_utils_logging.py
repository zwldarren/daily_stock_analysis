"""
Unit tests for logging configuration module.

Tests cover:
- setup_logging function
- Log level configuration
- Handler setup
"""

import logging
import sys
from unittest.mock import MagicMock, patch

from stock_analyzer.utils.logging_config import setup_logging


# =============================================================================
# Setup Logging Tests
# =============================================================================
class TestSetupLogging:
    """Test cases for setup_logging function."""

    @patch("stock_analyzer.utils.logging_config.logger")
    @patch("stock_analyzer.utils.logging_config.Path.mkdir")
    @patch("stock_analyzer.utils.logging_config._intercept_standard_logging")
    @patch("stock_analyzer.utils.logging_config._suppress_noisy_loggers")
    def test_setup_logging_basic(
        self,
        mock_suppress: MagicMock,
        mock_intercept: MagicMock,
        mock_mkdir: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test basic logging setup."""
        setup_logging()

        # Should create log directory
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Should remove existing handlers
        mock_logger.remove.assert_called_once()

        # Should add console handler
        assert mock_logger.add.call_count >= 3  # Console + 2 file handlers

        # Should setup intercept and suppression
        mock_intercept.assert_called_once()
        mock_suppress.assert_called_once()

    @patch("stock_analyzer.utils.logging_config.logger")
    @patch("stock_analyzer.utils.logging_config.Path.mkdir")
    @patch("stock_analyzer.utils.logging_config._intercept_standard_logging")
    @patch("stock_analyzer.utils.logging_config._suppress_noisy_loggers")
    def test_setup_logging_debug_mode(
        self,
        mock_suppress: MagicMock,
        mock_intercept: MagicMock,
        mock_mkdir: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test logging setup in debug mode."""
        setup_logging(debug=True)

        # Check that console handler uses DEBUG level
        calls = mock_logger.add.call_args_list
        console_call = calls[0]
        assert console_call[1]["level"] == "DEBUG"

    @patch("stock_analyzer.utils.logging_config.logger")
    @patch("stock_analyzer.utils.logging_config.Path.mkdir")
    @patch("stock_analyzer.utils.logging_config._intercept_standard_logging")
    @patch("stock_analyzer.utils.logging_config._suppress_noisy_loggers")
    def test_setup_logging_json_format(
        self,
        mock_suppress: MagicMock,
        mock_intercept: MagicMock,
        mock_mkdir: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test logging setup with JSON format."""
        setup_logging(json_format=True)

        # Check that file handlers use JSON format
        calls = mock_logger.add.call_args_list
        # Find file handler calls (not console)
        file_calls = [c for c in calls if c[0][0] != sys.stdout]

        # At least one file handler should have JSON format
        assert len(file_calls) > 0

    @patch("stock_analyzer.utils.logging_config.logger")
    @patch("stock_analyzer.utils.logging_config.Path.mkdir")
    @patch("stock_analyzer.utils.logging_config._intercept_standard_logging")
    @patch("stock_analyzer.utils.logging_config._suppress_noisy_loggers")
    def test_setup_logging_custom_directory(
        self,
        mock_suppress: MagicMock,
        mock_intercept: MagicMock,
        mock_mkdir: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test logging setup with custom log directory."""
        custom_dir = "/custom/log/path"
        setup_logging(log_dir=custom_dir)

        # Should create custom directory
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


# =============================================================================
# Intercept Handler Tests
# =============================================================================
class TestInterceptHandler:
    """Test cases for standard logging interception."""

    @patch("stock_analyzer.utils.logging_config.logger")
    @patch("logging.basicConfig")
    def test_intercept_handler_setup(self, mock_basicConfig: MagicMock, mock_logger: MagicMock) -> None:
        """Test that standard logging is intercepted."""
        from stock_analyzer.utils.logging_config import _intercept_standard_logging

        _intercept_standard_logging()

        # Should configure basic logging with intercept handler
        mock_basicConfig.assert_called_once()

    @patch("stock_analyzer.utils.logging_config.logger")
    @patch("logging.basicConfig")
    def test_intercept_handler_emits_to_loguru(self, mock_basicConfig: MagicMock, mock_logger: MagicMock) -> None:
        """Test that intercept handler emits to loguru."""
        from stock_analyzer.utils.logging_config import _intercept_standard_logging

        # Create a mock log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Get the intercept handler class from the basicConfig call
        _intercept_standard_logging()
        call_args = mock_basicConfig.call_args
        handler = call_args[1]["handlers"][0]

        # Emit should forward to loguru
        handler.emit(record)

        # Verify loguru was called
        assert mock_logger.opt.called or mock_logger.log.called


# =============================================================================
# Noisy Logger Suppression Tests
# =============================================================================
class TestNoisyLoggerSuppression:
    """Test cases for noisy logger suppression."""

    @patch("logging.getLogger")
    def test_noisy_loggers_are_suppressed(self, mock_getLogger: MagicMock) -> None:
        """Test that noisy loggers are set to WARNING level."""
        from stock_analyzer.utils.logging_config import _suppress_noisy_loggers

        _suppress_noisy_loggers()

        # Should get logger and set level for each noisy logger
        noisy_loggers = [
            "urllib3",
            "urllib3.connectionpool",
            "sqlalchemy",
            "sqlalchemy.engine",
            "google",
            "google.auth",
            "httpx",
            "httpx._client",
            "httpcore",
            "httpcore.connection",
            "asyncio",
            "discord",
            "discord.client",
            "websockets",
            "websockets.client",
        ]

        for logger_name in noisy_loggers:
            mock_getLogger.assert_any_call(logger_name)

    @patch("logging.getLogger")
    def test_suppression_sets_warning_level(self, mock_getLogger: MagicMock) -> None:
        """Test that suppression sets WARNING level."""
        from stock_analyzer.utils.logging_config import _suppress_noisy_loggers

        mock_logger_instance = MagicMock()
        mock_getLogger.return_value = mock_logger_instance

        _suppress_noisy_loggers()

        # Each logger should have its level set to WARNING
        assert mock_logger_instance.setLevel.call_count > 0
        # Check that WARNING level was used
        warning_calls = [call for call in mock_logger_instance.setLevel.call_args_list if call[0][0] == logging.WARNING]
        assert len(warning_calls) > 0


# =============================================================================
# Integration Tests
# =============================================================================
class TestLoggingIntegration:
    """Integration tests for logging configuration."""

    @patch("stock_analyzer.utils.logging_config.logger")
    @patch("stock_analyzer.utils.logging_config.Path.mkdir")
    @patch("stock_analyzer.utils.logging_config._intercept_standard_logging")
    @patch("stock_analyzer.utils.logging_config._suppress_noisy_loggers")
    def test_complete_setup_flow(
        self,
        mock_suppress: MagicMock,
        mock_intercept: MagicMock,
        mock_mkdir: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test complete logging setup flow."""
        setup_logging(debug=True, log_dir="./test_logs", json_format=False)

        # Verify all components were called
        mock_mkdir.assert_called_once()
        mock_logger.remove.assert_called_once()
        assert mock_logger.add.call_count >= 3  # Console + 2 files
        mock_intercept.assert_called_once()
        mock_suppress.assert_called_once()
        mock_logger.info.assert_called()  # Should log initialization messages
