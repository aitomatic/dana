"""
SearchComponents - Finding information through web searches.

Provides reusable search operations that can be composed into workflows.
"""

import logging
from datetime import datetime
from urllib.parse import urlparse

from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.resource.base_resource import BaseResource
from adana.lib.agents.web_research.workflows.resources.components import _web_fetcher
from adana.core.workflow.workflow_executor import observable

logger = logging.getLogger(__name__)


class SearchResource(BaseResource):
    """Reusable search operations for workflow composition."""

    def __init__(self, **kwargs):
        """
        Initialize search components.
        """
        super().__init__(**kwargs)
        self.web_fetcher = _web_fetcher

    @tool_use
    @observable
    def search_web(self, query: str, max_results: int = 5) -> DictParams:
        """
        Perform web search and return results.

        Uses Google Custom Search API. Requires GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables.

        Args:
            query: Search query string
            max_results: Maximum number of results (1-20)

        Returns:
            Search results with success status, query, results list
        """
        import os

        # Check for required Google API credentials
        if not os.getenv("GOOGLE_API_KEY") or not os.getenv("GOOGLE_SEARCH_ENGINE_ID"):
            return {
                "success": False,
                "error": "Google API credentials not found. Please set GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables.",
                "query": query,
                "results": [],
                "total_results": 0,
            }

        return self.web_fetcher.search_web(query, max_results, "google")

    def filter_by_domain_authority(self, results: list[DictParams], authoritative_domains: list[str] | None = None) -> list[DictParams]:
        """
        Filter search results to prioritize authoritative domains.

        Args:
            results: List of search results
              - url
              - title
              - snippet
              - domain
            authoritative_domains: List of trusted domains (e.g., ".gov", ".edu")

        Returns:
            Filtered results with authoritative sources first
        """
        if not authoritative_domains:
            authoritative_domains = [
                ".gov",
                ".edu",
                ".org",
                "wikipedia.org",
                "github.com",
                "stackoverflow.com",
                "python.org",
                "mozilla.org",
                "w3.org",
            ]

        def is_authoritative(url: str) -> bool:
            domain = urlparse(url).netloc.lower()
            return any(auth in domain for auth in authoritative_domains)

        # Partition into authoritative and non-authoritative
        authoritative = [r for r in results if is_authoritative(r["url"])]
        non_authoritative = [r for r in results if not is_authoritative(r["url"])]

        return authoritative + non_authoritative

    def filter_by_date(self, results: list[DictParams], max_age_months: int = 12) -> list[DictParams]:
        """
        Filter search results by recency (based on URL patterns and snippets).

        Args:
            results: List of search results
            max_age_months: Maximum age in months

        Returns:
            Results filtered by recency indicators
        """
        # This is a heuristic approach since we don't have full metadata
        # Look for date patterns in URLs and snippets
        import re

        current_year = datetime.now().year
        cutoff_year = current_year - (max_age_months // 12)

        def has_recent_indicator(result: DictParams) -> bool:
            text = f"{result.get('url', '')} {result.get('snippet', '')}"

            # Look for year patterns
            years = re.findall(r"\b(20\d{2})\b", text)
            if years:
                latest_year = max(int(y) for y in years)
                return latest_year >= cutoff_year

            # Look for recency keywords
            recency_keywords = ["latest", "recent", "new", "updated", "2024", "2025"]
            return any(keyword in text.lower() for keyword in recency_keywords)

        # Partition into recent and older
        recent = [r for r in results if has_recent_indicator(r)]
        older = [r for r in results if not has_recent_indicator(r)]

        return recent + older

    @observable
    def rank_by_relevance(self, query: str, results: list[DictParams], criteria: str = "relevance") -> DictParams:
        """
        Use LLM reasoning to intelligently rank search results.

        Args:
            query: Original search query
            results: List of search results
            criteria: Ranking criteria

        Returns:
            Ranked results with scores and reasoning
        """
        return self.web_fetcher.rank_search_results(query, results, criteria)

    def search_comparison_articles(self, item1: str, item2: str, max_results: int = 5) -> DictParams:
        """
        Search for comparison articles between two items.

        Args:
            item1: First item to compare
            item2: Second item to compare
            max_results: Maximum number of results

        Returns:
            Search results focused on comparisons
        """
        # Try multiple query patterns for best coverage
        queries = [
            f"{item1} vs {item2}",
            f"{item1} compared to {item2}",
            f"compare {item1} and {item2}",
            f"difference between {item1} and {item2}",
        ]

        all_results = []
        seen_urls = set()

        for query in queries:
            search_result = self.web_fetcher.search_web(query, max_results=max_results)

            if search_result.get("success"):
                for result in search_result.get("results", []):
                    url = result["url"]
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(result)

            # Stop if we have enough results
            if len(all_results) >= max_results:
                break

        return {
            "success": True,
            "query": f"{item1} vs {item2}",
            "results": all_results[:max_results],
            "total_results": len(all_results[:max_results]),
        }

    @observable
    def search_with_date_filter(self, query: str, max_results: int = 5, max_age_months: int = 6) -> DictParams:
        """
        Search with focus on recent results.

        Args:
            query: Search query
            max_results: Maximum number of results
            max_age_months: Maximum age in months

        Returns:
            Search results filtered by recency
        """
        # Add recency keywords to query
        current_year = datetime.now().year
        query_with_date = f"{query} {current_year}"

        search_result = self.web_fetcher.search_web(
            query_with_date,
            max_results=max_results * 2,  # Get more to compensate for filtering
        )

        if not search_result["success"]:
            return search_result

        # Filter by date
        filtered_results = self.filter_by_date(search_result["results"], max_age_months=max_age_months)

        return {
            "success": True,
            "query": query_with_date,
            "results": filtered_results[:max_results],
            "total_results": len(filtered_results[:max_results]),
        }

    def search_documentation(self, topic: str, max_results: int = 5) -> DictParams:
        """
        Search for official documentation.

        Args:
            topic: Topic to find documentation for
            max_results: Maximum number of results

        Returns:
            Search results focused on documentation sites
        """
        # Add documentation-specific keywords
        query = f"{topic} documentation official"

        search_result = self.web_fetcher.search_web(query, max_results=max_results * 2)

        if not search_result["success"]:
            return search_result

        # Filter for documentation domains
        doc_domains = [
            "docs.",
            "documentation.",
            "developer.",
            "readthedocs.io",
            "/docs/",
            "/documentation/",
            ".org/guide/",
            ".org/manual/",
            ".org/reference/",
        ]

        def is_documentation_site(url: str) -> bool:
            return any(domain in url.lower() for domain in doc_domains)

        doc_results = [r for r in search_result["results"] if is_documentation_site(r["url"])]
        other_results = [r for r in search_result["results"] if not is_documentation_site(r["url"])]

        # Prioritize documentation sites
        combined = doc_results + other_results

        return {"success": True, "query": query, "results": combined[:max_results], "total_results": len(combined[:max_results])}

    def search_tutorials(self, topic: str, max_results: int = 5) -> DictParams:
        """
        Search for tutorials and how-to guides.

        Args:
            topic: Topic to find tutorials for
            max_results: Maximum number of results

        Returns:
            Search results focused on tutorials
        """
        # Try multiple tutorial-focused queries
        queries = [f"{topic} tutorial", f"how to {topic}", f"{topic} step by step guide"]

        all_results = []
        seen_urls = set()

        for query in queries:
            search_result = self.web_fetcher.search_web(query, max_results=max_results)

            if search_result["success"]:
                for result in search_result["results"]:
                    url = result["url"]
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(result)

            if len(all_results) >= max_results:
                break

        return {
            "success": True,
            "query": f"{topic} tutorial",
            "results": all_results[:max_results],
            "total_results": len(all_results[:max_results]),
        }
