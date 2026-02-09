"""
Unit tests for CompressedTimeline class.
"""

from datetime import datetime
import json
import tempfile
from unittest.mock import Mock

import pytest

from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.core.agent.compressed_timeline import (
    COMPRESSED_CONTEXT_KEY,
    COMPRESSED_ENTRIES_COUNT_KEY,
    COMPRESSION_TIMESTAMP_KEY,
    CompressedTimeline,
    CompressedTimelineConfig,
)
from dana.core.agent.timeline import TimelineEntry, TimelineEntryType


class MockAgentForCompressedTimeline(BaseAgent):
    """Mock agent for compressed timeline testing."""

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


class TestCompressedTimelineConfig:
    """Test CompressedTimelineConfig."""

    def test_default_cutoff_calculation(self):
        """Test that cutoff_when_token_reach is calculated from max_tokens_until_compression."""
        config = CompressedTimelineConfig(max_tokens_until_compression=10000)
        assert config.cutoff_when_token_reach == 3000  # 0.3 * 10000

    def test_explicit_cutoff(self):
        """Test explicit cutoff_when_token_reach value."""
        config = CompressedTimelineConfig(max_tokens_until_compression=10000, cutoff_when_token_reach=5000)
        assert config.cutoff_when_token_reach == 5000

    def test_zero_cutoff_triggers_default(self):
        """Test that zero cutoff triggers default calculation."""
        config = CompressedTimelineConfig(max_tokens_until_compression=10000, cutoff_when_token_reach=0)
        assert config.cutoff_when_token_reach == 3000


class TestCompressedTimelineInitialization:
    """Test CompressedTimeline initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        defaults = CompressedTimelineConfig()
        timeline = CompressedTimeline()
        assert timeline.max_tokens_until_compression == defaults.max_tokens_until_compression
        assert timeline.max_recent_entries_to_keep == defaults.max_recent_entries_to_keep
        assert timeline.cutoff_when_token_reach == int(0.3 * defaults.max_tokens_until_compression)

    def test_initialization_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=10000,
            max_recent_entries_to_keep=10,
            cutoff_when_token_reach=2000,
        )
        assert timeline.max_tokens_until_compression == 10000
        assert timeline.max_recent_entries_to_keep == 10
        assert timeline.cutoff_when_token_reach == 2000

    def test_initialization_with_agent(self):
        """Test initialization with agent."""
        agent = MockAgentForCompressedTimeline()
        timeline = CompressedTimeline(agent=agent)
        assert timeline._agent == agent
        assert timeline._repository is not None


class TestCompressedTimelineNeedsCompression:
    """Test needs_compression method."""

    def test_no_compression_when_few_entries(self):
        """Test that compression is not needed with few entries."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=10000,
            max_recent_entries_to_keep=5,
        )
        # Add fewer entries than max_recent_entries_to_keep
        for i in range(3):
            timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content=f"Message {i}"))
        assert not timeline.needs_compression()

    def test_compression_needed_when_tokens_exceeded(self):
        """Test that compression is needed when tokens exceed threshold."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=100,  # Very low threshold
            max_recent_entries_to_keep=5,
        )
        # Add many entries with lots of content
        for i in range(20):
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content=f"This is a long message number {i} with many words to exceed the token limit quickly",
                )
            )
        assert timeline.needs_compression()


class TestCompressedTimelineEntriesPartitioning:
    """Test get_entries_to_keep_and_compress method."""

    @pytest.fixture
    def timeline(self):
        """Create a compressed timeline with entries."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=10000,
            max_recent_entries_to_keep=5,
            cutoff_when_token_reach=500,
        )
        # Add 10 entries
        for i in range(10):
            timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content=f"Message {i}"))
        return timeline

    def test_partitioning_respects_max_entries(self, timeline):
        """Test that partitioning respects max_recent_entries_to_keep."""
        entries_to_keep, entries_to_compress = timeline.get_entries_to_keep_and_compress()

        # Should keep at most max_recent_entries_to_keep
        assert len(entries_to_keep) <= timeline.max_recent_entries_to_keep
        # Should compress the rest
        assert len(entries_to_compress) == len(timeline.timeline) - len(entries_to_keep)

    def test_partitioning_keeps_recent_entries(self, timeline):
        """Test that most recent entries are kept."""
        entries_to_keep, entries_to_compress = timeline.get_entries_to_keep_and_compress()

        # Most recent entries should be in entries_to_keep
        for entry in entries_to_keep:
            assert entry in timeline.timeline[-len(entries_to_keep) :]

    def test_partitioning_with_tool_pairs(self):
        """Test that tool_call/tool_result pairs are kept together."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=10000,
            max_recent_entries_to_keep=3,
            cutoff_when_token_reach=100,
        )

        # Add entries with a tool call and its result
        for i in range(5):
            timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content=f"Message {i}"))

        # Add tool call
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.TOOL_CALL,
                content="",
                tool_calls=[{"id": "call_123", "function": {"name": "test"}}],
            )
        )

        # Add tool result
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.RESOURCE_RESULT,
                content="Result",
                tool_call_id="call_123",
            )
        )

        entries_to_keep, entries_to_compress = timeline.get_entries_to_keep_and_compress()

        # If tool result is kept, its tool call should also be kept
        has_tool_result = any(e.tool_call_id for e in entries_to_keep)
        if has_tool_result:
            has_tool_call = any(e.tool_calls for e in entries_to_keep)
            assert has_tool_call, "Tool result kept without its tool call"


class TestCompressedTimelineCompressionPrompt:
    """Test build_compression_prompt method."""

    @pytest.fixture
    def timeline_with_entries(self):
        """Create timeline with various entry types."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=10000,
            max_recent_entries_to_keep=3,
            cutoff_when_token_reach=100,
        )
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Hello"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="Hi there!"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_THOUGHTS, content="Thinking..."))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="What time is it?"))
        timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="It's 3 PM"))
        return timeline

    def test_compression_prompt_format(self, timeline_with_entries):
        """Test that compression prompt has expected format."""
        prompt = timeline_with_entries.build_compression_prompt()

        assert prompt is not None
        assert "compressing conversation history" in prompt.lower()
        assert "JSON" in prompt
        assert '"summary"' in prompt

    def test_compression_prompt_includes_entries(self, timeline_with_entries):
        """Test that prompt includes entry content."""
        prompt = timeline_with_entries.build_compression_prompt()

        # Should include content from entries to compress
        assert "Hello" in prompt or "Hi there" in prompt

    def test_no_prompt_when_nothing_to_compress(self):
        """Test that no prompt is generated when nothing to compress."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=10000,
            max_recent_entries_to_keep=10,
        )
        # Add fewer entries than max_recent_entries_to_keep
        for i in range(3):
            timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content=f"Msg {i}"))

        prompt = timeline.build_compression_prompt()
        assert prompt is None


class TestCompressedTimelineCompression:
    """Test compress method."""

    @pytest.fixture
    def timeline_with_llm(self):
        """Create timeline with mock LLM function."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=100,
            max_recent_entries_to_keep=3,
            cutoff_when_token_reach=50,
        )

        # Mock LLM function that returns valid JSON
        def mock_llm_call(prompt: str) -> str:
            return json.dumps({"summary": "This is a test summary of the conversation."})

        timeline.set_llm_call_fn(mock_llm_call)

        # Add enough entries to trigger compression
        for i in range(10):
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content=f"This is message number {i} with some content to fill tokens",
                )
            )

        return timeline

    def test_compression_removes_old_entries(self, timeline_with_llm):
        """Test that compression removes old entries."""
        initial_count = len(timeline_with_llm.timeline)
        compressed_count = timeline_with_llm.compress()

        assert compressed_count > 0
        assert len(timeline_with_llm.timeline) < initial_count

    def test_compression_stores_context_in_metadata(self, timeline_with_llm):
        """Test that compression stores context in metadata."""
        timeline_with_llm.compress()

        # Check that the oldest kept entry has compressed context
        assert timeline_with_llm.has_compressed_context()
        context = timeline_with_llm.get_compressed_context()
        assert context is not None
        assert "test summary" in context.lower()

    def test_compression_without_llm_function_raises(self):
        """Test that compression without LLM function raises error."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=100,
            max_recent_entries_to_keep=3,
        )
        for i in range(10):
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content=f"Message {i} with content",
                )
            )

        with pytest.raises(RuntimeError, match="LLM call function not set"):
            timeline.compress()

    def test_compression_returns_zero_when_not_needed(self):
        """Test that compression returns zero when not needed."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=100000,  # High threshold
            max_recent_entries_to_keep=100,
        )
        timeline.set_llm_call_fn(lambda x: '{"summary": "test"}')

        for i in range(3):
            timeline.add_entry(TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content=f"Msg {i}"))

        result = timeline.compress()
        assert result == 0


class TestCompressedTimelineAsyncCompression:
    """Test compress_async method."""

    @pytest.fixture
    def timeline_with_async_llm(self):
        """Create timeline with mock async LLM function."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=100,
            max_recent_entries_to_keep=3,
            cutoff_when_token_reach=50,
        )

        # Mock async LLM function
        async def mock_llm_call_async(prompt: str) -> str:
            return json.dumps({"summary": "Async summary of the conversation."})

        timeline.set_llm_call_async_fn(mock_llm_call_async)

        # Add entries with enough content to exceed 100 tokens (~1.3 tokens/word)
        # Need > 100 / 1.3 = ~77 words total
        for i in range(10):
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content=f"This is message number {i} with a lot more content words to ensure we exceed the token threshold for compression testing purposes",
                )
            )

        return timeline

    @pytest.mark.asyncio
    async def test_async_compression(self, timeline_with_async_llm):
        """Test async compression works."""
        compressed_count = await timeline_with_async_llm.compress_async()
        assert compressed_count > 0
        assert timeline_with_async_llm.has_compressed_context()


class TestCompressedTimelineToLLMMessages:
    """Test to_llm_messages method with compressed context."""

    def test_includes_compressed_context(self):
        """Test that LLM messages include compressed context."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=100,
            max_recent_entries_to_keep=3,
            cutoff_when_token_reach=50,
        )
        timeline.set_llm_call_fn(lambda x: '{"summary": "Previous context: User asked about weather."}')

        # Add entries with enough content to exceed 100 tokens
        for i in range(10):
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content=f"This is message number {i} with a lot more content words to ensure we exceed the token threshold for compression testing purposes",
                )
            )

        timeline.compress()
        messages = timeline.to_llm_messages()

        # Should include summary message (either [SUMMARY] or [Previous context summary] format)
        summary_messages = [m for m in messages if "[SUMMARY]" in m.content or "Previous context summary" in m.content]
        assert len(summary_messages) == 1
        assert "weather" in summary_messages[0].content.lower()

    def test_no_duplicate_summaries(self):
        """Test that calling to_llm_messages twice doesn't duplicate summaries."""
        timeline = CompressedTimeline(
            max_tokens_until_compression=100,
            max_recent_entries_to_keep=3,
            cutoff_when_token_reach=50,
        )
        timeline.set_llm_call_fn(lambda x: '{"summary": "Test summary"}')

        # Add entries with enough content to exceed 100 tokens
        for i in range(10):
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.USER_MESSAGE,
                    content=f"This is message number {i} with a lot more content words to ensure we exceed the token threshold for compression testing purposes",
                )
            )

        timeline.compress()

        # Call twice
        messages1 = timeline.to_llm_messages()
        messages2 = timeline.to_llm_messages()

        # Summary can appear as [SUMMARY] or [Previous context summary]
        summary_count1 = sum(1 for m in messages1 if "[SUMMARY]" in m.content or "Previous context summary" in m.content)
        summary_count2 = sum(1 for m in messages2 if "[SUMMARY]" in m.content or "Previous context summary" in m.content)

        assert summary_count1 == 1
        assert summary_count2 == 1


class TestCompressedTimelineLoadFromEntries:
    """Test load_from_entries method."""

    def test_load_from_entries_with_compressed_context(self):
        """Test loading entries with compressed context stops at that entry."""
        timeline = CompressedTimeline()

        # Create entries, some with compressed context
        entries = [
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Old message 1"),
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Old message 2"),
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Message with context",
                metadata={
                    COMPRESSED_CONTEXT_KEY: "Summary of older messages",
                    COMPRESSION_TIMESTAMP_KEY: datetime.now().isoformat(),
                    COMPRESSED_ENTRIES_COUNT_KEY: 5,
                },
            ),
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Recent message 1"),
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Recent message 2"),
        ]

        timeline.load_from_entries(entries)

        # Should only have entries from the one with compressed context onwards
        assert len(timeline.timeline) == 3
        assert timeline.timeline[0].content == "Message with context"
        assert timeline.has_compressed_context()

    def test_load_from_entries_without_compressed_context(self):
        """Test loading entries without compressed context loads all."""
        timeline = CompressedTimeline()

        entries = [
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Message 1"),
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Message 2"),
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="Message 3"),
        ]

        timeline.load_from_entries(entries)

        assert len(timeline.timeline) == 3
        assert not timeline.has_compressed_context()


class TestSummaryExtraction:
    """Test _extract_summary_from_response method."""

    @pytest.fixture
    def timeline(self):
        """Create timeline for testing."""
        return CompressedTimeline()

    def test_extract_json_summary(self, timeline):
        """Test extracting summary from JSON response."""
        response = '{"summary": "This is the extracted summary"}'
        result = timeline._extract_summary_from_response(response)
        assert result == "This is the extracted summary"

    def test_extract_json_in_code_block(self, timeline):
        """Test extracting summary from JSON in markdown code block."""
        response = """```json
{"summary": "Summary in code block"}
```"""
        result = timeline._extract_summary_from_response(response)
        assert result == "Summary in code block"

    def test_extract_plain_text(self, timeline):
        """Test extracting plain text response."""
        response = "This is a plain text summary without JSON"
        result = timeline._extract_summary_from_response(response)
        assert result == "This is a plain text summary without JSON"

    def test_extract_empty_response(self, timeline):
        """Test extracting from empty response."""
        result = timeline._extract_summary_from_response("")
        assert result is None or result == ""
