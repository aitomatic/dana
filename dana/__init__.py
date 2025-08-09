"""
Dana - Domain-Aware Neurosymbolic Agents

A language and framework for building domain-expert multi-agent systems.
"""

import os

#
# Get the version of the dana package
#
from importlib.metadata import version

try:
    __version__ = version("dana")
except Exception:
    __version__ = "0.25.7.29"

from .common import dana_load_dotenv, ConfigLoader, DANA_LOGGER

#
# Make sure we have the environment variables loaded first
#
dana_load_dotenv()

#
# Initialize the configuration loader (singleton pattern)
# This sets up the config system but doesn't load heavy resources yet
#
# Pre-load the configuration to cache it and avoid repeated file I/O
# This ensures all subsequent ConfigLoader calls use the cached version
#
ConfigLoader().get_default_config()

#
# Configure logging with default settings if not already configured
#
DANA_LOGGER.configure(level=DANA_LOGGER.INFO, console=True)

#
# Initialize the Dana module system with default search paths
# This enables .na file imports and module resolution
# DEFERRED: Custom search paths - these are set per DanaSandbox instance
#
if not os.getenv("DANA_TEST_MODE"):
    from .core.runtime.modules.core import initialize_module_system

    initialize_module_system()


#
# Initialize critical Data libaries early
#
import dana.libs as __dana_libs

#
# And the omnipresent Parser, Interpreter, and Sandbox
#
from .core import DanaInterpreter, DanaParser, DanaSandbox

#
# Import the bridge for Dana to import Python modules
# TODO: rename to a better name than "dana_module"
#
from .integrations.python.to_dana import dana as dana_module

__all__ = [
    "__dana_libs",
    "DanaParser",
    "DanaInterpreter",
    "DanaSandbox",
    "DANA_LOGGER",
    "__version__",
    "dana_module",
]
