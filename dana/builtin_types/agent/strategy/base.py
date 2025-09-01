"""
Base Strategy Interface

This module defines the base interface for all agent strategies.
"""

from abc import ABC, abstractmethod

from dana.builtin_types.agent.context import ProblemContext
from dana.builtin_types.workflow.workflow_system import WorkflowInstance


class BaseStrategy(ABC):
    """Base interface for all solving strategies."""

    @abstractmethod
    def can_handle(self, problem: str, context: ProblemContext) -> bool:
        """Determine if this strategy can handle the problem."""
        pass

    @abstractmethod
    def create_workflow(self, problem: str, context: ProblemContext, agent_instance=None, sandbox_context=None) -> WorkflowInstance:
        """Create a workflow instance for the problem."""
        pass
