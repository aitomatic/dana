"""
Unit tests for web research workflows.
"""

from unittest.mock import patch

from dana_agent.lib.workflows.web_research import (
    ExtractFactWorkflow,
    FetchResultWorkflow,
    FormatWorkflow,
    SearchWorkflow,
)


class TestSearchWorkflow:
    """Test SearchWorkflow class functionality."""

    def test_search_workflow_initialization(self):
        """Test SearchWorkflow initialization."""
        workflow = SearchWorkflow()
        assert workflow is not None
        assert hasattr(workflow, "_do_execute")
        assert callable(workflow.execute)

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_do_execute_with_query(self, mock_search_resource):
        """Test SearchWorkflow.do_execute with a query."""
        # Mock the search_web method
        mock_search_resource.search_web.return_value = {
            "success": True,
            "query": "Python programming",
            "search_engine": "google",
            "results": [
                {
                    "title": "Python.org",
                    "url": "https://www.python.org",
                    "snippet": "Official Python website",
                    "position": 1,
                },
                {
                    "title": "Python Tutorial",
                    "url": "https://docs.python.org/3/tutorial/",
                    "snippet": "Python tutorial for beginners",
                    "position": 2,
                },
            ],
            "total_results": 2,
            "search_time_ms": 150,
        }

        workflow = SearchWorkflow()
        result = workflow._do_execute(query="Python programming", max_results=10)

        # Verify the search_web method was called
        mock_search_resource.search_web.assert_called_once_with(query="Python programming", max_results=10)

        # Verify the result structure
        assert result["success"] is True
        assert result["query"] == "Python programming"
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Python.org"

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_do_execute_with_default_max_results(self, mock_search_resource):
        """Test SearchWorkflow.do_execute with default max_results."""
        mock_search_resource.search_web.return_value = {
            "success": True,
            "query": "test query",
            "search_engine": "google",
            "results": [],
            "total_results": 0,
            "search_time_ms": 100,
        }

        workflow = SearchWorkflow()
        workflow._do_execute(query="test query")

        # Should use default max_results=10
        mock_search_resource.search_web.assert_called_once_with(query="test query", max_results=10)

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_do_execute_returns_search_result(self, mock_search_resource):
        """Test that do_execute returns the search result directly."""
        mock_search_resource.search_web.return_value = {
            "success": True,
            "query": "test",
            "search_engine": "google",
            "results": [],
            "total_results": 0,
            "search_time_ms": 50,
        }

        workflow = SearchWorkflow()
        result = workflow._do_execute(query="test", custom_field="custom_value")

        # Should return the search result directly
        assert result["success"] is True
        assert result["query"] == "test"
        assert result["search_engine"] == "google"
        # Note: input kwargs are NOT preserved in do_execute() return value
        assert "custom_field" not in result

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_do_execute_with_search_failure(self, mock_search_resource):
        """Test SearchWorkflow.do_execute when search fails."""
        mock_search_resource.search_web.return_value = {
            "success": False,
            "error": "API key not found",
            "query": "test query",
            "results": [],
            "total_results": 0,
        }

        workflow = SearchWorkflow()
        result = workflow._do_execute(query="test query")

        assert result["success"] is False
        assert "error" in result

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_do_execute_with_custom_max_results(self, mock_search_resource):
        """Test SearchWorkflow.do_execute with custom max_results."""
        mock_search_resource.search_web.return_value = {
            "success": True,
            "query": "test",
            "search_engine": "google",
            "results": [
                {"title": f"Result {i}", "url": f"https://example.com/{i}", "snippet": f"Snippet {i}", "position": i} for i in range(5)
            ],
            "total_results": 5,
            "search_time_ms": 200,
        }

        workflow = SearchWorkflow()
        result = workflow._do_execute(query="test", max_results=5)

        mock_search_resource.search_web.assert_called_once_with(query="test", max_results=5)
        assert len(result["results"]) == 5

    def test_do_execute_output_structure(self):
        """Test that do_execute returns the expected output structure."""
        with patch("dana_agent.lib.workflows.web_research._search_resource") as mock_resource:
            mock_resource.search_web.return_value = {
                "success": True,
                "query": "Python",
                "search_engine": "google",
                "results": [
                    {"title": "Python", "url": "https://python.org", "snippet": "Python is...", "position": 1},
                ],
                "total_results": 1,
                "search_time_ms": 100,
            }

            workflow = SearchWorkflow()
            result = workflow._do_execute(query="Python", extra_param="test")

            # Verify the direct search result structure
            assert "success" in result
            assert "query" in result
            assert "search_engine" in result
            assert "results" in result
            assert isinstance(result["results"], list)
            assert "total_results" in result
            assert "search_time_ms" in result

            # Verify each result has required fields
            if result["results"]:
                for result_item in result["results"]:
                    assert "title" in result_item
                    assert "url" in result_item
                    assert "snippet" in result_item
                    assert "position" in result_item


class TestFetchResultWorkflow:
    """Test FetchResultWorkflow class functionality."""

    def test_fetch_result_workflow_initialization(self):
        """Test FetchResultWorkflow initialization."""
        workflow = FetchResultWorkflow()
        assert workflow is not None
        assert hasattr(workflow, "_do_execute")
        assert callable(workflow.execute)

    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    def test_do_execute_with_url_and_purpose(self, mock_fetch_resource):
        """Test FetchResultWorkflow.do_execute with url and purpose."""
        mock_fetch_resource.fetch_and_extract_single.return_value = {
            "success": True,
            "url": "https://example.com",
            "title": "Example Page",
            "content_text": "This is the main content of the page.",
            "content_markdown": "# Example\nThis is the main content.",
            "word_count": 100,
            "reading_time_minutes": 1,
            "metadata": {"author": "John Doe", "date": "2024-01-01"},
            "quality": {"quality_score": 0.9, "is_sufficient": True},
            "sufficient": True,
            "key_points": ["Point 1", "Point 2"],
            "summary": "Brief summary",
            "code_blocks": [],
            "error": None,
        }

        workflow = FetchResultWorkflow()
        result = workflow._do_execute(url="https://example.com", purpose="test purpose")

        # Verify the fetch_and_extract_single method was called
        mock_fetch_resource.fetch_and_extract_single.assert_called_once_with(url="https://example.com", purpose="test purpose")

        # Verify the result structure (direct return from resource)
        assert result["success"] is True
        assert result["url"] == "https://example.com"
        assert result["title"] == "Example Page"

    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    def test_do_execute_with_empty_url(self, mock_fetch_resource):
        """Test FetchResultWorkflow.do_execute with missing/empty url - validation should catch it."""
        workflow = FetchResultWorkflow()

        # Test 1: No url provided
        result = workflow._do_execute()
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "required" in result["message"].lower()
        mock_fetch_resource.fetch_and_extract_single.assert_not_called()

        # Test 2: Empty string url
        result = workflow._do_execute(url="")
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "length" in result["message"].lower()
        mock_fetch_resource.fetch_and_extract_single.assert_not_called()

    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    def test_do_execute_returns_fetch_result(self, mock_fetch_resource):
        """Test that do_execute returns the fetch result directly."""
        mock_fetch_resource.fetch_and_extract_single.return_value = {
            "success": True,
            "url": "https://example.com",
            "title": "Test",
            "content_text": "Content",
            "content_markdown": "Content",
            "word_count": 10,
            "metadata": {},
            "quality": {},
            "key_points": [],
            "summary": "",
            "code_blocks": [],
        }

        workflow = FetchResultWorkflow()
        result = workflow._do_execute(url="https://example.com", purpose="test", custom_field="value")

        # Should return the fetch result directly
        assert result["url"] == "https://example.com"
        assert result["title"] == "Test"
        # Note: input kwargs are NOT preserved in do_execute() return value
        assert "custom_field" not in result

    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    def test_do_execute_output_structure(self, mock_fetch_resource):
        """Test that do_execute returns the expected output structure."""
        mock_fetch_resource.fetch_and_extract_single.return_value = {
            "success": True,
            "url": "https://example.com/final",
            "title": "Example Page",
            "content_text": "Main content text",
            "content_markdown": "# Example\nContent",
            "word_count": 150,
            "reading_time_minutes": 2,
            "metadata": {"author": "Jane", "published_date": "2024-01-01"},
            "quality": {"quality_score": 0.85, "is_sufficient": True},
            "sufficient": True,
            "key_points": ["Key point 1", "Key point 2", "Key point 3"],
            "summary": "This is a summary",
            "code_blocks": [{"language": "python", "code": "print('hello')"}],
            "error": None,
        }

        workflow = FetchResultWorkflow()
        result = workflow._do_execute(url="https://example.com", purpose="analysis")

        # Verify the direct fetch result structure
        assert "success" in result
        assert "url" in result
        assert "title" in result
        assert "content_text" in result
        assert "content_markdown" in result
        assert "word_count" in result
        assert "reading_time_minutes" in result
        assert "metadata" in result
        assert "quality" in result
        assert "sufficient" in result
        assert "key_points" in result
        assert isinstance(result["key_points"], list)
        assert "summary" in result
        assert "code_blocks" in result
        assert isinstance(result["code_blocks"], list)


class TestExtractFactWorkflow:
    """Test ExtractFactWorkflow class functionality."""

    def test_extract_fact_workflow_initialization(self):
        """Test ExtractFactWorkflow initialization."""
        workflow = ExtractFactWorkflow()
        assert workflow is not None
        assert hasattr(workflow, "_do_execute")
        assert callable(workflow.execute)

    @patch("dana_agent.lib.workflows.web_research._extract_resource")
    def test_do_execute_with_content_and_query(self, mock_extract_resource):
        """Test ExtractFactWorkflow.do_execute with content and query."""
        mock_extract_resource.extract_fact.return_value = {
            "fact": "Python was created in 1991",
            "confidence": 0.9,
            "context": "Python is a high-level programming language...",
        }

        workflow = ExtractFactWorkflow()
        result = workflow._do_execute(
            content="Python is a high-level programming language created in 1991", query="When was Python created?"
        )

        # Verify the extract_fact method was called
        mock_extract_resource.extract_fact.assert_called_once_with(
            content="Python is a high-level programming language created in 1991", query="When was Python created?"
        )

        # Verify the result structure (direct return from resource)
        assert result["fact"] == "Python was created in 1991"
        assert result["confidence"] == 0.9

    @patch("dana_agent.lib.workflows.web_research._extract_resource")
    def test_do_execute_with_none_values(self, mock_extract_resource):
        """Test ExtractFactWorkflow.do_execute with None values."""
        mock_extract_resource.extract_fact.return_value = {
            "fact": "No content provided",
            "confidence": 0.0,
            "context": "",
        }

        workflow = ExtractFactWorkflow()
        workflow._do_execute()  # No content or query provided

        # Should pass None values
        mock_extract_resource.extract_fact.assert_called_once_with(content=None, query=None)

    @patch("dana_agent.lib.workflows.web_research._extract_resource")
    def test_do_execute_returns_extracted_fact(self, mock_extract_resource):
        """Test that do_execute returns the extracted fact directly."""
        mock_extract_resource.extract_fact.return_value = {
            "fact": "Test fact",
            "confidence": 0.8,
            "context": "Context",
        }

        workflow = ExtractFactWorkflow()
        result = workflow._do_execute(content="Some content", query="Query?", extra="data")

        # Should return the extracted fact directly
        assert result["fact"] == "Test fact"
        assert result["confidence"] == 0.8
        # Note: input kwargs are NOT preserved in do_execute() return value
        assert "extra" not in result

    @patch("dana_agent.lib.workflows.web_research._extract_resource")
    def test_do_execute_output_structure(self, mock_extract_resource):
        """Test that do_execute returns the expected output structure."""
        mock_extract_resource.extract_fact.return_value = {
            "fact": "The capital of France is Paris",
            "confidence": 0.95,
            "context": "Paris is the capital and most populous city of France...",
        }

        workflow = ExtractFactWorkflow()
        result = workflow._do_execute(content="Paris is the capital city...", query="What is the capital of France?")

        # Verify the direct extracted fact structure
        assert "fact" in result
        assert isinstance(result["fact"], str)
        assert "confidence" in result
        assert isinstance(result["confidence"], int | float)
        assert "context" in result
        assert isinstance(result["context"], str)


class TestFormatWorkflow:
    """Test FormatWorkflow class functionality."""

    def test_format_workflow_initialization(self):
        """Test FormatWorkflow initialization."""
        workflow = FormatWorkflow()
        assert workflow is not None
        assert hasattr(workflow, "_do_execute")
        assert callable(workflow.execute)

    @patch("dana_agent.lib.workflows.web_research._format_resource")
    def test_do_execute_with_content_and_metadata(self, mock_format_resource):
        """Test FormatWorkflow.do_execute with content and metadata."""
        mock_format_resource.format_with_metadata.return_value = """# Test Title

---
**Topic:** Python Programming
**Sources:** 3
**Generated:** 2024-01-01 12:00:00
---

This is the main content."""

        workflow = FormatWorkflow()
        result = workflow._do_execute(content="This is the main content.", metadata={"title": "Test Title", "topic": "Python Programming"})

        # Verify the format_with_metadata method was called
        mock_format_resource.format_with_metadata.assert_called_once_with(
            content="This is the main content.", metadata={"title": "Test Title", "topic": "Python Programming"}
        )

        # Verify the result structure (dict with formatted_text key)
        assert isinstance(result, dict)
        assert "formatted_text" in result
        assert "# Test Title" in result["formatted_text"]

    @patch("dana_agent.lib.workflows.web_research._format_resource")
    def test_do_execute_with_empty_content(self, mock_format_resource):
        """Test FormatWorkflow.do_execute with empty content."""
        mock_format_resource.format_with_metadata.return_value = "---\n---\n"

        workflow = FormatWorkflow()
        workflow._do_execute()  # No content or metadata provided

        # Should use empty defaults
        mock_format_resource.format_with_metadata.assert_called_once_with(content="", metadata={})

    @patch("dana_agent.lib.workflows.web_research._format_resource")
    def test_do_execute_returns_formatted_dict(self, mock_format_resource):
        """Test that do_execute returns a dict with formatted_text key."""
        mock_format_resource.format_with_metadata.return_value = "Formatted content"

        workflow = FormatWorkflow()
        result = workflow._do_execute(content="Content", metadata={"title": "Test"}, custom="value")

        # Should return a dict with formatted_text key
        assert isinstance(result, dict)
        assert result["formatted_text"] == "Formatted content"

    @patch("dana_agent.lib.workflows.web_research._format_resource")
    def test_do_execute_output_structure(self, mock_format_resource):
        """Test that do_execute returns the expected output structure."""
        formatted_output = """# Research Report

---
**Topic:** Web Research
**Sources:** 5
**Workflow:** FactFinding
**Generated:** 2024-01-01 10:00:00
---

Main content goes here with findings and analysis."""

        mock_format_resource.format_with_metadata.return_value = formatted_output

        workflow = FormatWorkflow()
        result = workflow._do_execute(
            content="Main content goes here with findings and analysis.",
            metadata={"title": "Research Report", "topic": "Web Research", "sources_count": 5, "workflow": "FactFinding"},
        )

        # Verify the result is a dict with formatted_text key
        assert isinstance(result, dict)
        assert "formatted_text" in result
        assert isinstance(result["formatted_text"], str)
        assert "# Research Report" in result["formatted_text"]
        assert "**Topic:**" in result["formatted_text"]
        assert "Main content" in result["formatted_text"]
