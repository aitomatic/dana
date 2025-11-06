"""
EventLog API for managing observation events and timeline persistence.

This module provides EventLogAPI following the LocalPromptAPI pattern.
Events come ONLY from Observer.observe() - no action events, no tool call events.
"""

from collections.abc import Iterator
from datetime import datetime
from typing import TYPE_CHECKING

from structlog import get_logger

from dana.common.schemas import Event
from dana.config.storage_config import FileStorageConfig


if TYPE_CHECKING:
    from dana.core.agent.base_agent import BaseAgent
    from dana.core.knowledge.prompts.codecs import AbstractCodec
    from dana.repositories.repository_protocol import EventRepositoryProtocol

from .observer import ObserverProtocol


logger = get_logger()


class EventLogAPI:
    """
    API for managing observation events and timeline persistence.
    Simplified version of LocalPromptAPI pattern.
    
    IMPORTANT: Events ONLY come from Observer. No other sources.
    - No action events
    - No tool call events  
    - No feedback events
    - ONLY observations from Observer.observe()
    """
    
    def __init__(
        self,
        agent: "BaseAgent",
        codec: type["AbstractCodec"] | None,
        storage_config: FileStorageConfig,
        observer: ObserverProtocol,
        repository: "EventRepositoryProtocol | None" = None,
    ):
        """
        Initialize EventLog API.

        Args:
            agent: Agent instance
            codec: Codec class for path structure (for backward compatibility)
            storage_config: Storage configuration (for backward compatibility)
            observer: Observer for environment data (REQUIRED)
            repository: Event repository (if None and agent provided, creates default)

        Note: Observer is required - EventLog only works with Observer.
        """
        self._agent = agent
        self._codec = codec
        self._storage_config = storage_config
        self._observer = observer
        self._current_session_id: str | None = None
        self._event_buffer: list[Event] = []  # Buffer for observations only

        # Initialize repository if provided, otherwise create default from agent
        if repository:
            self._repository = repository
        elif agent:
            from dana.repositories import LocalEventRepository
            self._repository = LocalEventRepository(agent)
        else:
            self._repository = None
    
    def observe_and_record(self) -> Event | None:
        """
        Observe environment via Observer and create event.
        
        This is the ONLY way events are created - from Observer.observe()
        No other sources (actions, tool calls, etc.) create events.
        
        Returns:
            Event if observer returned data, None otherwise
        """
        try:
            # Observer is the ONLY source of events
            data = self._observer.observe()
            if data:
                event = Event(
                    type="observation",  # Always "observation"
                    data=data,
                    metadata={"source": "observer"}
                )
                event.agent_id = self._agent.object_id
                event.session_id = self._current_session_id
                self._event_buffer.append(event)
                return event
        except Exception as e:
            # Log but don't crash
            logger.warning(f"Observer failed: {e}")
        return None
    
    def save(self, session_id: str) -> None:
        """
        Save events for a session.

        Args:
            session_id: Session identifier
        """
        if self._repository is None:
            raise ValueError("Cannot save events: repository is None. Initialize EventLogAPI with repository or agent.")

        self._current_session_id = session_id

        # Save events using repository
        self._repository.save(session_id, self._event_buffer)

        # Log before clearing buffer
        num_events = len(self._event_buffer)
        # Clear buffer after save
        self._event_buffer.clear()
        logger.info(f"Saved {num_events} events for session {session_id}")
    
    def read_since(self, checkpoint: int) -> Iterator[Event]:
        """
        Read events since checkpoint for the current session.

        Args:
            checkpoint: Starting index for reading events.
                Negative values are supported (e.g., -10 means "last 10 events").
                -1 means "last event only", -2 means "last 2 events", etc.

        Yields:
            Event objects since checkpoint
        """
        if self._repository is None:
            raise ValueError("Cannot read events: repository is None. Initialize EventLogAPI with repository or agent.")

        if self._agent is None:
            raise ValueError("Cannot read events: agent is None. Session ID cannot be extracted.")

        # Extract session_id from agent
        session_id = getattr(self._agent, "_session_id", None)
        if session_id is None:
            raise ValueError("Cannot read events: agent has no _session_id. Set session_id on agent first.")

        # Collect all events from the session
        all_events = list(self._repository.read_session_events(session_id))

        # Convert negative checkpoint to positive index
        if checkpoint < 0:
            total_count = len(all_events)
            # Convert negative index: -1 = last event, -2 = second to last, etc.
            # Similar to Python list slicing: checkpoint = total_count + checkpoint
            checkpoint = max(0, total_count + checkpoint)

        # Yield events from checkpoint onwards
        for i in range(checkpoint, len(all_events)):
            yield all_events[i]

