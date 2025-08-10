"""Initialization library for Dana.

This module provides initialization and startup functionality for Dana applications,
including environment loading, configuration setup, and bootstrap utilities.
"""

import logging
import os

from .dana_load_dotenv import dana_load_dotenv

__all__ = ["dana_load_dotenv"]

# =============================================================================
# DANA STARTUP INITIALIZATION
# =============================================================================
# This module performs early initialization of critical Dana systems.
# We use a phased approach to balance startup speed with functionality.


def _initialize_dana_startup():
    """Initialize critical Dana systems during module import.

    This function performs essential startup activities that should happen
    early in the Dana application lifecycle. We defer heavy initialization
    to maintain fast startup times and avoid unnecessary resource usage.
    """

    # =============================================================================
    # PHASE 1: ESSENTIAL ENVIRONMENT & CONFIGURATION SETUP
    # =============================================================================
    # These must happen first as other systems depend on them.

    # Load environment variables from .env files following Dana's search hierarchy
    # This ensures environment variables are available for all subsequent operations
    dana_load_dotenv()

    # Initialize the configuration loader (singleton pattern)
    # This sets up the config system but doesn't load heavy resources yet
    from dana.common.config.config_loader import ConfigLoader

    _config_loader = ConfigLoader()

    # Pre-load the configuration to cache it and avoid repeated file I/O
    # This ensures all subsequent ConfigLoader calls use the cached version
    _config_loader.get_default_config()

    # =============================================================================
    # PHASE 2: CORE SYSTEM INITIALIZATION (Conditional)
    # =============================================================================
    # These systems are commonly needed but can be deferred in some cases.

    # Skip heavy initialization in test mode to improve test performance
    if not os.getenv("DANA_TEST_MODE"):
        # Initialize the Dana module system with default search paths
        # This enables .na file imports and module resolution
        # DEFERRED: Custom search paths - these are set per DanaSandbox instance
        from dana.core.runtime.modules.core import initialize_module_system

        initialize_module_system()

        # Set up logging system with default configuration
        # This ensures consistent logging behavior across the application
        # DEFERRED: Custom log levels - these can be set per application
        from dana.common.utils.logging import DANA_LOGGER

        # Configure logging with default settings if not already configured
        DANA_LOGGER.configure(level=logging.INFO, console=True)

    # =============================================================================
    # PHASE 3: CORE LIBRARY PRELOADING
    # =============================================================================
    # Core library functions are preloaded during startup to ensure they are
    # immediately available when DanaInterpreter is created.
    _preload_corelib_functions()

    # =============================================================================
    # PHASE 4: STANDARD LIBRARY PATH SETUP
    # =============================================================================
    # Ensure stdlib is in DANA_PATH for on-demand loading
    _ensure_stdlib_in_danapath()


def _preload_corelib_functions():
    """Preload core library functions during startup.

    This ensures core library functions are available immediately when
    DanaInterpreter is created, without requiring deferred registration.
    """
    try:
        # Import and register core library functions
        from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry
        from dana.libs.corelib.register_corelib_functions import register_corelib_functions

        # Create a temporary registry for preloading
        temp_registry = FunctionRegistry()

        # Register core library functions
        register_corelib_functions(temp_registry)

        # Store the preloaded functions for later use by DanaInterpreter
        # This avoids the need for deferred registration
        import dana.core.lang.interpreter.functions.function_registry as registry_module

        registry_module._preloaded_functions = temp_registry._functions.copy()

    except Exception as e:
        # Log error but don't fail startup - corelib functions will be loaded normally
        import logging

        logging.warning(f"Failed to preload corelib functions: {e}")


def _ensure_stdlib_in_danapath():
    """Ensure stdlib is in DANA_PATH for on-demand loading.

    This adds the stdlib path to the DANA_PATH environment variable
    so that stdlib modules can be imported on-demand.
    """
    try:
        from pathlib import Path

        # Get the stdlib path
        stdlib_path = str(Path(__file__).parent.parent / "stdlib")

        # Get current DANA_PATH
        current_danapath = os.environ.get("DANAPATH", "")

        # Add stdlib path if not already present
        if stdlib_path not in current_danapath:
            if current_danapath:
                new_danapath = f"{stdlib_path}{os.pathsep}{current_danapath}"
            else:
                new_danapath = stdlib_path

            os.environ["DANAPATH"] = new_danapath

    except Exception as e:
        # Log error but don't fail startup
        import logging

        logging.warning(f"Failed to add stdlib to DANA_PATH: {e}")


# =============================================================================
# DEFERRED INITIALIZATION (What we're NOT doing here)
# =============================================================================
# The following components are intentionally NOT initialized during startup
# to maintain fast startup times and avoid unnecessary resource usage:
#
# 1. LLMResource - Requires API keys and network connectivity
#    - Initialized when first instantiated (lazy loading)
#    - Can cause startup failures if API keys aren't configured
#    - Network connections are expensive and not always needed
#
# 2. DanaSandbox - Heavy resource initialization
#    - Created on-demand when needed
#    - Includes LLMResource, API services, and other heavy components
#    - Not all applications need full sandbox functionality
#
# 3. API Services - Network-dependent services
#    - APIServiceManager, APIClient, etc.
#    - Require network connectivity and API keys
#    - Initialized when DanaSandbox is created
#
# 4. Standard Library Functions - Loaded on-demand via DANA_PATH
#    - reason(), log(), str(), print(), etc.
#    - Available through module imports when needed
#    - DANA_PATH ensures stdlib modules can be found
#
# 5. Custom Module Search Paths - Set per instance
#    - Module search paths are configured per DanaSandbox instance
#    - Allows different applications to use different module paths
#
# 6. Heavy Configuration Loading - Lazy loading
#    - dana_config.json is loaded when ConfigLoader.get_default_config() is called
#    - Prevents startup delays when config isn't immediately needed

# =============================================================================
# STARTUP EXECUTION
# =============================================================================
# Execute the startup sequence when this module is imported.
# This ensures critical systems are ready immediately.

_initialize_dana_startup()
