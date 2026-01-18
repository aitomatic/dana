"""
SimpleWebSearch - Web search without API keys.

Uses multiple backends for reliability:
1. duckduckgo-search package (if installed)
2. DuckDuckGo HTML interface fallback
"""

import logging
import re
import time
from urllib.parse import quote_plus, urljoin

import requests

from dana.common.protocols import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


logger = logging.getLogger(__name__)

# Try to import ddgs package (preferred) or duckduckgo_search (legacy)
try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAS_DDGS = True
    except ImportError:
        HAS_DDGS = False


class SimpleWebSearch(BaseResource):
    """
    Simple web search resource that works without API keys.

    Uses duckduckgo-search package if available, falls back to HTML scraping.
    """

    def __init__(self, resource_id: str = "web-search", **kwargs):
        """Initialize simple web search.

        Args:
            resource_id: ID for this resource (default: "web-search")
        """
        super().__init__(resource_id=resource_id, **kwargs)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

    @tool_use
    def search(self, query: str, max_results: int = 5) -> DictParams:
        """
        Search the web using DuckDuckGo.

        This search does NOT require any API keys or credentials.
        Use this to find information on the web about any topic.

        Args:
            query: What to search for (e.g., "AI trends 2024", "python tutorials")
            max_results: Maximum number of results to return (1-10)

        Returns:
            dict with:
            - success (bool): Whether search succeeded
            - query (str): The search query used
            - results (list): List of search results, each with:
                - title (str): Page title
                - url (str): Page URL
                - snippet (str): Brief description
            - total_results (int): Number of results returned
            - error (str): Error message if failed

        Example:
            search("latest AI trends") -> Returns top 5 articles about AI trends
        """
        # Try duckduckgo-search package first (most reliable)
        if HAS_DDGS:
            try:
                results = self._search_with_ddgs(query, max_results)
                if results:
                    return {
                        "success": True,
                        "query": query,
                        "results": results,
                        "total_results": len(results),
                        "error": "",
                    }
            except Exception as e:
                logger.warning(f"DDGS search failed, trying fallback: {e}")

        # Fallback to HTML scraping
        try:
            results = self._search_with_html(query, max_results)
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
                "error": "" if results else "No results found",
            }
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "success": False,
                "query": query,
                "results": [],
                "total_results": 0,
                "error": f"Search error: {str(e)}",
            }

    def _search_with_ddgs(self, query: str, max_results: int) -> list[DictParams]:
        """Search using duckduckgo-search package."""
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                })
        return results

    def _search_with_html(self, query: str, max_results: int) -> list[DictParams]:
        """Search using DuckDuckGo HTML interface (fallback)."""
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

        # Add delay to avoid rate limiting
        time.sleep(0.5)

        response = self.session.get(search_url, timeout=15, allow_redirects=True)

        # Handle 202 (Accepted) - DDG sometimes returns this
        if response.status_code == 202:
            # Wait and retry once
            time.sleep(1)
            response = self.session.get(search_url, timeout=15, allow_redirects=True)

        response.raise_for_status()
        return self._parse_ddg_html(response.text, max_results)

    def _parse_ddg_html(self, html: str, max_results: int) -> list[DictParams]:
        """Parse DuckDuckGo HTML search results."""
        from urllib.parse import unquote

        results = []

        # Pattern to find result links
        link_pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE
        )

        # Pattern for snippets
        snippet_pattern = re.compile(
            r'class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE
        )

        # Split by result div blocks - use looser pattern
        result_blocks = re.split(r'<div[^>]+class="result\s', html)

        for block in result_blocks[1:]:  # Skip first (before first result)
            if len(results) >= max_results:
                break

            link_match = link_pattern.search(block)
            if not link_match:
                continue

            url = link_match.group(1)

            # DuckDuckGo wraps URLs in redirect - extract actual URL
            # Format: //duckduckgo.com/l/?uddg=<encoded_url>&...
            if "uddg=" in url:
                url_match = re.search(r'uddg=([^&]+)', url)
                if url_match:
                    url = unquote(url_match.group(1))

            # Skip ads - they have patterns like /y.js?ad_domain= or ad_provider=
            if "/y.js?" in url or "ad_domain=" in url or "ad_provider=" in url:
                continue

            # Skip DuckDuckGo internal URLs
            if "duckduckgo.com" in url:
                continue

            # Skip if not a valid http URL
            if not url.startswith("http"):
                continue

            title = self._clean_html(link_match.group(2))

            # Find snippet in same block
            snippet_match = snippet_pattern.search(block)
            snippet = self._clean_html(snippet_match.group(1)) if snippet_match else ""

            results.append({
                "title": title,
                "url": url,
                "snippet": snippet,
            })

        return results

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean up text."""
        import html

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities (handles &#x27; &#39; &amp; etc.)
        text = html.unescape(text)
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @tool_use
    def fetch_url(self, url: str) -> DictParams:
        """
        Fetch the content of a web page.

        Use this to read the full content of a URL found via search.

        Args:
            url: The URL to fetch (must start with http:// or https://)

        Returns:
            dict with:
            - success (bool): Whether fetch succeeded
            - url (str): The URL fetched
            - title (str): Page title if found
            - content (str): Page text content (HTML stripped)
            - error (str): Error message if failed
        """
        try:
            if not url.startswith(("http://", "https://")):
                return {
                    "success": False,
                    "url": url,
                    "title": "",
                    "content": "",
                    "error": "URL must start with http:// or https://",
                }

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            html = response.text

            # Extract title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            title = self._clean_html(title_match.group(1)) if title_match else ""

            # Extract main content (simple approach - get text from body)
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.IGNORECASE | re.DOTALL)
            if body_match:
                content = body_match.group(1)
                # Remove script and style tags
                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                content = self._clean_html(content)
                # Limit content length
                if len(content) > 10000:
                    content = content[:10000] + "... [truncated]"
            else:
                content = self._clean_html(html)[:10000]

            # Detect blocked/error pages that return 200 but no useful content
            # Check beginning of content for common block indicators
            content_lower = content.lower()
            content_start = content_lower[:500] if len(content_lower) > 500 else content_lower
            blocked_indicators = [
                "oops, something went wrong",
                "access denied",
                "please verify you are a human",
                "enable javascript",
                "checking your browser",
                "just a moment",
                "captcha",
                "blocked",
            ]
            for indicator in blocked_indicators:
                if indicator in content_start:
                    return {
                        "success": False,
                        "url": url,
                        "title": title,
                        "content": "",
                        "error": f"Page blocked or requires JavaScript. Try a different URL.",
                    }

            return {
                "success": True,
                "url": url,
                "title": title,
                "content": content,
                "error": "",
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "url": url,
                "title": "",
                "content": "",
                "error": f"Fetch failed: {str(e)}",
            }
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "title": "",
                "content": "",
                "error": f"Error: {str(e)}",
            }
