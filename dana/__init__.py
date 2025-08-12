"""
Dana - Domain-Aware Neurosymbolic Agents

A language and framework for building domain-expert multi-agent systems.
"""

#
# Get the version of the dana package
#
from importlib.metadata import version

try:
    __version__ = version("dana")
except Exception:
    __version__ = "0.25.7.29"


#
# Dana Startup Sequence - Initialize all systems in dependency order
#
import os

if not os.getenv("DANA_TEST_MODE"):
    # 1. Environment System - Load .env files and validate environment
    from .core.runtime.environment.core import initialize_environment_system

    initialize_environment_system()

    # 2. Configuration System - Pre-load and cache configuration
    from .core.runtime.config.core import initialize_config_system

    initialize_config_system()

    # 3. Logging System - Configure logging with default settings
    from .core.runtime.logging.core import initialize_logging_system

    initialize_logging_system()

    # 4. Module System - Set up .na file imports and module resolution
    from .core.runtime.modules.core import initialize_module_system

    initialize_module_system()

    # 5. Resource System - Load stdlib resources at startup
    from .core.runtime.resources.core import initialize_resource_system

    initialize_resource_system()

    # 6. Library System - Initialize core Dana libraries
    from .core.runtime.library.core import initialize_library_system

    initialize_library_system()

    # 7. Corelib System - Initialize critical data libraries
    from .core.runtime.corelib.core import initialize_corelib_system

    initialize_corelib_system()

    # 8. Integration System - Set up integration bridges
    from .core.runtime.integrations.core import initialize_integration_system

    initialize_integration_system()

    # 9. Runtime System - Initialize Parser, Interpreter, and Sandbox
    from .core.runtime.runtime.core import initialize_runtime_system

    initialize_runtime_system()

else:
    # Test mode - minimal initialization
    from .core.runtime.environment.core import initialize_environment_system

    initialize_environment_system()

    from .core.runtime.logging.core import initialize_logging_system

    initialize_logging_system()

# Import core components for public API
from .common import DANA_LOGGER
from .core import DanaInterpreter, DanaParser, DanaSandbox
from .integrations.python.to_dana import dana as py2na_module

__all__ = [
    "DanaParser",
    "DanaInterpreter",
    "DanaSandbox",
    "DANA_LOGGER",
    "__version__",
    "py2na_module",
]
