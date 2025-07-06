"""
Context expansion and similarity search components for OpenDXA KNOWS system.

This module handles similarity search, context expansion, and semantic matching.
"""

from .expander import ContextExpander
from .similarity import SimilaritySearcher

__all__ = ["SimilaritySearcher", "ContextExpander"]
