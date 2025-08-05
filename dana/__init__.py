"""
Dana - Domain-Aware Neurosymbolic Agents

A language and framework for building domain-expert multi-agent systems.
"""

from importlib.metadata import version

# Initialize critical Dana systems early
import dana.libs.initlib as _dana_initlib
from dana.integrations.python.to_dana import dana as dana_module

from .common import DANA_LOGGER
from .core import DanaInterpreter, DanaParser, DanaSandbox

__version__ = version("dana")

__all__ = [
    "_dana_initlib",
    "DanaParser",
    "DanaInterpreter",
    "DanaSandbox",
    "DANA_LOGGER",
    "__version__",
    "dana_module",
]
