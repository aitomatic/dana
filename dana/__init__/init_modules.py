"""
Dana Dana Module System - Core

This module provides the core functionality for Dana's module system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from pathlib import Path

from dana.core.runtime.modules.errors import ModuleError
from dana.core.runtime.modules.loader import ModuleLoader
from dana.registry.module_registry import ModuleRegistry

_module_registry: ModuleRegistry | None = None
_module_loader: ModuleLoader | None = None


def initialize_module_system(search_paths: list[str] | None = None) -> None:
    """Initialize the Dana module system.

    Args:
        search_paths: Optional list of paths to search for modules. If not provided,
                     defaults to current directory and DANAPATH environment variable.
    """
    global _module_registry, _module_loader

    import os

    import dana as dana_module
    from dana.registry import GLOBAL_REGISTRY

    dana_module_path = Path(dana_module.__file__).parent
    # Set up default search paths
    if search_paths is None:
        search_paths = []

    search_paths.extend(
        [
            str(dana_module_path / "libs" / "stdlib"),
            str(dana_module_path / "libs"),
            str(Path.cwd()),  # Current directory
            str(Path.cwd() / "dana"),  # ./dana directory
            str(Path.home() / ".dana" / "libs"),
        ]
    )

    # Add paths from DANAPATH environment variable
    if "DANAPATH" in os.environ:
        search_paths.extend(os.environ["DANAPATH"].split(os.pathsep))

    # Ensure DANAPATH environment variable includes our default search paths
    _ensure_danapath_includes_defaults(search_paths)

    # Create registry and loader

    _module_registry = GLOBAL_REGISTRY.modules
    _module_loader = ModuleLoader(search_paths, _module_registry)

    # DO NOT install import hook in sys.meta_path to avoid interfering with Python imports
    # The loader will be called directly by Dana's import statement executor


def _ensure_danapath_includes_defaults(search_paths: list[str]) -> None:
    """Ensure DANAPATH environment variable includes the default search paths.

    This is particularly important for stdlib to be discoverable on-demand.

    Args:
        search_paths: List of default search paths to include in DANAPATH.
    """
    import os

    # Get current DANAPATH, if any
    current_danapath = os.environ.get("DANAPATH", "")
    existing_paths = [p for p in current_danapath.split(os.pathsep) if p]

    # Add default search paths that aren't already in DANAPATH
    for path in search_paths:
        if path not in existing_paths:
            existing_paths.append(path)

    # Update DANAPATH environment variable
    os.environ["DANAPATH"] = os.pathsep.join(existing_paths)


def get_module_registry() -> ModuleRegistry:
    """Get the global module registry instance."""
    global _module_registry
    if _module_registry is None:
        initialize_module_system()
        # After initialization, the registry must be set
        assert _module_registry is not None
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
    # Core functions
    "initialize_module_system",
    "reset_module_system",
    "get_module_registry",
    "get_module_loader",
]
