"""Unit tests for ContextBuilder."""

import pytest

from dana.core.context import Context, ContextBuilder


class MockQueryable:
    """Mock Queryable source for testing."""

    def __init__(self, response: str = "mocked response"):
        self.response = response
        self.last_query = None

    def query(self, question: str) -> str:
        self.last_query = question
        return self.response


class FailingQueryable:
    """Queryable that raises an exception."""

    def query(self, question: str) -> str:
        raise RuntimeError("Query failed")


class TestContextBuilder:
    """Tests for ContextBuilder class."""

    def test_add_string_source(self):
        """Test registering a string source."""
        builder = ContextBuilder()
        builder.add_source("timeline", "Some timeline content")

        assert "timeline" in builder._sources
        assert builder._sources["timeline"] == "Some timeline content"

    def test_add_rlm_source(self):
        """Test registering an RLM-like source."""
        builder = ContextBuilder()
        mock_rlm = MockQueryable()
        builder.add_source("codebase", mock_rlm)

        assert "codebase" in builder._sources
        assert builder._sources["codebase"] is mock_rlm

    def test_build_string_only(self):
        """Test building context with only string sources."""
        builder = ContextBuilder(token_budget=10000)
        builder.add_source("timeline", "Timeline entry 1\nTimeline entry 2")
        builder.add_source("notes", "Some notes here")

        context = builder.build()

        assert "Timeline entry 1" in context.text
        assert "Some notes here" in context.text
        assert "timeline" in context.sources_used
        assert "notes" in context.sources_used
        assert context.tokens_used > 0
        assert context.budget == 10000

    def test_build_respects_budget(self):
        """Test that build respects token budget."""
        builder = ContextBuilder(token_budget=10)  # Very small budget
        builder.add_source("small", "Hi")  # ~1 token
        builder.add_source("large", "A" * 1000)  # ~250 tokens

        context = builder.build()

        # Small should fit, large should not
        assert "small" in context.sources_used
        assert "large" not in context.sources_used
        assert context.tokens_used <= context.budget

    def test_build_with_rlm(self):
        """Test that build queries RLM sources with task."""
        builder = ContextBuilder()
        mock_rlm = MockQueryable(response="Auth is handled in auth.py")
        builder.add_source("codebase", mock_rlm)

        context = builder.build(task="Find auth code")

        assert mock_rlm.last_query == "Find auth code"
        assert "Auth is handled in auth.py" in context.text
        assert "codebase" in context.sources_used

    def test_tokens_counted(self):
        """Test that token usage is tracked."""
        builder = ContextBuilder()
        builder.add_source("content", "This is some content with several words")

        context = builder.build()

        assert context.tokens_used > 0
        # Our estimate: max(word_count, char_count // 4)
        # Word count = 7, char count = 39, // 4 = 9
        assert context.tokens_used == 9

    def test_sources_tracked(self):
        """Test that used sources are tracked."""
        builder = ContextBuilder()
        builder.add_source("source1", "Content 1")
        builder.add_source("source2", "Content 2")
        mock_rlm = MockQueryable("RLM content")
        builder.add_source("source3", mock_rlm)

        context = builder.build(task="test")

        assert len(context.sources_used) == 3
        assert "source1" in context.sources_used
        assert "source2" in context.sources_used
        assert "source3" in context.sources_used

    def test_empty_builder(self):
        """Test building with no sources."""
        builder = ContextBuilder()

        context = builder.build()

        assert context.text == ""
        assert context.tokens_used == 0
        assert context.sources_used == []

    def test_failing_queryable_skipped(self):
        """Test that failing queryables are skipped gracefully."""
        builder = ContextBuilder()
        builder.add_source("good", "Good content")
        builder.add_source("bad", FailingQueryable())

        context = builder.build(task="test")

        assert "Good content" in context.text
        assert "good" in context.sources_used
        assert "bad" not in context.sources_used

    def test_default_query_when_no_task(self):
        """Test default query is used when no task provided."""
        builder = ContextBuilder()
        mock_rlm = MockQueryable()
        builder.add_source("memory", mock_rlm)

        builder.build()  # No task

        assert mock_rlm.last_query == "What is relevant from memory?"


class TestContext:
    """Tests for Context dataclass."""

    def test_context_immutable(self):
        """Test that Context is immutable (frozen)."""
        context = Context(
            text="content",
            tokens_used=100,
            sources_used=["a", "b"],
            budget=1000,
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            context.text = "new content"

    def test_context_fields(self):
        """Test Context has all expected fields."""
        context = Context(
            text="test content",
            tokens_used=50,
            sources_used=["source1"],
            budget=500,
        )

        assert context.text == "test content"
        assert context.tokens_used == 50
        assert context.sources_used == ["source1"]
        assert context.budget == 500
