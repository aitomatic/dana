"""
Dana Agent - Main conversational coordinator.

Dana is a conversational agent that manages and orchestrates other agents,
resources, and workflows through natural language interaction.
"""

from dana_agent.apps.dana.thought_logger import ThoughtLogger
from dana_agent.core.agent.star_agent import STARAgent
from dana_agent.lib.agents import WebResearchAgent
from dana_agent.lib.resources import _google_searcher
from dana_agent.lib.workflows import google_lookup_workflow


class DanaAgent(STARAgent):
    def __init__(self, thought_logger: ThoughtLogger, **kwargs):
        """Initialize Dana agent."""
        super().__init__(agent_id="dana_agent", agent_type="dana_agent", **kwargs)

        self.with_agents(
            WebResearchAgent(),
        ).with_workflows(
            google_lookup_workflow,
        ).with_resources(
            _google_searcher,
        ).with_notifiable(
            thought_logger,
        )
