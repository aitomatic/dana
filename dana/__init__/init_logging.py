"""
Dana Logging System - Core

This module provides the core functionality for Dana's logging system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.common import DANA_LOGGER


def initialize_logging_system() -> None:
    """Initialize the Dana logging system.

    This function configures logging with default settings, including
    log level, output formatting, and console output. It should be
    called early in the startup sequence to ensure proper logging
    throughout the application lifecycle.
    """
    # Configure logging with default settings if not already configured
    DANA_LOGGER.configure(level=DANA_LOGGER.INFO, console=True)


def reset_logging_system() -> None:
    """Reset the logging system.

    This is primarily useful for testing when you need to reinitialize
    the logging system.
    """
    # Reset logging configuration to defaults
    DANA_LOGGER.configure(level=DANA_LOGGER.INFO, console=True)


__all__ = [
    # Core functions
    "initialize_logging_system",
    "reset_logging_system",
]
