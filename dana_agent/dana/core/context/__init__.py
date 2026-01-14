"""Context assembly for LLM prompts.

Provides ContextBuilder for assembling context from multiple sources
(strings, RLMResource, LTMemory) with automatic access pattern selection.
"""

from dana.core.context.builder import ContextBuilder
from dana.core.context.context import Context

__all__ = ["Context", "ContextBuilder"]
