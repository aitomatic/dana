"""
EventLog API for managing observation events and timeline persistence.

This module provides EventLogAPI following the LocalPromptAPI pattern.
Events come ONLY from Observer.observe() - no action events, no tool call events.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, TYPE_CHECKING
from uuid import uuid4
import inspect
import json

from dana.config.storage_config import FileStorageConfig
from dana.core.agent.timeline import Timeline
from structlog import get_logger

if TYPE_CHECKING:
    from dana.core.agent.base_agent import BaseAgent
    from dana.core.knowledge.prompts.codecs import AbstractCodec

from .observer import ObserverProtocol

logger = get_logger()


@dataclass
class Event:
    """
    Single observation event in the event log.
    
    NOTE: Events ONLY come from Observer. No actions, tool calls, or feedback.
    Events = Observations from environment/sensors only.
    """
    type: str = "observation"  # Always "observation" - events only from observer
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: str = ""
    session_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)  # Observer data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(uuid4()),
            "type": self.type,  # Always "observation"
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "data": self.data,  # Observer data (e.g., sensor readings)
            "metadata": self.metadata,
        }


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
        codec: type["AbstractCodec"],
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
        self._storage_config = storage_config
        self._observer = observer
        self._current_session_id: Optional[str] = None
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
        return f"{self._codec.__qualname__}/{self._agent.__class__.__qualname__}__{filename}/events"
    
    def observe_and_record(self) -> Optional[Event]:
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
    
    def save(self, timeline: Timeline, session_id: str) -> None:
        """
        Save events and timeline for a session.
        
        Args:
            timeline: Timeline to save
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
        
        # Save timeline to JSON
        timeline_file = session_folder / "timeline.json"
        timeline_data = {
            "session_id": session_id,
            "agent_id": self._agent.object_id,
            "agent_type": self._agent.agent_type if hasattr(self._agent, "agent_type") else None,
            "entries": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "type": entry.entry_type.value,
                    "content": entry.content,
                    "metadata": entry.metadata,
                }
                for entry in timeline.timeline
            ]
        }
        with open(timeline_file, "w") as f:
            json.dump(timeline_data, f, indent=2)
        
        # Log before clearing buffer
        num_events = len(self._event_buffer)
        # Clear buffer after save
        self._event_buffer.clear()
        logger.info(f"Saved {num_events} events and timeline for session {session_id}")
    
    def read_since(self, checkpoint: int) -> Iterator[Event]:
        """
        Read events since checkpoint (for learning pipeline).
        
        Args:
            checkpoint: Starting index for reading events
            
        Yields:
            Event objects since checkpoint
        """
        # Read from all session folders
        for session_folder in self._workspace_folder.iterdir():
            if not session_folder.is_dir():
                continue
            
            events_file = session_folder / "events.jsonl"
            if not events_file.exists():
                continue
            
            with open(events_file, "r") as f:
                for i, line in enumerate(f):
                    if i >= checkpoint:
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
                            yield event
                        except Exception as e:
                            logger.warning(f"Failed to parse event at line {i}: {e}")
                            continue

