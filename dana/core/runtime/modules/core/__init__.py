"""
Dana Dana Module System - Core

This module provides the core functionality for Dana's module system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from pathlib import Path

from .errors import ModuleError
from .loader import ModuleLoader
from .registry import ModuleRegistry
from .types import Module, ModuleSpec, ModuleType

_module_registry: ModuleRegistry | None = None
_module_loader: ModuleLoader | None = None


def initialize_module_system(search_paths: list[str] | None = None) -> None:
    """Initialize the Dana module system.

    Args:
        search_paths: Optional list of paths to search for modules. If not provided,
                     defaults to current directory and DANAPATH environment variable.
    """
    global _module_registry, _module_loader

    # Set up default search paths
    if search_paths is None:
        search_paths = [
            str(Path.cwd()),  # Current directory
            str(Path.cwd() / "dana"),  # ./dana directory
        ]

        # Add paths from DANAPATH environment variable
        import os

        if "DANAPATH" in os.environ:
            search_paths.extend(os.environ["DANAPATH"].split(os.pathsep))

    # Create registry and loader
    _module_registry = ModuleRegistry()
    _module_loader = ModuleLoader(search_paths, _module_registry)

    # DO NOT install import hook in sys.meta_path to avoid interfering with Python imports
    # The loader will be called directly by Dana's import statement executor


def get_module_registry() -> ModuleRegistry:
    """Get the global module registry instance."""
    if _module_registry is None:
        raise ModuleError("Module system not initialized. Call initialize_module_system() first.")
    return _module_registry


def get_module_loader() -> ModuleLoader:
    """Get the global module loader instance."""
    if _module_loader is None:
        raise ModuleError("Module system not initialized. Call initialize_module_system() first.")
    return _module_loader


def reset_module_system() -> None:
    """Reset the module system, clearing all cached modules and specs.

    This is primarily useful for testing when you need to reinitialize
    the module system with different search paths.
    """
    global _module_registry, _module_loader

    if _module_registry is not None:
        _module_registry.clear()

    _module_registry = None
    _module_loader = None


__all__ = [
    # Core types
    "Module",
    "ModuleSpec",
    "ModuleType",
    "ModuleError",
    # Core functions
    "initialize_module_system",
    "reset_module_system",
    "get_module_registry",
    "get_module_loader",
]
