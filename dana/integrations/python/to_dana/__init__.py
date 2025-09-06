"""
Python-to-Dana Integration

This module provides seamless Python-to-Dana integration.
It enables Python developers to use Dana's reasoning capabilities with familiar Python syntax.
Now supports direct importing of Dana .na files into Python code.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.integrations.python.to_dana.core.module_importer import install_import_hook, list_available_modules, uninstall_import_hook
from dana.integrations.python.to_dana.dana_module import Dana

# Create the main dana instance that will be imported
dana = Dana()


# Convenience functions for module imports
def enable_dana_imports(search_paths: list[str] | None = None, debug: bool = False) -> None:
    """Enable importing Dana .na files directly in Python.

    Args:
        search_paths: Optional list of paths to search for .na files.
                     If None, automatically includes the calling script's directory.
        debug: Enable debug mode

    Example:
        from dana.integrations.python import enable_dana_imports
        enable_dana_imports()

        import simple_math  # This will load simple_math.na from the script's directory
        result = simple_math.add(5, 3)
    """
    dana.enable_module_imports(search_paths)
    if debug:
        dana._debug = True


def disable_dana_imports() -> None:
    """Disable Dana module imports."""
    dana.disable_module_imports()


def list_dana_modules(search_paths: list[str] | None = None) -> list[str]:
    """List all available Dana modules.

    Args:
        search_paths: Optional list of paths to search

    Returns:
        List of available module names
    """
    return dana.list_modules(search_paths)


__all__ = [
    "dana",
    "Dana",
    "enable_dana_imports",
    "disable_dana_imports",
    "list_dana_modules",
    "install_import_hook",
    "uninstall_import_hook",
    "list_available_modules",
]
