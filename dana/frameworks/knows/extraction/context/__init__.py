"""
Context expansion and similarity search components for OpenDXA KNOWS system.

This module handles similarity search, context expansion, and semantic matching.
"""

from .similarity import SimilaritySearcher
from .expander import ContextExpander

__all__ = [
    "SimilaritySearcher",
    "ContextExpander"
] 