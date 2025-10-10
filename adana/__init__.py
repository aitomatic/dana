"""
Adana - Minimal LLM Library

A simple, clean interface for interacting with any LLM provider.
Follows KISS principle with just the essential methods most clients need.
"""

# Import library initialization FIRST (loads .env automatically)
from .__init__ import initialize


initialize()

from .common import LLM, LLMMessage, LLMResponse
from .core import STARAgent


__version__ = "0.1.0"
__all__ = ["LLM", "LLMMessage", "LLMResponse", "STARAgent"]
