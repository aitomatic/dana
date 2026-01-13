"""Unit tests for LTMemory."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dana.core.memory import LTMemory


class TestLTMemory:
    """Tests for LTMemory class."""

    def test_store(self, tmp_path):
        """Test persists memory to file."""
        ltmem = LTMemory(path=str(tmp_path))

        ltmem.store({
            "type": "lesson",
            "content": "Test lesson content",
            "context": "testing",
            "timestamp": "2024-01-15T10:30:00Z",
        })

        # Verify file exists and contains the memory
        content = ltmem.memories_file.read_text()
        assert "## Memory [2024-01-15T10:30:00Z]" in content
        assert "**Type**: lesson" in content
        assert "**Context**: testing" in content
        assert "**Content**: Test lesson content" in content
        assert "---" in content

    def test_store_auto_timestamp(self, tmp_path):
        """Test generates timestamp if missing."""
        ltmem = LTMemory(path=str(tmp_path))

        ltmem.store({
            "type": "fact",
            "content": "Some fact",
        })

        content = ltmem.memories_file.read_text()
        # Should have auto-generated timestamp
        assert "## Memory [" in content
        assert "**Type**: fact" in content
        assert "**Content**: Some fact" in content

    def test_store_without_context(self, tmp_path):
        """Test storing memory without optional context."""
        ltmem = LTMemory(path=str(tmp_path))

        ltmem.store({
            "type": "pattern",
            "content": "A pattern observed",
            "timestamp": "2024-01-15T11:00:00Z",
        })

        content = ltmem.memories_file.read_text()
        assert "**Content**: A pattern observed" in content
        # Context line should not be present
        assert "**Context**:" not in content

    @patch("dana.core.memory.ltmemory.RLMResource")
    def test_query(self, mock_rlm_class, tmp_path):
        """Test retrieves relevant memories via RLM."""
        # Setup mock
        mock_rlm = MagicMock()
        mock_rlm.query.return_value = "Auth bugs often relate to token expiry"
        mock_rlm_class.return_value = mock_rlm

        ltmem = LTMemory(path=str(tmp_path))

        # Add a memory first (directly to file to avoid mock interference)
        ltmem.memories_file.write_text("## Memory [2024-01-15T10:30:00Z]\n- **Type**: lesson\n- **Content**: Test\n\n---\n")

        result = ltmem.query("What do I know about auth bugs?")

        mock_rlm.query.assert_called_once_with("What do I know about auth bugs?")
        assert result == "Auth bugs often relate to token expiry"

    def test_query_empty_memory(self, tmp_path):
        """Test query returns message when no memories stored."""
        ltmem = LTMemory(path=str(tmp_path))

        result = ltmem.query("Any question")
        assert result == "No memories stored yet."

    def test_creates_directory(self, tmp_path):
        """Test creates path if missing."""
        new_path = tmp_path / "nested" / "memory" / "dir"
        assert not new_path.exists()

        ltmem = LTMemory(path=str(new_path))

        assert new_path.exists()
        assert ltmem.memories_file.exists()

    def test_count(self, tmp_path):
        """Test returns memory count."""
        ltmem = LTMemory(path=str(tmp_path))

        assert ltmem.count() == 0

        ltmem.store({"type": "lesson", "content": "First"})
        assert ltmem.count() == 1

        ltmem.store({"type": "fact", "content": "Second"})
        assert ltmem.count() == 2

        ltmem.store({"type": "episode", "content": "Third"})
        assert ltmem.count() == 3

    def test_count_empty_file(self, tmp_path):
        """Test count returns 0 for empty file."""
        ltmem = LTMemory(path=str(tmp_path))
        assert ltmem.count() == 0

    def test_multiple_stores_append(self, tmp_path):
        """Test multiple stores append to file."""
        ltmem = LTMemory(path=str(tmp_path))

        ltmem.store({
            "type": "lesson",
            "content": "First lesson",
            "timestamp": "2024-01-15T10:00:00Z",
        })
        ltmem.store({
            "type": "fact",
            "content": "Second fact",
            "timestamp": "2024-01-15T11:00:00Z",
        })

        content = ltmem.memories_file.read_text()
        assert "First lesson" in content
        assert "Second fact" in content
        assert content.count("## Memory") == 2
