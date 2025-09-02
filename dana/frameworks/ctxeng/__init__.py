"""
Context Engineering Framework

Provides intelligent context assembly for LLM interactions, maximizing relevance
while minimizing token usage.
"""

from .assemblers import BaseTemplate, TextTemplate, XMLTemplate
from .engine import ContextEngine
from .resources import ContextResource, ContextWorkflow

__all__ = [
    "ContextEngine",
    "ContextResource",
    "ContextWorkflow",
    "BaseTemplate",
    "XMLTemplate",
    "TextTemplate",
]

__version__ = "1.0.0"
