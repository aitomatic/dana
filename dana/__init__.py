"""
Dana - Domain-Aware Neurosymbolic Agents

A language and framework for building domain-expert multi-agent systems.
"""

from importlib.metadata import version

from dana.integrations.python.to_dana import dana as dana_module

from .common import DANA_LOGGER
from .core import DanaInterpreter, DanaParser, DanaSandbox

try:
    __version__ = version("dana")
except Exception:
    __version__ = "0.25.7.29"

__all__ = [
    "DanaParser",
    "DanaInterpreter",
    "DanaSandbox",
    "DANA_LOGGER",
    "__version__",
    "dana_module",
]
