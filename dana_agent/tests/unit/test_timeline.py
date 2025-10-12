"""
Unit tests for Timeline and TimelineEntry classes.
"""

from datetime import datetime

import pytest

from dana.common.llm.types import LLMMessage
from dana.core.agent.timeline import Timeline, TimelineEntry, TimelineEntryType


class TestTimelineEntry:
    """Test TimelineEntry functionality."""

    def test_timeline_entry_creation(self):
        """Test TimelineEntry creation with all fields."""
        entry = TimelineEntry(
            timestamp=datetime.now(), entry_type=TimelineEntryType.CALLER_MESSAGE, content="Hello world", metadata={"key": "value"}
        )

        assert entry.entry_type == TimelineEntryType.CALLER_MESSAGE
        assert entry.content == "Hello world"
        assert entry.metadata == {"key": "value"}

    def test_timeline_entry_to_llm_message_user(self):
        """Test conversion to LLM message for user input."""
        entry = TimelineEntry(timestamp=datetime.now(), entry_type=TimelineEntryType.CALLER_MESSAGE, content="Hello world")

        message = entry.to_llm_message()
        assert isinstance(message, LLMMessage)
        assert message.role == "user"
        assert message.content == "Hello world"

    def test_timeline_entry_to_llm_message_assistant(self):
        """Test conversion to LLM message for assistant response."""
        entry = TimelineEntry(timestamp=datetime.now(), entry_type=TimelineEntryType.MY_RESPONSE, content="Hi there!")

        message = entry.to_llm_message()
        assert message.role == "assistant"
        assert message.content == "Hi there!"

    def test_timeline_entry_to_llm_message_agent_interaction(self):
        """Test conversion to LLM message for agent interaction."""
        entry = TimelineEntry(timestamp=datetime.now(), entry_type=TimelineEntryType.AGENT_RESPONSE, content="Let me help you with that")

        message = entry.to_llm_message()
        assert message.role == "system"
        assert message.content == "[Tool Response (Agent)] Let me help you with that"

    def test_timeline_entry_to_llm_message_resource_call(self):
        """Test conversion to LLM message for resource call."""
        entry = TimelineEntry(entry_type=TimelineEntryType.RESOURCE_RESULT, content="Processing data")

        message = entry.to_llm_message()
        assert message.role == "system"
        assert message.content == "[Tool Response (Resource)] Processing data"

    def test_timeline_entry_to_llm_message_system_event(self):
        """Test conversion to LLM message for system event."""
        entry = TimelineEntry(entry_type=TimelineEntryType.MY_THOUGHTS, content="System initialized")

        message = entry.to_llm_message()
        assert message.role == "system"
        assert message.content == "[My Thoughts] System initialized"

    def test_timeline_entry_to_llm_message_error_event(self):
        """Test conversion to LLM message for error event."""
        entry = TimelineEntry(entry_type=TimelineEntryType.MY_LEARNING, content="Connection failed")

        message = entry.to_llm_message()
        assert message.role == "system"
        assert message.content == "[My Learning] Connection failed"

    def test_timeline_entry_to_string(self):
        """Test string representation of timeline entry."""
        timestamp = datetime(2024, 1, 15, 10, 30, 45)
        entry = TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="Hello world", timestamp=timestamp)

        string_repr = entry.to_string()
        assert "[2024-01-15 10:30:45]" in string_repr
        assert "[User/Caller Message]" in string_repr
        assert "Hello world" in string_repr

    def test_timeline_entry_type_checks(self):
        """Test entry type checking methods."""
        caller_entry = TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="test")
        resource_entry = TimelineEntry(entry_type=TimelineEntryType.RESOURCE_RESULT, content="test")
        response_entry = TimelineEntry(entry_type=TimelineEntryType.MY_RESPONSE, content="test")

        assert caller_entry.is_caller_message()
        assert not caller_entry.is_resource_result()
        assert resource_entry.is_resource_result()
        assert not resource_entry.is_caller_message()
        assert not response_entry.is_caller_message()
        assert not response_entry.is_resource_result()


class TestTimeline:
    """Test Timeline functionality."""

    @pytest.fixture
    def timeline(self):
        """Create a timeline for testing."""
        return Timeline(max_context_tokens=1000)

    def test_timeline_initialization(self, timeline):
        """Test timeline initialization."""
        assert timeline.timeline == []
        assert timeline.max_context_tokens == 1000

    def test_add_entry(self, timeline):
        """Test adding entries to timeline."""
        entry = TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="Test message")

        timeline.add_entry(entry)
        assert len(timeline.timeline) == 1
        assert timeline.timeline[0] == entry

    def test_get_entry_count(self, timeline):
        """Test getting entry count."""
        assert timeline.get_entry_count() == 0

        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="test1"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="test2"))

        assert timeline.get_entry_count() == 2

    def test_get_recent_entries(self, timeline):
        """Test getting recent entries."""
        # Add multiple entries
        for i in range(5):
            timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content=f"message {i}"))

        recent = timeline.get_recent_entries(3)
        assert len(recent) == 3
        assert recent[0].content == "message 2"
        assert recent[1].content == "message 3"
        assert recent[2].content == "message 4"

    def test_get_entries_by_type(self, timeline):
        """Test filtering entries by type."""
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="msg1"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.MY_RESPONSE, content="msg2"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="msg3"))

        caller_entries = timeline.get_entries_by_type(TimelineEntryType.CALLER_MESSAGE)
        response_entries = timeline.get_entries_by_type(TimelineEntryType.MY_RESPONSE)

        assert len(caller_entries) == 2
        assert len(response_entries) == 1
        assert caller_entries[0].content == "msg1"
        assert caller_entries[1].content == "msg3"

    def test_get_context_basic(self, timeline):
        """Test basic context building."""
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="Hello"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.MY_RESPONSE, content="Hi there!"))

        context = timeline.get_context()
        assert len(context) == 2
        assert context[0].role == "user"
        assert context[0].content == "Hello"
        assert context[1].role == "assistant"
        assert context[1].content == "Hi there!"

    def test_get_context_with_token_limit(self, timeline):
        """Test context building with token limits."""
        # Add many entries to test token limiting
        for i in range(10):
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.CALLER_MESSAGE,
                    content=f"This is a very long message number {i} with lots of words to test token counting",
                )
            )

        context = timeline.get_context(max_tokens=50)
        # Should be limited by token count
        assert len(context) < 10

    def test_get_context_empty_timeline(self, timeline):
        """Test context building with empty timeline."""
        context = timeline.get_context()
        assert context == []

    def test_get_timeline_summary(self, timeline):
        """Test timeline summary generation."""
        timeline.add_entry(
            TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="Hello", timestamp=datetime(2024, 1, 15, 10, 30, 0))
        )
        timeline.add_entry(
            TimelineEntry(entry_type=TimelineEntryType.MY_RESPONSE, content="Hi there!", timestamp=datetime(2024, 1, 15, 10, 30, 5))
        )

        summary = timeline.get_timeline_summary()
        assert "2024-01-15 10:30:00" in summary
        assert "2024-01-15 10:30:05" in summary
        assert "[User/Caller Message]" in summary
        assert "[My Response]" in summary
        assert "Hello" in summary
        assert "Hi there!" in summary

    def test_get_entry_count_by_type(self, timeline):
        """Test getting entry counts by type."""
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="msg1"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="msg2"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.MY_RESPONSE, content="resp1"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.MY_LEARNING, content="learning1"))

        counts = timeline.get_entry_count_by_type()
        assert counts[TimelineEntryType.CALLER_MESSAGE] == 2
        assert counts[TimelineEntryType.MY_RESPONSE] == 1
        assert counts[TimelineEntryType.MY_LEARNING] == 1

    def test_clear_old_entries(self, timeline):
        """Test clearing old entries."""
        old_time = datetime(2024, 1, 1, 10, 0, 0)
        new_time = datetime(2024, 1, 2, 10, 0, 0)

        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="old message", timestamp=old_time))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.CALLER_MESSAGE, content="new message", timestamp=new_time))

        removed_count = timeline.clear_old_entries(datetime(2024, 1, 1, 15, 0, 0))
        assert removed_count == 1
        assert len(timeline.timeline) == 1
        assert timeline.timeline[0].content == "new message"
