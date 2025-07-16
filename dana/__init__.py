"""
Dana - Domain-Aware Neurosymbolic Agents

A language and framework for building domain-expert multi-agent systems.
"""

from importlib.metadata import version

from .common import DANA_LOGGER
from .core import DanaInterpreter, DanaParser, DanaSandbox


# Python-to-Dana Integration - Natural Python API with lazy loading
def __getattr__(name: str):
    """Lazy loading for dana module to avoid circular imports."""
    if name == "dana":
        from dana.integrations.python.to_dana import dana as _dana

        return _dana
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__version__ = version("dana-agent")

__all__ = [
    "DanaParser",
    "DanaInterpreter",
    "DanaSandbox",
    "DANA_LOGGER",
    "__version__",
    "dana",
]
