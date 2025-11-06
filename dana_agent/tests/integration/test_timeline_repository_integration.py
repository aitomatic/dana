"""
Integration tests for Timeline with repository pattern.

Tests the full save/read cycle with LocalTimelineRepository.
"""

from datetime import datetime
import tempfile
import shutil
from unittest.mock import Mock

import pytest

from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.core.agent.timeline import Timeline, TimelineEntry, TimelineEntryType
from dana.repositories import LocalTimelineRepository


class MockAgentForIntegration(BaseAgent):
    """Mock agent for integration testing."""
    def __init__(self, codec=None, storage_config=None, **kwargs):
        super().__init__(agent_type="test_agent", agent_id="test-agent-123", **kwargs)
        if codec is None:
            self._codec = Mock()
            self._codec.__qualname__ = "TestCodec"
        else:
            self._codec = codec
        if storage_config is None:
            self._storage_config = FileStorageConfig(workspace_folder=tempfile.mkdtemp())
        else:
            self._storage_config = storage_config
        self._session_id = "test-session-001"


class TestTimelineRepositoryIntegration:
    """Integration tests for Timeline with repository."""

    def test_save_and_read_from_same_session(self):
        """Test saving and reading from the same session."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            repository = LocalTimelineRepository(agent)
            timeline = Timeline(max_context_tokens=1000, repository=repository, agent=agent)
            
            # Add entries
            entry1 = TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Message 1",
                timestamp=datetime.now(),
            )
            entry2 = TimelineEntry(
                entry_type=TimelineEntryType.AGENT_RESPONSE,
                content="Response 1",
                timestamp=datetime.now(),
            )
            timeline.add_entry(entry1)
            timeline.add_entry(entry2)
            
            # Save
            session_id = agent._session_id
            timeline.save(session_id)
            
            # Read back (no session_id parameter needed)
            read_entries = list(timeline.read_since(checkpoint=0))
            
            assert len(read_entries) == 2
            assert read_entries[0].content == "Message 1"
            assert read_entries[1].content == "Response 1"
        finally:
            shutil.rmtree(temp_dir)

    def test_read_since_with_session_id_works_correctly(self):
        """Test read_since with session_id works correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            repository = LocalTimelineRepository(agent)
            timeline = Timeline(max_context_tokens=1000, repository=repository, agent=agent)
            
            # Add multiple entries
            for i in range(5):
                entry = TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content=f"Message {i}",
                    timestamp=datetime.now(),
                )
                timeline.add_entry(entry)
            
            # Save
            session_id = agent._session_id
            timeline.save(session_id)
            
            # Read from checkpoint 2 (no session_id parameter needed)
            read_entries = list(timeline.read_since(checkpoint=2))
            
            assert len(read_entries) == 3
            assert read_entries[0].content == "Message 2"
            assert read_entries[1].content == "Message 3"
            assert read_entries[2].content == "Message 4"
        finally:
            shutil.rmtree(temp_dir)

    def test_checkpoint_logic_with_session_id(self):
        """Test checkpoint logic (negative index) with session_id."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            repository = LocalTimelineRepository(agent)
            timeline = Timeline(max_context_tokens=1000, repository=repository, agent=agent)
            
            # Add multiple entries
            for i in range(5):
                entry = TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content=f"Message {i}",
                    timestamp=datetime.now(),
                )
                timeline.add_entry(entry)
            
            # Save
            session_id = agent._session_id
            timeline.save(session_id)
            
            # Read last 2 entries (negative checkpoint, no session_id parameter needed)
            read_entries = list(timeline.read_since(checkpoint=-2))
            
            assert len(read_entries) == 2
            assert read_entries[0].content == "Message 3"
            assert read_entries[1].content == "Message 4"
        finally:
            shutil.rmtree(temp_dir)

    def test_timeline_auto_creates_repository_from_agent(self):
        """Test Timeline automatically creates repository from agent."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            # Create timeline with agent only (no repository)
            timeline = Timeline(max_context_tokens=1000, agent=agent)
            
            # Should have repository
            assert timeline._repository is not None
            assert isinstance(timeline._repository, LocalTimelineRepository)
            
            # Should work
            entry = TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Test message",
                timestamp=datetime.now(),
            )
            timeline.add_entry(entry)
            session_id = agent._session_id
            timeline.save(session_id)
            
            # Read back (no session_id parameter needed)
            read_entries = list(timeline.read_since(checkpoint=0))
            assert len(read_entries) == 1
            assert read_entries[0].content == "Test message"
        finally:
            shutil.rmtree(temp_dir)

