"""
Context engineering for the agent solving system.

This module defines how information flows through the agent solving system,
ensuring that each component has the information it needs to make intelligent
decisions while maintaining system simplicity and performance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProblemContext:
    """Problem-specific information with hierarchical structure."""

    problem_statement: str  # Current problem to solve
    objective: str  # What we're trying to achieve
    original_problem: str  # Root problem description
    depth: int = 0  # Current recursion level
    constraints: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)

    def create_sub_context(self, sub_problem: str, sub_objective: str) -> "ProblemContext":
        """Create context for sub-problem."""
        return ProblemContext(
            problem_statement=sub_problem,
            objective=sub_objective,
            original_problem=self.original_problem,
            depth=self.depth + 1,
            constraints=self.constraints.copy(),
            assumptions=self.assumptions.copy(),
        )


@dataclass
class Action:
    """Represents an action taken during problem solving."""

    action_type: str  # Type of action taken
    description: str  # Description of the action
    depth: int  # Recursion depth when action occurred
    timestamp: datetime  # When action occurred
    result: Any  # Result of the action
    workflow_id: str  # ID of workflow that took the action
    problem_statement: str  # Problem being solved
    success: bool  # Did it succeed?
    execution_time: float  # How long it took
    error_message: str | None = None  # What went wrong (if any)


class ActionHistory:
    """Linear, append-only history across all workflow levels."""

    def __init__(self):
        self.actions: list[Action] = []

    def add_action(self, action: Action) -> None:
        """Add action to global history."""
        self.actions.append(action)

    def get_recent_actions(self, count: int = 10) -> list[Action]:
        """Get most recent actions for LLM context."""
        return self.actions[-count:]

    def get_actions_by_depth(self, depth: int) -> list[Action]:
        """Get actions from specific recursion depth."""
        return [a for a in self.actions if a.depth == depth]

    def get_actions_by_type(self, action_type: str) -> list[Action]:
        """Get actions of specific type."""
        return [a for a in self.actions if a.action_type == action_type]


class ComputableContext:
    """Context that can be computed from existing data."""

    def get_complexity_indicators(self, context: ProblemContext, action_history: ActionHistory) -> dict[str, Any]:
        """Compute complexity indicators from execution data."""
        actions = action_history.actions

        if not actions:
            return {"sub_problem_count": 0, "execution_time_total": 0.0, "error_rate": 0.0, "max_depth_reached": 0}

        return {
            "sub_problem_count": len([a for a in actions if a.action_type == "agent_solve_call"]),
            "execution_time_total": sum(a.execution_time for a in actions),
            "error_rate": len([a for a in actions if not a.success]) / len(actions),
            "max_depth_reached": max(a.depth for a in actions) if actions else 0,
        }

    def get_constraint_violations(self, context: ProblemContext, action_history: ActionHistory) -> list[str]:
        """Extract constraint violations from failed actions."""
        violations = []
        for action in action_history.actions:
            if not action.success and action.error_message:
                # Simple pattern matching for constraint violations
                if any(keyword in action.error_message.lower() for keyword in ["constraint", "limit", "violation", "exceeded"]):
                    violations.append(f"{action.description}: {action.error_message}")
        return violations

    def get_successful_patterns(self, context: ProblemContext, action_history: ActionHistory) -> list[str]:
        """Identify patterns from successful actions."""
        patterns = []
        successful_actions = [a for a in action_history.actions if a.success]

        # Count action types
        action_counts = {}
        for action in successful_actions:
            action_counts[action.action_type] = action_counts.get(action.action_type, 0) + 1

        # Identify common patterns
        if action_counts.get("agent_solve_call", 0) > 2:
            patterns.append("recursive_decomposition")
        if action_counts.get("agent_input", 0) > 0:
            patterns.append("user_interaction")
        if action_counts.get("agent_reason", 0) > 3:
            patterns.append("reasoning_intensive")

        return patterns
