"""
Timeline class for agent history tracking.

This module defines the concrete Timeline class that provides
a flexible, extensible system for tracking temporal sequences of agent activities
with type-based persistence and async loading.
"""

import json
import threading
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .timeline_event import AgentAction, ConversationTurn, LearningEvent, TimelineEvent


class Timeline:
    """Concrete class for temporal sequences of events with type-based persistence."""

    def __init__(self, agent_id: str = "default", persistence_config: dict[str, bool] | None = None):
        """Initialize timeline with type-based persistence.

        Args:
            agent_id: Agent identifier for file organization
            persistence_config: Configuration for which event types to persist
        """
        self.agent_id = agent_id
        self.timeline_dir = Path(f"~/.dana/agents/{agent_id}/timeline").expanduser()

        # Default persistence configuration
        self.persistence_config = {
            "conversation": True,    # Always persist conversations
            "action": True,          # Persist actions for audit
            "learning": False,       # Don't persist learning events by default
            "custom": False          # Don't persist custom events by default
        }
        if persistence_config:
            self.persistence_config.update(persistence_config)

        # Event storage
        self.conversation_events: list[ConversationTurn] = []
        self.action_events: list[AgentAction] = []
        self.learning_events: list[LearningEvent] = []
        self.custom_events: list[TimelineEvent] = []

        # Loading state
        self._loading = True
        self._load_thread = None
        self._load_lock = threading.Lock()

        # Start async loading
        self._start_loading()

    def _start_loading(self):
        """Start loading all event types in background thread."""
        self._load_thread = threading.Thread(target=self._load_all_events)
        self._load_thread.daemon = True
        self._load_thread.start()

    def _load_all_events(self):
        """Load all event types from disk."""
        try:
            with self._load_lock:
                if self.persistence_config.get("conversation", True):
                    self._load_conversation_events()
                if self.persistence_config.get("action", True):
                    self._load_action_events()
                if self.persistence_config.get("learning", False):
                    self._load_learning_events()
                if self.persistence_config.get("custom", False):
                    self._load_custom_events()
        finally:
            self._loading = False

    def _wait_for_loading(self):
        """Block until loading is complete."""
        if self._loading and self._load_thread:
            self._load_thread.join()

    # ============================================================================
    # Event Addition Methods
    # ============================================================================

    def add_conversation_turn(self, user_input: str, agent_response: str, turn_number: int, metadata: dict[str, Any] | None = None) -> ConversationTurn:
        """Add conversation turn and persist immediately.

        Args:
            user_input: The user's input message
            agent_response: The agent's response
            turn_number: The conversation turn number
            metadata: Optional metadata for this turn

        Returns:
            The created ConversationTurn event
        """
        turn = ConversationTurn(user_input, agent_response, turn_number, metadata)
        self.conversation_events.append(turn)

        if self.persistence_config.get("conversation", True):
            self._save_conversation_events()

        return turn

    def add_action(self, action_type: str, action_name: str, depth: int, execution_time: float = 0.0, result: Any = None, error_message: str = None, metadata: dict[str, Any] | None = None) -> AgentAction:
        """Add action event and persist immediately.

        Args:
            action_type: Type of action (e.g., "workflow_start", "workflow_complete")
            action_name: Name of the action
            depth: Recursion depth of this action
            execution_time: Time taken to execute
            result: Result of the action
            error_message: Error message if action failed
            metadata: Optional metadata

        Returns:
            The created AgentAction event
        """
        action = AgentAction(action_type, action_name, depth, execution_time, result, error_message, metadata)
        self.action_events.append(action)

        if self.persistence_config.get("action", True):
            self._save_action_events()

        return action

    def add_learning_event(self, learning_type: str, learning_data: dict[str, Any], confidence: float = 1.0, metadata: dict[str, Any] | None = None) -> LearningEvent:
        """Add learning event and persist immediately.

        Args:
            learning_type: Type of learning (e.g., "pattern_learned", "strategy_adapted")
            learning_data: The learning data
            confidence: Confidence level (0.0-1.0)
            metadata: Optional metadata

        Returns:
            The created LearningEvent
        """
        learning = LearningEvent(learning_type, learning_data, confidence, metadata)
        self.learning_events.append(learning)

        if self.persistence_config.get("learning", False):
            self._save_learning_events()

        return learning

    def add_custom_event(self, event_type: str, data: dict[str, Any], metadata: dict[str, Any] | None = None) -> TimelineEvent:
        """Add custom event and persist immediately.

        Args:
            event_type: Type of the custom event
            data: Event-specific data
            metadata: Optional metadata

        Returns:
            The created custom TimelineEvent
        """
        # Create a generic TimelineEvent for custom events
        event = TimelineEvent(metadata=metadata)
        event._event_type = event_type
        event._data = data
        self.custom_events.append(event)

        if self.persistence_config.get("custom", False):
            self._save_custom_events()

        return event

    # ============================================================================
    # Event Retrieval Methods
    # ============================================================================

    def get_all_events(self) -> Iterator[TimelineEvent]:
        """Get all events in chronological order.

        Returns:
            Iterator over all events sorted by timestamp
        """
        self._wait_for_loading()

        all_events = []
        all_events.extend(self.conversation_events)
        all_events.extend(self.action_events)
        all_events.extend(self.learning_events)
        all_events.extend(self.custom_events)

        return sorted(all_events, key=lambda e: e.timestamp)

    def get_events_by_type(self, event_type: str) -> list[TimelineEvent]:
        """Get events of specific type.

        Args:
            event_type: Type of events to retrieve

        Returns:
            List of events of the specified type
        """
        self._wait_for_loading()

        if event_type == "conversation":
            return self.conversation_events.copy()
        elif event_type == "action":
            return self.action_events.copy()
        elif event_type == "learning":
            return self.learning_events.copy()
        elif event_type == "custom":
            return self.custom_events.copy()
        else:
            return []

    def get_recent_events(self, count: int = 10) -> list[TimelineEvent]:
        """Get the most recent events from the timeline.

        Args:
            count: Number of recent events to retrieve

        Returns:
            List of the most recent events
        """
        all_events = list(self.get_all_events())
        return all_events[-count:] if all_events else []

    def get_events_in_range(self, start_time: datetime, end_time: datetime) -> list[TimelineEvent]:
        """Get events within a specific time range.

        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)

        Returns:
            List of events within the time range
        """
        all_events = list(self.get_all_events())
        return [event for event in all_events if start_time <= event.timestamp <= end_time]

    # ============================================================================
    # Conversation-Specific Methods
    # ============================================================================

    def get_conversation_context(self, max_turns: int = 3) -> str:
        """Get conversation context summary for LLM.

        Args:
            max_turns: Maximum number of conversation turns to include

        Returns:
            Formatted conversation context string
        """
        self._wait_for_loading()

        recent_turns = self.conversation_events[-max_turns:] if self.conversation_events else []

        context_parts = []
        for turn in recent_turns:
            if turn.agent_response:  # Include completed turns
                context_parts.append(turn.get_context_string())
            elif turn.user_input:  # Include current turn with user input
                context_parts.append(f"User: {turn.user_input}")

        return "\n\n".join(context_parts)

    def search_conversation(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search conversation history for matching turns.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of matching conversation turns
        """
        self._wait_for_loading()

        query_lower = query.lower()
        matches = []

        for turn in self.conversation_events:
            if query_lower in turn.user_input.lower() or query_lower in turn.agent_response.lower():
                matches.append({
                    "user_input": turn.user_input,
                    "agent_response": turn.agent_response,
                    "turn_number": turn.turn_number,
                    "timestamp": turn.timestamp.isoformat(),
                    "metadata": turn.metadata or {},
                })

        # Return most recent matches first
        return matches[-max_results:] if matches else []

    def get_previous_user_requests(self, count: int = 5) -> list[str]:
        """Get previous user requests for context.

        Args:
            count: Number of previous requests to retrieve

        Returns:
            List of user request strings
        """
        self._wait_for_loading()
        return [turn.user_input for turn in self.conversation_events[-count:]]

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def get_event_count(self) -> int:
        """Get the total number of events on the timeline.

        Returns:
            Number of events
        """
        self._wait_for_loading()
        return (len(self.conversation_events) +
                len(self.action_events) +
                len(self.learning_events) +
                len(self.custom_events))

    def is_empty(self) -> bool:
        """Check if the timeline has any events.

        Returns:
            True if timeline is empty, False otherwise
        """
        self._wait_for_loading()
        return (len(self.conversation_events) == 0 and
                len(self.action_events) == 0 and
                len(self.learning_events) == 0 and
                len(self.custom_events) == 0)

    def clear(self) -> None:
        """Remove all events from the timeline."""
        self._wait_for_loading()

        self.conversation_events.clear()
        self.action_events.clear()
        self.learning_events.clear()
        self.custom_events.clear()

        # Clear persisted files
        self._clear_persisted_events()

    def get_timeline_summary(self) -> dict[str, Any]:
        """Get a summary of the timeline.

        Returns:
            Dictionary containing timeline statistics and metadata
        """
        self._wait_for_loading()

        if self.is_empty():
            return {
                "total_events": 0,
                "event_types": {},
                "time_span": None,
                "first_event": None,
                "last_event": None
            }

        all_events = list(self.get_all_events())

        # Count events by type
        event_types = {
            "conversation": len(self.conversation_events),
            "action": len(self.action_events),
            "learning": len(self.learning_events),
            "custom": len(self.custom_events),
        }

        return {
            "total_events": len(all_events),
            "event_types": event_types,
            "time_span": (all_events[-1].timestamp - all_events[0].timestamp).total_seconds() if len(all_events) > 1 else 0,
            "first_event": all_events[0].timestamp.isoformat(),
            "last_event": all_events[-1].timestamp.isoformat(),
        }

    # ============================================================================
    # Persistence Methods
    # ============================================================================

    def _save_conversation_events(self):
        """Save conversation events to conversation.json."""
        filepath = self.timeline_dir / "conversation.json"
        self._save_events_to_file(self.conversation_events, filepath)

    def _load_conversation_events(self):
        """Load conversation events from conversation.json."""
        filepath = self.timeline_dir / "conversation.json"
        self.conversation_events = self._load_events_from_file(filepath, ConversationTurn)

    def _save_action_events(self):
        """Save action events to action.json."""
        filepath = self.timeline_dir / "action.json"
        self._save_events_to_file(self.action_events, filepath)

    def _load_action_events(self):
        """Load action events from action.json."""
        filepath = self.timeline_dir / "action.json"
        self.action_events = self._load_events_from_file(filepath, AgentAction)

    def _save_learning_events(self):
        """Save learning events to learning.json."""
        filepath = self.timeline_dir / "learning.json"
        self._save_events_to_file(self.learning_events, filepath)

    def _load_learning_events(self):
        """Load learning events from learning.json."""
        filepath = self.timeline_dir / "learning.json"
        self.learning_events = self._load_events_from_file(filepath, LearningEvent)

    def _save_custom_events(self):
        """Save custom events to custom.json."""
        filepath = self.timeline_dir / "custom.json"
        self._save_events_to_file(self.custom_events, filepath)

    def _load_custom_events(self):
        """Load custom events from custom.json."""
        filepath = self.timeline_dir / "custom.json"
        self.custom_events = self._load_events_from_file(filepath, TimelineEvent)

    def _save_events_to_file(self, events: list, filepath: Path):
        """Generic method to save events to file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "events": [self._event_to_dict(event) for event in events],
            "last_updated": datetime.now(UTC).isoformat(),
            "event_count": len(events)
        }

        # Atomic write
        temp_path = filepath.with_suffix(".json.tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        temp_path.replace(filepath)

    def _load_events_from_file(self, filepath: Path, event_class) -> list:
        """Generic method to load events from file."""
        if not filepath.exists():
            return []

        try:
            with open(filepath) as f:
                data = json.load(f)

            events = []
            for event_data in data.get("events", []):
                event = self._dict_to_event(event_data, event_class)
                if event:
                    events.append(event)

            return events
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Failed to load events from {filepath}: {e}")
            return []

    def _event_to_dict(self, event: TimelineEvent) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        base_data = {
            "timestamp": event.timestamp.isoformat(),
            "conversation_turn": event.conversation_turn,
            "depth": event.depth,
            "references": event.references or {},
        }

        if isinstance(event, ConversationTurn):
            base_data.update({
                "event_type": "conversation_turn",
                "user_input": event.user_input,
                "agent_response": event.agent_response,
                "turn_number": event.turn_number,
                "metadata": event.metadata or {},
            })
        elif isinstance(event, AgentAction):
            base_data.update({
                "event_type": "agent_action",
                "action_type": event.action_type,
                "action_name": event.action_name,
                "execution_time": event.execution_time,
                "result": event.result,
                "error_message": event.error_message,
                "metadata": event.metadata or {},
            })
        elif isinstance(event, LearningEvent):
            base_data.update({
                "event_type": "learning_event",
                "learning_type": event.learning_type,
                "learning_data": event.learning_data,
                "confidence": event.confidence,
                "metadata": event.metadata or {},
            })
        else:
            # Custom event
            base_data.update({
                "event_type": getattr(event, "_event_type", "custom"),
                "data": getattr(event, "_data", {}),
                "metadata": event.metadata or {},
            })

        return base_data

    def _dict_to_event(self, event_data: dict, event_class) -> TimelineEvent | None:
        """Convert dictionary to event object."""
        try:
            timestamp = datetime.fromisoformat(event_data["timestamp"].replace("Z", "+00:00"))

            if event_class == ConversationTurn:
                turn = ConversationTurn(
                    user_input=event_data["user_input"],
                    agent_response=event_data["agent_response"],
                    turn_number=event_data["turn_number"],
                    metadata=event_data.get("metadata", {}),
                )
                # Set timestamp after creation
                turn.timestamp = timestamp
                return turn
            elif event_class == AgentAction:
                action = AgentAction(
                    action_type=event_data["action_type"],
                    action_name=event_data["action_name"],
                    depth=event_data["depth"],
                    execution_time=event_data.get("execution_time", 0.0),
                    result=event_data.get("result"),
                    error_message=event_data.get("error_message"),
                    metadata=event_data.get("metadata", {}),
                )
                # Set timestamp after creation
                action.timestamp = timestamp
                return action
            elif event_class == LearningEvent:
                learning = LearningEvent(
                    learning_type=event_data["learning_type"],
                    learning_data=event_data["learning_data"],
                    confidence=event_data.get("confidence", 1.0),
                    metadata=event_data.get("metadata", {}),
                )
                # Set timestamp after creation
                learning.timestamp = timestamp
                return learning
            else:
                # Custom event
                event = TimelineEvent(timestamp=timestamp, metadata=event_data.get("metadata", {}))
                event._event_type = event_data.get("event_type", "custom")
                event._data = event_data.get("data", {})
                return event

        except (KeyError, ValueError) as e:
            print(f"Warning: Failed to deserialize event: {e}")
            return None

    def _clear_persisted_events(self):
        """Clear all persisted event files."""
        for event_type in ["conversation", "action", "learning", "custom"]:
            filepath = self.timeline_dir / f"{event_type}.json"
            if filepath.exists():
                filepath.unlink()

    # ============================================================================
    # Magic Methods
    # ============================================================================

    def __iter__(self) -> Iterator[TimelineEvent]:
        """Make Timeline iterable over its events.

        Returns:
            Iterator over events in reverse chronological order (most recent first)
        """
        all_events = list(self.get_all_events())
        return reversed(all_events)

    def __len__(self) -> int:
        """Get the number of events in the timeline.

        Returns:
            Number of events
        """
        return self.get_event_count()

    def __getitem__(self, index: int) -> TimelineEvent:
        """Get an event by index.

        Args:
            index: Index of the event to retrieve

        Returns:
            Event at the specified index

        Raises:
            IndexError: If index is out of range
        """
        all_events = list(self.get_all_events())
        return all_events[index]

    def __contains__(self, event: TimelineEvent) -> bool:
        """Check if an event is in the timeline.

        Args:
            event: Event to check for

        Returns:
            True if event is in timeline, False otherwise
        """
        self._wait_for_loading()

        if isinstance(event, ConversationTurn):
            return event in self.conversation_events
        elif isinstance(event, AgentAction):
            return event in self.action_events
        elif isinstance(event, LearningEvent):
            return event in self.learning_events
        else:
            return event in self.custom_events
