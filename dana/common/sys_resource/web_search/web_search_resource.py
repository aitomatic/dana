"""Web Search Resource implementation for DANA framework."""

from dana.common.sys_resource.web_search.utils.summarizer import ContentSummarizer
from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.common.exceptions import ResourceError

from .core.models import SearchRequest, SearchResults, SearchDepth
from .google_search_service import GoogleSearchService
from .llama_search_service import LlamaSearchService

from dataclasses import asdict


class WebSearchResource(BaseSysResource):
    """Simple Web Search Resource using Google or Llama-Search services."""

    def __init__(self, service_type: str = "", name: str = "web_search", description: str | None = None, **kwargs):
        """Initialize WebSearchResource."""
        super().__init__(name, description or f"Web Search Resource using {service_type}")

        self._service_type = service_type or "llama-search"  # Store service type for error messages

        if service_type == "google":
            self._search_service = GoogleSearchService()
        elif service_type == "llama-search":
            self._search_service = LlamaSearchService()
        else:
            self._search_service = LlamaSearchService()

        self._is_ready = False

    async def initialize(self) -> None:
        """Initialize the web search resource."""
        await super().initialize()

        if hasattr(self._search_service, "is_available") and not self._search_service.is_available():
            raise ResourceError(f"Search service '{self._service_type}' is not available")

        self._is_ready = True

    async def search(
        self,
        query: str,
        search_depth: SearchDepth = SearchDepth.BASIC,
        domain: str = "",
        with_full_content: bool = False,
    ) -> SearchResults:
        """Execute web search with given query."""
        if not self._is_ready:
            await self.initialize()

        # Use provided search_depth or fallback to config default

        request = SearchRequest(
            query=query,
            search_depth=search_depth,
            domain=domain,
            with_full_content=with_full_content,
        )

        try:
            return await self._search_service.search(request)
        except Exception as e:
            raise ResourceError(f"Search failed: {e}") from e

    async def answer(
        self, query: str, search_depth: SearchDepth = SearchDepth.BASIC, domain: str = "", with_full_content: bool = False
    ) -> dict:
        """Answer a question using web search."""
        result = await self.search(query, search_depth, domain, with_full_content)
        context = "\n\n".join([source.content for source in result.sources])
        summarizer = ContentSummarizer(context)
        summary = await summarizer.summarize_for_query(query)
        data = asdict(result)
        data["summary"] = summary
        return data
