"""
EventLog API for managing observation events and timeline persistence.

This module provides EventLogAPI following the LocalPromptAPI pattern.
Events come ONLY from Observer.observe() - no action events, no tool call events.
"""

from collections.abc import Iterator
from datetime import datetime
import inspect
import json
from pathlib import Path
from typing import TYPE_CHECKING

from structlog import get_logger

from dana.common.schemas import Event
from dana.config.storage_config import FileStorageConfig


if TYPE_CHECKING:
    from dana.core.agent.base_agent import BaseAgent
    from dana.core.knowledge.prompts.codecs import AbstractCodec

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
    ):
        """
        Initialize EventLog API.
        
        Args:
            agent: Agent instance
            codec: Codec class for path structure
            storage_config: Storage configuration
            observer: Observer for environment data (REQUIRED)
        
        Note: Observer is required - EventLog only works with Observer.
        """
        self._agent = agent
        self._codec = codec
        self._codec_prefix = codec.__qualname__ if codec else "default"
        self._storage_config = storage_config
        self._observer = observer
        self._current_session_id: str | None = None
        self._event_buffer: list[Event] = []  # Buffer for observations only
        
        # Calculate path following prompt_api.py pattern
        # Path: {codec.__qualname__}/{agent.__class__.__qualname__}__{filename}/events/{session_id}
        self._workspace_folder = Path(storage_config.workspace_folder) / self.relative_path
        self._workspace_folder.mkdir(parents=True, exist_ok=True)
    
    @property
    def relative_path(self) -> str:
        """Calculate relative path following prompt_api.py pattern."""
        filepath = inspect.getfile(self._agent.__class__)
        filename = Path(filepath).stem
        return f"{self._codec_prefix}/{self._agent.__class__.__qualname__}__{filename}/events"
    
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
        self._current_session_id = session_id
        
        # Create session folder
        session_folder = self._workspace_folder / session_id
        session_folder.mkdir(parents=True, exist_ok=True)
        
        # Save events to JSONL
        events_file = session_folder / "events.jsonl"
        with open(events_file, "a") as f:
            for event in self._event_buffer:
                f.write(json.dumps(event.to_dict()) + "\n")
        
        # Log before clearing buffer
        num_events = len(self._event_buffer)
        # Clear buffer after save
        self._event_buffer.clear()
        logger.info(f"Saved {num_events} events for session {session_id}")
    
    def read_since(self, checkpoint: int) -> Iterator[Event]:
        """
        Read events since checkpoint (for learning pipeline).
        
        Args:
            checkpoint: Starting index for reading events.
                Negative values are supported (e.g., -10 means "last 10 events").
                -1 means "last event only", -2 means "last 2 events", etc.
            
        Yields:
            Event objects since checkpoint
        """
        # First pass: collect all events to support negative checkpoints
        all_events: list[Event] = []
        
        # Read from all session folders
        for session_folder in self._workspace_folder.iterdir():
            if not session_folder.is_dir():
                continue
            
            events_file = session_folder / "events.jsonl"
            if not events_file.exists():
                continue
            
            with open(events_file) as f:
                for line in f:
                    try:
                        event_data = json.loads(line)
                        # Reconstruct Event from dict
                        event = Event(
                            type=event_data.get("type", "observation"),
                            timestamp=datetime.fromisoformat(event_data["timestamp"]),
                            agent_id=event_data.get("agent_id", ""),
                            session_id=event_data.get("session_id"),
                            data=event_data.get("data", {}),
                            metadata=event_data.get("metadata", {}),
                        )
                        all_events.append(event)
                    except Exception as e:
                        logger.warning(f"Failed to parse event: {e}")
                        continue
        
        # Convert negative checkpoint to positive index
        if checkpoint < 0:
            total_count = len(all_events)
            # Convert negative index: -1 = last event, -2 = second to last, etc.
            # Similar to Python list slicing: checkpoint = total_count + checkpoint
            checkpoint = max(0, total_count + checkpoint)
        
        # Yield events from checkpoint onwards
        for i in range(checkpoint, len(all_events)):
            yield all_events[i]

