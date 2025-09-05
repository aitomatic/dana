"""
Context engineering for the agent solving system.

This module defines how information flows through the agent solving system,
ensuring that each component has the information it needs to make intelligent
decisions while maintaining system simplicity and performance.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .timeline import Timeline


@dataclass
class ProblemContext:
    """Problem-specific information with hierarchical structure."""

    problem_statement: str  # Current problem to solve
    objective: str = ""  # What we're trying to achieve (defaults to problem_statement if empty)
    original_problem: str = ""  # Root problem description (defaults to problem_statement if empty)
    depth: int = 0  # Current recursion level
    constraints: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Set default values for objective and original_problem if not provided."""
        if not self.objective:
            self.objective = self.problem_statement
        if not self.original_problem:
            self.original_problem = self.problem_statement

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization and context passing.

        Returns:
            Dictionary representation of the problem context
        """
        return {
            "problem_statement": self.problem_statement,
            "objective": self.objective,
            "original_problem": self.original_problem,
            "depth": self.depth,
            "constraints": self.constraints,
            "assumptions": self.assumptions,
        }

    def create_sub_context(self, sub_problem: str, sub_objective: str) -> "ProblemContext":
        """Create context for sub-problem."""
        import copy

        return ProblemContext(
            problem_statement=sub_problem,
            objective=sub_objective,
            original_problem=self.original_problem,
            depth=self.depth + 1,
            constraints=copy.deepcopy(self.constraints),
            assumptions=copy.deepcopy(self.assumptions),
        )


class ComputableContext:
    """Context that can be computed from existing data."""

    def get_complexity_indicators(self, context: ProblemContext, timeline: "Timeline") -> dict[str, Any]:
        """Compute complexity indicators from execution data."""
        events = timeline.events

        if not events:
            return {"sub_problem_count": 0, "execution_time_total": 0.0, "error_rate": 0.0, "max_depth_reached": 0}

        return {
            "sub_problem_count": len([e for e in events if e.event_type == "agent_solve_call"]),
            "execution_time_total": sum(e.data.get("execution_time", 0.0) for e in events),
            "error_rate": len([e for e in events if e.event_type == "workflow_error"]) / len(events),
            "max_depth_reached": max(e.depth for e in events) if events else 0,
        }

    def get_constraint_violations(self, context: ProblemContext, timeline: "Timeline") -> list[str]:
        """Extract constraint violations from failed actions."""
        violations = []
        for event in timeline.events:
            if event.event_type == "workflow_error" and event.data.get("error_message"):
                error_message = event.data["error_message"]
                # Simple pattern matching for constraint violations
                if any(keyword in error_message.lower() for keyword in ["constraint", "limit", "violation", "exceeded"]):
                    violations.append(f"{event.data.get('description', 'Unknown')}: {error_message}")
        return violations

    def get_successful_patterns(self, context: ProblemContext, timeline: "Timeline") -> list[str]:
        """Identify patterns from successful actions."""
        patterns = []
        successful_events = [e for e in timeline.events if e.event_type != "workflow_error"]

        # Count event types
        event_counts = {}
        for event in successful_events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

        # Identify common patterns
        if event_counts.get("agent_solve_call", 0) > 2:
            patterns.append("recursive_decomposition")
        if event_counts.get("agent_input", 0) > 0:
            patterns.append("user_interaction")
        if event_counts.get("agent_reason", 0) > 3:
            patterns.append("reasoning_intensive")

        return patterns
