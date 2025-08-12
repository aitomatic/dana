"""
Dana Config System - Core

This module provides the core functionality for Dana's configuration system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.common.config import ConfigLoader


def initialize_config_system() -> None:
    """Initialize the Dana configuration system.

    This function pre-loads the default configuration to cache it and avoid
    repeated file I/O operations. This ensures all subsequent ConfigLoader
    calls use the cached version.
    """
    # Pre-load the configuration to cache it and avoid repeated file I/O
    # This ensures all subsequent ConfigLoader calls use the cached version
    ConfigLoader().get_default_config()


def reset_config_system() -> None:
    """Reset the configuration system, clearing the cache.

    This is primarily useful for testing when you need to reinitialize
    the configuration system.
    """
    # Clear the cached config to force reloading
    ConfigLoader().clear_cache()


__all__ = [
    # Core functions
    "initialize_config_system",
    "reset_config_system",
]
