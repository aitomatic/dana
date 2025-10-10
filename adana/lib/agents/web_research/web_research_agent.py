"""
WebResearchAgent - Prompt-driven agent for web research and information synthesis.

This agent is configured entirely through its system prompt and uses resources/workflows
to perform web research tasks.
"""

from adana.core.agent.star_agent import STARAgent
from adana.lib.workflows import google_lookup_workflow
from adana.lib.resources import (
    _google_searcher,
    WorkflowSelectorResource,
)
from .workflows import (
    FactFindingWorkflow,
    ResearchSynthesisWorkflow,
    SingleSourceDeepDiveWorkflow,
    StructuredDataNavigationWorkflow,
)


class WebResearchAgent(STARAgent):
    """
    Prompt-driven agent for web research and information synthesis.
    """

    def __init__(self, agent_id: str | None = None, **kwargs):
        """
        Initialize WebResearchAgent.

        Args:
            agent_id: Optional agent identifier
            **kwargs: Additional arguments passed to STARAgent
        """
        # Initialize STARAgent with web-research type
        super().__init__(agent_type="web-researcher", agent_id=agent_id or "web-researcher", **kwargs)

        # Initialize resources for agent
        resources = {
            # "todo": ToDoResource(resource_id="todo-123"),
            "google_search": _google_searcher,
            "workflow_selector": WorkflowSelectorResource(resource_id="workflow-selector"),
        }

        # Initialize workflows for agent
        workflows = {
            "google_lookup": google_lookup_workflow,
            "fact_finding": FactFindingWorkflow(workflow_id="fact-finding"),
            "single_source": SingleSourceDeepDiveWorkflow(workflow_id="single-source-deep-dive"),
            "research": ResearchSynthesisWorkflow(workflow_id="research-synthesis"),
            "structured_data": StructuredDataNavigationWorkflow(workflow_id="structured-data-navigation"),
        }

        self.with_workflows(*workflows.values()).with_resources(*resources.values())
