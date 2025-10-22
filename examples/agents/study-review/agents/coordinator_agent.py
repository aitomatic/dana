"""
CoordinatorAgent - Orchestrates the study session.

This agent directly manages the conversational flow, loads materials at the beginning,
and orchestrates quiz generation and evaluation until all sections are covered.
"""

import os
import sys

from dana.apps.dana.thought_logger import ThoughtLogger

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from agents.quiz_master_agent import QuizMasterAgent
from resources.file_search_resource import FileSearchResource


class CoordinatorAgent(STARAgent):
    """
    Agent that orchestrates the complete study session.

    This agent directly manages the conversational flow, loads materials at the beginning,
    and orchestrates quiz generation and evaluation until all sections are covered.
    """

    def __init__(self, agent_id: str | None = None, llm_provider: str = "openai", **kwargs):
        """
        Initialize the CoordinatorAgent.

        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(agent_type="study-coordinator", agent_id=agent_id or "study-coordinator", llm_provider=llm_provider, **kwargs)

        # Initialize file search resource for loading materials
        self.file_search_resource = FileSearchResource(resource_id="file-search")
        self.with_resources(self.file_search_resource)

        # Initialize specialist agents
        self.quiz_master = QuizMasterAgent(agent_id="quiz-master", llm_provider=llm_provider)
        self.with_agents(self.quiz_master)

        # Create thought logger
        self.thought_logger = ThoughtLogger(verbose=True, show_tool_calls=True)
        self.with_notifiable(self.thought_logger)
