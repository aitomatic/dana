"""
Dana Agent - Main conversational coordinator.

Dana is a conversational agent that manages and orchestrates other agents,
resources, and workflows through natural language interaction.
"""

from adana.apps.dana.thought_logger import ThoughtLogger
from adana.core.agent.star_agent import STARAgent
from adana.lib.agents import WebResearchAgent
from adana.lib.resources import _google_searcher
from adana.lib.workflows import google_lookup_workflow


class DanaAgent(STARAgent):
    def __init__(self, thought_logger: ThoughtLogger, **kwargs):
        """Initialize Dana agent."""
        super().__init__(agent_id="dana-agent", agent_type="dana-agent", **kwargs)

        self.with_agents(
            WebResearchAgent(),
        ).with_workflows(
            google_lookup_workflow,
        ).with_resources(
            _google_searcher,
        ).with_notifiable(
            thought_logger,
        )
