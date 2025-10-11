"""
State: Handles state management and context.

This component provides functionality for:
- Agent state management and context
- Interactive conversation interface
- Learning phase implementations (STAR reflection)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from adana.core.agent.star_agent import STARAgent


@dataclass
class State:
    """Component providing state management and timeline functionality."""

    _agent: "STARAgent"
    session_metadata: dict[str, Any] = field(default_factory=dict)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    task_state: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================

    def get_state(self) -> dict[str, Any]:
        """Get current agent state as dictionary."""
        return {
            "object_id": self._agent.object_id,
            "agent_type": self._agent.agent_type,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "session_metadata": self.session_metadata,
            "user_preferences": self.user_preferences,
            "task_state": self.task_state,
            "resources": self._agent.available_resources,
            "workflows": [],
            "timeline_entries": self._agent._timeline.get_entry_count(),
        }

    # ============================================================================
    # UTILITIES
    # ============================================================================

    def __str__(self) -> str:
        """String representation of the agent."""
        agent_type = getattr(self._agent, "agent_type", "Unknown")
        object_id = getattr(self._agent, "object_id", "No ID")
        resources_count = len(getattr(self._agent, "available_resources", []))
        return f"STARAgent(type={agent_type}, id={object_id}, resources={resources_count})"

    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        agent_type = getattr(self._agent, "agent_type", "Unknown")
        object_id = getattr(self._agent, "object_id", "No ID")
        available_resources = getattr(self._agent, "available_resources", [])
        return f"STARAgent(agent_type='{agent_type}', object_id='{object_id}', resources={available_resources})"
