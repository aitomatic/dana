"""
Unit tests for LocalTimelineRepository.

Tests the local file-based timeline repository with agent binding.
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
from dana.core.agent.timeline import TimelineEntry, TimelineEntryType
from dana.repositories import LocalTimelineRepository


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


class TestLocalTimelineRepositoryInitialization:
    """Test LocalTimelineRepository initialization."""

    def test_initialization_extracts_codec_from_agent(self):
        """Test initialization extracts codec from agent."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
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
            repository = LocalTimelineRepository(agent)
            
            assert repository._storage_config == config
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
            repository = LocalTimelineRepository(agent)
            
            assert repository._storage_config is not None
            assert isinstance(repository._storage_config, FileStorageConfig)
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_codec_prefix_logic_with_codec(self):
        """Test codec prefix logic when codec is provided."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
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
            repository = LocalTimelineRepository(agent)
            
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
            repository = LocalTimelineRepository(agent)
            
            assert repository._codec_prefix == "default"
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_calculates_events_path(self):
        """Test initialization calculates correct events path."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
            # Path should be: {codec_prefix}/{agent.__class__.__qualname__}__{filename}/events
            # Check path structure (doesn't need to exist yet)
            path_str = str(repository._events_path)
            assert "TestCodec" in path_str
            assert "MockAgent" in path_str
            assert "events" in path_str
            assert path_str.endswith("/events")
        finally:
            shutil.rmtree(temp_dir)


class TestLocalTimelineRepositorySave:
    """Test LocalTimelineRepository save method."""

    def test_save_creates_session_folder(self):
        """Test save creates session folder structure."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
            entries = [
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content="Test message",
                    timestamp=datetime.now(),
                )
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, entries)
            
            session_folder = repository._events_path / session_id
            assert session_folder.exists()
            assert session_folder.is_dir()
        finally:
            shutil.rmtree(temp_dir)

    def test_save_writes_timeline_json(self):
        """Test save writes correct timeline.json file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
            timestamp = datetime(2024, 1, 15, 10, 30, 0)
            entries = [
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content="Test message",
                    timestamp=timestamp,
                    metadata={"key": "value"},
                )
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, entries)
            
            timeline_file = repository._events_path / session_id / "timeline.json"
            assert timeline_file.exists()
            
            with open(timeline_file) as f:
                timeline_data = json.load(f)
            
            assert timeline_data["session_id"] == session_id
            assert timeline_data["agent_id"] == agent.object_id
            assert len(timeline_data["entries"]) == 1
            assert timeline_data["entries"][0]["type"] == "user_message"
            assert timeline_data["entries"][0]["content"] == "Test message"
            assert timeline_data["entries"][0]["metadata"] == {"key": "value"}
        finally:
            shutil.rmtree(temp_dir)

    def test_save_sanitizes_metadata(self):
        """Test save sanitizes non-serializable objects in metadata."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
            # Create a non-serializable object
            class NonSerializable:
                def __init__(self):
                    self.value = "test"
            
            non_serializable = NonSerializable()
            entries = [
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content="Test message",
                    timestamp=datetime.now(),
                    metadata={"obj": non_serializable},
                )
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, entries)
            
            timeline_file = repository._events_path / session_id / "timeline.json"
            with open(timeline_file) as f:
                timeline_data = json.load(f)
            
            # Metadata should be sanitized (converted to dict representation)
            metadata = timeline_data["entries"][0]["metadata"]
            assert "obj" in metadata
            assert isinstance(metadata["obj"], dict)
            assert "__class__" in metadata["obj"]
        finally:
            shutil.rmtree(temp_dir)

    def test_save_handles_multiple_entries(self):
        """Test save handles multiple entries correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
            entries = [
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content="Message 1",
                    timestamp=datetime.now(),
                ),
                TimelineEntry(
                    entry_type=TimelineEntryType.AGENT_RESPONSE,
                    content="Response 1",
                    timestamp=datetime.now(),
                ),
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, entries)
            
            timeline_file = repository._events_path / session_id / "timeline.json"
            with open(timeline_file) as f:
                timeline_data = json.load(f)
            
            assert len(timeline_data["entries"]) == 2
        finally:
            shutil.rmtree(temp_dir)


class TestLocalTimelineRepositoryRead:
    """Test LocalTimelineRepository read_session_entries method."""

    def test_read_session_entries_reads_correctly(self):
        """Test read_session_entries reads and parses entries correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
            timestamp = datetime(2024, 1, 15, 10, 30, 0)
            entries = [
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content="Test message",
                    timestamp=timestamp,
                    metadata={"key": "value"},
                )
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, entries)
            
            # Read back
            read_entries = list(repository.read_session_entries(session_id))
            
            assert len(read_entries) == 1
            assert read_entries[0].entry_type == TimelineEntryType.USER_MESSAGE
            assert read_entries[0].content == "Test message"
            assert read_entries[0].metadata == {"key": "value"}
        finally:
            shutil.rmtree(temp_dir)

    def test_read_session_entries_handles_missing_session(self):
        """Test read_session_entries handles missing session gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
            # Try to read non-existent session
            read_entries = list(repository.read_session_entries("non-existent-session"))
            
            assert len(read_entries) == 0
        finally:
            shutil.rmtree(temp_dir)

    def test_read_session_entries_handles_missing_file(self):
        """Test read_session_entries handles missing timeline.json file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
            # Create session folder but no timeline.json
            session_folder = repository._events_path / "test-session-001"
            session_folder.mkdir(parents=True, exist_ok=True)
            
            read_entries = list(repository.read_session_entries("test-session-001"))
            
            assert len(read_entries) == 0
        finally:
            shutil.rmtree(temp_dir)

    def test_read_session_entries_handles_invalid_json(self):
        """Test read_session_entries handles invalid JSON gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
            # Create session folder with invalid JSON
            session_folder = repository._events_path / "test-session-001"
            session_folder.mkdir(parents=True, exist_ok=True)
            timeline_file = session_folder / "timeline.json"
            timeline_file.write_text("invalid json {")
            
            # Should not raise exception, just return empty
            read_entries = list(repository.read_session_entries("test-session-001"))
            
            # Should handle gracefully (either empty or log warning)
            assert isinstance(read_entries, list)
        finally:
            shutil.rmtree(temp_dir)

    def test_read_session_entries_handles_multiple_entries(self):
        """Test read_session_entries reads multiple entries correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalTimelineRepository(agent)
            
            entries = [
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content="Message 1",
                    timestamp=datetime.now(),
                ),
                TimelineEntry(
                    entry_type=TimelineEntryType.AGENT_RESPONSE,
                    content="Response 1",
                    timestamp=datetime.now(),
                ),
            ]
            
            session_id = "test-session-001"
            repository.save(session_id, entries)
            
            read_entries = list(repository.read_session_entries(session_id))
            
            assert len(read_entries) == 2
            assert read_entries[0].content == "Message 1"
            assert read_entries[1].content == "Response 1"
        finally:
            shutil.rmtree(temp_dir)

