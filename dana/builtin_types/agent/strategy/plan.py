"""
Strategy Plan Implementation

This module defines the StrategyPlan dataclass and related functionality.
"""

from dataclasses import dataclass
from typing import Any, Union

from dana.builtin_types.agent.agent_instance import AgentInstance

from .enums import PlanType


@dataclass
class StrategyPlan:
    """Unified plan structure that supports all current return types."""

    # Core plan metadata
    strategy_name: str
    confidence: float
    plan_type: PlanType

    # Plan content (supports all current types)
    content: Union[str, dict, Any]  # Can be string, dict, WorkflowInstance, etc.

    # Additional metadata
    reasoning: str = ""
    complexity: str = "moderate"
    estimated_duration: str = "unknown"
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def execute(self, agent_instance: AgentInstance, problem: str, sandbox_context: Any = None, context: dict | None = None) -> Any:
        """Execute this plan using the provided agent instance."""
        # Avoid circular import by using the global function
        from . import get_strategy_by_name

        strategy = get_strategy_by_name(self.strategy_name)
        if strategy is None:
            raise ValueError(f"Strategy '{self.strategy_name}' not found")
        return strategy.execute_plan(agent_instance, self, problem, sandbox_context, context)

    def get_plan_summary(self) -> dict[str, Any]:
        """Get a summary of the plan for inspection."""
        return {
            "strategy": self.strategy_name,
            "confidence": self.confidence,
            "type": self.plan_type.value,
            "content_type": type(self.content).__name__,
            "reasoning": self.reasoning,
            "complexity": self.complexity,
            "estimated_duration": self.estimated_duration,
        }

    def is_executable(self) -> bool:
        """Check if this plan can be executed."""
        return self.content is not None and self.plan_type != PlanType.ESCALATE

    def get_execution_method(self) -> str:
        """Get the method that will be used for execution."""
        if isinstance(self.content, str):
            if self.content.startswith("agent:"):
                return "delegate"
            elif self.plan_type == PlanType.ESCALATE:
                return "escalate"
            else:
                return "direct"
        elif isinstance(self.content, dict):
            return self.content.get("type", "unknown").lower()
        elif hasattr(self.content, "execute"):
            return "workflow"
        else:
            return "manual"
