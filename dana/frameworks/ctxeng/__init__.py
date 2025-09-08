"""
Context Engineering Framework

Provides intelligent context assembly for LLM interactions, maximizing relevance
while minimizing token usage.
"""

from .templates.base import BaseTemplate, TextTemplate, XMLTemplate
from .context_data import (
    ContextData,
    ConversationContextData,
    ExecutionContextData,
    MemoryContextData,
    ProblemContextData,
    ResourceContextData,
    WorkflowContextData,
)
from .engineer import ContextEngineer

__all__ = [
    "ContextEngineer",
    "ContextData",
    "ProblemContextData",
    "WorkflowContextData",
    "ConversationContextData",
    "ResourceContextData",
    "MemoryContextData",
    "ExecutionContextData",
    "BaseTemplate",
    "XMLTemplate",
    "TextTemplate",
]

__version__ = "1.0.0"
