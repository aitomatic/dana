from dana_agent.common.protocols import DictParams
from dana_agent.core.workflow.base_workflow import BaseWorkflow
from dana_agent.core.workflow.validation import validate_input, validate_output
from dana_agent.lib.agents.web_research.resources.extract import ExtractResource
from dana_agent.lib.agents.web_research.resources.fetch import FetchResource
from dana_agent.lib.agents.web_research.resources.format import FormatResource
from dana_agent.lib.agents.web_research.resources.search import SearchResource
from dana_agent.lib.agents.web_research.resources.synthesize import SynthesizeResource


_search_resource = SearchResource()
_fetch_resource = FetchResource()
_extract_resource = ExtractResource()
_format_resource = FormatResource()
_synthesize_resource = SynthesizeResource()


# ============================================================================
# Internal Helper Workflows (not exported)
# ============================================================================


class _RankResultsWorkflow(BaseWorkflow):
    """Internal workflow to rank search results by relevance."""

    def _do_execute(self, **kwargs) -> DictParams:
        """
        Rank search results by relevance.

        Args:
            query (str): Search query
            results (list): Search results to rank
            criteria (str): Ranking criteria (default "relevance")

        Returns:
            Dict with ranked_results
        """
        return _search_resource.rank_by_relevance(
            query=kwargs.get("query", ""), results=kwargs.get("results", []), criteria=kwargs.get("criteria", "relevance")
        )


class _FetchMultipleWorkflow(BaseWorkflow):
    """Internal workflow to fetch and extract multiple URLs."""

    def _do_execute(self, **kwargs) -> DictParams:
        """
        Fetch and extract content from multiple URLs.

        Args:
            urls (list): List of URLs to fetch
            max_workers (int): Max parallel workers (default 3)
            deduplicate (bool): Remove duplicate content (default True)

        Returns:
            Dict with extraction results
        """
        return _fetch_resource.fetch_and_extract(
            urls=kwargs.get("urls", []), max_workers=kwargs.get("max_workers", 3), deduplicate=kwargs.get("deduplicate", True)
        )


class _SynthesizeWorkflow(BaseWorkflow):
    """Internal workflow to synthesize content from multiple sources."""

    @validate_input(
        extractions={"required": True, "type": list, "min_length": 1},
        topic={"required": True, "type": str, "min_length": 1},
        synthesis_type={"type": str, "enum": ["themes", "timeline"], "default": "themes"},
    )
    @validate_output(success={"required": True, "type": bool})
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Synthesize content from multiple extractions.

        Args:
            extractions (list): List of content extractions (Required, min 1 item)
            topic (str): Research topic (Required, min length 1)
            synthesis_type (str): Type of synthesis - themes|timeline (default "themes")

        Returns:
            Dict with synthesis results containing success field
        """
        synthesis_type = kwargs["synthesis_type"]
        synthesize_method = getattr(_synthesize_resource, f"synthesize_by_{synthesis_type}")
        return synthesize_method(extractions=kwargs["extractions"], topic=kwargs["topic"])


class _SelectTopUrlsWorkflow(BaseWorkflow):
    """Internal workflow to extract top N URLs from ranked results."""

    def _do_execute(self, **kwargs) -> DictParams:
        """
        Extract top N URLs from ranked search results.

        Args:
            ranked_results (list): Ranked search results
            max_sources (int): Maximum number of URLs to extract (default 5)

        Returns:
            Dict with urls list
        """
        ranked_results = kwargs.get("ranked_results", [])
        max_sources = kwargs.get("max_sources", 5)

        # Extract URLs from top N results
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
        return _search_resource.search_web(query=kwargs["query"], max_results=kwargs["max_results"])


class FetchResultWorkflow(BaseWorkflow):
    @validate_input(
        url={"required": True, "type": str, "min_length": 1},
        purpose={"type": str, "default": "general analysis"},
    )
    @validate_output(
        success={"required": True, "type": bool},
        content_text={"required": True, "type": str},
        metadata={"required": True, "type": dict},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Fetch and extract content from a single URL.

        Args:
            **kwargs: Input parameters, should contain:
                url (str): The URL to fetch. (Required, min length 1)
                purpose (str, optional): The purpose of the fetch (e.g., "general analysis"). Defaults to "general analysis".

        Returns:
            DictParams: A dictionary with the fetch and extraction results containing:
                success (bool): Whether the fetch and extraction succeeded.
                url (str): Final URL (after redirects).
                title (str): Page title.
                content_text (str): Extracted text content.
                content_markdown (str): Extracted markdown content.
                word_count (int): Number of words in content.
                reading_time_minutes (int): Estimated reading time in minutes.
                metadata (dict): Page metadata (author, date, etc.).
                quality (dict): Quality assessment with quality_score and is_sufficient.
                sufficient (bool): Whether content is sufficient for the purpose.
                key_points (list[str]): List of key points extracted from content.
                summary (str): Brief summary of the content.
                code_blocks (list[dict]): List of code blocks (if any), each with:
                    language (str | None): Programming language.
                    code (str): Code content.
                    index (int): Block index.
                error (str | None): Error message if success is False.

        Example:
            >>> workflow = FetchResultWorkflow()
            >>> result = workflow._do_execute(url="https://example.com", purpose="research")
            >>> print(result["title"])
            'Example Page'
        """
        return _fetch_resource.fetch_and_extract_single(url=kwargs["url"], purpose=kwargs["purpose"])


class ExtractAnswerWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Extract answer from search results (snippet/title).

        Args:
            **kwargs: Input parameters, should contain:
                results (list): List of search results from SearchWorkflow.

        Returns:
            DictParams: A dictionary with the extraction results containing:
                success (bool): Whether extraction was successful.
                answer (str): The extracted answer (snippet or title).
                source (str): The source URL.

        Example:
            >>> workflow = ExtractAnswerWorkflow()
            >>> result = workflow._do_execute(results=[{"snippet": "Python was created in 1991", "url": "..."}])
            >>> print(result["answer"])
            'Python was created in 1991'
        """
        return _extract_resource.extract_answer_from_search(results=kwargs.get("results", []))


class GoogleLookupWorkflow(BaseWorkflow):
    """
    Quick Google search for simple factual answers.

    USE FOR: Simple facts, definitions, quick lookups
    EXAMPLES: "What is the capital of France?", "When was Python created?"
    AVOID: Complex analysis, multiple sources, deep research
    STEPS: Search → Extract
    """

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
        workflow = SearchWorkflow() | ExtractAnswerWorkflow("results=result.results")
        return workflow.execute(**kwargs)


class ExtractFactWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Extract factual information from content based on a query.

        Args:
            **kwargs: Input parameters, should contain:
                content (str, optional): The text content to extract facts from.
                query (str, optional): The query to guide fact extraction.

        Returns:
            DictParams: A dictionary with the extraction results containing:
                fact (str): The extracted fact.
                confidence (float): Confidence score (0.0 to 1.0).
                context (str): Surrounding context for the fact.

        Example:
            >>> workflow = ExtractFactWorkflow()
            >>> result = workflow._do_execute(
            ...     content="Python was created by Guido van Rossum in 1991.",
            ...     query="When was Python created?"
            ... )
            >>> print(result["fact"])
            'Python was created by Guido van Rossum in 1991.'
        """
        return _extract_resource.extract_fact(content=kwargs.get("content"), query=kwargs.get("query"))


class FormatWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Format content with metadata header.

        Args:
            **kwargs: Input parameters, should contain:
                content (str, optional): Main content to format. Defaults to "".
                metadata (dict, optional): Metadata to include in header. Defaults to {}.
                    Supported metadata fields:
                        title (str): Document title.
                        topic (str): Topic or subject.
                        sources_count (int): Number of sources.
                        workflow (str): Workflow name.
                        synthesis_type (str): Type of synthesis.
                        timestamp (str): Generation timestamp.

        Returns:
            DictParams: A dictionary with the formatted text containing:
                formatted_text (str): The formatted text.
                    - Title (if provided in metadata)
                    - Metadata block with key-value pairs
                    - Main content

        Example:
            >>> workflow = FormatWorkflow()
            >>> result = workflow._do_execute(
            ...     content="Main content here.",
            ...     metadata={"title": "Report", "topic": "Research", "sources_count": 3}
            ... )
            >>> print(result["formatted_text"])
            # Report
            <BLANKLINE>
            ---
            **Topic:** Research
            **Sources:** 3
            **Generated:** 2024-01-01 12:00:00
            ---
            <BLANKLINE>
            Main content here.
        """
        return {
            "formatted_text": _format_resource.format_with_metadata(content=kwargs.get("content", ""), metadata=kwargs.get("metadata", {}))
        }


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
        workflow = (
            SearchWorkflow()
            | FetchResultWorkflow("url=result.results.0.url|url, purpose=query -> fetch_result")
            | ExtractFactWorkflow("content=fetch_result.content_text")
            | FormatWorkflow("content=result.fact, metadata=fetch_result.metadata")
        )
        return workflow.execute(**kwargs)


class SingleSourceDeepDiveWorkflow(BaseWorkflow):
    """
    Thorough analysis of a single document or webpage.

    USE FOR: Specific documents, deep analysis, technical content
    EXAMPLES: "Analyze this research paper", "Summarize this report"
    AVOID: Simple facts, multiple sources, structured data
    STEPS: Fetch → Extract
    """

    @validate_input(
        url={"required": True, "type": str, "min_length": 1},
        purpose={"type": str, "default": "general analysis"},
        extract_code={"type": bool, "default": False},
        max_key_points={"type": int, "min_value": 1, "max_value": 20, "default": 5},
    )
    @validate_output(
        success={"required": True, "type": bool},
        content_text={"required": True, "type": str},
        metadata={"required": True, "type": dict},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Deep analysis of a single document.

        Args:
            url (str): URL to analyze (Required)
            purpose (str): Analysis purpose (default "general analysis")
            extract_code (bool): Extract code blocks (default False)
            max_key_points (int): Maximum key points to extract (default 5, range 1-20)

        Returns:
            Dict with content, summary, key_points, metadata
        """
        return _fetch_resource.fetch_and_extract_single(
            url=kwargs["url"],
            purpose=kwargs["purpose"],
            extract_code=kwargs["extract_code"],
            max_key_points=kwargs["max_key_points"],
        )


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

        # Compose workflows declaratively with pre_callable for dynamic calculation
        workflow = (
            SearchWorkflow(pre_callable=adjust_max_results)
            | _RankResultsWorkflow("results=result.results")
            | _SelectTopUrlsWorkflow("ranked_results=result.ranked_results, max_sources=max_sources")
            | _FetchMultipleWorkflow("urls=result.urls")
            | _SynthesizeWorkflow("extractions=result.result, topic=query")
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

        return _extract_resource.navigate_and_extract_structured(
            start_url=url,
            query=query,
            max_pages=kwargs["max_pages"],
            extract_tables=kwargs["extract_tables"],
            extract_lists=kwargs["extract_lists"],
            rate_limit_sec=kwargs["rate_limit_sec"],
        )
