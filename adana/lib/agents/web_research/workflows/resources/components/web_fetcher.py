"""
WebFetcherResource - HTTP fetching and web search operations.

This resource handles all network I/O operations including:
- Fetching URLs with rate limiting
- Searching the web
- Validating URLs
- Managing per-domain rate limits
"""

import logging
import time
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from adana.common.llm import LLM
from adana.common.observable import observable
from adana.common.protocols import DictParams
from adana.core.resource.base_resource import BaseResource


logger = logging.getLogger(__name__)


class WebFetcher(BaseResource):
    """
    Component for fetching web content and performing web searches.

    Handles HTTP/HTTPS operations with rate limiting, retries, and
    intelligent result ranking using LLM reasoning.
    """

    def __init__(self, llm_client: LLM | None = None, **kwargs):
        kwargs["llm_client"] = llm_client
        super().__init__(**kwargs)

        # Rate limiting state: domain -> (last_request_time, request_count)
        self._rate_limits: dict[str, tuple[float, int]] = {}
        self._user_agent_index = 0  # For rotating user agents

        # Configuration
        self.config = {
            "rate_limit_per_domain": 1.0,  # 1 request per second per domain
            "max_size": 5_000_000,  # 5MB max page size
            "timeout": 30,
            "user_agents": [
                # Modern browser user agents - rotate through these
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            ],
            "retry_attempts": 3,
            "retry_backoff": 1.0,
            "retry_on_status": [408, 429, 500, 502, 503, 504],
        }

        # Create session with retry logic
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic."""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.config["retry_attempts"],
            backoff_factor=self.config["retry_backoff"],
            status_forcelist=self.config["retry_on_status"],
            allowed_methods=["GET", "POST", "HEAD"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc

    def _get_browser_headers(self, custom_user_agent: str | None = None) -> dict[str, str]:
        """
        Get browser-like headers to avoid bot detection.

        Rotates through user agents and includes common browser headers.
        """
        if custom_user_agent:
            user_agent = custom_user_agent
        else:
            # Rotate through user agents
            user_agent = self.config["user_agents"][self._user_agent_index]
            self._user_agent_index = (self._user_agent_index + 1) % len(self.config["user_agents"])

        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _enforce_rate_limit(self, domain: str) -> None:
        """Enforce rate limit for domain (1 req/sec)."""
        rate_limit = self.config["rate_limit_per_domain"]

        if domain in self._rate_limits:
            last_time, count = self._rate_limits[domain]
            elapsed = time.time() - last_time

            if elapsed < rate_limit:
                wait_time = rate_limit - elapsed
                logger.debug(f"Rate limiting {domain}: waiting {wait_time:.2f}s")
                time.sleep(wait_time)

        # Update rate limit state
        self._rate_limits[domain] = (time.time(), 1)

    def fetch_url(
        self, url: str, timeout: int | None = 10, max_size: int | None = None, allow_redirects: bool = True, user_agent: str | None = None
    ) -> DictParams:
        """
        Fetch content from a URL.

        Args:
            url: The URL to fetch (must be http:// or https://)
            timeout: Request timeout in seconds
            max_size: Maximum response size in bytes
            allow_redirects: Follow redirects
            user_agent: Custom user agent

        Returns:
            {
                "success": bool,
                "url": str,  # Final URL after redirects
                "status_code": int,
                "content_type": str,
                "content": str,  # Raw content
                "headers": dict,
                "encoding": str,
                "size_bytes": int,
                "fetch_time_ms": int,
                "error": str | None
            }
        """
        start_time = time.time()

        # Validate URL scheme
        if not url.startswith(("http://", "https://")):
            return {"success": False, "error": f"Invalid URL scheme. Must be http:// or https://: {url}"}

        # Extract domain and enforce rate limit
        domain = self._get_domain(url)
        self._enforce_rate_limit(domain)

        # Set defaults
        timeout = timeout or self.config["timeout"]
        max_size = max_size or self.config["max_size"]

        # Use browser-like headers
        headers = self._get_browser_headers(custom_user_agent=user_agent)

        try:
            response = self.session.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=allow_redirects,
                stream=True,  # Stream for size checking
            )

            # Check size before reading
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > max_size:
                return {"success": False, "error": f"Content too large: {content_length} bytes (max: {max_size})"}

            # Read content with size limit
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > max_size:
                    logger.warning(f"Content exceeded max_size for {url}, truncating")
                    break

            # Decode content
            encoding = response.encoding or "utf-8"
            try:
                decoded_content = content.decode(encoding, errors="replace")
            except Exception as e:
                decoded_content = content.decode("utf-8", errors="replace")
                logger.warning(f"Encoding error for {url}: {e}, using UTF-8")

            fetch_time_ms = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "url": response.url,  # Final URL after redirects
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "content": decoded_content,
                "headers": dict(response.headers),
                "encoding": encoding,
                "size_bytes": len(content),
                "fetch_time_ms": fetch_time_ms,
                "error": None,
            }

        except requests.exceptions.Timeout:
            return {"success": False, "error": f"Request timeout after {timeout}s"}
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Fetch error: {str(e)}"}

    def search_web(self, query: str, max_results: int = 5, search_engine: str = "google") -> DictParams:
        """
        Search the web using Google Custom Search API.

        Args:
            query: Search query string
            max_results: Maximum number of results (1-20)
            search_engine: Which search engine to use (only "google" supported)

        Returns:
            {
                "success": bool,
                "query": str,
                "search_engine": str,
                "results": [
                    {
                        "title": str,
                        "url": str,
                        "snippet": str,
                        "position": int
                    }
                ],
                "total_results": int,
                "search_time_ms": int,
                "error": str | None
            }
        """
        start_time = time.time()

        if search_engine == "google":
            return self._search_google(query, max_results, start_time)
        else:
            return {"success": False, "error": f"Unsupported search engine: {search_engine}. Only Google is supported."}

    def _search_google(self, query: str, max_results: int, start_time: float) -> DictParams:
        """
        Search using Google Custom Search API.

        Requires:
        - Google Cloud project with Custom Search API enabled
        - GOOGLE_API_KEY environment variable
        - GOOGLE_SEARCH_ENGINE_ID environment variable

        Setup instructions:
        1. Go to https://console.cloud.google.com/
        2. Enable Custom Search API
        3. Create credentials (API key)
        4. Create Custom Search Engine at https://programmablesearchengine.google.com/
        5. Set environment variables:
           export GOOGLE_API_KEY="your-api-key"
           export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"
        """
        import os

        api_key = os.getenv("GOOGLE_API_KEY")
        search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

        if not api_key or not search_engine_id:
            return {
                "success": False,
                "error": (
                    "Google Custom Search requires GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID "
                    "environment variables. See WebFetcherResource._search_google() docstring for setup."
                ),
            }

        try:
            # Google Custom Search API endpoint
            url = "https://www.googleapis.com/customsearch/v1"

            params = {
                "key": api_key,
                "cx": search_engine_id,
                "q": query,
                "num": min(max_results, 10),  # API max is 10 per request
            }

            response = self.session.get(url, params=params, timeout=self.config["timeout"])

            if response.status_code != 200:
                return {"success": False, "error": f"Google API error {response.status_code}: {response.text}"}

            data = response.json()

            results = []
            for i, item in enumerate(data.get("items", []), 1):
                results.append(
                    {"title": item.get("title", ""), "url": item.get("link", ""), "snippet": item.get("snippet", ""), "position": i}
                )

            search_time_ms = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "query": query,
                "search_engine": "google",
                "results": results,
                "total_results": len(results),
                "search_time_ms": search_time_ms,
                "error": None,
            }

        except Exception as e:
            return {"success": False, "error": f"Google Custom Search error: {str(e)}"}

    def validate_url(self, url: str) -> DictParams:
        """
        Validate URL accessibility without fetching full content.

        Args:
            url: URL to validate

        Returns:
            {
                "valid": bool,
                "accessible": bool,
                "status_code": int | None,
                "content_type": str | None,
                "error": str | None
            }
        """
        # Check URL format
        if not url.startswith(("http://", "https://")):
            return {"valid": False, "accessible": False, "status_code": None, "content_type": None, "error": "Invalid URL scheme"}

        try:
            # HEAD request to check accessibility
            domain = self._get_domain(url)
            self._enforce_rate_limit(domain)

            response = self.session.head(url, timeout=10, allow_redirects=True, headers=self._get_browser_headers())

            return {
                "valid": True,
                "accessible": 200 <= response.status_code < 400,
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type"),
                "error": None,
            }

        except Exception as e:
            return {
                "valid": True,  # URL format is valid
                "accessible": False,
                "status_code": None,
                "content_type": None,
                "error": str(e),
            }

    def get_rate_limit_status(self, domain: str) -> DictParams:
        """
        Get current rate limit status for a domain.

        Args:
            domain: Domain to check (e.g., "example.com")

        Returns:
            {
                "domain": str,
                "requests_made": int,
                "time_window_seconds": float,
                "next_available_ms": int,  # Milliseconds until next request allowed
                "rate_limit_active": bool
            }
        """
        if domain not in self._rate_limits:
            return {"domain": domain, "requests_made": 0, "time_window_seconds": 0, "next_available_ms": 0, "rate_limit_active": False}

        last_time, count = self._rate_limits[domain]
        elapsed = time.time() - last_time
        rate_limit = self.config["rate_limit_per_domain"]

        next_available = max(0, rate_limit - elapsed)

        return {
            "domain": domain,
            "requests_made": count,
            "time_window_seconds": elapsed,
            "next_available_ms": int(next_available * 1000),
            "rate_limit_active": next_available > 0,
        }

    def rank_search_results(self, query: str, results: list[DictParams], criteria: str = "relevance") -> DictParams:
        """
        Use LLM reasoning to rank search results intelligently.

        Args:
            query: Original search query
            results: List of search results to rank
            criteria: Ranking criteria (e.g., "relevance", "authority", "recency")

        Returns:
            {
                "ranked_results": list[dict],  # Results with scores
                "reasoning": dict[str, str],   # URL -> explanation
                "recommended_count": int       # How many to fetch
            }
        """
        # Use BaseWAR.reason() for intelligent ranking
        ranking_result = self.reason(
            {
                "task": "Rank search results by relevance, quality, and specified criteria",
                "input": {
                    "query": query,
                    "num_results": len(results),
                    "results": [
                        {
                            "url": r.get("url", ""),
                            "title": r.get("title", ""),
                            "snippet": r.get("snippet", ""),
                            "domain": urlparse(r.get("url", "")).netloc,
                        }
                        for r in results
                    ],
                    "criteria": criteria,
                },
                "output_schema": {
                    "ranked_results": "list[dict] (results ordered by score, each with 'url', 'score' (0.0-1.0), and 'rank' (1-N) keys)",
                    "reasoning": "dict[str, str] (url -> explanation of ranking)",
                    "recommended_count": "int (how many results to fetch, typically 3-5)",
                    "quality_assessment": "str (overall quality of search results)",
                },
                "context": {
                    "ranking_factors": [
                        "Relevance to query (most important)",
                        "Source authority (domain reputation)",
                        "Content freshness (prefer recent if relevant)",
                        "Snippet quality (does it answer the query?)",
                        "Content type match (tutorial vs article vs docs)",
                    ],
                    "known_authoritative_domains": [
                        "stackoverflow.com",
                        "github.com",
                        "python.org",
                        "mozilla.org",
                        "wikipedia.org",
                        "realpython.com",
                        ".gov",
                        ".edu",
                    ],
                },
                "temperature": 0.1,
                "max_tokens": 1500,
                "fallback": {
                    "ranked_results": results,  # Keep original order
                    "reasoning": {},
                    "recommended_count": min(3, len(results)),
                },
            }
        )

        return ranking_result
