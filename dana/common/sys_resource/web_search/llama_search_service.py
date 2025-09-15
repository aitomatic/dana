"""
Llama Search Service

Implements the SearchService protocol using the llama-search SDK.
This service replaces the OpenAI service by using the official llama-search Python SDK.
"""

import os

from llama_search import AsyncLlamaSearch
from .core.models import SearchRequest, SearchResults, SearchSource


class LlamaSearchService:
    """
    Search service implementation using the llama-search SDK.

    This service uses the official llama-search Python SDK which handles
    authentication, rate limiting, and error handling automatically.
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 180,
    ):
        """
        Initialize the llama-search service.

        Args:
            api_key: API key for llama-search.com (defaults to LLAMA_SEARCH_API_KEY env var)
            timeout: Request timeout in seconds (passed to SDK)
        """
        self.api_key = api_key or os.getenv("LLAMA_SEARCH_API_KEY")
        if not self.api_key:
            raise ValueError("API key required (set LLAMA_SEARCH_API_KEY or pass api_key)")

        self.timeout = float(timeout)

        # Initialize the SDK client with correct parameters
        self._client = AsyncLlamaSearch(api_key=self.api_key, timeout=self.timeout)

    async def search(self, request: SearchRequest) -> SearchResults:
        """
        Execute a web search using the llama-search SDK and return standardized results.

        This method uses the official llama-search Python SDK which handles
        authentication, rate limiting, and error handling automatically.

        Args:
            request: Standardized search request

        Returns:
            SearchResults: Standardized search results with sources
        """
        try:
            # Use the SDK's web_search method
            async with self._client as client:
                result = await client.web_search(
                    query=request.query,
                    search_depth=request.search_depth,
                    domain=request.domain,
                )

                # Transform SDK result to our SearchResults format
                sources = [
                    SearchSource(
                        url=source.url,
                        content=source.content,
                        full_content=source.full_content or "",
                    )
                    for source in result.sources
                ]

                return SearchResults(
                    success=True,  # SDK successful response
                    sources=sources,
                    error_message="",
                )

        except Exception as e:
            # SDK handles most error cases, but catch any remaining exceptions
            error_message = str(e)

            # Handle common SDK error patterns
            if "invalid api key" in error_message.lower() or "unauthorized" in error_message.lower():
                error_message = "Invalid API key"
            elif "insufficient credits" in error_message.lower() or "payment required" in error_message.lower():
                error_message = "Insufficient credits"
            elif "timeout" in error_message.lower():
                error_message = "Request timeout"
            else:
                error_message = f"Llama search failed: {error_message}"

            return SearchResults(
                success=False,
                sources=[],
                error_message=error_message,
            )

    def get_service_info(self) -> dict[str, any]:
        """Get information about this search service."""
        return {
            "service_type": "llama_search_sdk",
            "timeout": self.timeout,
            "supported_depths": ["basic", "standard", "extensive"],
            "sdk_version": "official_llama_search_sdk",
        }


class MockLlamaSearchService(LlamaSearchService):
    """
    Mock version of Llama search service for testing and development.

    Returns simulated search results without making actual API calls.
    Useful for development when you don't want to consume credits.
    """

    def __init__(self, **kwargs):
        """Initialize mock service without requiring API key."""
        self.base_url = kwargs.get("base_url", "https://mock-llama-search.com")
        self.timeout = kwargs.get("timeout", 120)

    async def search(self, request: SearchRequest) -> SearchResults:
        """Return mock search results that simulate llama-search.com responses."""
        # Simulate API delay
        import asyncio

        await asyncio.sleep(0.2)

        # Generate mock sources based on the query
        mock_sources = [
            SearchSource(
                url=f"https://official-source.com/product-{request.query.replace(' ', '-')}",
                content=f"Official product information for {request.query}. "
                f"This mock result simulates what llama-search.com would return "
                f"for a {request.search_depth} search.",
                full_content=(f"Extended mock content for {request.query} from llama-search.com" if request.with_full_content else ""),
            ),
            SearchSource(
                url="https://manufacturer.com/specifications",
                content=f"Technical specifications for {request.query}. "
                f"Domain: {request.domain if request.domain else 'general'}. "
                f"Detailed technical information and compatibility data.",
                full_content=(f"Complete technical documentation for {request.query}" if request.with_full_content else ""),
            ),
            SearchSource(
                url="https://reviews.com/expert-review",
                content=f"Expert reviews and analysis for {request.query}. "
                f"Comprehensive evaluation including performance metrics and comparisons.",
                full_content=(f"Detailed expert analysis and benchmark data for {request.query}" if request.with_full_content else ""),
            ),
        ]

        # Vary number of sources based on search depth
        depth_limits = {"basic": 1, "standard": 2, "extensive": 3}
        limit = depth_limits.get(request.search_depth, 2)

        return SearchResults(
            success=True,
            sources=mock_sources[:limit],
            raw_data=f"Mock llama-search executed for: {request.query}",
            error_message="",
        )

    def __str__(self) -> str:
        return f"MockLlamaSearchService(base_url={self.base_url})"
