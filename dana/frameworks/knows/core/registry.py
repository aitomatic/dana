"""
Knowledge Organization (KO) Registry for Dana KNOWS system.

This module provides a registry system for managing different types of knowledge organizations
and their configurations.
"""

from typing import Any

from dana.common.utils.logging import DANA_LOGGER


class KORegistry:
    """Registry for Knowledge Organization types and configurations."""

    def __init__(self):
        """Initialize the KO registry."""
        self._ko_types: dict[str, type] = {}
        self._ko_configs: dict[str, dict[str, Any]] = {}
        DANA_LOGGER.info("Initialized KO Registry")

    def register_ko_type(self, name: str, ko_class: type) -> None:
        """Register a Knowledge Organization type.

        Args:
            name: Name of the KO type (e.g., "vector", "relational", "workflow")
            ko_class: Class implementing the KO interface
        """
        if name in self._ko_types:
            DANA_LOGGER.warning(f"KO type '{name}' already registered, overwriting")

        self._ko_types[name] = ko_class
        DANA_LOGGER.info(f"Registered KO type: {name}")

    def register_ko_config(self, name: str, config: dict[str, Any]) -> None:
        """Register a configuration for a KO type.

        Args:
            name: Name of the KO type
            config: Configuration dictionary
        """
        self._ko_configs[name] = config
        DANA_LOGGER.info(f"Registered KO config for: {name}")

    def get_ko_type(self, name: str) -> type:
        """Get a registered KO type.

        Args:
            name: Name of the KO type

        Returns:
            The KO class

        Raises:
            ValueError: If KO type is not registered
        """
        if name not in self._ko_types:
            available_types = list(self._ko_types.keys())
            raise ValueError(f"KO type '{name}' not found. Available types: {available_types}")

        return self._ko_types[name]

    def get_ko_config(self, name: str) -> dict[str, Any]:
        """Get configuration for a KO type.

        Args:
            name: Name of the KO type

        Returns:
            Configuration dictionary

        Raises:
            ValueError: If KO config is not found
        """
        if name not in self._ko_configs:
            available_configs = list(self._ko_configs.keys())
            raise ValueError(f"KO config for '{name}' not found. Available configs: {available_configs}")

        return self._ko_configs[name].copy()

    def list_ko_types(self) -> list[str]:
        """List all registered KO types.

        Returns:
            List of KO type names
        """
        return list(self._ko_types.keys())

    def list_ko_configs(self) -> list[str]:
        """List all registered KO configurations.

        Returns:
            List of KO config names
        """
        return list(self._ko_configs.keys())

    def create_ko_instance(self, name: str, **kwargs) -> Any:
        """Create an instance of a KO type with its configuration.

        Args:
            name: Name of the KO type
            **kwargs: Additional arguments to override config

        Returns:
            Instance of the KO type

        Raises:
            ValueError: If KO type is not registered
        """
        ko_class = self.get_ko_type(name)

        # Get base config if available
        config = {}
        if name in self._ko_configs:
            config = self.get_ko_config(name)

        # Override with provided kwargs
        config.update(kwargs)

        DANA_LOGGER.info(f"Creating KO instance: {name} with config: {config}")
        return ko_class(**config)


# Global registry instance
ko_registry = KORegistry()
