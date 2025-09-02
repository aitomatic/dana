"""
Context Resource and Workflow interfaces for the Context Engineering Framework.
"""

from abc import ABC, abstractmethod
from typing import Any


class ContextResource(ABC):
    """Abstract base for context data sources."""

    @abstractmethod
    def get_context_for(self, query: str, **options) -> dict[str, Any]:
        """Get context data for the query."""
        pass

    def get_priority(self) -> int:
        """Get resource priority (lower = higher priority)."""
        return 100

    def can_handle(self, use_case: str) -> bool:
        """Check if resource can handle this use case."""
        return True

    def get_supported_use_cases(self) -> list[str]:
        """Get list of supported use cases."""
        return ["general"]


class ContextWorkflow(ABC):
    """Abstract base for workflows that provide context."""

    @abstractmethod
    def get_execution_context(self) -> dict[str, Any]:
        """Get current workflow execution context."""
        pass

    @abstractmethod
    def get_pattern_info(self) -> dict[str, Any]:
        """Get workflow pattern information."""
        pass


# Example implementations for common agent resources


class EventHistoryResource(ContextResource):
    """Provides event history and conversation context."""

    def __init__(self, event_history):
        self.event_history = event_history

    def get_context_for(self, query: str, **options) -> dict[str, Any]:
        """Get conversation context from event history."""
        if not self.event_history:
            return {}

        try:
            conversation_context = self.event_history.get_conversation_context()
            recent_events = self._get_recent_events()

            return {"conversation_history": conversation_context, "recent_events": recent_events}
        except Exception as e:
            return {"error": f"Failed to get event history: {e}"}

    def _get_recent_events(self) -> list[str]:
        """Get recent events for context."""
        try:
            events = self.event_history.events[-5:] if self.event_history.events else []
            return [f"{e.event_type}: {e.data.get('description', 'No description')}" for e in events]
        except Exception:
            return []

    def get_priority(self) -> int:
        return 10  # High priority for conversation context

    def can_handle(self, use_case: str) -> bool:
        return use_case in ["problem_solving", "conversation"]


class ProblemContextResource(ContextResource):
    """Provides problem-solving context."""

    def __init__(self, problem_context):
        self.problem_context = problem_context

    def get_context_for(self, query: str, **options) -> dict[str, Any]:
        """Get problem context."""
        if not self.problem_context:
            return {}

        try:
            return {
                "problem_statement": self.problem_context.problem_statement,
                "objective": self.problem_context.objective,
                "current_depth": self.problem_context.depth,
                "constraints": self.problem_context.constraints,
                "assumptions": self.problem_context.assumptions,
            }
        except Exception as e:
            return {"error": f"Failed to get problem context: {e}"}

    def get_priority(self) -> int:
        return 5  # Very high priority for problem context

    def can_handle(self, use_case: str) -> bool:
        return use_case == "problem_solving"


class WorkflowStateResource(ContextResource):
    """Provides workflow execution state."""

    def __init__(self, workflow_instance):
        self.workflow_instance = workflow_instance

    def get_context_for(self, query: str, **options) -> dict[str, Any]:
        """Get workflow execution context."""
        if not self.workflow_instance:
            return {}

        try:
            return {
                "current_workflow": getattr(self.workflow_instance, "name", "unknown"),
                "workflow_state": getattr(self.workflow_instance, "_execution_state", "unknown"),
                "workflow_values": getattr(self.workflow_instance, "_values", {}),
            }
        except Exception as e:
            return {"error": f"Failed to get workflow state: {e}"}

    def get_priority(self) -> int:
        return 20  # Medium priority

    def can_handle(self, use_case: str) -> bool:
        return use_case in ["problem_solving", "workflow_execution"]
