"""
StructuredDataNavigationWorkflow - Multi-page navigation with structured data extraction.

Use Case (Complex): Multi-page structured data extraction
- Search for data source
- Navigate pagination
- Extract tables/lists from each page
- Aggregate structured data
- Format as comprehensive dataset
"""

import logging

from adana.common.observable import observable
from adana.common.protocols import DictParams
from adana.common.protocols.war import tool_use
from adana.core.workflow.base_workflow import BaseWorkflow, WorkflowStep
from adana.core.workflow.workflow_executor import WorkflowExecutor
from .resources import (
    _resources_for_workflows,
    ExtractResource,
    FormatResource,
)


logger = logging.getLogger(__name__)


class StructuredDataNavigationWorkflow(BaseWorkflow):
    """
    Extract structured data (tables, lists, statistics) from multiple pages.

    USE FOR: Tables, lists, statistics, datasets from multiple pages
    EXAMPLES: "Get company financial data", "Extract population by country"
    AVOID: Simple facts, analysis, single documents, unstructured content
    STEPS: Navigate → Extract
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.workflow_id = "structured-data-navigation-123"

    @observable
    @tool_use
    def execute(self, **kwargs) -> DictParams:
        """
        Extract structured data from multiple pages.

        Args:
            query (str): Search query (optional)
            url (str): Starting URL (optional)
            max_pages (int): Max pages to navigate (default 10)

        Returns:
            Dict with tables, lists, statistics, sources
        """
        query = kwargs.get("query")
        start_url = kwargs.get("url")

        if not query and not start_url:
            return {"success": False, "error": "missing_input", "message": "Either query or url parameter is required"}

        max_pages = kwargs.get("max_pages", 10)
        extract_tables = kwargs.get("extract_tables", True)
        extract_lists = kwargs.get("extract_lists", True)
        rate_limit_sec = kwargs.get("rate_limit_sec", 1.0)

        # Get resources for lambda usage
        extract: ExtractResource = _resources_for_workflows.get("extract")
        format: FormatResource = _resources_for_workflows.get("format")

        # Define predetermined steps using WorkflowStep dataclass
        steps = [
            # Step 1: Navigate and extract structured data
            WorkflowStep(
                name="Navigate and Extract Structured Data",
                callable=lambda ctx: extract.navigate_and_extract_structured(
                    start_url=start_url,
                    query=query,
                    max_pages=max_pages,
                    extract_tables=extract_tables,
                    extract_lists=extract_lists,
                    rate_limit_sec=rate_limit_sec,
                ),
                store_as="structured_data",
                required=True,
                validate={"not_empty": True, "has_keys": ["tables", "lists", "statistics"]},
            ),
            # Step 2: Format output with sections - COMMENTED OUT: Agent will handle formatting
            # WorkflowStep(
            #     name="Format Output",
            #     callable=lambda ctx: format.format_summary_with_sections(
            #         sections=[
            #             {
            #                 "heading": "Summary",
            #                 "content": f"Extracted {ctx['structured_data']['statistics'].get('total_data_points', 0)} data points from {ctx['structured_data']['statistics'].get('pages_processed', 0)} pages",
            #                 "level": 2,
            #             },
            #             {
            #                 "heading": "Tables",
            #                 "content": "\n".join(
            #                     [
            #                         f"Table {i + 1}: {table.get('title', 'Untitled')}"
            #                         for i, table in enumerate(ctx["structured_data"]["tables"][:10])
            #                     ]
            #                 ),
            #                 "level": 2,
            #             },
            #             {
            #                 "heading": "Lists",
            #                 "content": "\n".join(
            #                     [
            #                         f"List {i + 1}: {list_item.get('title', 'Untitled')}"
            #                         for i, list_item in enumerate(ctx["structured_data"]["lists"][:10])
            #                     ]
            #                 ),
            #                 "level": 2,
            #             },
            #         ],
            #         title=f"Structured Data: {query or start_url}",
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
            logger.info(f"Structured data navigation completed: {result.get('success')}")
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
