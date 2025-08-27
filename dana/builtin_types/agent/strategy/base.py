"""
Base Strategy Interface

This module defines the base interface for all agent strategies.
"""

from abc import ABC, abstractmethod
from typing import Any

from dana.builtin_types.agent.agent_instance import AgentInstance
from dana.core.lang.sandbox_context import SandboxContext

from .plan import StrategyPlan


class BaseStrategy(ABC):
    """Base interface for all solving strategies."""

    @abstractmethod
    def can_handle(self, problem: str, context: dict[str, Any] | None = None) -> float:
        """Return confidence score (0.0-1.0) for handling this problem."""
        pass

    @abstractmethod
    def create_plan(
        self,
        agent_instance: AgentInstance,
        problem: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: dict[str, Any] | None = None,
    ) -> StrategyPlan:
        """Create a plan for this strategy."""
        pass

    @abstractmethod
    def execute_plan(
        self,
        agent_instance: AgentInstance,
        plan: StrategyPlan,
        problem: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a plan created by this strategy."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy identifier."""
        pass
