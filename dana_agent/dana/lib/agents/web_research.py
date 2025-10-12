"""
WebResearchAgent - Prompt-driven agent for web research and information synthesis.

This agent is configured entirely through its system prompt and uses resources/workflows
to perform web research tasks.
"""

from dana.core.agent.star_agent import STARAgent
from dana.lib.resources import (
    SearchResource,
    WorkflowSelectorResource,
)
from dana.lib.workflows.web_research import FactFindingWorkflow, GoogleLookupWorkflow


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

        self.with_workflows(
            GoogleLookupWorkflow(workflow_id="google-lookup"),
            FactFindingWorkflow(workflow_id="fact-finding"),
        ).with_resources(
            SearchResource(resource_id="web-search"),
            WorkflowSelectorResource(resource_id="workflow-selector"),
        )
