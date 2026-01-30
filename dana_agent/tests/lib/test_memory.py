"""Tests for dana.lib.memory module."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from dana.lib.memory import Memory, MemoryStore, available

pytestmark = pytest.mark.skipif(
    not available(),
    reason="dana[memory] optional dependencies not installed",
)


@pytest.fixture
def temp_store():
    """Create a temporary memory store for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = MemoryStore(store_path=Path(tmpdir) / "memory")
        yield store


@pytest.fixture
def populated_store(temp_store):
    """Create a store with some test memories."""
    temp_store.store(
        "When VAV damper is at 100% but zone is warm, check AHU supply air first",
        domain="hvac",
        source="session",
    )
    temp_store.store(
        "Chiller staging should follow load-based sequencing",
        domain="hvac",
        source="ontology",
    )
    temp_store.store(
        "Always close database connections in finally blocks to prevent leaks",
        domain="coding",
        source="bugfix",
    )
    return temp_store


class TestMemoryStore:
    """Tests for MemoryStore class."""

    def test_init_creates_directory(self, temp_store):
        """Test that init creates the store directory."""
        assert temp_store.store_path.exists()

    def test_store_returns_memory(self, temp_store):
        """Test that store returns a Memory object."""
        memory = temp_store.store("test memory", domain="test", source="test")

        assert isinstance(memory, Memory)
        assert memory.text == "test memory"
        assert memory.domain == "test"
        assert memory.source == "test"
        assert memory.id is not None
        assert len(memory.id) == 16  # SHA256 hash prefix

    def test_store_deduplicates(self, temp_store):
        """Test that storing the same text twice returns the same memory."""
        m1 = temp_store.store("duplicate test", domain="test")
        m2 = temp_store.store("duplicate test", domain="test")

        assert m1.id == m2.id

    def test_store_with_timestamp(self, temp_store):
        """Test storing with custom timestamp."""
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        memory = temp_store.store("timed memory", created=custom_time)

        assert memory.created == custom_time

    def test_query_returns_relevant(self, populated_store):
        """Test that query returns relevant memories."""
        results = populated_store.query("VAV temperature problems", limit=3)

        assert len(results) > 0
        # VAV memory should be most relevant
        assert "VAV" in results[0].text or "damper" in results[0].text

    def test_query_with_domain_filter(self, populated_store):
        """Test query filtering by domain."""
        results = populated_store.query("problems", domain="hvac", limit=10)

        for memory in results:
            assert memory.domain == "hvac"

    def test_query_with_min_score(self, populated_store):
        """Test query filtering by minimum score."""
        # Query something unrelated to get low scores
        results = populated_store.query("quantum physics", limit=10, min_score=0.5)

        for memory in results:
            assert memory.score >= 0.5

    def test_query_empty_store(self, temp_store):
        """Test query on empty store returns empty list."""
        results = temp_store.query("anything")
        assert results == []

    def test_count(self, populated_store):
        """Test counting memories."""
        total = populated_store.count()
        hvac_count = populated_store.count(domain="hvac")
        coding_count = populated_store.count(domain="coding")

        assert total == 3
        assert hvac_count == 2
        assert coding_count == 1

    def test_list_domains(self, populated_store):
        """Test listing domains."""
        domains = populated_store.list_domains()

        assert set(domains) == {"hvac", "coding"}

    def test_delete(self, temp_store):
        """Test deleting a memory."""
        memory = temp_store.store("to be deleted", domain="test")
        assert temp_store.count() == 1

        success = temp_store.delete(memory.id)
        assert success
        assert temp_store.count() == 0

    def test_delete_nonexistent(self, temp_store):
        """Test deleting nonexistent memory returns False."""
        success = temp_store.delete("nonexistent_id")
        assert not success

    def test_clear_all(self, populated_store):
        """Test clearing all memories."""
        assert populated_store.count() > 0

        populated_store.clear()

        assert populated_store.count() == 0

    def test_clear_domain(self, populated_store):
        """Test clearing specific domain."""
        initial_total = populated_store.count()
        hvac_count = populated_store.count(domain="hvac")

        populated_store.clear(domain="hvac")

        assert populated_store.count() == initial_total - hvac_count
        assert populated_store.count(domain="hvac") == 0
        assert populated_store.count(domain="coding") == 1

    def test_status(self, populated_store):
        """Test status returns expected structure."""
        status = populated_store.status()

        assert "store_path" in status
        assert "total_memories" in status
        assert "domains" in status
        assert "embedding_model" in status

        assert status["total_memories"] == 3
        assert "hvac" in status["domains"]
        assert "coding" in status["domains"]


class TestMemory:
    """Tests for Memory dataclass."""

    def test_to_dict(self):
        """Test Memory.to_dict serialization."""
        memory = Memory(
            id="abc123",
            text="test text",
            source="test",
            domain="test",
            created=datetime(2025, 1, 1, 12, 0, 0),
            score=0.75,
        )

        d = memory.to_dict()

        assert d["id"] == "abc123"
        assert d["text"] == "test text"
        assert d["source"] == "test"
        assert d["domain"] == "test"
        assert d["created"] == "2025-01-01T12:00:00"
        assert d["score"] == 0.75


class TestIndexDirectory:
    """Tests for directory indexing."""

    def test_index_markdown_files(self, temp_store):
        """Test indexing a directory of markdown files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test markdown files
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()

            (docs_dir / "guide.md").write_text("# User Guide\n\nThis is a test guide.")
            (docs_dir / "readme.md").write_text("# README\n\nProject description.")

            count = temp_store.index_directory(docs_dir, domain="test-docs")

            assert count == 2
            assert temp_store.count(domain="test-docs") == 2

    def test_index_with_glob_pattern(self, temp_store):
        """Test indexing with custom glob pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir)

            (docs_dir / "notes.md").write_text("markdown file")
            (docs_dir / "data.txt").write_text("text file")

            # Only index .txt files
            count = temp_store.index_directory(docs_dir, glob_pattern="*.txt", domain="txt")

            assert count == 1

    def test_index_nonexistent_raises(self, temp_store):
        """Test indexing nonexistent directory raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            temp_store.index_directory("/nonexistent/path")

    def test_index_chunks_large_files(self, temp_store):
        """Test that large files are chunked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir)

            # Create a large file (>1500 chars to trigger chunking)
            large_content = "This is a test. " * 200  # ~3200 chars
            (docs_dir / "large.md").write_text(large_content)

            count = temp_store.index_directory(docs_dir, domain="large")

            # Should be chunked into multiple memories
            assert count > 1


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_text_generates_id(self, temp_store):
        """Test that empty-ish text still works."""
        memory = temp_store.store("   ", domain="test")
        assert memory.id is not None

    def test_unicode_text(self, temp_store):
        """Test storing and querying unicode text."""
        memory = temp_store.store("温度が高すぎる場合は冷却を確認", domain="test")
        assert memory.id is not None

        results = temp_store.query("温度", limit=1)
        assert len(results) > 0

    def test_very_long_text(self, temp_store):
        """Test storing very long text (text is stored fully, embedding is truncated)."""
        long_text = "word " * 10000  # 50k chars
        memory = temp_store.store(long_text, domain="test")

        assert memory.id is not None
        # Full text is stored (embedding is truncated internally)
        assert memory.text == long_text

        # Should still be queryable
        results = temp_store.query("word", limit=1)
        assert len(results) > 0

    def test_special_characters_in_domain(self, temp_store):
        """Test domain names with special characters."""
        memory = temp_store.store("test", domain="project-name_v2.0")
        assert memory.domain == "project-name_v2.0"

        results = temp_store.query("test", domain="project-name_v2.0")
        assert len(results) > 0
