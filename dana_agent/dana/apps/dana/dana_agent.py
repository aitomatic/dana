"""
Dana Agent - Main conversational coordinator.

Dana is a conversational agent that manages and orchestrates other agents,
resources, and workflows through natural language interaction.
"""

from dana.apps.dana.thought_logger import ThoughtLogger
from dana.core.agent.star_agent import STARAgent
from dana.lib.agents import WebResearchAgent
from dana.lib.resources import SearchResource
from dana.lib.workflows import GoogleLookupWorkflow


class DanaAgent(STARAgent):
    def __init__(self, thought_logger: ThoughtLogger, **kwargs):
        """Initialize Dana agent."""
        super().__init__(agent_id="dana_agent", agent_type="dana_agent", **kwargs)

        self.with_agents(
            WebResearchAgent(),
        ).with_workflows(
            GoogleLookupWorkflow(),
        ).with_resources(
            SearchResource(),
        ).with_notifiable(
            thought_logger,
        )
