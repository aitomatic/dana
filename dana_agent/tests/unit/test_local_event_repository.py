"""
Unit tests for LocalEventRepository.

Tests the local file-based event repository with agent binding.
"""

from datetime import datetime
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import MagicMock, Mock

import pytest


# Mock the problematic import before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

# Now import normally
from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.common.schemas import Event
from dana.repositories import LocalEventRepository


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    def __init__(self, codec=None, storage_config=None, **kwargs):
        super().__init__(agent_type="test_agent", agent_id="test-agent-123", **kwargs)
        # Mock codec
        if codec is None:
            self._codec = Mock()
            self._codec.__qualname__ = "TestCodec"
        else:
            self._codec = codec
        # Mock storage_config
        if storage_config is None:
            self._storage_config = FileStorageConfig(workspace_folder=tempfile.mkdtemp())
        else:
            self._storage_config = storage_config


class TestLocalEventRepositoryInitialization:
    """Test LocalEventRepository initialization."""

    def test_initialization_extracts_codec_from_agent(self):
        """Test initialization extracts codec from agent."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            assert repository._codec is not None
            assert repository._codec.__qualname__ == "TestCodec"
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_extracts_storage_config_from_agent(self):
        """Test initialization extracts storage_config from agent."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            assert repository.storage_config == config
            assert repository._workspace_folder == Path(temp_dir)
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_creates_default_storage_config_if_missing(self):
        """Test initialization creates default storage_config if agent doesn't have it."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            # Remove storage_config
            delattr(agent, "_storage_config")
            repository = LocalEventRepository(config, agent)
            
            assert repository.storage_config is not None
            assert isinstance(repository.storage_config, FileStorageConfig)
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_codec_prefix_logic_with_codec(self):
        """Test codec prefix logic when codec is provided."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            assert repository._codec_prefix == "TestCodec"
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_codec_prefix_logic_without_codec(self):
        """Test codec prefix logic when codec is None."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config, codec=None)
            # Ensure codec is actually None
            agent._codec = None
            repository = LocalEventRepository(config, agent)
            
            assert repository._codec_prefix == "default"
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_codec_prefix_logic_with_magic_codec(self):
        """Test codec prefix logic when codec has 'magic' in qualname."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            mock_codec = Mock()
            mock_codec.__qualname__ = "magic_codec"
            agent = MockAgent(storage_config=config, codec=mock_codec)
            repository = LocalEventRepository(config, agent)
            
            assert repository._codec_prefix == "default"
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_calculates_events_path(self):
        """Test initialization calculates correct events path."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            # Path should be: {codec_prefix}/{agent.__class__.__qualname__}__{filename}/events
            # Check path structure (doesn't need to exist yet)
            path_str = str(repository._events_path)
            assert "TestCodec" in path_str
            assert "MockAgent" in path_str
            assert "events" in path_str
            assert path_str.endswith("/events")
        finally:
            shutil.rmtree(temp_dir)


class TestLocalEventRepositorySave:
    """Test LocalEventRepository save method."""

    def test_save_creates_session_folder(self):
        """Test save creates session folder structure."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            events = [
                Event(
                    type="observation",
                    data={"key": "value"},
                    timestamp=datetime.now(),
                )
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, events)
            
            session_folder = repository._events_path / session_id
            assert session_folder.exists()
            assert session_folder.is_dir()
        finally:
            shutil.rmtree(temp_dir)

    def test_save_writes_events_jsonl(self):
        """Test save writes correct events.jsonl file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            timestamp = datetime(2024, 1, 15, 10, 30, 0)
            events = [
                Event(
                    type="observation",
                    data={"key": "value"},
                    timestamp=timestamp,
                    agent_id=agent.object_id,
                    session_id="test-session-001",
                )
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, events)
            
            events_file = repository._events_path / session_id / "events.jsonl"
            assert events_file.exists()
            
            # Read and verify JSONL content
            with open(events_file) as f:
                lines = f.readlines()
                assert len(lines) == 1
                event_data = json.loads(lines[0])
                assert event_data["type"] == "observation"
                assert event_data["data"] == {"key": "value"}
                assert event_data["agent_id"] == agent.object_id
        finally:
            shutil.rmtree(temp_dir)

    def test_save_handles_multiple_events(self):
        """Test save handles multiple events correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            events = [
                Event(
                    type="observation",
                    data={"event": 1},
                    timestamp=datetime.now(),
                ),
                Event(
                    type="observation",
                    data={"event": 2},
                    timestamp=datetime.now(),
                ),
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, events)
            
            events_file = repository._events_path / session_id / "events.jsonl"
            with open(events_file) as f:
                lines = f.readlines()
                assert len(lines) == 2
        finally:
            shutil.rmtree(temp_dir)

    def test_save_appends_to_existing_file(self):
        """Test save appends to existing events.jsonl file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            session_id = "test-session-001"
            
            # First save
            events1 = [Event(type="observation", data={"event": 1}, timestamp=datetime.now())]
            repository.save(session_id, events1)
            
            # Second save (should append)
            events2 = [Event(type="observation", data={"event": 2}, timestamp=datetime.now())]
            repository.save(session_id, events2)
            
            events_file = repository._events_path / session_id / "events.jsonl"
            with open(events_file) as f:
                lines = f.readlines()
                assert len(lines) == 2
        finally:
            shutil.rmtree(temp_dir)


class TestLocalEventRepositoryRead:
    """Test LocalEventRepository read_session_events method."""

    def test_read_session_events_reads_correctly(self):
        """Test read_session_events reads and parses events correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            timestamp = datetime(2024, 1, 15, 10, 30, 0)
            events = [
                Event(
                    type="observation",
                    data={"key": "value"},
                    timestamp=timestamp,
                    agent_id=agent.object_id,
                    session_id="test-session-001",
                )
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, events)
            
            # Read back
            read_events = list(repository.read_session_events(session_id))
            
            assert len(read_events) == 1
            assert read_events[0].type == "observation"
            assert read_events[0].data == {"key": "value"}
            assert read_events[0].agent_id == agent.object_id
        finally:
            shutil.rmtree(temp_dir)

    def test_read_session_events_handles_missing_session(self):
        """Test read_session_events handles missing session gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            # Try to read non-existent session
            read_events = list(repository.read_session_events("non-existent-session"))
            
            assert len(read_events) == 0
        finally:
            shutil.rmtree(temp_dir)

    def test_read_session_events_handles_missing_file(self):
        """Test read_session_events handles missing events.jsonl file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            # Create session folder but no events.jsonl
            session_folder = repository._events_path / "test-session-001"
            session_folder.mkdir(parents=True, exist_ok=True)
            
            read_events = list(repository.read_session_events("test-session-001"))
            
            assert len(read_events) == 0
        finally:
            shutil.rmtree(temp_dir)

    def test_read_session_events_handles_invalid_json(self):
        """Test read_session_events handles invalid JSON gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            # Create session folder with invalid JSON
            session_folder = repository._events_path / "test-session-001"
            session_folder.mkdir(parents=True, exist_ok=True)
            events_file = session_folder / "events.jsonl"
            events_file.write_text("invalid json {")
            
            # Should not raise exception, just skip invalid lines
            read_events = list(repository.read_session_events("test-session-001"))
            
            # Should handle gracefully (either empty or log warning)
            assert isinstance(read_events, list)
        finally:
            shutil.rmtree(temp_dir)

    def test_read_session_events_handles_multiple_events(self):
        """Test read_session_events reads multiple events correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalEventRepository(config, agent)
            
            events = [
                Event(
                    type="observation",
                    data={"event": 1},
                    timestamp=datetime.now(),
                ),
                Event(
                    type="observation",
                    data={"event": 2},
                    timestamp=datetime.now(),
                ),
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, events)
            
            read_events = list(repository.read_session_events(session_id))
            
            assert len(read_events) == 2
            assert read_events[0].data == {"event": 1}
            assert read_events[1].data == {"event": 2}
        finally:
            shutil.rmtree(temp_dir)

