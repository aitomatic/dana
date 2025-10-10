"""
GoogleLookupWorkflow — **Primary tool for fast factual questions.**

Use this workflow FIRST for:
- Simple, real-time, or single-source facts (e.g., weather, time, dates, names, definitions)
- Quick one-sentence answers requiring no analysis or synthesis
- Short-term data queries (exchange rates, forecasts, current events)

Examples:
- “What is the weather forecast today in Palo Alto?”
- “When was Python first released?”
- “What is the current USD to EUR exchange rate?”

💡 Tip: If the answer can fit in one sentence, use this workflow.
"""

import logging

from adana.common.observable import observable
from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.workflow.base_workflow import BaseWorkflow, WorkflowStep
from adana.core.workflow.workflow_executor import WorkflowExecutor
from adana.lib.agents.web_research.workflows.resources.search import SearchResource


logger = logging.getLogger(__name__)


class GoogleLookupWorkflow(BaseWorkflow):
    """
    Quick Google search for simple factual answers.

    USE FOR: Simple facts, definitions, quick lookups
    EXAMPLES: "What is the capital of France?", "When was Python created?"
    AVOID: Complex analysis, multiple sources, deep research
    STEPS: Search → Extract
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.workflow_id = "google-lookup-123"

    @observable
    @tool_use
    def execute(self, **kwargs) -> DictParams:
        """
        Quick Google search for simple facts.

        Args:
            query (str): Simple factual question
            max_results (int): Max results to check (default 1)

        Returns:
            Dict with answer, source, success status
        """
        query = kwargs.get("query")
        if not query:
            return {"success": False, "error": "Query parameter is required", "context": {}}

        max_results = kwargs.get("max_results", 1)

        # Get resources for lambda usage
        search: SearchResource = SearchResource()

        # Define workflow steps
        steps = [
            WorkflowStep(
                name="Google Search",
                callable=lambda ctx: search.search_web(query=query, max_results=max_results),
                store_as="search_result",
                required=True,
                validate={"not_empty": True, "has_keys": ["results"]},
            ),
            WorkflowStep(
                name="Extract Answer",
                callable=lambda ctx: self._extract_answer_from_search(search_results=ctx["search_result"]["results"], query=query),
                store_as="extracted_answer",
                required=True,
                validate={"not_empty": True, "has_keys": ["answer", "source"]},
            ),
            # WorkflowStep(
            #    name="Format Response",
            #    callable=lambda ctx: self._format_google_response(
            #        answer=ctx["extracted_answer"]["answer"], source=ctx["extracted_answer"]["source"], query=query
            #    ),
            #    store_as="formatted_response",
            #    required=True,
            #    validate={"not_empty": True},
            # ),
        ]

        # Execute workflow
        executor = WorkflowExecutor(
            name=self.workflow_id,
            steps=steps,
            max_retries=2,
            retry_delay=0.5,
            exponential_backoff=True,
        )
        result = executor.execute()

        if result.get("success", False):
            logger.info(f"Google lookup completed successfully for query: {query}")
            return {
                "success": True,
                "answer": result.get("extracted_answer", {}).get("answer"),
                "source": result.get("extracted_answer", {}).get("source"),
                "formatted_response": result.get("formatted_response"),
                "context": result,
            }
        else:
            logger.error(f"Google lookup failed for query: {query}")
            return {"success": False, "error": result.get("error", "Unknown error"), "context": result}

    def _extract_answer_from_search(self, search_results: list, query: str) -> DictParams:
        """
        Extract answer from Google search results.

        Args:
            search_results: List of search results
            query: The original query

        Returns:
            Dictionary with answer and source
        """
        if not search_results:
            return {"answer": "No results found", "source": "Google Search"}

        # Get the first result
        first_result = search_results[0]

        # Extract snippet or title as answer
        answer = first_result.get("snippet", first_result.get("title", "No answer available"))

        return {"answer": answer, "source": first_result.get("url", "Unknown source")}

    def _format_google_response(self, answer: str, source: str, query: str) -> str:
        """
        Format the Google lookup response.

        Args:
            answer: The extracted answer
            source: The source URL
            query: The original query

        Returns:
            Formatted response string
        """
        return f"""**Answer:** {answer}

**Source:** {source}

*Found via Google search for: "{query}"*"""
