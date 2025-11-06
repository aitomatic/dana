"""
Unit tests for Timeline and TimelineEntry classes.
"""

from datetime import datetime

import pytest

from dana.core.agent.timeline import Timeline, TimelineEntry, TimelineEntryType


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
        assert "[User-to-Agent Message]" in string_repr
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
        assert "[User-to-Agent Message]" in summary
        assert "[Agent-to-User Response]" in summary
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
        """Test LLM message conversion with different entry types."""
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="User message"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_THOUGHTS, content="Agent thinking"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.RESOURCE_RESULT, content="Resource result"))

        messages = timeline.to_llm_messages()
        assert len(messages) == 3
        assert messages[0].role == "user"
        assert messages[0].content == "User message"
        assert messages[1].role == "assistant"
        assert messages[1].content == "[Agent's Internal Thoughts] Agent thinking"
        assert messages[2].role == "assistant"
        assert messages[2].content == "[Resource-to-Agent Result] Resource result"

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
        """Test LLM message conversion with custom default role."""
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.TOOL_CALL, content="Tool call"))

        messages = timeline.to_llm_messages(default_role="system")
        assert len(messages) == 1
        assert messages[0].role == "system"
        assert messages[0].content == "[TimelineEntryType.TOOL_CALL] Tool call"

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
        assert messages[1].content == "[Agent's Internal Thoughts] Agent thinking"
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
