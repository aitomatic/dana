"""
Dana Resource System - Core

This module provides the core functionality for Dana's resource system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.core.resource.context_integration import get_resource_integrator


def initialize_resource_system() -> None:
    """Initialize the Dana resource system.

    This function loads all stdlib resources at startup to ensure they are
    available immediately, not lazily loaded when first accessed.
    """
    # Get the global resource integrator (this triggers _ensure_loaded())
    # The existing singleton pattern in context_integration.py ensures
    # we get the same instance every time
    integrator = get_resource_integrator()

    # The get_resource_integrator() call triggers _ensure_loaded() which
    # calls load_all() to load core plugins and stdlib resources


def reset_resource_system() -> None:
    """Reset the resource system, clearing all loaded resources.

    This is primarily useful for testing when you need to reinitialize
    the resource system.
    """
    integrator = get_resource_integrator()

    # Reset the integrator to force reloading
    integrator._initialized = False
    integrator.loader.plugins.clear()
    integrator._ensure_loaded()


__all__ = [
    # Core functions
    "initialize_resource_system",
    "reset_resource_system",
    "get_resource_integrator",
]
