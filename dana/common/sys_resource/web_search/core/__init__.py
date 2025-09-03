"""
Core components for the web search system.

This module contains the fundamental interfaces and data models
that define the contracts for search services and domain handlers.
"""

from .interfaces import SearchService, DomainHandler, ResultValidator
from .models import (
    ProductInfo,
    ResearchRequest,
    SearchRequest,
    SearchSource,
    SearchResults,
    DomainResult,
    SearchDepthType,
    ConfidenceType,
)

__all__ = [
    # Interfaces
    "SearchService",
    "DomainHandler",
    "ResultValidator",
    # Models
    "ProductInfo",
    "ResearchRequest",
    "SearchRequest",
    "SearchSource",
    "SearchResults",
    "DomainResult",
    # Types
    "SearchDepthType",
    "ConfidenceType",
]
