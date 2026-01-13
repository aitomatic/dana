"""Unit tests for RLMResource."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from dana.common.resource.rlm_resource import RLMResource


@patch("dana.common.resource.rlm_resource.LLM")
class TestRLMResource:
    """Tests for RLMResource class."""

    def test_init_creates_file(self, mock_llm_class):
        """Test that init creates file if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_context.md"
            assert not file_path.exists()

            resource = RLMResource(file=str(file_path), auto_register=False)

            assert file_path.exists()
            assert file_path.read_text() == ""

    def test_append(self, mock_llm_class):
        """Test that append adds timestamped content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_context.md"
            resource = RLMResource(file=str(file_path), auto_register=False)

            result = resource.append("Test content", category="note")

            assert "Appended" in result
            assert "note" in result

            content = file_path.read_text()
            assert "Test content" in content
            assert "[note]" in content

    def test_load_file(self, mock_llm_class):
        """Test that load_file ingests file contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source file
            source_path = Path(tmpdir) / "source.txt"
            source_path.write_text("Source file content")

            # Create resource
            context_path = Path(tmpdir) / "context.md"
            resource = RLMResource(file=str(context_path), auto_register=False)

            result = resource.load_file(str(source_path))

            assert "Loaded" in result
            assert "source.txt" in result

            content = context_path.read_text()
            assert "Source file content" in content
            assert "[file: source.txt]" in content

    def test_load_file_not_found(self, mock_llm_class):
        """Test load_file with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context_path = Path(tmpdir) / "context.md"
            resource = RLMResource(file=str(context_path), auto_register=False)

            result = resource.load_file("/nonexistent/file.txt")

            assert "Error" in result
            assert "not found" in result

    def test_query_basic(self, mock_llm_class):
        """Test that query returns answer for simple query."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create context file with content
            context_path = Path(tmpdir) / "context.md"
            context_path.write_text("The answer to life is 42.")

            # Mock LLM to return code that finds the answer
            mock_llm = AsyncMock()
            mock_llm.chat = AsyncMock(
                side_effect=[
                    # First iteration: LLM searches for "answer"
                    "print(re.findall(r'answer.*?\\d+', context))",
                    # Second iteration: LLM has the answer
                    "FINAL(42)",
                ]
            )
            mock_llm_class.return_value = mock_llm

            resource = RLMResource(file=str(context_path), auto_register=False)

            result = resource.query("What is the answer to life?")

            assert result == "42"

    def test_query_empty_context(self, mock_llm_class):
        """Test query with empty context returns error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context_path = Path(tmpdir) / "context.md"
            context_path.write_text("")

            resource = RLMResource(file=str(context_path), auto_register=False)

            result = resource.query("What is in the context?")

            assert "Error" in result
            assert "empty" in result.lower()


@patch("dana.common.resource.rlm_resource.LLM")
class TestRLMResourceIntegration:
    """Integration tests for RLMResource (require mocking)."""

    def test_query_with_final_var(self, mock_llm_class):
        """Test query with FINAL_VAR extracts variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context_path = Path(tmpdir) / "context.md"
            context_path.write_text("Some test content with data.")

            mock_llm = AsyncMock()
            mock_llm.chat = AsyncMock(
                side_effect=[
                    # First: set a variable
                    "result = 'found the data'",
                    # Second: return via FINAL_VAR
                    "FINAL_VAR(result)",
                ]
            )
            mock_llm_class.return_value = mock_llm

            resource = RLMResource(file=str(context_path), auto_register=False)
            result = resource.query("Find the data")

            assert result == "found the data"

    def test_query_max_iterations(self, mock_llm_class):
        """Test query stops after max iterations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context_path = Path(tmpdir) / "context.md"
            context_path.write_text("Some content")

            mock_llm = AsyncMock()
            # Always return code that doesn't finish
            mock_llm.chat = AsyncMock(return_value="print('still looking')")
            mock_llm_class.return_value = mock_llm

            resource = RLMResource(file=str(context_path), auto_register=False)
            result = resource.query("Find something")

            assert "Maximum iterations" in result

    def test_append_multiple(self, mock_llm_class):
        """Test multiple appends accumulate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context_path = Path(tmpdir) / "context.md"
            resource = RLMResource(file=str(context_path), auto_register=False)

            resource.append("First entry", category="note")
            resource.append("Second entry", category="data")
            resource.append("Third entry", category="note")

            content = context_path.read_text()
            assert "First entry" in content
            assert "Second entry" in content
            assert "Third entry" in content
            assert content.count("[note]") == 2
            assert content.count("[data]") == 1
