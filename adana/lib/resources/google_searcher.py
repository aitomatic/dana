"""
GoogleSearchResource - Quick Google search for simple factual queries.

Use Case: Direct Google search for quick facts
- Search Google for query
- Extract first result snippet
- Return concise answer

Execution Pattern: Direct resource call (95% deterministic, $0 LLM cost)
- Direct API call to Google Custom Search
- Return raw search results
- No workflow orchestration needed
"""

import logging

from adana.common.observable import observable
from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.resource.base_resource import BaseResource
from adana.lib.agents.web_research.workflows.resources.search import SearchResource


logger = logging.getLogger(__name__)


class GoogleSearcherResource(BaseResource):
    """
    Lightweight interface for direct Google searches.

    Returns raw results (titles, snippets, URLs) without reasoning or synthesis.
    Use for fast, low-cost retrieval or as input to higher-level workflows.
    """

    def __init__(self, **kwargs):
        super().__init__(resource_type="google_searcher", **kwargs)
        self.search_resource = SearchResource()

    @observable
    @tool_use
    def search(self, query: str, max_results: int = 10) -> DictParams:
        """
        Perform a raw Google search and return unprocessed results.

        Use for: exploratory or open-ended queries where you need titles, snippets, and URLs,
        not a synthesized answer. Ideal as a first step before deeper analysis.

        Avoid for: direct factual questions (→ use GoogleLookupWorkflow)
        or multi-source synthesis (→ use WebResearchAgent).

        Args:
            query: Search string.
            max_results: Number of results to return (default 10).

        Returns:
            DictParams with "results" (list of {title, url, snippet}), "success", and "source".
        """

        if not query:
            return {"success": False, "error": "Query parameter is required", "context": {}}

        # Direct search call without workflow orchestration
        result = self.search_resource.search_web(query=query, max_results=max_results)

        if result.get("success", False):
            logger.info(f"Google Search completed successfully for query: {query}")
            return {"success": True, "answer": result, "context": result}
        else:
            logger.error(f"Google Search failed for query: {query}")
            return {"success": False, "error": result.get("error", "Unknown error"), "context": result}
