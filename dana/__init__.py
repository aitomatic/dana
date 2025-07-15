"""
Dana - Domain-Aware Neurosymbolic Agents

A language and framework for building domain-expert multi-agent systems.
"""

from importlib.metadata import version

from .common import DANA_LOGGER
from .core import DanaInterpreter, DanaParser, DanaSandbox

__version__ = version("dana-agent")

__all__ = ["DanaParser", "DanaInterpreter", "DanaSandbox", "DANA_LOGGER", "__version__"]
