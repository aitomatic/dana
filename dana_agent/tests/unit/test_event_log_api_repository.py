"""
Unit tests for EventLogAPI with repository pattern.

Tests EventLogAPI using LocalEventRepository.
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


class MockAgentForEventAPI(BaseAgent):
    """Mock agent for EventLogAPI testing."""
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


class MockObserver(ObserverProtocol):
    """Mock observer for testing."""
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


class TestEventLogAPIWithRepository:
    """Test EventLogAPI with repository pattern."""

    def test_event_log_api_initialization_with_repository(self):
        """Test EventLogAPI creates repository from agent."""
        agent = MockAgentForEventAPI()
        observer = MockObserver()
        event_log = EventLogAPI(
            agent=agent,
            codec=None,
            observer=observer,
        )

        assert event_log._repository is not None
        assert isinstance(event_log._repository, LocalEventRepository)
        assert event_log._event_buffer == []

    def test_event_log_api_initialization_creates_default_repository(self):
        """Test EventLogAPI creates default repository from agent if not provided."""
        agent = MockAgentForEventAPI()
        observer = MockObserver()
        event_log = EventLogAPI(
            agent=agent,
            codec=None,
            observer=observer,
        )

        assert event_log._repository is not None
        assert isinstance(event_log._repository, LocalEventRepository)
        assert event_log._repository._agent == agent

    def test_event_log_api_save_uses_repository(self):
        """Test EventLogAPI.save() uses repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForEventAPI(storage_config=config)
            observer = MockObserver({"key": "value"})
            event_log = EventLogAPI(
                agent=agent,
                codec=None,
                observer=observer,
            )

            # Record an event
            event_log.observe_and_record()

            session_id = "test-session-001"
            event_log.save(session_id)

            # Verify repository was called (check file exists)
            session_folder = event_log._repository._events_path / session_id
            events_file = session_folder / "events.jsonl"
            assert events_file.exists()
        finally:
            shutil.rmtree(temp_dir)

    def test_event_log_api_read_since_extracts_session_id_from_agent(self):
        """Test EventLogAPI.read_since() extracts session_id from agent."""
        agent = MockAgentForEventAPI()
        agent._session_id = "test-session-001"
        observer = MockObserver()
        event_log = EventLogAPI(
            agent=agent,
            codec=None,
            observer=observer,
        )

        # Should work without session_id parameter
        read_events = list(event_log.read_since(checkpoint=0))
        assert isinstance(read_events, list)

    def test_event_log_api_read_since_with_session_id(self):
        """Test EventLogAPI.read_since() works by extracting session_id from agent."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForEventAPI(storage_config=config)
            agent._session_id = "test-session-001"
            observer = MockObserver({"key": "value"})
            event_log = EventLogAPI(
                agent=agent,
                codec=None,
                observer=observer,
            )

            # Record and save an event
            event_log.observe_and_record()
            session_id = agent._session_id
            event_log.save(session_id)

            # Read back (no session_id parameter needed)
            read_events = list(event_log.read_since(checkpoint=0))
            assert len(read_events) == 1
            assert read_events[0].data == {"key": "value"}
        finally:
            shutil.rmtree(temp_dir)

    def test_event_log_api_read_since_checkpoint_negative(self):
        """Test EventLogAPI.read_since() with negative checkpoint."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForEventAPI(storage_config=config)
            agent._session_id = "test-session-001"
            observer = MockObserver({"event": 0})
            event_log = EventLogAPI(
                agent=agent,
                codec=None,
                observer=observer,
            )

            # Record multiple events
            for i in range(5):
                observer.return_data = {"event": i}
                event_log.observe_and_record()

            session_id = agent._session_id
            event_log.save(session_id)

            # Read last 2 events (no session_id parameter needed)
            read_events = list(event_log.read_since(checkpoint=-2))
            assert len(read_events) == 2
            assert read_events[0].data == {"event": 3}
            assert read_events[1].data == {"event": 4}
        finally:
            shutil.rmtree(temp_dir)

    def test_event_log_api_read_since_checkpoint_positive(self):
        """Test EventLogAPI.read_since() with positive checkpoint."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForEventAPI(storage_config=config)
            agent._session_id = "test-session-001"
            observer = MockObserver({"event": 0})
            event_log = EventLogAPI(
                agent=agent,
                codec=None,
                observer=observer,
            )

            # Record multiple events
            for i in range(5):
                observer.return_data = {"event": i}
                event_log.observe_and_record()

            session_id = agent._session_id
            event_log.save(session_id)

            # Read from index 2 onwards (no session_id parameter needed)
            read_events = list(event_log.read_since(checkpoint=2))
            assert len(read_events) == 3
            assert read_events[0].data == {"event": 2}
        finally:
            shutil.rmtree(temp_dir)

    def test_event_log_api_read_since_error_when_no_repository(self):
        """Test EventLogAPI.read_since() raises error when repository is None."""
        agent = MockAgentForEventAPI()
        observer = MockObserver()
        event_log = EventLogAPI(
            agent=agent,
            codec=None,
            observer=observer,
        )
        # Manually set repository to None to test error case
        event_log._repository = None

        with pytest.raises(ValueError, match="repository is None"):
            list(event_log.read_since(checkpoint=0))

    def test_event_log_api_read_since_error_when_no_session_id(self):
        """Test EventLogAPI.read_since() raises error when agent has no _session_id."""
        agent = MockAgentForEventAPI()
        # Explicitly remove _session_id to test error case
        delattr(agent, "_session_id")
        observer = MockObserver()
        event_log = EventLogAPI(
            agent=agent,
            codec=None,
            observer=observer,
        )
        
        with pytest.raises(ValueError, match="agent has no _session_id"):
            list(event_log.read_since(checkpoint=0))

    def test_event_log_api_save_error_when_no_repository(self):
        """Test EventLogAPI.save() raises error when repository is None."""
        agent = MockAgentForEventAPI()
        observer = MockObserver()
        event_log = EventLogAPI(
            agent=agent,
            codec=None,
            observer=observer,
        )
        # Manually set repository to None to test error case
        event_log._repository = None

        with pytest.raises(ValueError, match="repository is None"):
            event_log.save("test-session")

