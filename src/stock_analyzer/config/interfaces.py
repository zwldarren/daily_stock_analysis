"""
Configuration storage interfaces.

This module defines abstract interfaces for configuration storage,
following the Dependency Inversion Principle of DDD.
"""

from abc import ABC, abstractmethod
from typing import Any

from stock_analyzer.config.config import Config


class IConfigStorage(ABC):
    """Abstract interface for configuration storage.

    This interface defines the contract for storing and retrieving
    configuration data. Implementations can use various backends
    such as .env files, databases, or remote configuration services.
    """

    @abstractmethod
    def save_to_env(self, config_dict: dict[str, Any]) -> None:
        """Save configuration to .env file.

        Args:
            config_dict: Configuration dictionary with env var names as keys.
        """
        pass

    @abstractmethod
    def save_config_to_env(self, config: Config) -> None:
        """Save complete Config object to .env file.

        Args:
            config: Configuration object to save.
        """
        pass

    @abstractmethod
    def load_from_db(self) -> dict[str, str]:
        """Load configuration from database.

        Returns:
            Dictionary of configuration key-value pairs.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close storage connection and release resources."""
        pass


class IConfigConverter(ABC):
    """Abstract interface for configuration conversion.

    Converts between Config objects and various formats (dict, env vars).
    """

    @abstractmethod
    def to_dict(self, config: Config) -> dict[str, Any]:
        """Convert Config object to dictionary.

        Args:
            config: Configuration object.

        Returns:
            Dictionary representation of the configuration.
        """
        pass

    @abstractmethod
    def parse_comma_list(self, value: str | None) -> list[str]:
        """Parse comma-separated string into list.

        Args:
            value: Comma-separated string or None.

        Returns:
            List of trimmed string values.
        """
        pass
