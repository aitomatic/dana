"""
SingleSourceDeepDiveWorkflow - Thoroughly analyze one specific document.

Use Case (Simple): Single URL fetch and summarize
- Fetch URL
- Extract content
- Assess quality
- Generate summary with key points
"""

import logging

from adana.common.observable import observable
from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.workflow.base_workflow import BaseWorkflow, WorkflowStep
from adana.core.workflow.workflow_executor import WorkflowExecutor
from .resources import (
    _resources_for_workflows,
    FetchResource,
    FormatResource,
)

logger = logging.getLogger(__name__)


class SingleSourceDeepDiveWorkflow(BaseWorkflow):
    """
    Thorough analysis of a single document or webpage.

    USE FOR: Specific documents, deep analysis, technical content
    EXAMPLES: "Analyze this research paper", "Summarize this report"
    AVOID: Simple facts, multiple sources, structured data
    STEPS: Fetch → Extract
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.workflow_id = "single-source-deep-dive-123"

    @observable
    @tool_use
    def execute(self, **kwargs) -> DictParams:
        """
        Deep analysis of a single document.

        Args:
            url (str): URL to analyze
            purpose (str): Analysis purpose (optional)
            extract_code (bool): Extract code blocks (default False)

        Returns:
            Dict with content, summary, key_points, metadata
        """
        url = kwargs.get("url")
        if not url:
            return {"success": False, "error": "missing_url", "message": "URL parameter is required"}

        purpose = kwargs.get("purpose", "general analysis")
        extract_code = kwargs.get("extract_code", False)
        max_key_points = kwargs.get("max_key_points", 5)

        # Get resources for lambda usage
        fetch: FetchResource = _resources_for_workflows.get("fetch")
        format: FormatResource = _resources_for_workflows.get("format")

        # Define predetermined steps using WorkflowStep dataclass
        steps = [
            # Step 1: Fetch and extract single URL
            WorkflowStep(
                name="Fetch and Extract",
                callable=lambda ctx: fetch.fetch_and_extract_single(
                    url=url, purpose=purpose, extract_code=extract_code, max_key_points=max_key_points
                ),
                store_as="analysis_result",
                required=True,
                validate={"not_empty": True, "has_keys": ["content_text", "metadata", "summary"]},
            ),
            # Step 2: Format output with sections - COMMENTED OUT: Agent will handle formatting
            # WorkflowStep(
            #     name="Format Output",
            #     callable=lambda ctx: format.format_summary_with_sections(
            #         sections=[
            #             {
            #                 "heading": "Overview",
            #                 "content": ctx["analysis_result"].get("summary", "No summary available"),
            #                 "level": 2,
            #             },
            #             {
            #                 "heading": "Key Points",
            #                 "content": "\n".join(ctx["analysis_result"].get("key_points", ["No key points available"])),
            #                 "level": 2,
            #             },
            #             {
            #                 "heading": "Code Examples",
            #                 "content": "\n".join(ctx["analysis_result"].get("code_blocks", ["No code examples available"])),
            #                 "level": 2,
            #             },
            #             {
            #                 "heading": "Full Content",
            #                 "content": ctx["analysis_result"].get("content_markdown", "No content available"),
            #                 "level": 2,
            #             },
            #         ],
            #         title=ctx["analysis_result"].get("metadata", {}).get("title", f"Analysis: {url}"),
            #     ),
            #     store_as="formatted_document",
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
            logger.info(f"Single source deep dive completed: {result.get('success')}")
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
