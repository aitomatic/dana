"""
Context Engineering Framework

Provides intelligent context assembly for LLM interactions, maximizing relevance
while minimizing token usage.
"""

from .actor_mixin import ContextEngineerMixin
from .assemblers import BaseTemplate, TextTemplate, XMLTemplate
from .engine import ContextEngine
from .resources import ContextResource, ContextWorkflow

__all__ = [
    "ContextEngine",
    "ContextEngineerMixin",
    "ContextResource",
    "ContextWorkflow",
    "BaseTemplate",
    "XMLTemplate",
    "TextTemplate",
]

__version__ = "1.0.0"
