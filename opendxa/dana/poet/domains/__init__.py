"""
POET Domain Plugins Registry

Centralized registry for discovering and loading domain plugins.
"""

from typing import Dict, Type, Optional
import importlib
from pathlib import Path


class PluginRegistry:
    """Registry for POET domain plugins."""

    _plugins: Dict[str, Type] = {}
    _initialized = False

    @classmethod
    def register_plugin(cls, domain: str, plugin_class: Type):
        """Register a domain plugin."""
        cls._plugins[domain] = plugin_class

    @classmethod
    def get_plugin(cls, domain: str) -> Optional[Type]:
        """Get a plugin class by domain name."""
        if not cls._initialized:
            cls._discover_plugins()
        return cls._plugins.get(domain)

    @classmethod
    def list_domains(cls) -> list[str]:
        """List all available domains."""
        if not cls._initialized:
            cls._discover_plugins()
        return list(cls._plugins.keys())

    @classmethod
    def _discover_plugins(cls):
        """Discover all available domain plugins."""
        # Register known plugins
        try:
            from .llm_optimization import LLMOptimizationPlugin

            cls._plugins["llm_optimization"] = LLMOptimizationPlugin
        except ImportError:
            pass

        try:
            from .building_management import BuildingManagementPlugin

            cls._plugins["building_management"] = BuildingManagementPlugin
        except ImportError:
            pass

        try:
            from .financial_services import FinancialServicesPlugin

            cls._plugins["financial_services"] = FinancialServicesPlugin
        except ImportError:
            pass

        try:
            from .semiconductor import SemiconductorPlugin

            cls._plugins["semiconductor"] = SemiconductorPlugin
        except ImportError:
            pass

        cls._initialized = True


# Initialize the registry
PLUGIN_REGISTRY = PluginRegistry()
