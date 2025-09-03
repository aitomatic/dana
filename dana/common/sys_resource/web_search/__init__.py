"""
Web Search Resource for DANA framework.

This module provides web search capabilities through different search services
(Google Custom Search, Llama Search) wrapped in DANA's resource system.

The WebSearchResource class provides a unified interface for web searching
that can be used via DANA's `use()` function in .na files.
"""

# Core resource classes
from .web_search_resource import WebSearchResource

# Search service implementations
from .google_search_service import GoogleSearchService
from .llama_search_service import LlamaSearchService

__all__ = [
    # Main exports for DANA integration
    "WebSearchResource",
    # Service implementations (for advanced usage)
    "GoogleSearchService",
    "LlamaSearchService",
]
