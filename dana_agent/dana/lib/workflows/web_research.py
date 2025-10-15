from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output
from dana.lib.resources.web_research.extract import ExtractResource
from dana.lib.resources.web_research.fetch import FetchResource
from dana.lib.resources.web_research.format import FormatResource
from dana.lib.resources.web_research.search import SearchResource
from dana.lib.resources.web_research.synthesize import SynthesizeResource


_searcher = SearchResource()
_fetcher = FetchResource()
_extractor = ExtractResource()
_formatter = FormatResource()
_synthesizer = SynthesizeResource()


# ============================================================================
# Internal Helper Functions (using new callable workflow feature)
# ============================================================================


def _synthesize(extractions, topic, synthesis_type="themes"):
    """
    Synthesize content from multiple extractions.

    Dynamically selects synthesis method based on synthesis_type.

    Args:
        extractions (list): List of content extractions
        topic (str): Research topic
        synthesis_type (str): Type of synthesis - "themes" or "timeline"

    Returns:
        Dict with synthesis results
    """
    method = getattr(_synthesizer, f"synthesize_by_{synthesis_type}")
    return method(extractions=extractions, topic=topic)


def _select_top_urls(ranked_results, max_sources=5):
    """
    Extract top N URLs from ranked search results.

    Args:
        ranked_results (list): Ranked search results
        max_sources (int): Maximum number of URLs to extract (default 5)

    Returns:
        Dict with urls list
    """
    urls = [result.get("url") for result in ranked_results[:max_sources] if result.get("url")]
    return {"urls": urls, "count": len(urls)}


# ============================================================================
# Public Workflows
# ============================================================================


class SearchWorkflow(BaseWorkflow):
    @validate_input(
        query={"required": True, "type": str, "min_length": 1},
        max_results={"type": int, "min_value": 1, "max_value": 100, "default": 10},
    )
    @validate_output(
        success={"required": True, "type": bool},
        query={"required": True, "type": str},
        results={"required": True, "type": list},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Perform web search and return results.

        Args:
            **kwargs: Input parameters, should contain:
                query (str): The query to search for. (Required, min length 1)
                max_results (int, optional): The maximum number of results to return. Defaults to 10. (Range: 1-100)

        Returns:
            DictParams: A dictionary with the search results containing:
                success (bool): Whether the search was successful.
                query (str): The original search query.
                search_engine (str): Search engine used (e.g., "google").
                results (list[dict]): List of search results, each with:
                    title (str): Result title.
                    url (str): Result URL.
                    snippet (str): Result snippet/description.
                    position (int): Result position in search results.
                total_results (int): Total number of results returned.
                search_time_ms (int): Time taken for the search in milliseconds.
                error (str, optional): Error message if success is False.

        Example:
            >>> workflow = SearchWorkflow()
            >>> result = workflow._do_execute(query="Python programming", max_results=5)
            >>> print(result["results"][0]["title"])
            'Python.org'
        """
        return _searcher.search(query=kwargs["query"], max_results=kwargs["max_results"])


class GoogleLookupWorkflow(BaseWorkflow):
    """
    Quick Google search for simple factual answers.

    USE FOR: Simple facts, definitions, quick lookups
    EXAMPLES: "What is the capital of France?", "When was Python created?"
    AVOID: Complex analysis, multiple sources, deep research
    STEPS: Search → Extract
    """

    def __init__(self, workflow_id: str | None = None, **kwargs):
        """
        Initialize GoogleLookupWorkflow.
        """
        super().__init__(workflow_id=workflow_id or "google-lookup", **kwargs)

    @validate_input(
        query={"required": True, "type": str, "min_length": 1},
        max_results={"type": int, "min_value": 1, "max_value": 10, "default": 1},
    )
    @validate_output(
        success={"required": True, "type": bool},
        answer={"required": True, "type": str},
        source={"required": True, "type": str},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Quick Google search for simple facts.

        Args:
            **kwargs: Input parameters, should contain:
                query (str): Simple factual question (Required, min length 1)
                max_results (int, optional): Max results to check (default 1, range 1-10)

        Returns:
            DictParams: Dictionary with success, answer, source.

        Example:
            >>> workflow = GoogleLookupWorkflow()
            >>> result = workflow._do_execute(query="When was Python created?")
            >>> print(result["answer"])
        """
        # Use direct method composition - no wrapper workflow needed!
        workflow = SearchWorkflow() | _extractor.extract_answer_from_search
        return workflow.execute(**kwargs)


class FactFindingWorkflow(BaseWorkflow):
    """
    Quick factual answers from authoritative sources.

    USE FOR: Simple facts, definitions, specific data points
    EXAMPLES: "What is the capital of France?", "When was Python created?"
    AVOID: Complex topics, analysis, multiple sources needed
    STEPS: Search → Fetch → Extract
    """

    @validate_input(
        query={"required": True, "type": str, "min_length": 1},
        max_results={"type": int, "min_value": 1, "max_value": 10, "default": 5},
    )
    @validate_output(
        success={"required": False, "type": bool},
        formatted_text={"required": False, "type": str},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Quick factual answers from authoritative sources.

        Args:
            **kwargs: Input parameters, should contain:
                query (str): Factual question (Required, min length 1)
                max_results (int, optional): Max search results (default 5, range 1-10)

        Returns:
            DictParams: Dictionary with formatted answer and metadata.
        """

        # Use CallableWorkflow with args_transform for clean parameter mapping!
        from dana.core.workflow.callable_workflow import CallableWorkflow

        workflow = (
            SearchWorkflow()
            | CallableWorkflow(_fetcher.fetch_and_extract_single, "url=result.results.0.url|url, purpose=query -> fetch_result")
            | CallableWorkflow(_extractor.extract_fact, "content=fetch_result.content_text, query=query")
            | CallableWorkflow(_formatter.format_with_metadata, "content=result.fact, metadata=fetch_result.metadata")
        )
        return workflow.execute(**kwargs)


class ResearchSynthesisWorkflow(BaseWorkflow):
    """
    Multi-source research and synthesis for complex topics.

    USE FOR: Complex topics, comparisons, comprehensive analysis
    EXAMPLES: "Compare renewable energy policies", "Latest AI developments"
    AVOID: Simple facts, single documents, structured data
    STEPS: Search → Rank → Select URLs → Fetch → Synthesize
    """

    @validate_input(
        query={"required": True, "type": str, "min_length": 1},
        max_sources={"type": int, "min_value": 2, "max_value": 20, "default": 5},
        synthesis_type={"type": str, "enum": ["themes", "timeline"], "default": "themes"},
    )
    @validate_output(success={"required": True, "type": bool})
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Multi-source research and synthesis.

        Args:
            query (str): Research query (Required, min length 1)
            max_sources (int): Max sources to analyze (default 5, range 2-20)
            synthesis_type (str): themes|timeline (default "themes")

        Returns:
            Dict with synthesis, themes, sources, confidence
        """

        # Pre-processing: Calculate search multiplier
        def adjust_max_results(params):
            params["max_results"] = params.get("max_sources", 5) * 2

        # Compose workflows using direct methods and callables
        workflow = (
            SearchWorkflow(pre_callable=adjust_max_results)
            | _searcher.rank_by_relevance
            | _select_top_urls
            | _fetcher.fetch_and_extract
            | _synthesize
        )

        return workflow.execute(**kwargs)


class StructuredDataNavigationWorkflow(BaseWorkflow):
    """
    Extract structured data (tables, lists, statistics) from multiple pages.

    USE FOR: Tables, lists, statistics, datasets from multiple pages
    EXAMPLES: "Get company financial data", "Extract population by country"
    AVOID: Simple facts, analysis, single documents, unstructured content
    STEPS: Navigate → Extract
    """

    @validate_input(
        query={"type": str},
        url={"type": str},
        max_pages={"type": int, "min_value": 1, "max_value": 100, "default": 10},
        extract_tables={"type": bool, "default": True},
        extract_lists={"type": bool, "default": True},
        rate_limit_sec={"type": (int, float), "min_value": 0.1, "max_value": 10.0, "default": 1.0},
    )
    @validate_output(
        success={"required": True, "type": bool},
        tables={"required": True, "type": list},
        lists={"required": True, "type": list},
        statistics={"required": True, "type": dict},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Extract structured data from multiple pages.

        Args:
            query (str): Search query (optional, but either query or url required)
            url (str): Starting URL (optional, but either query or url required)
            max_pages (int): Max pages to navigate (default 10, range 1-100)
            extract_tables (bool): Extract tables (default True)
            extract_lists (bool): Extract lists (default True)
            rate_limit_sec (float): Rate limit in seconds (default 1.0, range 0.1-10.0)

        Returns:
            Dict with tables, lists, statistics, sources
        """
        # Custom validation: at least one of query or url must be provided
        query = kwargs.get("query")
        url = kwargs.get("url")

        if not query and not url:
            return {
                "success": False,
                "error": "validation_error",
                "message": "Either 'query' or 'url' parameter must be provided",
                "field": "query/url",
                "tables": [],
                "lists": [],
                "statistics": {},
            }

        return _extractor.navigate_and_extract_structured(
            start_url=url,
            query=query,
            max_pages=kwargs["max_pages"],
            extract_tables=kwargs["extract_tables"],
            extract_lists=kwargs["extract_lists"],
            rate_limit_sec=kwargs["rate_limit_sec"],
        )
