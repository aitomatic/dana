"""
Core data models for the product research system.

These models define the standardized data structures used across all domains and search services.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal


class SearchDepth(str, Enum):
    """Search depth levels for web search operations.

    BASIC: Quick search with minimal results
    STANDARD: Balanced search with moderate depth
    EXTENSIVE: Comprehensive search including reference links
    """

    BASIC = "basic"
    STANDARD = "standard"
    EXTENSIVE = "extensive"


@dataclass
class ProductInfo:
    """Product information input for research."""

    manufacturer: str = ""
    part_number: str = ""
    description: str = ""

    def __str__(self) -> str:
        parts = [p for p in [self.manufacturer, self.part_number, self.description] if p]
        return " ".join(parts)


@dataclass
class ResearchRequest:
    """Research request containing product data and search options."""

    product: ProductInfo
    search_depth: SearchDepth = SearchDepth.STANDARD
    with_full_content: bool = False


@dataclass
class SearchRequest:
    """Standardized input for search services."""

    query: str
    search_depth: SearchDepth = SearchDepth.STANDARD
    domain: str = ""
    with_full_content: bool = False
    target_sites: list[str] = None


@dataclass
class SearchSource:
    """Individual search result source."""

    url: str
    content: str
    full_content: str = ""

    def __post_init__(self):
        """Ensure content is not empty."""
        if not self.content.strip():
            raise ValueError("content cannot be empty")


@dataclass
class SearchResults:
    """Standardized output from search services."""

    success: bool
    sources: list[SearchSource]
    raw_data: str = ""  # For debugging/logging
    error_message: str = ""

    def __post_init__(self):
        """Validate search results."""
        if self.success and not self.sources:
            raise ValueError("successful search must have sources")
        if not self.success and not self.error_message:
            raise ValueError("failed search must have error_message")


@dataclass
class DomainResult:
    """Final result from domain-specific processing."""

    success: bool
    data: dict[str, Any]  # Domain-specific structured data
    confidence: Literal["high", "medium", "low"] = "medium"
    sources: list[str] = None  # no-qa
    reasoning: str = ""
    error_message: str = ""

    def __post_init__(self):
        """Initialize sources if None and validate."""
        if self.sources is None:
            self.sources = []

        if self.success and not self.data:
            raise ValueError("successful result must have data")
        if not self.success and not self.error_message:
            raise ValueError("failed result must have error_message")


# Enums for better type safety
SearchDepthType = Literal["basic", "standard", "extensive"]
ConfidenceType = Literal["high", "medium", "low"]
