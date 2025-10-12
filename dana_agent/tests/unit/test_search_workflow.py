"""
Unit tests for web research workflows.
"""

from unittest.mock import patch

from dana.lib.workflows.web_research import SearchWorkflow


class TestSearchWorkflow:
    """Test SearchWorkflow class functionality."""

    def test_search_workflow_initialization(self):
        """Test SearchWorkflow initialization."""
        workflow = SearchWorkflow()
        assert workflow is not None
        assert hasattr(workflow, "_do_execute")
        assert callable(workflow.execute)

    @patch("dana.lib.workflows.web_research._searcher")
    def test_do_execute_with_query(self, mock_searcher):
        """Test SearchWorkflow.do_execute with a query."""
        # Mock the search_web method
        mock_searcher.search_web.return_value = {
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
        mock_searcher.search_web.assert_called_once_with(query="Python programming", max_results=10)

        # Verify the result structure
        assert result["success"] is True
        assert result["query"] == "Python programming"
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Python.org"

    @patch("dana.lib.workflows.web_research._searcher")
    def test_do_execute_with_default_max_results(self, mock_searcher):
        """Test SearchWorkflow.do_execute with default max_results."""
        mock_searcher.search_web.return_value = {
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
        mock_searcher.search_web.assert_called_once_with(query="test query", max_results=10)

    @patch("dana.lib.workflows.web_research._searcher")
    def test_do_execute_returns_search_result(self, mock_searcher):
        """Test that do_execute returns the search result directly."""
        mock_searcher.search_web.return_value = {
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

    @patch("dana.lib.workflows.web_research._searcher")
    def test_do_execute_with_search_failure(self, mock_searcher):
        """Test SearchWorkflow.do_execute when search fails."""
        mock_searcher.search_web.return_value = {
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

    @patch("dana.lib.workflows.web_research._searcher")
    def test_do_execute_with_custom_max_results(self, mock_searcher):
        """Test SearchWorkflow.do_execute with custom max_results."""
        mock_searcher.search_web.return_value = {
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

        mock_searcher.search_web.assert_called_once_with(query="test", max_results=5)
        assert len(result["results"]) == 5

    def test_do_execute_output_structure(self):
        """Test that do_execute returns the expected output structure."""
        with patch("dana.lib.workflows.web_research._searcher") as mock_resource:
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
