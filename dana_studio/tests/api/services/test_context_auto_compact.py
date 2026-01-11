"""
Unit tests for Context Auto-Compaction Service.

Tests cover:
- Token estimation
- Compaction triggering
- Summary generation
- Metadata attachment
- Cache behavior
- Fallback handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from dana.studio.api.services.context_auto_compact import (
    ContextAutoCompactor,
    CompactionConfig,
    inject_compacted_context_to_content,
)
from dana.studio.api.core.schemas import MessageData, SenderRole


class TestContextAutoCompactor:
    """Tests for ContextAutoCompactor class."""

    @pytest.fixture
    def compactor(self):
        """Create a compactor with mocked LLM."""
        mock_llm = MagicMock()
        mock_llm.query = AsyncMock(return_value={"choices": [{"message": {"content": "## Summary\n- Test summary"}}]})
        return ContextAutoCompactor(llm=mock_llm)

    @pytest.fixture
    def sample_conversation(self):
        """Create a sample conversation for testing."""
        messages = []
        for i in range(15):
            role = SenderRole.USER if i % 2 == 0 else SenderRole.ASSISTANT
            messages.append(
                MessageData(
                    role=role,
                    content=f"Message {i}: " + "x" * 100,  # ~100 chars each
                    metadata={},
                )
            )
        return messages

    @pytest.fixture
    def conversation_with_instructions(self):
        """Create a conversation containing user instructions."""
        return [
            MessageData(role=SenderRole.USER, content="Help me edit the template"),
            MessageData(role=SenderRole.ASSISTANT, content="<view_template>...</view_template>"),
            MessageData(role=SenderRole.USER, content="Add questions about safety"),
            MessageData(role=SenderRole.ASSISTANT, content="<replace_in_template>...</replace_in_template>"),
            MessageData(role=SenderRole.USER, content="Keep section 3 unchanged from now on"),  # Key instruction
            MessageData(role=SenderRole.ASSISTANT, content="Understood, I'll preserve section 3"),
            MessageData(role=SenderRole.USER, content="Now update question 1"),
            MessageData(role=SenderRole.ASSISTANT, content="<thinking>...</thinking>"),
            MessageData(role=SenderRole.USER, content="Make it more specific"),
            MessageData(role=SenderRole.ASSISTANT, content="<replace_in_template>...</replace_in_template>"),
        ]


class TestTokenEstimation:
    """Tests for token estimation."""

    def test_estimate_empty_conversation(self):
        """Empty conversation should return 0 tokens."""
        compactor = ContextAutoCompactor()
        result = compactor.estimate_conversation_tokens([])
        assert result == 0

    def test_estimate_single_message(self):
        """Single message should return reasonable token count."""
        compactor = ContextAutoCompactor()
        messages = [MessageData(role=SenderRole.USER, content="Hello world")]
        result = compactor.estimate_conversation_tokens(messages)
        assert result > 0
        assert result < 50  # "Hello world" should be just a few tokens

    def test_estimate_includes_metadata(self):
        """Token count should include compacted_context from metadata."""
        compactor = ContextAutoCompactor()
        messages = [
            MessageData(
                role=SenderRole.USER,
                content="Hello",
                metadata={"compacted_context": "This is a long summary " * 50},
            )
        ]
        result_with_metadata = compactor.estimate_conversation_tokens(messages)

        messages_no_metadata = [MessageData(role=SenderRole.USER, content="Hello")]
        result_without_metadata = compactor.estimate_conversation_tokens(messages_no_metadata)

        assert result_with_metadata > result_without_metadata


class TestCompactionTriggering:
    """Tests for compaction triggering logic."""

    @pytest.mark.asyncio
    async def test_no_compaction_below_threshold(self):
        """Conversation below threshold should not be compacted."""
        config = CompactionConfig(compaction_trigger=100000, preserve_recent_count=6)
        compactor = ContextAutoCompactor(config=config)

        messages = [MessageData(role=SenderRole.USER, content="Short message")]

        result = await compactor.compact_if_needed(messages)

        assert result.summary_created is False
        assert result.messages_compacted == 0
        assert result.compacted_conversation == messages

    @pytest.mark.asyncio
    async def test_no_compaction_fewer_than_preserve_count(self):
        """Conversation with fewer messages than preserve_count should not be compacted."""
        config = CompactionConfig(preserve_recent_count=10)
        compactor = ContextAutoCompactor(config=config)

        messages = [
            MessageData(role=SenderRole.USER, content=f"Message {i}")
            for i in range(5)  # Less than preserve_recent_count
        ]

        result = await compactor.compact_if_needed(messages)

        assert result.summary_created is False
        assert len(result.compacted_conversation) == 5

    @pytest.mark.asyncio
    async def test_compaction_triggered_above_threshold(self):
        """Conversation above threshold should trigger compaction."""
        config = CompactionConfig(
            compaction_trigger=100,  # Very low threshold for testing
            target_token_limit=50,
            preserve_recent_count=2,
        )

        mock_llm = MagicMock()
        mock_llm.query = AsyncMock(return_value={"choices": [{"message": {"content": "## Summary\n- Compacted"}}]})
        compactor = ContextAutoCompactor(llm=mock_llm, config=config)

        # Create messages that exceed the threshold
        messages = [MessageData(role=SenderRole.USER, content="x" * 200) for _ in range(10)]

        result = await compactor.compact_if_needed(messages)

        assert result.summary_created is True
        assert result.messages_compacted > 0
        assert len(result.compacted_conversation) == config.preserve_recent_count


class TestSummaryAttachment:
    """Tests for summary attachment to metadata."""

    def test_attach_summary_to_first_message(self):
        """Summary should be attached to first message's metadata."""
        compactor = ContextAutoCompactor()

        messages = [
            MessageData(role=SenderRole.USER, content="First message"),
            MessageData(role=SenderRole.ASSISTANT, content="Second message"),
        ]

        summary = "## Summary\n- Test summary content"
        result = compactor.attach_summary_to_first_message(messages, summary)

        assert len(result) == 2
        assert result[0].metadata.get("compacted_context") == summary
        assert result[0].content == "First message"  # Original content unchanged
        assert result[1].metadata.get("compacted_context") is None

    def test_attach_summary_preserves_existing_metadata(self):
        """Existing metadata should be preserved when attaching summary."""
        compactor = ContextAutoCompactor()

        messages = [
            MessageData(
                role=SenderRole.USER,
                content="Message",
                metadata={"existing_key": "existing_value"},
            )
        ]

        summary = "## Summary"
        result = compactor.attach_summary_to_first_message(messages, summary)

        assert result[0].metadata.get("existing_key") == "existing_value"
        assert result[0].metadata.get("compacted_context") == summary

    def test_attach_summary_empty_list(self):
        """Empty list should return empty list."""
        compactor = ContextAutoCompactor()
        result = compactor.attach_summary_to_first_message([], "## Summary")
        assert result == []


class TestInjectCompactedContext:
    """Tests for inject_compacted_context_to_content helper."""

    def test_inject_with_compacted_context(self):
        """Should inject compacted context when present."""
        message = MessageData(
            role=SenderRole.USER,
            content="Original content",
            metadata={"compacted_context": "## Summary\n- Point 1"},
        )

        result = inject_compacted_context_to_content(message)

        assert "<prior_conversation_summary>" in result
        assert "## Summary" in result
        assert "Original content" in result
        assert result.endswith("Original content")

    def test_inject_without_compacted_context(self):
        """Should return original content when no compacted context."""
        message = MessageData(
            role=SenderRole.USER,
            content="Original content",
            metadata={},
        )

        result = inject_compacted_context_to_content(message)

        assert result == "Original content"
        assert "<prior_conversation_summary>" not in result


class TestFallbackBehavior:
    """Tests for fallback behavior when LLM fails."""

    def test_extract_key_information_fallback_with_instructions(self):
        """Fallback should extract user instructions."""
        compactor = ContextAutoCompactor()

        messages = [
            MessageData(role=SenderRole.USER, content="Keep section 3 unchanged"),
            MessageData(role=SenderRole.ASSISTANT, content="Okay"),
            MessageData(role=SenderRole.USER, content="Always remember this rule"),
        ]

        result = compactor._extract_key_information_fallback(messages)

        assert "Keep section 3" in result or "instruction" in result.lower()
        assert "Always remember" in result or "instruction" in result.lower()

    def test_extract_key_information_fallback_with_tools(self):
        """Fallback should note tool usage."""
        compactor = ContextAutoCompactor()

        messages = [
            MessageData(
                role=SenderRole.ASSISTANT,
                content="<view_template>...</view_template>",
                treat_as_tool=True,
            ),
            MessageData(
                role=SenderRole.ASSISTANT,
                content="<replace_in_template>...</replace_in_template>",
                treat_as_tool=True,
            ),
        ]

        result = compactor._extract_key_information_fallback(messages)

        assert "viewed" in result.lower() or "template" in result.lower()
        assert "modified" in result.lower() or "template" in result.lower()


class TestCaching:
    """Tests for summary caching."""

    def test_content_hash_consistency(self):
        """Same messages should produce same hash."""
        compactor = ContextAutoCompactor()

        messages = [MessageData(role=SenderRole.USER, content="Test message")]

        hash1 = compactor._get_content_hash(messages)
        hash2 = compactor._get_content_hash(messages)

        assert hash1 == hash2

    def test_content_hash_different_for_different_messages(self):
        """Different messages should produce different hashes."""
        compactor = ContextAutoCompactor()

        messages1 = [MessageData(role=SenderRole.USER, content="Message 1")]
        messages2 = [MessageData(role=SenderRole.USER, content="Message 2")]

        hash1 = compactor._get_content_hash(messages1)
        hash2 = compactor._get_content_hash(messages2)

        assert hash1 != hash2

    def test_cache_stores_and_retrieves(self):
        """Cache should store and retrieve summaries."""
        config = CompactionConfig(enable_cache=True, cache_ttl_seconds=3600)
        compactor = ContextAutoCompactor(config=config)

        content_hash = "test_hash"
        summary = "## Test Summary"

        compactor._cache_summary(content_hash, summary)
        result = compactor._get_cached_summary(content_hash)

        assert result == summary

    def test_cache_disabled(self):
        """Cache should not store when disabled."""
        config = CompactionConfig(enable_cache=False)
        compactor = ContextAutoCompactor(config=config)

        content_hash = "test_hash"
        summary = "## Test Summary"

        compactor._cache_summary(content_hash, summary)
        result = compactor._get_cached_summary(content_hash)

        assert result is None


class TestAggressiveTruncationFallback:
    """Tests for aggressive truncation fallback."""

    def test_aggressive_truncation_reduces_messages(self):
        """Aggressive truncation should keep only recent messages."""
        config = CompactionConfig(preserve_recent_count=6)
        compactor = ContextAutoCompactor(config=config)

        messages = [MessageData(role=SenderRole.USER, content=f"Message {i}") for i in range(20)]

        result = compactor._aggressive_truncation_fallback(messages)

        # Should keep preserve_recent_count // 2 = 3 messages
        assert result.messages_preserved <= config.preserve_recent_count
        assert result.messages_compacted > 0
        assert result.summary_created is False
