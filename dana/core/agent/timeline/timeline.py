"""
Timeline class for agent history tracking.

This module defines the concrete Timeline class that provides
a flexible, extensible system for tracking temporal sequences of agent activities.
"""

import json
import shutil
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .timeline_event import ConversationTurn, TimelineEvent


class Timeline:
    """Concrete class for temporal sequences of events with conversation persistence."""

    def __init__(self, conversation_persistence: bool = True, conversation_filepath: str | None = None):
        """Initialize an empty timeline with optional conversation persistence.

        Args:
            conversation_persistence: Whether to persist conversation turns to disk
            conversation_filepath: Path to conversation persistence file (optional)
        """
        self.events: list[TimelineEvent] = []
        self._current_turn: int = 0

        # Conversation persistence settings
        self.conversation_persistence = conversation_persistence
        if conversation_persistence:
            if conversation_filepath:
                self.conversation_filepath = Path(conversation_filepath)
            else:
                # Default to user's agents directory structure
                default_dir = Path("~/.dana/agents/default/state/timeline/conversations").expanduser()
                default_dir.mkdir(parents=True, exist_ok=True)
                self.conversation_filepath = default_dir / f"conversation_{uuid.uuid4()}.json"

            # Conversation metadata
            self.conversation_id = str(uuid.uuid4())
            self.conversation_created_at = datetime.now(UTC).isoformat()
            self.conversation_updated_at = self.conversation_created_at
            self.conversation_metadata = {"session_count": 1, "total_turns": 0}

            # Load existing conversation if file exists
            self._load_conversation()

    def add_event(self, event: TimelineEvent) -> TimelineEvent:
        """Add an event to the timeline.

        Args:
            event: The TimelineEvent to add

        Returns:
            The added TimelineEvent
        """
        self.events.append(event)

        # Auto-persist conversation turns if persistence is enabled
        if self.conversation_persistence and isinstance(event, ConversationTurn):
            self._persist_conversation_turn(event)

        return event

    def walk_forward(self, start_index: int = 0) -> Iterator[TimelineEvent]:
        """Walk through timeline events forward from a starting index.

        Args:
            start_index: Index to start walking from (default: 0)

        Yields:
            TimelineEvent objects in chronological order
        """
        for i in range(start_index, len(self.events)):
            yield self.events[i]

    def walk_backward(self, start_index: int = -1) -> Iterator[TimelineEvent]:
        """Walk through timeline events backward from a starting index.

        Args:
            start_index: Index to start walking from (default: -1 for last event)

        Yields:
            TimelineEvent objects in reverse chronological order
        """
        if start_index == -1:
            start_index = len(self.events) - 1
        for i in range(start_index, -1, -1):
            yield self.events[i]

    def get_events_by_type(self, event_type: str) -> list[TimelineEvent]:
        """Get all events of a specific type.

        Args:
            event_type: Type of events to retrieve

        Returns:
            List of TimelineEvent objects matching the type
        """
        return [event for event in self.events if event.event_type == event_type]

    def get_recent_events(self, count: int = 10) -> list[TimelineEvent]:
        """Get the most recent events from the timeline.

        Args:
            count: Number of recent events to retrieve

        Returns:
            List of the most recent TimelineEvent objects
        """
        return self.events[-count:] if self.events else []

    def get_events_in_range(self, start_time: datetime, end_time: datetime) -> list[TimelineEvent]:
        """Get events within a specific time range.

        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)

        Returns:
            List of TimelineEvent objects within the time range
        """
        return [event for event in self.events if start_time <= event.timestamp <= end_time]

    def get_event_count(self) -> int:
        """Get the total number of events on the timeline.

        Returns:
            Number of events
        """
        return len(self.events)

    def is_empty(self) -> bool:
        """Check if the timeline has any events.

        Returns:
            True if timeline is empty, False otherwise
        """
        return len(self.events) == 0

    def clear(self) -> None:
        """Remove all events from the timeline."""
        self.events.clear()
        self._current_turn = 0

    def get_timeline_summary(self) -> dict[str, Any]:
        """Get a summary of the timeline.

        Returns:
            Dictionary containing timeline statistics and metadata
        """
        if not self.events:
            return {"total_events": 0, "event_types": {}, "time_span": None, "first_event": None, "last_event": None}

        # Count events by type
        event_types = {}
        for event in self.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        return {
            "total_events": len(self.events),
            "event_types": event_types,
            "time_span": (self.events[-1].timestamp - self.events[0].timestamp).total_seconds() if len(self.events) > 1 else 0,
            "first_event": self.events[0].timestamp.isoformat(),
            "last_event": self.events[-1].timestamp.isoformat(),
        }

    def __iter__(self) -> Iterator[TimelineEvent]:
        """Make Timeline iterable over its events.

        Returns:
            Iterator over TimelineEvent objects in reverse chronological order (most recent first)
        """
        return reversed(self.events)

    def __len__(self) -> int:
        """Get the number of events in the timeline.

        Returns:
            Number of events
        """
        return len(self.events)

    def __getitem__(self, index: int) -> TimelineEvent:
        """Get an event by index.

        Args:
            index: Index of the event to retrieve

        Returns:
            TimelineEvent at the specified index

        Raises:
            IndexError: If index is out of range
        """
        return self.events[index]

    def __contains__(self, event: TimelineEvent) -> bool:
        """Check if an event is in the timeline.

        Args:
            event: TimelineEvent to check for

        Returns:
            True if event is in timeline, False otherwise
        """
        return event in self.events

    # ---------------------------
    # Conversation Persistence Methods
    # ---------------------------

    def _persist_conversation_turn(self, conversation_turn: ConversationTurn) -> None:
        """Persist a conversation turn to disk.

        Args:
            conversation_turn: The ConversationTurn to persist
        """
        if not self.conversation_persistence:
            return

        try:
            # Convert ConversationTurn to persistence format
            turn_data = {
                "turn_id": str(uuid.uuid4()),
                "user_input": conversation_turn.user_input,
                "agent_response": conversation_turn.agent_response,
                "turn_number": conversation_turn.turn_number,
                "timestamp": conversation_turn.timestamp.isoformat(),
                "metadata": conversation_turn.metadata or {},
            }

            # Update conversation metadata
            self.conversation_metadata["total_turns"] += 1
            self.conversation_updated_at = turn_data["timestamp"]

            # Save to disk
            self._save_conversation()

        except Exception as e:
            # Graceful degradation - don't fail the timeline if persistence fails
            print(f"Warning: Failed to persist conversation turn: {e}")

    def _save_conversation(self, backup: bool = True) -> None:
        """Save conversation data to JSON file.

        Args:
            backup: Whether to create a backup before saving
        """
        if not self.conversation_persistence:
            return

        try:
            # Create backup if requested and file exists
            if backup and self.conversation_filepath.exists():
                backup_path = self.conversation_filepath.with_suffix(".json.bak")
                shutil.copy2(self.conversation_filepath, backup_path)

            # Get all conversation turns from timeline
            conversation_turns = [e for e in self.events if isinstance(e, ConversationTurn)]

            # Convert to persistence format
            history = []
            for turn in conversation_turns:
                history.append(
                    {
                        "turn_id": str(uuid.uuid4()),
                        "user_input": turn.user_input,
                        "agent_response": turn.agent_response,
                        "turn_number": turn.turn_number,
                        "timestamp": turn.timestamp.isoformat(),
                        "metadata": turn.metadata or {},
                    }
                )

            # Prepare data for serialization
            data = {
                "conversation_id": self.conversation_id,
                "created_at": self.conversation_created_at,
                "updated_at": self.conversation_updated_at,
                "history": history,
                "summaries": [],  # Future feature
                "metadata": self.conversation_metadata,
            }

            # Ensure directory exists
            self.conversation_filepath.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first (atomic write)
            temp_path = self.conversation_filepath.with_suffix(".json.tmp")
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)

            # Move temp file to final location (atomic on most systems)
            temp_path.replace(self.conversation_filepath)

        except Exception as e:
            print(f"Warning: Failed to save conversation: {e}")

    def _load_conversation(self) -> bool:
        """Load conversation data from JSON file.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.conversation_persistence or not self.conversation_filepath.exists():
            return False

        try:
            with open(self.conversation_filepath) as f:
                data = json.load(f)

            # Restore conversation metadata
            self.conversation_id = data.get("conversation_id", self.conversation_id)
            self.conversation_created_at = data.get("created_at", self.conversation_created_at)
            self.conversation_updated_at = data.get("updated_at", self.conversation_updated_at)
            self.conversation_metadata = data.get("metadata", self.conversation_metadata)

            # Restore conversation turns to timeline
            history_data = data.get("history", [])
            for turn_data in history_data:
                conversation_turn = ConversationTurn(
                    user_input=turn_data["user_input"],
                    agent_response=turn_data["agent_response"],
                    turn_number=turn_data["turn_number"],
                    metadata=turn_data.get("metadata", {}),
                    timestamp=datetime.fromisoformat(turn_data["timestamp"].replace("Z", "+00:00")),
                )
                # Add to timeline without triggering persistence (to avoid recursion)
                self.events.append(conversation_turn)

            # Update session count
            self.conversation_metadata["session_count"] = self.conversation_metadata.get("session_count", 0) + 1

            return True

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Failed to load conversation: {e}")
            # Try to load backup if available
            backup_path = self.conversation_filepath.with_suffix(".json.bak")
            if backup_path.exists():
                shutil.copy2(backup_path, self.conversation_filepath)
                return self._load_conversation()  # Recursive call to load backup
            return False

    def get_conversation_context(self, max_turns: int = 3) -> str:
        """Get conversation context summary for LLM from timeline.

        Args:
            max_turns: Maximum number of conversation turns to include

        Returns:
            Formatted conversation context string
        """
        return ConversationTurn.get_conversation_context(self, max_turns)

    def search_conversation(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search conversation history for matching turns.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of matching conversation turns
        """
        if not self.conversation_persistence:
            return []

        query_lower = query.lower()
        conversation_turns = [e for e in self.events if isinstance(e, ConversationTurn)]

        matches = []
        for turn in conversation_turns:
            if query_lower in turn.user_input.lower() or query_lower in turn.agent_response.lower():
                matches.append(
                    {
                        "user_input": turn.user_input,
                        "agent_response": turn.agent_response,
                        "turn_number": turn.turn_number,
                        "timestamp": turn.timestamp.isoformat(),
                        "metadata": turn.metadata or {},
                    }
                )

        # Return most recent matches first
        return matches[-max_results:] if matches else []

    def clear_conversation(self) -> None:
        """Clear conversation persistence data."""
        if self.conversation_persistence:
            self.conversation_metadata = {"session_count": 1, "total_turns": 0}
            self.conversation_updated_at = datetime.now(UTC).isoformat()
            self._save_conversation()
