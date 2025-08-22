"""
Dana - Domain-Aware Neurosymbolic Agents

A language and framework for building domain-expert multi-agent systems.
"""

#
# Dana Startup Sequence - Initialize all systems in dependency order
#

# 1. Environment System - Load .env files and validate environment
from .init_environment import initialize_environment_system

initialize_environment_system()

# 2. Configuration System - Pre-load and cache configuration
from .init_config import initialize_config_system

initialize_config_system()

# 3. Logging System - Configure logging with default settings
from .init_logging import initialize_logging_system

initialize_logging_system()

# 4. Module System - Set up .na file imports and module resolution
from .init_modules import initialize_module_system

initialize_module_system()

# 5. Resource System - Load stdlib resources at startup
from .init_resources import initialize_resource_system

initialize_resource_system()

# 6. Library System - Initialize core Dana libraries
from .init_libs import initialize_library_system

initialize_library_system()

# 7. FSM System - Initialize FSM struct type
from .init_fsm import initialize_fsm_system

initialize_fsm_system()

# 8. Integration System - Set up integration bridges
from .init_integrations import initialize_integration_system

initialize_integration_system()

# 9. Runtime System - Initialize Parser, Interpreter, and Sandbox
from .init_runtime import initialize_runtime_system

initialize_runtime_system()

#
# Get the version of the dana package
#
from importlib.metadata import version

try:
    __version__ = version("dana")
except Exception:
    __version__ = "0.25.7.29"

# Import core components for public API
from dana.common import DANA_LOGGER
from dana.core import DanaInterpreter, DanaParser, DanaSandbox
from dana.integrations.python.to_dana import dana as py2na

from .init_modules import initialize_module_system, reset_module_system

__all__ = [
    "__version__",
    "DANA_LOGGER",
    "DanaParser",
    "DanaInterpreter",
    "DanaSandbox",
    "py2na",
    "initialize_module_system",
    "reset_module_system",
]
