from collections.abc import Iterator
from datetime import datetime
import inspect
import json
import os
from pathlib import Path

from structlog import get_logger

from dana.common.base_war import BaseWAR
from dana.common.protocols.war import AgentProtocol, ResourceProtocol, WorkflowProtocol
from dana.common.schemas import Event, PromptVersionSnapshot
from dana.config.storage_config import FileStorageConfig
from dana.core.agent.base_agent import BaseAgent
from dana.core.agent.timeline import TimelineEntry, TimelineEntryType, _sanitize_for_json

from .repository_protocol import EventRepositoryProtocol, PromptRepositoryProtocol, TimelineRepositoryProtocol


logger = get_logger()


class LocalRepositoryMixin:
    """
    Mixin class providing shared functionality for local file-based repositories.
    
    Provides common methods for codec extraction, codec prefix computation,
    and storage config extraction from agents.
    """

    def _extract_codec_from_agent(self, agent: BaseAgent):
        """
        Extract codec from agent.
        
        Args:
            agent: Agent instance
            
        Returns:
            Codec instance or None
        """
        return getattr(agent, "_codec", None)

    def _extract_storage_config_from_agent(self, agent: BaseAgent) -> FileStorageConfig:
        """
        Extract storage_config from agent, or create default if not found.
        
        Args:
            agent: Agent instance
            
        Returns:
            FileStorageConfig instance
        """
        storage_config = getattr(agent, "_storage_config", None)
        if storage_config is None:
            return FileStorageConfig()
        return storage_config

    def _get_codec_prefix(self, agent: BaseAgent) -> str:
        """
        Compute codec prefix from agent's codec.
        
        Returns "default" if codec is None or has "magic" in qualname,
        otherwise returns the codec's qualname.
        
        Args:
            agent: Agent instance
            
        Returns:
            Codec prefix string
        """
        codec = self._extract_codec_from_agent(agent)
        if codec is None or "magic" in str(codec.__qualname__):
            return "default"
        return codec.__qualname__

    def _get_relative_storage_path(self, agent: BaseAgent) -> str:
        _codec_str = self._get_codec_prefix(agent)
        filepath = inspect.getfile(agent.__class__)
        filename = Path(filepath).stem
        return f"{_codec_str}/{agent.__class__.__qualname__}__{filename}"


class LocalPromptRepository(LocalRepositoryMixin, PromptRepositoryProtocol):
    def __init__(self, storage_config: FileStorageConfig, agent: BaseAgent, component: BaseWAR | None = None):
        self.storage_config = storage_config
        self._agent = agent
        self._component = component
        self._workspace_folder = Path(self.storage_config.workspace_folder)
        # Compute and cache the prompt path
        self._prompt_path = self._get_relative_prompt_path()

    def _get_relative_prompt_path(self) -> Path:
        _codec_str = self._get_codec_prefix(self._agent)
        if self._component is None:
            # NOTE : For agent, we only store system prompt template
            target_path = Path(self._workspace_folder / self._get_relative_storage_path(self._agent) / "prompts" / "system_prompt_template")
        else:
            # NOTE : For resource and workflow, we store prompts in the respective subfolders
            if isinstance(self._component, AgentProtocol):
                subfolder = "agents"
            elif isinstance(self._component, ResourceProtocol):
                subfolder = "resources"
            elif isinstance(self._component, WorkflowProtocol):
                subfolder = "workflows"
            else:
                raise ValueError(f"Invalid component type: {type(self._component)}. Only accepts instance of subclasses of {ResourceProtocol.__name__}, {AgentProtocol.__name__}, {WorkflowProtocol.__name__}")
            target_path = Path(self._workspace_folder / self._get_relative_storage_path(self._agent) / "prompts" / subfolder / self._component.__class__.__qualname__)
        target_path.mkdir(parents=True, exist_ok=True)
        return target_path

    def has_any_versions(self) -> bool:
        return len(self.list_versions()) > 0

    def get_active(self, error_if_not_found: bool = True) -> PromptVersionSnapshot | None:
        """Get active version snapshot with optional error handling."""
        if not error_if_not_found:
            if not self.has_any_versions():
                return None
        try:
            version = self._get_current_version()
            return self.load_snapshot(version, error_if_not_found)
        except ValueError:
            if error_if_not_found:
                raise
            return None

    def list_versions(self) -> list[str]:
        def _filter(item: str) -> bool:
            return item.startswith("v") and item[1:].isdigit()
        versions_folder = self._prompt_path / "versions"
        if not versions_folder.exists():
            return []
        items = [_path.stem for _path in versions_folder.iterdir()]
        return sorted([item for item in items if _filter(item)], key=lambda x: int(x.split("v")[1]))

    def load_snapshot(self, version: str, error_if_not_found: bool = True) -> PromptVersionSnapshot | None:
        """Load snapshot with optional error handling."""
        versions_folder = self._prompt_path / "versions"
        versions_folder.mkdir(parents=True, exist_ok=True)
        content_file = versions_folder / f"{version}.prompt"
        
        if not content_file.exists():
            if error_if_not_found:
                raise ValueError(f"Version {version} not found")
            return None
        
        created_at = os.path.getctime(content_file)
        updated_at = os.path.getmtime(content_file)
        content = content_file.read_text()
        
        return PromptVersionSnapshot(
            version=version,
            content=content,
            created_at=datetime.fromtimestamp(created_at),
            updated_at=datetime.fromtimestamp(updated_at),
            provenance=self._load_provenances().get(version, {}),
            metrics=self._load_metrics().get(version, {}),
        )

    def set_active_version(self, version: str) -> None:
        version_file = self._prompt_path / "version.txt"
        version_file.write_text(version)

    def set_active(self, version: str) -> None:
        """Alias for set_active_version for backward compatibility."""
        self.set_active_version(version)

    def create_snapshot(self, content: str, provenance: dict, metrics: dict) -> PromptVersionSnapshot:
        try:
            current_version = self._get_latest_version()
            new_version_number = int(current_version.split("v")[1]) + 1
            version = f"v{new_version_number}"
        except ValueError:
            version = "v1"
        
        versions_folder = self._prompt_path / "versions"
        versions_folder.mkdir(parents=True, exist_ok=True)
        content_file = versions_folder / f"{version}.prompt"
        
        provenances = self._load_provenances()
        provenances[version] = provenance
        metrics_dict = self._load_metrics()
        metrics_dict[version] = metrics
        
        content_file.write_text(content)
        
        provenance_file = self._prompt_path / "provenance.json"
        metrics_file = self._prompt_path / "metrics.json"
        provenance_file.write_text(json.dumps(provenances, indent=4))
        metrics_file.write_text(json.dumps(metrics_dict, indent=4))
        
        return PromptVersionSnapshot(
            version=version,
            content=content,
            created_at=datetime.fromtimestamp(os.path.getctime(content_file)),
            updated_at=datetime.fromtimestamp(os.path.getmtime(content_file)),
            provenance=provenance,
            metrics=metrics,
        )
    
    def _load_provenances(self) -> dict:
        provenance_file = self._prompt_path / "provenance.json"
        if provenance_file.exists():
            return json.loads(provenance_file.read_text())
        return {}

    def _load_metrics(self) -> dict:
        metrics_file = self._prompt_path / "metrics.json"
        if metrics_file.exists():
            return json.loads(metrics_file.read_text())
        return {}

    def _get_current_version(self) -> str:
        version_file = self._prompt_path / "version.txt"
        if version_file.exists():
            return version_file.read_text().strip()
        return self._get_latest_version()

    def _get_latest_version(self) -> str:
        versions = self.list_versions()
        if versions:
            return versions[-1]
        raise ValueError("No versions found")





class LocalTimelineRepository(LocalRepositoryMixin, TimelineRepositoryProtocol):
    def __init__(self, agent: BaseAgent):
        """
        Initialize timeline repository with agent.

        Extracts codec and storage_config from agent, following same pattern as LocalPromptRepository.

        Args:
            agent: Agent instance (extracts codec and storage_config from agent)
        """
        self._agent = agent
        # Extract codec from agent (same logic as LocalPromptRepository)
        self._codec = self._extract_codec_from_agent(self._agent)
        # Extract storage_config from agent, or create default
        self._storage_config = self._extract_storage_config_from_agent(self._agent)

        self._workspace_folder = Path(self._storage_config.workspace_folder)
        # Compute codec prefix using mixin method
        self._codec_prefix = self._get_codec_prefix(self._agent)

        self._events_path = self._get_events_path()

    def _get_events_path(self) -> Path:
        """Calculate the events folder path based on agent and codec."""
        relative_path = f"{self._get_relative_storage_path(self._agent)}/events"
        return self._workspace_folder / relative_path

    def save(self, session_id: str, entries: list[TimelineEntry]) -> None:
        """
        Save timeline entries for a session.

        Args:
            session_id: Session identifier
            entries: List of TimelineEntry objects to save
        """
        # Create session folder
        session_folder = self._events_path / session_id
        session_folder.mkdir(parents=True, exist_ok=True)

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
                    "metadata": _sanitize_for_json(entry.metadata),
                }
                for entry in entries
            ],
        }
        with open(timeline_file, "w") as f:
            json.dump(timeline_data, f, indent=2)

        logger.info(f"Saved timeline with {len(entries)} entries for session {session_id}")

    def read_session_entries(self, session_id: str) -> Iterator[TimelineEntry]:
        """
        Read timeline entries for a specific session.

        Args:
            session_id: Session identifier

        Yields:
            TimelineEntry objects from the session
        """
        session_folder = self._events_path / session_id
        timeline_file = session_folder / "timeline.json"

        if not timeline_file.exists():
            return

        try:
            with open(timeline_file) as f:
                timeline_data = json.load(f)
                entries_data = timeline_data.get("entries", [])
                for entry_data in entries_data:
                    try:
                        entry_type_str = entry_data.get("type", "user_message")
                        entry_type = TimelineEntryType(entry_type_str)
                        entry = TimelineEntry(
                            entry_type=entry_type,
                            timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                            content=entry_data.get("content", ""),
                            metadata=entry_data.get("metadata", {}),
                        )
                        yield entry
                    except Exception as e:
                        logger.warning(f"Failed to parse timeline entry: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Failed to read timeline file {timeline_file}: {e}")


class LocalEventRepository(LocalRepositoryMixin, EventRepositoryProtocol):
    def __init__(self, agent: BaseAgent):
        """
        Initialize event repository with agent.

        Extracts codec and storage_config from agent, following same pattern as LocalTimelineRepository.

        Args:
            agent: Agent instance (extracts codec and storage_config from agent)
        """
        self._agent = agent
        # Extract codec from agent (same logic as LocalTimelineRepository)
        self._codec = self._extract_codec_from_agent(self._agent)
        # Extract storage_config from agent, or create default
        self._storage_config = self._extract_storage_config_from_agent(self._agent)

        self._workspace_folder = Path(self._storage_config.workspace_folder)
        # Compute codec prefix using mixin method
        self._codec_prefix = self._get_codec_prefix(self._agent)

        self._events_path = self._get_events_path()

    def _get_events_path(self) -> Path:
        """Calculate the events folder path based on agent and codec."""
        relative_path = f"{self._get_relative_storage_path(self._agent)}/events"
        return self._workspace_folder / relative_path

    def save(self, session_id: str, events: list[Event]) -> None:
        """
        Save events for a session.

        Args:
            session_id: Session identifier
            events: List of Event objects to save
        """
        # Create session folder
        session_folder = self._events_path / session_id
        session_folder.mkdir(parents=True, exist_ok=True)

        # Save events to JSONL (one event per line)
        events_file = session_folder / "events.jsonl"
        with open(events_file, "a") as f:
            for event in events:
                f.write(json.dumps(event.to_dict()) + "\n")

        logger.info(f"Saved {len(events)} events for session {session_id}")

    def read_session_events(self, session_id: str) -> Iterator[Event]:
        """
        Read events for a specific session.

        Args:
            session_id: Session identifier

        Yields:
            Event objects from the session
        """
        session_folder = self._events_path / session_id
        events_file = session_folder / "events.jsonl"

        if not events_file.exists():
            return

        try:
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
                        yield event
                    except Exception as e:
                        logger.warning(f"Failed to parse event: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Failed to read events file {events_file}: {e}")
