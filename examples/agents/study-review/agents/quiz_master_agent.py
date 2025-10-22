"""
QuizMasterAgent - Generates quizzes and evaluates student answers.

This agent is specialized for quiz generation and answer evaluation using LLM reasoning.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent


class QuizMasterAgent(STARAgent):
    """
    Agent that generates quiz questions and evaluates student answers.

    This agent uses LLM reasoning for quiz generation and answer evaluation.
    """

    def __init__(self, agent_id: str | None = None, llm_provider: str = "openai", model: str = "gpt-4o-mini", **kwargs):
        """
        Initialize the QuizMasterAgent.

        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(agent_type="quiz-master", agent_id=agent_id or "quiz-master-001", llm_provider=llm_provider, model=model, **kwargs)
