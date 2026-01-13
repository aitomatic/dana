"""Parallel source gathering workflow for SmartResearchAgent."""

import asyncio
import time

from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output
from dana.lib.resources.web_research.search import SearchResource
from dana.lib.resources.web_research.web_fetcher import WebFetcher

# Import the new resource
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from resources.source_ranking import SourceRankingResource


class ParallelGatheringWorkflow(BaseWorkflow):
    """
    Gathers information from diverse sources in parallel.

    Based on strategy, searches multiple source types simultaneously,
    ranks results, and fetches content from top sources.
    """

    def __init__(self, workflow_id: str | None = None, **kwargs):
        super().__init__(workflow_id=workflow_id or "parallel-gathering", **kwargs)
        self.search_resource = SearchResource()
        self.web_fetcher = WebFetcher()
        self.ranking_resource = SourceRankingResource()

    @validate_input(
        query={"required": True, "type": str},
        strategy={"required": True, "type": dict},
    )
    @validate_output(
        success={"required": True, "type": bool},
        sources={"required": True, "type": list},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Execute parallel source gathering.

        Args:
            query: Search query
            strategy: Strategy configuration with source types

        Returns:
            {
                "success": True,
                "sources": [...],  # Ranked sources with content
                "total_found": int,
                "total_fetched": int,
                "metadata": {...}
            }
        """
        query = kwargs["query"]
        strategy = kwargs["strategy"]
        start_time = time.time()

        try:
            # Step 1: Parallel search across source types
            max_sources = strategy.get("max_sources", 10)
            source_types = strategy.get("sources", ["google_search"])

            # Run searches in parallel
            all_sources = asyncio.run(self._parallel_search(query, source_types, max_sources))

            if not all_sources:
                return {"success": False, "error": "No sources found", "sources": [], "total_found": 0, "total_fetched": 0}

            # Step 2: Rank sources by quality
            ranking_result = self.ranking_resource.rank_by_quality(sources=all_sources, query=query)

            if not ranking_result.get("success"):
                ranked_sources = all_sources  # Fallback to unranked
            else:
                ranked_sources = ranking_result["ranked_sources"]

            # Step 3: Select top N sources
            top_sources = ranked_sources[:max_sources]

            # Step 4: Fetch content from top sources (in parallel)
            sources_with_content = asyncio.run(self._fetch_content(top_sources))

            processing_time = time.time() - start_time

            return {
                "success": True,
                "sources": sources_with_content,
                "total_found": len(all_sources),
                "total_fetched": len(sources_with_content),
                "source_types": source_types,
                "metadata": {
                    "processing_time": round(processing_time, 3),
                    "strategy": strategy.get("type", "unknown"),
                    "timestamp": time.time(),
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e), "sources": [], "total_found": 0, "total_fetched": 0}

    async def _parallel_search(self, query: str, source_types: list, max_per_type: int = 10) -> list:
        """
        Execute searches across multiple source types in parallel.

        Args:
            query: Search query
            source_types: List of source types to search
            max_per_type: Maximum results per source type

        Returns:
            List of source dictionaries
        """
        tasks = []

        for source_type in source_types:
            if source_type in ["google_search", "academic", "news", "documentation"]:
                tasks.append(self._search_google(query, max_per_type))
            # Add more source types as needed

        if not tasks:
            tasks.append(self._search_google(query, max_per_type))

        # Execute all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        all_sources = []
        for result in results:
            if isinstance(result, list):
                all_sources.extend(result)

        return all_sources

    async def _search_google(self, query: str, max_results: int = 10) -> list:
        """Search Google and return results."""
        try:
            result = self.search_resource.search_web(query=query, max_results=max_results)

            if not result.get("success"):
                return []

            # Convert search results to source format
            sources = []
            for item in result.get("results", []):
                sources.append(
                    {
                        "url": item.get("link", ""),
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "domain": item.get("displayLink", ""),
                        "date": "",  # Google search doesn't always provide dates
                        "content": "",  # Will be fetched later
                        "type": "web",
                    }
                )

            return sources

        except Exception:
            return []

    async def _fetch_content(self, sources: list) -> list:
        """
        Fetch content from sources in parallel.

        Args:
            sources: List of source dictionaries with URLs

        Returns:
            Sources with content field populated
        """
        tasks = []
        for source in sources:
            tasks.append(self._fetch_single(source))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        sources_with_content = []
        for result in results:
            if isinstance(result, dict) and result.get("success"):
                sources_with_content.append(result["source"])

        return sources_with_content

    async def _fetch_single(self, source: dict) -> dict:
        """Fetch content for a single source."""
        try:
            url = source.get("url", "")
            if not url:
                return {"success": False}

            # Use WebFetcher to get content
            fetch_result = self.web_fetcher.fetch_url(url)

            if fetch_result.get("success"):
                content = fetch_result.get("content_text", "")
                # Limit content size
                if len(content) > 5000:
                    content = content[:5000] + "..."

                source["content"] = content
                return {"success": True, "source": source}

            return {"success": False}

        except Exception:
            return {"success": False}
