from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from dana.common.base_war import BaseWAR
from dana.common.schemas import PromptVersionSnapshot
from dana.config.storage_config import StorageConfig
from dana.core.agent.base_agent import BaseAgent


if TYPE_CHECKING:
    from dana.common.schemas import Event
    from dana.core.agent.timeline import TimelineEntry


class PromptRepositoryProtocol(Protocol):
    def __init__(self, storage_config: StorageConfig, agent: BaseAgent, component: BaseWAR | None = None):
        ...

    @classmethod
    def instantiate(cls, storage_config: StorageConfig, agent: BaseAgent, component: BaseWAR | None = None) -> PromptRepositoryProtocol:
        return cls(storage_config, agent, component)
    
    def has_any_versions(self) -> bool:
        ...
    
    def get_active(self, error_if_not_found: bool = True) -> PromptVersionSnapshot | None:
        ...
    
    def list_versions(self) -> list[str]:
        ...

    def load_snapshot(self, version: str, error_if_not_found: bool = True) -> PromptVersionSnapshot | None:
        ...

    def set_active_version(self, version: str) -> None:
        ...

    def set_active(self, version: str) -> None:
        """Alias for set_active_version for backward compatibility."""
        ...

    def create_snapshot(self, content: str, provenance: dict, metrics: dict) -> PromptVersionSnapshot:
        ...


class TimelineRepositoryProtocol(Protocol):
    def __init__(self, storage_config: StorageConfig, agent: BaseAgent):
        """Initialize with storage_config and agent."""
        ...

    @classmethod
    def instantiate(cls, storage_config: StorageConfig, agent: BaseAgent) -> TimelineRepositoryProtocol:
        return cls(storage_config, agent)

    def save(self, session_id: str, entries: list[TimelineEntry]) -> None:
        """Save timeline entries for a session."""
        ...

    def read_session_entries(self, session_id: str) -> Iterator[TimelineEntry]:
        """Read timeline entries for a specific session."""
        ...


class EventRepositoryProtocol(Protocol):
    def __init__(self, storage_config: StorageConfig, agent: BaseAgent):
        """Initialize with storage_config and agent."""
        ...

    @classmethod
    def instantiate(cls, storage_config: StorageConfig, agent: BaseAgent) -> EventRepositoryProtocol:
        return cls(storage_config, agent)

    def save(self, session_id: str, events: list[Event]) -> None:
        """Save events for a session."""
        ...

    def read_session_events(self, session_id: str) -> Iterator[Event]:
        """Read events for a specific session."""
        ...


class LearningRepositoryProtocol(Protocol):
    def __init__(self, storage_config: StorageConfig, agent: BaseAgent):
        """Initialize with storage_config and agent."""
        ...

    @classmethod
    def instantiate(cls, storage_config: StorageConfig, agent: BaseAgent) -> LearningRepositoryProtocol:
        return cls(storage_config, agent)

    def save_acquisitive_loop(self, session_id: str, loop_data: dict, loop_id: str, timestamp: datetime) -> None:
        """Save acquisitive learning loop data for a session."""
        ...

    def load_acquisitive_loops(self, session_id: str) -> list[str]:
        """Load acquisitive learning loops for a session, returns list of learning_note strings."""
        ...

    def save_episodic_learning(self, session_id: str, content: str) -> None:
        """Save episodic learning content for a session."""
        ...

    def load_episodic_learning(self, session_id: str) -> str | None:
        """Load episodic learning content for a session."""
        ...

    def save_feedback(self, session_id: str, content: str) -> None:
        """Save feedback content for a session."""
        ...

    def load_feedback(self, session_id: str) -> str | None:
        """Load feedback content for a session."""
        ...