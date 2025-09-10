"""
Base Strategy Interface

This module defines the base interface for all agent strategies.
"""

from abc import ABC, abstractmethod
from typing import Any

from dana.core.agent.context import ProblemContext
from dana.core.workflow.workflow_system import WorkflowInstance


class BaseStrategy(ABC):
    """Base interface for all solving strategies."""

    # Registry of all available strategies - these are templates
    # Actual instances will be created with LLM clients from the agent
    _STRATEGY_TEMPLATES = {}

    @classmethod
    def _get_strategy_templates(cls):
        """Get the strategy templates registry, initializing it if needed."""
        if not cls._STRATEGY_TEMPLATES:
            # Import here to avoid circular imports
            from .iterative.iterative_strategy import IterativeStrategy
            from .recursive.recursive_strategy import RecursiveStrategy

            cls._STRATEGY_TEMPLATES = {
                "recursive": RecursiveStrategy,
                "iterative": IterativeStrategy,
            }
        return cls._STRATEGY_TEMPLATES

    @classmethod
    def get_strategy_by_name(cls, name: str) -> "BaseStrategy | None":
        """Get strategy by name."""
        templates = cls._get_strategy_templates()
        if name in templates:
            return templates[name]()
        return None

    @classmethod
    def select_best_strategy(cls, problem: str, context: Any = None, agent_instance=None) -> "BaseStrategy":
        """Select the best strategy for the given problem."""
        # Create default context if none provided
        if context is None:
            context = ProblemContext(problem_statement=problem, objective=f"Solve: {problem}", original_problem=problem, depth=0)

        best_strategy = None
        templates = cls._get_strategy_templates()

        for _, strategy_class in templates.items():
            strategy = strategy_class()
            if strategy.can_handle(problem, context):
                best_strategy = strategy
                break

        # Fallback to recursive if no strategy is confident
        if best_strategy is None:
            from .recursive.recursive_strategy import RecursiveStrategy

            best_strategy = RecursiveStrategy()

        return best_strategy

    @abstractmethod
    def can_handle(self, problem: str, context: ProblemContext) -> bool:
        """Determine if this strategy can handle the problem."""
        pass

    @abstractmethod
    def create_workflow(self, problem: str, context: ProblemContext, agent_instance=None, sandbox_context=None) -> WorkflowInstance:
        """Create a workflow instance for the problem."""
        pass
