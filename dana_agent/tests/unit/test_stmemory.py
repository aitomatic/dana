"""Unit tests for STMemory."""

from datetime import datetime

import pytest

from dana.core.memory import MemoryEntry, STMemory


class TestSTMemory:
    """Tests for STMemory class."""

    def test_append(self):
        """Test append adds entry with timestamp."""
        stmem = STMemory()
        stmem.append("user", "Hello")

        assert len(stmem) == 1
        entry = stmem.entries[0]
        assert entry.role == "user"
        assert entry.content == "Hello"
        assert isinstance(entry.timestamp, datetime)

    def test_max_entries(self):
        """Test drops oldest when limit exceeded."""
        stmem = STMemory(max_entries=3)

        stmem.append("user", "msg1")
        stmem.append("agent", "msg2")
        stmem.append("user", "msg3")
        stmem.append("agent", "msg4")  # Should trigger drop

        assert len(stmem) == 3
        # First entry should be msg2 (msg1 was dropped)
        assert stmem.entries[0].content == "msg2"
        assert stmem.entries[-1].content == "msg4"

    def test_recent(self):
        """Test returns N most recent entries."""
        stmem = STMemory()
        stmem.append("user", "msg1")
        stmem.append("agent", "msg2")
        stmem.append("observation", "msg3")
        stmem.append("agent", "msg4")

        recent = stmem.recent(2)
        assert len(recent) == 2
        assert recent[0].content == "msg3"
        assert recent[1].content == "msg4"

    def test_recent_more_than_available(self):
        """Test recent returns all when n > available entries."""
        stmem = STMemory()
        stmem.append("user", "msg1")
        stmem.append("agent", "msg2")

        recent = stmem.recent(10)
        assert len(recent) == 2

    def test_timeline(self):
        """Test returns all entries."""
        stmem = STMemory()
        stmem.append("user", "msg1")
        stmem.append("agent", "msg2")
        stmem.append("user", "msg3")

        timeline = stmem.timeline
        assert len(timeline) == 3
        assert timeline[0].content == "msg1"
        assert timeline[2].content == "msg3"

    def test_estimate_tokens(self):
        """Test returns reasonable estimate."""
        stmem = STMemory()
        stmem.append("user", "Hello world")  # ~11 chars content
        stmem.append("agent", "Hi there")  # ~8 chars content

        tokens = stmem.estimate_tokens()
        # Should be positive and reasonable (chars/4 roughly)
        assert tokens > 0
        assert tokens < 100  # Sanity check

    def test_estimate_tokens_empty(self):
        """Test estimate tokens on empty memory."""
        stmem = STMemory()
        assert stmem.estimate_tokens() == 0

    def test_to_text(self):
        """Test formats as readable text."""
        stmem = STMemory()
        stmem.append("user", "Hello")
        stmem.append("agent", "Hi there")

        text = stmem.to_text()
        assert "user: Hello" in text
        assert "agent: Hi there" in text
        # Should have timestamps
        assert "[" in text and "]" in text

    def test_to_text_empty(self):
        """Test to_text on empty memory."""
        stmem = STMemory()
        assert stmem.to_text() == ""

    def test_clear(self):
        """Test removes all entries."""
        stmem = STMemory()
        stmem.append("user", "msg1")
        stmem.append("agent", "msg2")

        assert len(stmem) == 2
        stmem.clear()
        assert len(stmem) == 0
        assert stmem.entries == []

    def test_len(self):
        """Test returns entry count."""
        stmem = STMemory()
        assert len(stmem) == 0

        stmem.append("user", "msg1")
        assert len(stmem) == 1

        stmem.append("agent", "msg2")
        assert len(stmem) == 2


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_creation_with_defaults(self):
        """Test entry creation with auto timestamp."""
        entry = MemoryEntry(role="user", content="test")
        assert entry.role == "user"
        assert entry.content == "test"
        assert isinstance(entry.timestamp, datetime)

    def test_creation_with_timestamp(self):
        """Test entry creation with explicit timestamp."""
        ts = datetime(2024, 1, 15, 10, 30, 0)
        entry = MemoryEntry(role="agent", content="response", timestamp=ts)
        assert entry.timestamp == ts
