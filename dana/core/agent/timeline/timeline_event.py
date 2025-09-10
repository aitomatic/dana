"""
TimelineEvent classes for agent history tracking.

This module defines the abstract TimelineEvent base class and concrete event types
that provide a flexible, extensible system for tracking temporal sequences of agent activities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import Self

    from .timeline import Timeline


class TimelineEvent(ABC):
    """Abstract base class for events on a timeline."""

    def __init__(
        self, timestamp: datetime | None = None, conversation_turn: int = 0, depth: int = 0, references: dict[str, Any] | None = None
    ):
        """Initialize a timeline event.

        Args:
            timestamp: When the event occurred (defaults to now)
            conversation_turn: Which conversation turn this event belongs to
            depth: Recursion depth of this event
            references: Optional references to other objects
        """
        self.timestamp = timestamp or datetime.now()
        self.conversation_turn = conversation_turn
        self.depth = depth
        self.references = references or {}

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Get the type of this event."""
        pass

    @property
    @abstractmethod
    def data(self) -> dict[str, Any]:
        """Get the event-specific data."""
        pass


@dataclass
class ConversationTurn(TimelineEvent):
    """A conversation turn between user and agent."""

    user_input: str
    agent_response: str
    turn_number: int
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata and call parent constructor."""
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

        # Call parent constructor to initialize timestamp and other attributes
        super().__init__(conversation_turn=self.turn_number)

    @property
    def event_type(self) -> str:
        """Get the event type."""
        return "conversation_turn"

    @property
    def data(self) -> dict[str, Any]:
        """Get the event data."""
        return {
            "user_input": self.user_input,
            "agent_response": self.agent_response,
            "turn_number": self.turn_number,
            "metadata": self.metadata,
        }

    @classmethod
    def start_new_turn(cls, user_request: str, turn_number: int) -> "Self":
        """Start a new conversation turn.

        Args:
            user_request: The user's request that starts the conversation turn
            turn_number: The conversation turn number

        Returns:
            A new ConversationTurn event
        """
        return cls(user_request, "", turn_number=turn_number)

    def complete_turn(self, agent_response: str) -> None:
        """Complete the conversation turn with agent response.

        Args:
            agent_response: The agent's response
        """
        object.__setattr__(self, "agent_response", agent_response)

    def get_context_string(self) -> str:
        """Get formatted conversation context string.

        Returns:
            Formatted string: "User: {input}\nAgent: {response}"
        """
        return f"User: {self.user_input}\nAgent: {self.agent_response}"

    @classmethod
    def get_conversation_context(cls, timeline: "Timeline", max_turns: int = 3) -> str:
        """Get conversation context summary for LLM from a timeline.

        Args:
            timeline: Timeline containing the events
            max_turns: Maximum number of conversation turns to include

        Returns:
            Formatted conversation context string
        """
        conversation_events = [e for e in timeline.events if isinstance(e, cls)]
        recent_events = conversation_events[-max_turns:] if conversation_events else []

        context_parts = []
        for event in recent_events:
            if event.agent_response:  # Include completed turns
                context_parts.append(event.get_context_string())
            elif event.user_input:  # Include current turn with user input
                context_parts.append(f"User: {event.user_input}")

        return "\n\n".join(context_parts)

    @classmethod
    def get_previous_user_requests(cls, timeline: "Timeline", count: int = 5) -> list[str]:
        """Get previous user requests for context from a timeline.

        Args:
            timeline: Timeline containing the events
            count: Number of previous requests to retrieve

        Returns:
            List of user request strings
        """
        conversation_events = [e for e in timeline.events if isinstance(e, cls)]
        return [e.user_input for e in conversation_events[-count:]]


@dataclass
class AgentAction(TimelineEvent):
    """An action performed by the agent."""

    action_type: str  # "workflow_start", "workflow_complete", "workflow_error", etc.
    action_name: str
    depth: int
    execution_time: float = 0.0
    result: Any = None
    error_message: str = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

        # Call parent constructor to initialize timestamp and other attributes
        super().__init__(conversation_turn=0, depth=self.depth)

    @property
    def event_type(self) -> str:
        """Get the event type."""
        return "agent_action"

    @property
    def data(self) -> dict[str, Any]:
        """Get the event data."""
        return {
            "action_type": self.action_type,
            "action_name": self.action_name,
            "depth": self.depth,
            "execution_time": self.execution_time,
            "result": self.result,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class LearningEvent(TimelineEvent):
    """A learning or adaptation event."""

    learning_type: str  # "pattern_learned", "preference_updated", "strategy_adapted", etc.
    learning_data: dict[str, Any]
    confidence: float = 1.0
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

        # Call parent constructor to initialize timestamp and other attributes
        super().__init__(conversation_turn=0, depth=0)

    @property
    def event_type(self) -> str:
        """Get the event type."""
        return "learning_event"

    @property
    def data(self) -> dict[str, Any]:
        """Get the event data."""
        return {
            "learning_type": self.learning_type,
            "learning_data": self.learning_data,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }
