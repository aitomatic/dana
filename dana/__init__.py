"""
Dana - Domain-Aware NeuroSymbolic Architecture

A language and framework for building domain-expert multi-agent systems.
"""

# Core components
from .core import DanaParser, DanaInterpreter, DanaSandbox

# Common utilities
from .common import DXA_LOGGER, DANA_LOGGER, DXALogger

# Frameworks
from .frameworks import poet, POETConfig, POETResult, DocumentLoader, KnowledgePoint, Agent

__version__ = "1.0.0"

__all__ = [
    # Core
    'DanaParser', 'DanaInterpreter', 'DanaSandbox',
    # Common
    'DXA_LOGGER', 'DANA_LOGGER', 'DXALogger',
    # Frameworks  
    'poet', 'POETConfig', 'POETResult',
    'DocumentLoader', 'KnowledgePoint',
    'Agent',
    # Version
    '__version__'
]