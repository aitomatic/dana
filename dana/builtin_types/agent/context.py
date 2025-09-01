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
        import copy

        return ProblemContext(
            problem_statement=sub_problem,
            objective=sub_objective,
            original_problem=self.original_problem,
            depth=self.depth + 1,
            constraints=copy.deepcopy(self.constraints),
            assumptions=copy.deepcopy(self.assumptions),
        )


@dataclass
class Event:
    """A single event in the linear timeline."""

    timestamp: datetime
    event_type: str  # "conversation_start", "workflow_start", "workflow_complete", etc.
    conversation_turn: int
    depth: int
    data: dict[str, Any]  # Flexible data container
    references: dict[str, Any]  # References to other data structures


class EventHistory:
    """Linear, append-only timeline of all events."""

    def __init__(self):
        self.events: list[Event] = []
        self._current_turn: int = 0

    def add_event(self, event_type: str, data: dict, references: dict = None) -> Event:
        """Add an event to the timeline."""
        event = Event(
            timestamp=datetime.now(),
            event_type=event_type,
            conversation_turn=self._current_turn,
            depth=data.get("depth", 0),
            data=data,
            references=references or {},
        )
        self.events.append(event)
        return event

    def start_new_conversation_turn(self, user_request: str) -> int:
        """Start a new conversation turn and return the turn number."""
        self._current_turn += 1
        self.add_event("conversation_start", {"user_request": user_request, "depth": 0})
        return self._current_turn

    def get_conversation_context(self) -> str:
        """Get conversation context summary for LLM."""
        recent_turns = self.get_recent_conversation_turns(3)
        context_parts = []

        for turn_events in recent_turns:
            # Find the conversation start event
            start_event = next((e for e in turn_events if e.event_type == "conversation_start"), None)
            if start_event:
                # Find the final result
                completion_events = [e for e in turn_events if e.event_type in ["workflow_complete", "workflow_error"]]
                final_result = completion_events[-1].data.get("result", "No result") if completion_events else "No result"
                context_parts.append(f"User: {start_event.data['user_request']}\nAgent: {final_result}")

        return "\n\n".join(context_parts)

    def get_recent_conversation_turns(self, count: int = 3) -> list[list[Event]]:
        """Get recent conversation turns grouped by turn."""
        turns = {}
        for event in self.events:
            if event.conversation_turn not in turns:
                turns[event.conversation_turn] = []
            turns[event.conversation_turn].append(event)

        # Return the most recent turns
        recent_turn_numbers = sorted(turns.keys())[-count:]
        return [turns[turn_num] for turn_num in recent_turn_numbers]

    def get_events_by_type(self, event_type: str) -> list[Event]:
        """Get events of specific type."""
        return [e for e in self.events if e.event_type == event_type]

    def get_events_by_conversation_turn(self, turn: int) -> list[Event]:
        """Get events from specific conversation turn."""
        return [e for e in self.events if e.conversation_turn == turn]

    def get_previous_user_requests(self, count: int = 5) -> list[str]:
        """Get previous user requests for context."""
        conversation_starts = [e for e in self.events if e.event_type == "conversation_start"]
        return [e.data["user_request"] for e in conversation_starts[-count:] if e.data.get("user_request")]


class ComputableContext:
    """Context that can be computed from existing data."""

    def get_complexity_indicators(self, context: ProblemContext, event_history: EventHistory) -> dict[str, Any]:
        """Compute complexity indicators from execution data."""
        events = event_history.events

        if not events:
            return {"sub_problem_count": 0, "execution_time_total": 0.0, "error_rate": 0.0, "max_depth_reached": 0}

        return {
            "sub_problem_count": len([e for e in events if e.event_type == "agent_solve_call"]),
            "execution_time_total": sum(e.data.get("execution_time", 0.0) for e in events),
            "error_rate": len([e for e in events if e.event_type == "workflow_error"]) / len(events),
            "max_depth_reached": max(e.depth for e in events) if events else 0,
        }

    def get_constraint_violations(self, context: ProblemContext, event_history: EventHistory) -> list[str]:
        """Extract constraint violations from failed actions."""
        violations = []
        for event in event_history.events:
            if event.event_type == "workflow_error" and event.data.get("error_message"):
                error_message = event.data["error_message"]
                # Simple pattern matching for constraint violations
                if any(keyword in error_message.lower() for keyword in ["constraint", "limit", "violation", "exceeded"]):
                    violations.append(f"{event.data.get('description', 'Unknown')}: {error_message}")
        return violations

    def get_successful_patterns(self, context: ProblemContext, event_history: EventHistory) -> list[str]:
        """Identify patterns from successful actions."""
        patterns = []
        successful_events = [e for e in event_history.events if e.event_type != "workflow_error"]

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
