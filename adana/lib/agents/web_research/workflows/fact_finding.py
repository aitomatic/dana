"""
FactFindingWorkflow - Quick factual answers from authoritative sources.

Use Case (Simple): Quick factual queries
- Search for query
- Fetch top authoritative result
- Extract key fact
- Return concise answer with source

Execution Pattern: SA-loop (95% deterministic, $0 LLM cost)
- SEE: Simple heuristic checks (no LLM reasoning)
- ACT: Execute predetermined steps with retry logic
- LOOP: Continue until fact found or error
"""

import logging
from typing import TYPE_CHECKING
from adana.common.observable import observable
from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.workflow.base_workflow import BaseWorkflow, WorkflowStep
from adana.core.workflow.workflow_executor import WorkflowExecutor
from .resources import (
    _resources_for_workflows,
    SearchResource,
    FetchResource,
    FormatResource,
)

logger = logging.getLogger(__name__)


class FactFindingWorkflow(BaseWorkflow):
    """
    Quick factual answers from authoritative sources.

    USE FOR: Simple facts, definitions, specific data points
    EXAMPLES: "What is the capital of France?", "When was Python created?"
    AVOID: Complex topics, analysis, multiple sources needed
    STEPS: Search → Fetch → Extract
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.workflow_id = "fact-finding-123"

    @observable
    @tool_use
    def execute(self, **kwargs) -> DictParams:
        """
        Quick factual answers from web search.

        Args:
            query (str): Factual question to answer
            max_sources (int): Max sources to check (default 3)

        Returns:
            Dict with fact, confidence, source metadata
        """
        query = kwargs.get("query")
        if not query:
            return {"success": False, "error": "Query parameter is required", "context": {}}

        max_sources = kwargs.get("max_sources", 3)

        # Get resources for lambda usage
        search: SearchResource = _resources_for_workflows.get("search")
        fetch: FetchResource = _resources_for_workflows.get("fetch")
        format: FormatResource = _resources_for_workflows.get("format")

        # Define workflow steps
        steps = [
            WorkflowStep(
                name="Search for Fact",
                callable=lambda ctx: search.search_web(query=query, max_results=max_sources),
                store_as="search_result",
                required=True,
                validate={"not_empty": True, "has_keys": ["results"]},
            ),
            WorkflowStep(
                name="Fetch Best Result",
                callable=lambda ctx: fetch.fetch_and_extract_single(
                    url=ctx["search_result"]["results"][0]["url"], purpose=f"Find fact: {query}"
                ),
                store_as="fetch_result",
                required=True,
                validate={"not_empty": True, "has_keys": ["content_text", "metadata"]},
            ),
            WorkflowStep(
                name="Extract Fact",
                callable=lambda ctx: self._extract_fact_from_content(content=ctx["fetch_result"]["content_text"], query=query),
                store_as="extracted_fact",
                required=True,
                validate={"not_empty": True, "has_keys": ["fact", "confidence"]},
            ),
            # WorkflowStep(
            #    name="Format Answer",
            #    callable=lambda ctx: format.format_with_metadata(
            #        content=ctx["extracted_fact"]["fact"],
            #        metadata={
            #            "source": ctx["fetch_result"]["metadata"].get("url", "Unknown"),
            #            "title": ctx["fetch_result"]["metadata"].get("title", "Unknown"),
            #            "query": query,
            #            "confidence": ctx["extracted_fact"]["confidence"],
            #        },
            #        metadata={
            #            "source": ctx["fetch_result"]["metadata"].get("url", "Unknown"),
            #            "title": ctx["fetch_result"]["metadata"].get("title", "Unknown"),
            #            "query": query,
            #            "confidence": ctx["extracted_fact"]["confidence"],
            #        },
            #        include_timestamp=True,
            #    ),
            #   store_as="formatted_answer",
            #    required=True,
            #    validate={"not_empty": True},
            # ),
        ]

        # Execute workflow
        executor = WorkflowExecutor(
            name=self.workflow_id,
            steps=steps,
            max_retries=3,
            retry_delay=1.0,
            exponential_backoff=True,
        )
        result = executor.execute()

        if result.get("success", False):
            logger.info(f"Fact finding completed successfully for query: {query}")
            return {
                "success": True,
                "fact": result.get("extracted_fact", {}).get("fact"),
                "source": result.get("fetch_result", {}).get("metadata", {}).get("url"),
                "source_title": result.get("fetch_result", {}).get("metadata", {}).get("title"),
                "formatted_text": result.get("formatted_answer"),
                "confidence": result.get("extracted_fact", {}).get("confidence"),
                "context": result,
            }
        else:
            logger.error(f"Fact finding failed for query: {query}")
            return {"success": False, "error": result.get("error", "Unknown error"), "context": result}

    def _extract_fact_from_content(self, content: str, query: str) -> DictParams:
        """
        Extract factual information from content based on query.

        Args:
            content: The content to extract from
            query: The original query

        Returns:
            Dictionary with fact and confidence
        """
        # Simple fact extraction logic
        # In a real implementation, this would use NLP/LLM to extract facts
        lines = content.split("\n")

        # Look for numerical data (exchange rates, prices, etc.)
        for line in lines:
            if any(keyword in query.lower() for keyword in ["rate", "price", "cost", "value", "exchange"]):
                if any(char.isdigit() for char in line):
                    return {"fact": line.strip(), "confidence": 0.8}

        # Fallback: return first meaningful line
        for line in lines:
            if len(line.strip()) > 10 and not line.startswith("#"):
                return {"fact": line.strip(), "confidence": 0.6}

        return {"fact": "No specific fact found", "confidence": 0.3}
