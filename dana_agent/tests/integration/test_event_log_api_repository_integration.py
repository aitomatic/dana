"""
Integration tests for EventLogAPI with repository pattern.

Tests the full save/read cycle with LocalEventRepository.
"""

from datetime import datetime
import tempfile
import shutil
from unittest.mock import Mock

import pytest

from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.common.schemas import Event
from dana.core.agent.components.event_log_api import EventLogAPI
from dana.core.agent.components.observer import ObserverProtocol
from dana.repositories import LocalEventRepository


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


class MockObserverForIntegration(ObserverProtocol):
    """Mock observer for integration testing."""
    def __init__(self, return_data=None):
        self.return_data = return_data or {}
        self.observe_count = 0

    def observe(self):
        """Mock observe method."""
        self.observe_count += 1
        return self.return_data

    def start(self) -> None:
        """Mock start method."""
        pass

    def stop(self) -> None:
        """Mock stop method."""
        pass


class TestEventLogAPIRepositoryIntegration:
    """Integration tests for EventLogAPI with repository."""

    def test_save_and_read_from_same_session(self):
        """Test saving and reading from the same session."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            observer = MockObserverForIntegration({"key": "value"})
            repository = LocalEventRepository(agent)
            event_log = EventLogAPI(
                agent=agent,
                codec=None,
                storage_config=config,
                observer=observer,
                repository=repository,
            )

            # Record an event
            event_log.observe_and_record()

            # Save
            session_id = agent._session_id
            event_log.save(session_id)

            # Read back (no session_id parameter needed)
            read_events = list(event_log.read_since(checkpoint=0))

            assert len(read_events) == 1
            assert read_events[0].data == {"key": "value"}
        finally:
            shutil.rmtree(temp_dir)

    def test_read_since_with_session_id_works_correctly(self):
        """Test read_since with session_id works correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            observer = MockObserverForIntegration({"event": 0})
            repository = LocalEventRepository(agent)
            event_log = EventLogAPI(
                agent=agent,
                codec=None,
                storage_config=config,
                observer=observer,
                repository=repository,
            )

            # Record multiple events
            for i in range(5):
                observer.return_data = {"event": i}
                event_log.observe_and_record()

            # Save
            session_id = agent._session_id
            event_log.save(session_id)

            # Read from checkpoint 2 (no session_id parameter needed)
            read_events = list(event_log.read_since(checkpoint=2))

            assert len(read_events) == 3
            assert read_events[0].data == {"event": 2}
            assert read_events[1].data == {"event": 3}
            assert read_events[2].data == {"event": 4}
        finally:
            shutil.rmtree(temp_dir)

    def test_checkpoint_logic_with_session_id(self):
        """Test checkpoint logic (negative index) with session_id."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            observer = MockObserverForIntegration({"event": 0})
            repository = LocalEventRepository(agent)
            event_log = EventLogAPI(
                agent=agent,
                codec=None,
                storage_config=config,
                observer=observer,
                repository=repository,
            )

            # Record multiple events
            for i in range(5):
                observer.return_data = {"event": i}
                event_log.observe_and_record()

            # Save
            session_id = agent._session_id
            event_log.save(session_id)

            # Read last 2 events (negative checkpoint, no session_id parameter needed)
            read_events = list(event_log.read_since(checkpoint=-2))

            assert len(read_events) == 2
            assert read_events[0].data == {"event": 3}
            assert read_events[1].data == {"event": 4}
        finally:
            shutil.rmtree(temp_dir)

    def test_event_log_api_auto_creates_repository_from_agent(self):
        """Test EventLogAPI automatically creates repository from agent."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            observer = MockObserverForIntegration({"key": "value"})
            # Create event_log with agent only (no repository)
            event_log = EventLogAPI(
                agent=agent,
                codec=None,
                storage_config=config,
                observer=observer,
            )

            # Should have repository
            assert event_log._repository is not None
            assert isinstance(event_log._repository, LocalEventRepository)

            # Should work
            event_log.observe_and_record()
            session_id = agent._session_id
            event_log.save(session_id)

            # Read back (no session_id parameter needed)
            read_events = list(event_log.read_since(checkpoint=0))
            assert len(read_events) == 1
            assert read_events[0].data == {"key": "value"}
        finally:
            shutil.rmtree(temp_dir)

