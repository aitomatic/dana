"""Google Custom Search Engine implementation."""

import logging
from typing import NamedTuple

import httpx

from .config import GoogleSearchConfig
from .exceptions import APIKeyError, RateLimitError, ServiceUnavailableError

logger = logging.getLogger(__name__)


def _sanitize_api_key(text: str, api_key: str) -> str:
    """Replace API key with masked version in text for secure logging."""
    if not api_key or len(api_key) < 8:
        return text

    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    return text.replace(api_key, masked_key)


class GoogleResult(NamedTuple):
    """Structured Google search result."""

    url: str
    title: str
    snippet: str
    display_link: str


class GoogleSearchEngine:
    """Google Custom Search API integration with async support."""

    def __init__(self, config: GoogleSearchConfig):
        """
        Initialize Google search engine.

        Args:
            config: Google search configuration
        """
        self.config = config
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search(self, query: str, max_results: int = None) -> list[GoogleResult]:
        """
        Perform async Google Custom Search and return structured results.

        Args:
            query: Search query string
            max_results: Maximum number of results (defaults to config.max_results)

        Returns:
            List of GoogleResult objects

        Raises:
            APIKeyError: If API key is invalid or quota exceeded
            RateLimitError: If rate limit is exceeded
            ServiceUnavailableError: If Google API is temporarily unavailable
        """
        if max_results is None:
            max_results = self.config.max_results

        # Limit to Google API maximum
        max_results = min(max_results, 10)

        params = {
            "q": query,
            "key": self.config.api_key,
            "cx": self.config.cse_id,
            "num": max_results,
            "lr": "lang_en",
            "gl": "us",
            "hl": "en",
        }

        logger.info(f"🔍 Google Search: {query[:100]}{'...' if len(query) > 100 else ''}")

        try:
            timeout = httpx.Timeout(timeout=self.config.timeout_seconds)

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(self.base_url, params=params)
                await self._handle_api_errors(response)
                results_data = response.json()

            if "items" not in results_data:
                logger.info(f"No search results for query: {query}")
                return []

            # Convert to structured results
            results = []
            for item in results_data["items"]:
                result = GoogleResult(
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    display_link=item.get("displayLink", ""),
                )
                results.append(result)

            logger.info(f"✅ Found {len(results)} Google search results")
            return results

        except (APIKeyError, RateLimitError, ServiceUnavailableError) as e:
            # Sanitize any API key that might appear in error message
            sanitized_error = _sanitize_api_key(str(e), self.config.api_key)
            logger.error(f"❌ Google Search error: {sanitized_error}")
            raise
        except httpx.TimeoutException:
            logger.error("❌ Google Search request timed out")
            raise ServiceUnavailableError("Google Search request timed out")
        except httpx.RequestError as e:
            sanitized_error = _sanitize_api_key(str(e), self.config.api_key)
            logger.error(f"❌ Google Search request failed: {sanitized_error}")
            raise ServiceUnavailableError(f"Google Search request failed: {sanitized_error}")
        except Exception as e:
            sanitized_error = _sanitize_api_key(str(e), self.config.api_key)
            logger.error(f"❌ Unexpected Google Search error: {sanitized_error}")
            raise ServiceUnavailableError(f"Unexpected error: {sanitized_error}")

    async def _handle_api_errors(self, response: httpx.Response) -> None:
        """
        Handle Google API specific errors.

        Args:
            response: HTTP response from Google API

        Raises:
            APIKeyError: For authentication/quota issues
            RateLimitError: For rate limiting
            ServiceUnavailableError: For server errors
        """
        if response.status_code == 200:
            return

        if response.status_code == 403:
            # Could be invalid API key, quota exceeded, or API not enabled
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            error_message = error_data.get("error", {}).get("message", "Authentication failed")
            sanitized_message = _sanitize_api_key(error_message, self.config.api_key)

            if "quota" in error_message.lower():
                raise APIKeyError(f"Google API quota exceeded: {sanitized_message}")
            elif "api key" in error_message.lower():
                raise APIKeyError(f"Invalid Google API key: {sanitized_message}")
            else:
                raise APIKeyError(f"Google API access denied: {sanitized_message}")

        elif response.status_code == 429:
            raise RateLimitError("Google API rate limit exceeded")

        elif response.status_code >= 500:
            raise ServiceUnavailableError(f"Google API server error: {response.status_code}")

        else:
            # Other client errors
            response.raise_for_status()

    def optimize_query(self, query: str, search_depth: str = "standard") -> str:
        """
        Optimize search query based on search depth.

        Args:
            query: Original search query
            search_depth: Search depth level ("basic", "standard", "extensive")

        Returns:
            Optimized search query
        """
        if search_depth == "extensive":
            # Add technical terms for comprehensive results
            return f"{query} with all specifications and relevant information"
        elif search_depth == "standard":
            # Add basic technical terms
            return f"{query} with all specifications"
        else:
            # Use query as-is for basic search
            return query

    def create_fallback_queries(self, base_query: str) -> list[str]:
        """
        Create fallback search queries for better coverage.

        Args:
            base_query: Base search query

        Returns:
            List of fallback query variations
        """
        queries = []

        # Try with different technical terms
        queries.append(f"{base_query} datasheet")
        queries.append(f"{base_query} manual")
        queries.append(f"{base_query} specifications")

        # Try with filetype restrictions for technical docs
        queries.append(f"{base_query} filetype:pdf")

        # Broader search without specific terms
        queries.append(base_query)

        return queries

    def is_available(self) -> bool:
        """
        Check if Google Search is properly configured.

        Returns:
            True if API key and CSE ID are available
        """
        return bool(self.config.api_key and self.config.cse_id)
