"""
Timeline class for agent history tracking.

This module defines the concrete Timeline class that provides
a flexible, extensible system for tracking temporal sequences of agent activities.
"""

from collections.abc import Iterator
from datetime import datetime
from typing import Any

from .timeline_event import TimelineEvent


class Timeline:
    """Concrete class for temporal sequences of events."""

    def __init__(self):
        """Initialize an empty timeline."""
        self.events: list[TimelineEvent] = []
        self._current_turn: int = 0

    def add_event(self, event: TimelineEvent) -> TimelineEvent:
        """Add an event to the timeline.

        Args:
            event: The TimelineEvent to add

        Returns:
            The added TimelineEvent
        """
        self.events.append(event)
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
