"""
Dana Agent - Main conversational coordinator.

Dana is a conversational agent that manages and orchestrates other agents,
resources, and workflows through natural language interaction.
"""

from dana.apps.dana.thought_logger import ThoughtLogger
from dana.core.agent.star_agent import STARAgent


class DanaAgent(STARAgent):
    def __init__(self, thought_logger: ThoughtLogger, **kwargs):
        """Initialize Dana agent."""
        super().__init__(agent_id="dana_agent", agent_type="dana_agent", **kwargs)

        # STARAgent provides by default:
        # - assistant__query (AssistantAgent with web search + code execution)
        # - web_search__search, web_search__fetch_url (SimpleWebSearch)
        # - claude_skills__execute (ClaudeCodeSkills)

        self.with_notifiable(thought_logger)
