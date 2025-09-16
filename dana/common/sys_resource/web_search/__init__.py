"""
Web Search Resource for DANA framework.
"""

# Core resource classes
from .web_search_resource import WebSearchResource

# Search service implementations
from .google_search_service import GoogleSearchService
from .llama_search_service import LlamaSearchService

__all__ = [
    "WebSearchResource",
    "GoogleSearchService",
    "LlamaSearchService",
]
