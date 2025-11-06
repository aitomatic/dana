from collections.abc import Iterator
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
    def __init__(self, agent: BaseAgent):
        """Initialize with agent (extracts codec and storage_config internally)."""
        ...

    def save(self, session_id: str, entries: list["TimelineEntry"]) -> None:
        """Save timeline entries for a session."""
        ...

    def read_session_entries(self, session_id: str) -> Iterator["TimelineEntry"]:
        """Read timeline entries for a specific session."""
        ...


class EventRepositoryProtocol(Protocol):
    def __init__(self, agent: BaseAgent):
        """Initialize with agent (extracts codec and storage_config internally)."""
        ...

    def save(self, session_id: str, events: list["Event"]) -> None:
        """Save events for a session."""
        ...

    def read_session_events(self, session_id: str) -> Iterator["Event"]:
        """Read events for a specific session."""
        ...