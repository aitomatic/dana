"""
ResearchSynthesisWorkflow - Understanding topics across 3-5 sources.

Use Case (Medium): Multi-source research and synthesis
- Search for query
- Fetch top results
- Extract content from each
- Synthesize across sources
- Generate comprehensive report

Execution Pattern: SA-loop (95% deterministic, $0 LLM cost)
- SEE: Simple heuristic checks (no LLM reasoning)
- ACT: Execute predetermined steps with retry logic
- LOOP: Continue until all steps complete or error
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
    SynthesizeResource,
)

logger = logging.getLogger(__name__)


class ResearchSynthesisWorkflow(BaseWorkflow):
    """
    Multi-source research and synthesis for complex topics.

    USE FOR: Complex topics, comparisons, comprehensive analysis
    EXAMPLES: "Compare renewable energy policies", "Latest AI developments"
    AVOID: Simple facts, single documents, structured data
    STEPS: Search → Rank → Fetch → Synthesize
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.workflow_id = "research-synthesis-123"

    @observable
    @tool_use
    def execute(self, **kwargs) -> DictParams:
        """
        Multi-source research and synthesis.

        Args:
            query (str): Research query
            max_sources (int): Max sources to analyze (default 5)
            synthesis_type (str): themes|timeline (default themes)

        Returns:
            Dict with synthesis, themes, sources, confidence
        """
        query = kwargs.get("query")
        if not query:
            return {"success": False, "error": "missing_query", "message": "Query parameter is required"}

        max_sources = kwargs.get("max_sources", 5)
        require_recent = kwargs.get("require_recent", False)
        synthesis_type = kwargs.get("synthesis_type", "themes")

        # Validate synthesis_type (comparison requires different workflow)
        if synthesis_type not in ["themes", "timeline"]:
            return {
                "success": False,
                "error": "invalid_synthesis_type",
                "message": f"synthesis_type must be 'themes' or 'timeline', got '{synthesis_type}'. "
                "Comparison synthesis requires a different workflow with item1/item2 parameters.",
            }

        # Get resources for lambda usage
        search: SearchResource = _resources_for_workflows.get("search")
        fetch: FetchResource = _resources_for_workflows.get("fetch")
        synthesize: SynthesizeResource = _resources_for_workflows.get("synthesize")

        # Define predetermined steps using WorkflowStep dataclass (type-safe and structured)
        steps = [
            # Step 1: Search (hybrid format with validation)
            WorkflowStep(
                name="Search",
                callable=lambda ctx: (
                    search.search_with_date_filter(query=query, max_results=max_sources * 2, max_age_months=6)
                    if require_recent
                    else search.search_web(query=query, max_results=max_sources * 2)
                ),
                store_as="search_results",
                required=True,
                validate={"not_empty": True},
            ),
            # Step 2: Rank (lambda wrapping resource method)
            WorkflowStep(
                name="Rank",
                callable=lambda ctx: search.rank_by_relevance(query=query, results=ctx["search_results"]["results"], criteria="relevance"),
                store_as="ranked_results",
                required=True,
            ),
            # Step 3: Select top N URLs (extract ranked_results, slice, and get URLs)
            WorkflowStep(
                name="Select Top Sources",
                callable=lambda ctx: [result["url"] for result in ctx["ranked_results"]["ranked_results"][:max_sources]],
                store_as="selected_urls",
                required=True,
                validate={"min_items": 2},  # Minimum 2 sources required
            ),
            # Step 4: Fetch and extract (lambda with abort condition)
            WorkflowStep(
                name="Fetch and Extract",
                callable=lambda ctx: fetch.fetch_and_extract(urls=ctx["selected_urls"]["result"], max_workers=3, deduplicate=True),
                store_as="unique_content",
                required=True,
                validate={"not_empty": True},
            ),
            # Step 5: Synthesize (dynamic method selection with lambda)
            WorkflowStep(
                name="Synthesize",
                callable=lambda ctx: getattr(synthesize, f"synthesize_by_{synthesis_type}")(
                    extractions=ctx["unique_content"]["result"], topic=query
                ),
                store_as="synthesis",
                required=True,
            ),
            # Step 6: Create executive summary (optional lambda)
            # WorkflowStep(
            #    name="Create Executive Summary",
            #    callable=lambda ctx: synthesize.create_executive_summary(
            #        extractions=ctx["unique_content"]["result"], topic=query, max_words=200
            #    ),
            #    store_as="summary",
            #    required=False,  # Optional - can continue without summary
            # ),
            # Step 7: Format report (lambda with fallback for missing summary) - COMMENTED OUT: Agent will handle formatting
            # WorkflowStep(
            #     name="Format Report",
            #     callable=lambda ctx: format.format_summary_with_sections(
            #         sections=[
            #             {
            #                 "heading": "Executive Summary",
            #                 "content": ctx.get("summary", {}).get("summary", "Summary unavailable"),
            #                 "level": 2,
            #             },
            #             {
            #                 "heading": "Key Findings",
            #                 "content": "\n".join(ctx.get("summary", {}).get("key_findings", ["No key findings available"])),
            #                 "level": 2,
            #             },
            #             {
            #                 "heading": "Analysis",
            #                 "content": ctx["synthesis"].get("synthesis", "No analysis available"),
            #                 "level": 2,
            #             },
            #             {
            #                 "heading": "Sources",
            #                 "content": "\n".join(
            #                     [
            #                         f"- [{extraction.get('title', 'Untitled')}]({extraction.get('url', '#')})"
            #                         for extraction in ctx["unique_content"]["result"]
            #                         if extraction.get("success") and extraction.get("url")
            #                     ]
            #                 )
            #                 or "No sources available",
            #                 "level": 2,
            #             },
            #         ],
            #         title=f"Research Synthesis: {query}",
            #     ),
            #     store_as="formatted_report",
            #     required=True,
            # ),
        ]

        # Execute workflow using SA-loop pattern
        executor = WorkflowExecutor(
            name=self.workflow_id,
            steps=steps,
            max_retries=3,
            retry_delay=1.0,
            exponential_backoff=True,
        )

        try:
            result = executor.execute()
            logger.info(f"Research synthesis completed: {result.get('success')}")
            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": "workflow_execution_failed",
                "message": str(e),
                "context": executor.context,
                "execution_log": executor.execution_log,
            }
