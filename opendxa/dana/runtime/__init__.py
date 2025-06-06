"""
Dana-Python Unified Runtime

This module automatically installs the Dana import system when imported.
"""
# Expose key runtime components
from opendxa.dana.runtime.import_system import DanaModuleFinder, DanaModuleLoader
from opendxa.dana.runtime.module_wrapper import DanaModuleWrapper


def _install_runtime():
    """Install Dana runtime integration automatically."""
    try:
        from opendxa.dana.runtime.import_system import install_dana_import_system
        install_dana_import_system()
    except Exception as e:
        import warnings
        warnings.warn(f"Failed to install Dana import system: {e}")

# Auto-install when module is imported
_install_runtime()


__all__ = ['DanaModuleFinder', 'DanaModuleLoader', 'DanaModuleWrapper'] 