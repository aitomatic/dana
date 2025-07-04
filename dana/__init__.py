"""
Dana - Domain-Aware NeuroSymbolic Architecture

A language and framework for building domain-expert multi-agent systems.
"""

# Core components
# Common utilities
from .common import DANA_LOGGER, DanaLogger
from .core import DanaInterpreter, DanaParser, DanaSandbox

# Frameworks
from .frameworks import Agent, DocumentLoader, KnowledgePoint, POETConfig, POETResult, poet

__version__ = "1.0.0"

__all__ = [
    # Core
    'DanaParser', 'DanaInterpreter', 'DanaSandbox',
    # Common
    'DANA_LOGGER', 'DanaLogger',
    # Frameworks  
    'poet', 'POETConfig', 'POETResult',
    'DocumentLoader', 'KnowledgePoint',
    'Agent',
    # Version
    '__version__'
]