"""
Dana Environment System - Core

This module provides the core functionality for Dana's environment system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from dana.common import dana_load_dotenv


def initialize_environment_system() -> None:
    """Initialize the Dana environment system.

    This function loads environment variables from .env files and validates
    critical environment settings. It should be called early in the startup
    sequence before other systems depend on environment variables.
    """
    # Load environment variables from .env files
    dana_load_dotenv()

    # Validate critical environment variables
    _validate_environment()


def _validate_environment() -> None:
    """Validate critical environment variables and settings."""
    # Check for test mode
    test_mode = os.getenv("DANA_TEST_MODE", "").lower() == "true"

    # Log environment status
    if test_mode:
        print("DANA_TEST_MODE enabled - skipping some initializations")

    # TODO: Add validation for critical environment variables
    # For example, check if required API keys are present
    # This could be configurable based on which features are enabled


def reset_environment_system() -> None:
    """Reset the environment system.

    This is primarily useful for testing when you need to reinitialize
    the environment system.
    """
    # Clear any cached environment variables
    # Note: This is limited by Python's os.environ behavior
    pass


__all__ = [
    # Core functions
    "initialize_environment_system",
    "reset_environment_system",
]
