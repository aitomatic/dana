"""
Dana Resource System - Core

This module provides the core functionality for Dana's resource system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.registry import TYPE_REGISTRY


def initialize_resource_system() -> None:
    """Initialize the Dana resource system.

    This function initializes the new resource system.
    Resources are now defined using the resource keyword in Dana code.
    """
    # The new resource system is initialized automatically when
    # resource definitions are executed. No manual initialization needed.
    pass


def reset_resource_system() -> None:
    """Reset the resource system, clearing all loaded resources.

    This is primarily useful for testing when you need to reinitialize
    the resource system.
    """
    TYPE_REGISTRY.clear()


__all__ = [
    # Core functions
    "initialize_resource_system",
    "reset_resource_system",
]
