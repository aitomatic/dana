"""
Unit tests for Timeline and TimelineEntry classes.
"""

from datetime import datetime
import tempfile
from unittest.mock import Mock

import pytest

from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.core.timeline.timeline import Timeline, TimelineEntry, TimelineEntryType
from dana.repositories import LocalTimelineRepository


class TestTimelineEntry:
    """Test TimelineEntry functionality."""

    def test_timeline_entry_creation(self):
        """Test TimelineEntry creation with all fields."""
        entry = TimelineEntry(
            timestamp=datetime.now(), entry_type=TimelineEntryType.USER_MESSAGE, content="Hello world", metadata={"key": "value"}
        )

        assert entry.entry_type == TimelineEntryType.USER_MESSAGE
        assert entry.content == "Hello world"
        assert entry.metadata == {"key": "value"}

    def test_timeline_entry_to_string(self):
        """Test string representation of timeline entry."""
        timestamp = datetime(2024, 1, 15, 10, 30, 45)
        entry = TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Hello world", timestamp=timestamp)

        string_repr = entry.to_string()
        assert "[2024-01-15 10:30:45]" in string_repr
        assert "[USER]" in string_repr
        assert "Hello world" in string_repr

    def test_timeline_entry_type_checks(self):
        """Test entry type checking methods."""
        caller_entry = TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test")
        resource_entry = TimelineEntry(entry_type=TimelineEntryType.RESOURCE_RESULT, content="test")
        response_entry = TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="test")

        assert caller_entry.is_caller_message()
        assert not caller_entry.is_resource_result()
        assert resource_entry.is_resource_result()
        assert not resource_entry.is_caller_message()
        assert not response_entry.is_caller_message()
        assert not response_entry.is_resource_result()

    def test_timeline_entry_to_dict_basic(self):
        """Test to_dict() serializes basic fields correctly."""
        timestamp = datetime(2024, 1, 15, 10, 30, 45)
        entry = TimelineEntry(
            entry_type=TimelineEntryType.USER_MESSAGE,
            content="Hello world",
            timestamp=timestamp,
            metadata={"key": "value"},
        )

        result = entry.to_dict()

        assert result["type"] == "user_message"
        assert result["content"] == "Hello world"
        assert result["timestamp"] == "2024-01-15T10:30:45"
        assert result["metadata"] == {"key": "value"}
        assert result["is_latest_user_message"] is False
        assert result["ephemeral"] is False
        # Optional fields should not be present when None
        assert "tool_call_id" not in result
        assert "tool_calls" not in result

    def test_timeline_entry_to_dict_with_tool_call_id(self):
        """Test to_dict() includes tool_call_id when present."""
        entry = TimelineEntry(
            entry_type=TimelineEntryType.RESOURCE_RESULT,
            content="Tool result",
            tool_call_id="call_abc123",
        )

        result = entry.to_dict()

        assert result["tool_call_id"] == "call_abc123"
        assert "tool_calls" not in result

    def test_timeline_entry_to_dict_with_tool_calls(self):
        """Test to_dict() includes tool_calls when present."""
        tool_calls = [{"id": "call_abc123", "type": "function", "function": {"name": "get_weather", "arguments": "{}"}}]
        entry = TimelineEntry(
            entry_type=TimelineEntryType.TOOL_CALL,
            content="Calling get_weather",
            tool_calls=tool_calls,
        )

        result = entry.to_dict()

        assert result["tool_calls"] == tool_calls
        assert "tool_call_id" not in result

    def test_timeline_entry_from_dict_basic(self):
        """Test from_dict() deserializes basic fields correctly."""
        data = {
            "type": "user_message",
            "content": "Hello world",
            "timestamp": "2024-01-15T10:30:45",
            "metadata": {"key": "value"},
            "is_latest_user_message": False,
            "ephemeral": False,
        }

        entry = TimelineEntry.from_dict(data)

        assert entry.entry_type == TimelineEntryType.USER_MESSAGE
        assert entry.content == "Hello world"
        assert entry.timestamp == datetime(2024, 1, 15, 10, 30, 45)
        assert entry.metadata == {"key": "value"}
        assert entry.is_latest_user_message is False
        assert entry.ephemeral is False
        assert entry.tool_call_id is None
        assert entry.tool_calls is None

    def test_timeline_entry_from_dict_with_tool_call_id(self):
        """Test from_dict() deserializes tool_call_id correctly."""
        data = {
            "type": "resource_result",
            "content": "Tool result",
            "timestamp": "2024-01-15T10:30:45",
            "tool_call_id": "call_abc123",
        }

        entry = TimelineEntry.from_dict(data)

        assert entry.tool_call_id == "call_abc123"
        assert entry.tool_calls is None

    def test_timeline_entry_from_dict_with_tool_calls(self):
        """Test from_dict() deserializes tool_calls correctly."""
        tool_calls = [{"id": "call_abc123", "type": "function", "function": {"name": "get_weather", "arguments": "{}"}}]
        data = {
            "type": "tool_call",
            "content": "Calling get_weather",
            "timestamp": "2024-01-15T10:30:45",
            "tool_calls": tool_calls,
        }

        entry = TimelineEntry.from_dict(data)

        assert entry.tool_calls == tool_calls
        assert entry.tool_call_id is None

    def test_timeline_entry_roundtrip_with_tool_fields(self):
        """Test round-trip serialization preserves tool_call_id and tool_calls."""
        # Test with tool_call_id
        entry_with_id = TimelineEntry(
            entry_type=TimelineEntryType.RESOURCE_RESULT,
            content="Tool result",
            timestamp=datetime(2024, 1, 15, 10, 30, 45),
            tool_call_id="call_abc123",
        )

        roundtrip_entry = TimelineEntry.from_dict(entry_with_id.to_dict())

        assert roundtrip_entry.entry_type == entry_with_id.entry_type
        assert roundtrip_entry.content == entry_with_id.content
        assert roundtrip_entry.timestamp == entry_with_id.timestamp
        assert roundtrip_entry.tool_call_id == entry_with_id.tool_call_id

        # Test with tool_calls
        tool_calls = [{"id": "call_xyz789", "type": "function", "function": {"name": "search", "arguments": '{"q":"test"}'}}]
        entry_with_calls = TimelineEntry(
            entry_type=TimelineEntryType.TOOL_CALL,
            content="Calling search",
            timestamp=datetime(2024, 1, 15, 10, 31, 0),
            tool_calls=tool_calls,
        )

        roundtrip_entry2 = TimelineEntry.from_dict(entry_with_calls.to_dict())

        assert roundtrip_entry2.tool_calls == entry_with_calls.tool_calls


class TestTimeline:
    """Test Timeline functionality."""

    @pytest.fixture
    def timeline(self):
        """Create a timeline for testing."""
        agent = MockAgentForTimeline()
        return Timeline(max_context_tokens=1000, agent=agent)

    def test_timeline_initialization(self, timeline):
        """Test timeline initialization."""
        assert timeline.timeline == []
        assert timeline.max_context_tokens == 1000

    def test_add_entry(self, timeline):
        """Test adding entries to timeline."""
        entry = TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Test message")

        timeline.add_entry(entry)
        assert len(timeline.timeline) == 1
        assert timeline.timeline[0] == entry

    def test_get_entry_count(self, timeline):
        """Test getting entry count."""
        assert timeline.get_entry_count() == 0

        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test1"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test2"))

        assert timeline.get_entry_count() == 2

    def test_get_recent_entries(self, timeline):
        """Test getting recent entries."""
        # Add multiple entries
        for i in range(5):
            timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content=f"message {i}"))

        recent = timeline.get_recent_entries(3)
        assert len(recent) == 3
        assert recent[0].content == "message 2"
        assert recent[1].content == "message 3"
        assert recent[2].content == "message 4"

    def test_get_entries_by_type(self, timeline):
        """Test filtering entries by type."""
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="msg1"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="msg2"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="msg3"))

        caller_entries = timeline.get_entries_by_type(TimelineEntryType.USER_MESSAGE)
        response_entries = timeline.get_entries_by_type(TimelineEntryType.AGENT_RESPONSE)

        assert len(caller_entries) == 2
        assert len(response_entries) == 1
        assert caller_entries[0].content == "msg1"
        assert caller_entries[1].content == "msg3"

    def test_get_timeline_summary(self, timeline):
        """Test timeline summary generation."""
        timeline.add_entry(
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Hello", timestamp=datetime(2024, 1, 15, 10, 30, 0))
        )
        timeline.add_entry(
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="Hi there!", timestamp=datetime(2024, 1, 15, 10, 30, 5))
        )

        summary = timeline.get_timeline_summary()
        assert "2024-01-15 10:30:00" in summary
        assert "2024-01-15 10:30:05" in summary
        assert "[USER]" in summary
        assert "[RESPONSE]" in summary
        assert "Hello" in summary
        assert "Hi there!" in summary

    def test_get_entry_count_by_type(self, timeline):
        """Test getting entry counts by type."""
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="msg1"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="msg2"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="resp1"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_LEARNING, content="learning1"))

        counts = timeline.get_entry_count_by_type()
        assert counts[TimelineEntryType.USER_MESSAGE] == 2
        assert counts[TimelineEntryType.AGENT_RESPONSE] == 1
        assert counts[TimelineEntryType.AGENT_LEARNING] == 1

    def test_clear_old_entries(self, timeline):
        """Test clearing old entries."""
        old_time = datetime(2024, 1, 1, 10, 0, 0)
        new_time = datetime(2024, 1, 2, 10, 0, 0)

        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="old message", timestamp=old_time))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="new message", timestamp=new_time))

        removed_count = timeline.clear_old_entries(datetime(2024, 1, 1, 15, 0, 0))
        assert removed_count == 1
        assert len(timeline.timeline) == 1
        assert timeline.timeline[0].content == "new message"

    def test_to_llm_messages_basic(self, timeline):
        """Test basic LLM message conversion."""
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Hello"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="Hi there!"))

        messages = timeline.to_llm_messages()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Hi there!"

    def test_to_llm_messages_with_roles(self, timeline):
        """Test LLM message conversion with different entry types.

        Note: Consecutive assistant messages (without tool_calls) are merged
        to avoid confusing LLMs like OpenAI's models.
        """
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="User message"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_THOUGHTS, content="Agent thinking"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.RESOURCE_RESULT, content="Resource result"))

        messages = timeline.to_llm_messages()
        # Consecutive assistant messages are merged
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "User message"
        assert messages[1].role == "assistant"
        # THOUGHT and TOOL_RESULT are merged into one assistant message
        assert "[THOUGHT] Agent thinking" in messages[1].content
        assert "[TOOL_RESULT] Resource result" in messages[1].content

    def test_to_llm_messages_with_token_limit(self, timeline):
        """Test LLM message conversion with token limits."""
        # Add many entries to test token limiting
        for i in range(10):
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content=f"This is a very long message number {i} with lots of words to test token counting and sliding window behavior",
                )
            )

        messages = timeline.to_llm_messages(max_tokens=100)
        # Should be limited by token count
        assert len(messages) < 10
        # Should maintain chronological order (most recent first due to sliding window)
        assert "message number 9" in messages[-1].content

    def test_to_llm_messages_default_role(self, timeline):
        """Test LLM message conversion with custom default role.

        Note: Only entry types not explicitly mapped use the default_role:
        - USER_MESSAGE → always "user"
        - TOOL_CALL, AGENT_*, etc. → always "assistant"
        - FAILED_TOOL_CALL, TIMELINE_SUMMARY → use default_role
        """
        # Use FAILED_TOOL_CALL which uses the default_role (not explicitly mapped)
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.FAILED_TOOL_CALL, content="Failed tool call"))

        messages = timeline.to_llm_messages(default_role="system")
        assert len(messages) == 1
        assert messages[0].role == "system"
        assert messages[0].content == "[TimelineEntryType.FAILED_TOOL_CALL] Failed tool call"

    def test_to_llm_messages_empty_timeline(self, timeline):
        """Test LLM message conversion with empty timeline."""
        messages = timeline.to_llm_messages()
        assert messages == []

    def test_to_llm_messages_separate_latest_user(self, timeline):
        """Test LLM message conversion with latest user message separation."""
        # Add context entries
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="Previous response"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_THOUGHTS, content="Agent thinking"))

        # Add latest user message
        latest_entry = TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Latest user message")
        latest_entry.is_latest_user_message = True
        timeline.add_entry(latest_entry)

        messages = timeline.to_llm_messages(separate_latest_user=True)

        # Should have context messages + latest user message
        assert len(messages) == 3
        assert messages[0].role == "assistant"
        assert messages[0].content == "Previous response"
        assert messages[1].role == "assistant"
        assert messages[1].content == "[THOUGHT] Agent thinking"
        assert messages[2].role == "user"
        assert messages[2].content == "Latest user message"

        # Latest user message should be marked as processed
        assert not latest_entry.is_latest_user_message

    def test_to_llm_messages_separate_latest_user_no_latest(self, timeline):
        """Test LLM message conversion with separation but no latest user message."""
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="Response"))

        messages = timeline.to_llm_messages(separate_latest_user=True)

        # Should work normally when no latest user message
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].content == "Response"


class MockAgentForTimeline(BaseAgent):
    """Mock agent for timeline testing."""

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


class TestTimelineWithRepository:
    """Test Timeline with repository pattern."""

    def test_timeline_initialization_with_repository(self):
        """Test Timeline creates repository from agent."""
        agent = MockAgentForTimeline()
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        assert timeline._repository is not None
        assert isinstance(timeline._repository, LocalTimelineRepository)
        assert timeline.timeline == []

    def test_timeline_initialization_creates_default_repository(self):
        """Test Timeline creates default repository from agent if not provided."""
        agent = MockAgentForTimeline()
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        assert timeline._repository is not None
        assert isinstance(timeline._repository, LocalTimelineRepository)
        assert timeline._repository._agent == agent

    def test_timeline_save_uses_repository(self):
        """Test Timeline.save() uses repository."""
        agent = MockAgentForTimeline()
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        entry = TimelineEntry(
            entry_type=TimelineEntryType.USER_MESSAGE,
            content="Test message",
            timestamp=datetime.now(),
        )
        timeline.add_entry(entry)

        session_id = "test-session-001"
        timeline.save(session_id)

        # Verify repository was called (check file exists)
        session_folder = timeline._repository._events_path / session_id
        timeline_file = session_folder / "timeline.json"
        assert timeline_file.exists()

    def test_timeline_read_since_extracts_session_id_from_agent(self):
        """Test Timeline.read_since() extracts session_id from agent."""
        agent = MockAgentForTimeline()
        agent._session_id = "test-session-001"
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        # Should work without session_id parameter
        read_entries = list(timeline.read_since(checkpoint=0))
        assert isinstance(read_entries, list)

    def test_timeline_read_since_with_session_id(self):
        """Test Timeline.read_since() works by extracting session_id from agent."""
        agent = MockAgentForTimeline()
        agent._session_id = "test-session-001"
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        # Save some entries
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

    def test_timeline_read_since_checkpoint_negative(self):
        """Test Timeline.read_since() with negative checkpoint."""
        agent = MockAgentForTimeline()
        agent._session_id = "test-session-001"
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        # Save multiple entries
        for i in range(5):
            entry = TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content=f"Message {i}",
                timestamp=datetime.now(),
            )
            timeline.add_entry(entry)

        session_id = agent._session_id
        timeline.save(session_id)

        # Read last 2 entries (no session_id parameter needed)
        read_entries = list(timeline.read_since(checkpoint=-2))
        assert len(read_entries) == 2
        assert read_entries[0].content == "Message 3"
        assert read_entries[1].content == "Message 4"

    def test_timeline_read_since_checkpoint_positive(self):
        """Test Timeline.read_since() with positive checkpoint."""
        agent = MockAgentForTimeline()
        agent._session_id = "test-session-001"
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        # Save multiple entries
        for i in range(5):
            entry = TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content=f"Message {i}",
                timestamp=datetime.now(),
            )
            timeline.add_entry(entry)

        session_id = agent._session_id
        timeline.save(session_id)

        # Read from index 2 onwards (no session_id parameter needed)
        read_entries = list(timeline.read_since(checkpoint=2))
        assert len(read_entries) == 3
        assert read_entries[0].content == "Message 2"

    def test_timeline_read_since_error_when_no_repository(self):
        """Test Timeline.read_since() raises error when repository is None."""
        timeline = Timeline(max_context_tokens=1000)

        with pytest.raises(ValueError, match="repository is None"):
            list(timeline.read_since(checkpoint=0))

    def test_timeline_read_since_error_when_no_agent(self):
        """Test Timeline.read_since() raises error when agent is None."""
        timeline = Timeline(max_context_tokens=1000)
        # Manually set repository to None to test error case
        timeline._repository = None

        with pytest.raises(ValueError, match="repository is None"):
            list(timeline.read_since(checkpoint=0))

    def test_timeline_read_since_error_when_no_session_id(self):
        """Test Timeline.read_since() raises error when agent has no _session_id."""
        agent = MockAgentForTimeline()
        # Don't set _session_id
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        with pytest.raises(ValueError, match="agent has no _session_id"):
            list(timeline.read_since(checkpoint=0))

    def test_timeline_save_error_when_no_repository(self):
        """Test Timeline.save() raises error when repository is None."""
        timeline = Timeline(max_context_tokens=1000)

        with pytest.raises(ValueError, match="repository is None"):
            timeline.save("test-session")

    def test_timeline_save_and_read_with_tool_call_id(self):
        """Test that tool_call_id is persisted and restored correctly."""
        agent = MockAgentForTimeline()
        agent._session_id = "test-session-tool-id"
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        # Add entry with tool_call_id (tool result)
        entry = TimelineEntry(
            entry_type=TimelineEntryType.RESOURCE_RESULT,
            content="Weather data: sunny, 72F",
            timestamp=datetime(2024, 1, 15, 10, 30, 45),
            tool_call_id="call_abc123",
        )
        timeline.add_entry(entry)

        session_id = agent._session_id
        timeline.save(session_id)

        # Read back and verify tool_call_id is preserved
        read_entries = list(timeline.read_since(checkpoint=0))
        assert len(read_entries) == 1
        assert read_entries[0].tool_call_id == "call_abc123"
        assert read_entries[0].content == "Weather data: sunny, 72F"

    def test_timeline_save_and_read_with_tool_calls(self):
        """Test that tool_calls array is persisted and restored correctly."""
        agent = MockAgentForTimeline()
        agent._session_id = "test-session-tool-calls"
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        # Add entry with tool_calls (assistant message with tool invocations)
        tool_calls = [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {"name": "get_weather", "arguments": '{"location": "NYC"}'},
            }
        ]
        entry = TimelineEntry(
            entry_type=TimelineEntryType.TOOL_CALL,
            content="",
            timestamp=datetime(2024, 1, 15, 10, 30, 45),
            tool_calls=tool_calls,
        )
        timeline.add_entry(entry)

        session_id = agent._session_id
        timeline.save(session_id)

        # Read back and verify tool_calls is preserved
        read_entries = list(timeline.read_since(checkpoint=0))
        assert len(read_entries) == 1
        assert read_entries[0].tool_calls == tool_calls
        assert read_entries[0].tool_calls[0]["id"] == "call_abc123"
        assert read_entries[0].tool_calls[0]["function"]["name"] == "get_weather"

    def test_timeline_save_and_read_full_tool_sequence(self):
        """Test that a complete tool call sequence is persisted correctly."""
        agent = MockAgentForTimeline()
        agent._session_id = "test-session-full-sequence"
        timeline = Timeline(max_context_tokens=1000, agent=agent)

        # 1. User message
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="What's the weather in NYC?",
                timestamp=datetime(2024, 1, 15, 10, 30, 0),
            )
        )

        # 2. Assistant with tool_calls
        tool_calls = [
            {
                "id": "call_weather123",
                "type": "function",
                "function": {"name": "get_weather", "arguments": '{"location": "NYC"}'},
            }
        ]
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.TOOL_CALL,
                content="",
                timestamp=datetime(2024, 1, 15, 10, 30, 1),
                tool_calls=tool_calls,
            )
        )

        # 3. Tool result with tool_call_id
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.RESOURCE_RESULT,
                content='{"temp": 72, "condition": "sunny"}',
                timestamp=datetime(2024, 1, 15, 10, 30, 2),
                tool_call_id="call_weather123",
            )
        )

        # 4. Assistant response
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.AGENT_RESPONSE,
                content="The weather in NYC is sunny with a temperature of 72F.",
                timestamp=datetime(2024, 1, 15, 10, 30, 3),
            )
        )

        session_id = agent._session_id
        timeline.save(session_id)

        # Read back and verify entire sequence
        read_entries = list(timeline.read_since(checkpoint=0))
        assert len(read_entries) == 4

        # Verify user message
        assert read_entries[0].entry_type == TimelineEntryType.USER_MESSAGE
        assert read_entries[0].content == "What's the weather in NYC?"

        # Verify assistant with tool_calls
        assert read_entries[1].entry_type == TimelineEntryType.TOOL_CALL
        assert read_entries[1].tool_calls is not None
        assert len(read_entries[1].tool_calls) == 1
        assert read_entries[1].tool_calls[0]["id"] == "call_weather123"

        # Verify tool result with tool_call_id
        assert read_entries[2].entry_type == TimelineEntryType.RESOURCE_RESULT
        assert read_entries[2].tool_call_id == "call_weather123"

        # Verify final response
        assert read_entries[3].entry_type == TimelineEntryType.AGENT_RESPONSE
        assert "72F" in read_entries[3].content
