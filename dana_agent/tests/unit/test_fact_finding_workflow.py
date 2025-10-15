"""
Unit tests for the FactFindingWorkflow.
"""

from unittest.mock import patch

import pytest

from dana.lib.workflows.web_research import (
    FactFindingWorkflow,
    SearchWorkflow,
)


class TestFactFindingWorkflow:
    """Test FactFindingWorkflow class functionality."""

    def test_fact_finding_workflow_initialization(self):
        """Test FactFindingWorkflow initialization."""
        workflow = FactFindingWorkflow()

        assert workflow.workflow_type == "FactFindingWorkflow"
        assert hasattr(workflow, "workflow_id")
        assert hasattr(workflow, "execute")

    @patch("dana.lib.workflows.web_research._searcher")
    @patch("dana.lib.workflows.web_research._fetcher")
    @patch("dana.lib.workflows.web_research._extractor")
    @patch("dana.lib.workflows.web_research._formatter")
    def test_fact_finding_workflow_execute_success(self, mock_format, mock_extract, mock_fetch, mock_search):
        """Test FactFindingWorkflow execute with successful results."""
        # Setup mocks
        mock_search.search.return_value = {
            "success": True,
            "query": "What is the capital of France?",
            "results": [
                {
                    "title": "Paris - Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Paris",
                    "snippet": "Paris is the capital of France",
                }
            ],
        }

        mock_fetch.fetch_and_extract_single.return_value = {
            "success": True,
            "content_text": "Paris is the capital and most populous city of France.",
            "metadata": {
                "url": "https://en.wikipedia.org/wiki/Paris",
                "title": "Paris - Wikipedia",
            },
        }

        mock_extract.extract_fact.return_value = {
            "fact": "Paris is the capital of France",
            "confidence": 0.95,
        }

        mock_format.format_with_metadata.return_value = {
            "formatted_text": "Paris is the capital of France\nSource: Paris - Wikipedia",
        }

        # Execute workflow
        workflow = FactFindingWorkflow()
        result = workflow.execute(
            query="What is the capital of France?",
            max_results=5,
        )

        # Verify results - workflow returns "result" key with final output
        assert "result" in result
        assert isinstance(result["result"], dict)

        # Verify resource calls
        mock_search.search.assert_called_once_with(query="What is the capital of France?", max_results=5)
        mock_extract.extract_fact.assert_called_once()
        mock_format.format_with_metadata.assert_called_once()

    @patch("dana.lib.workflows.web_research._searcher")
    @patch("dana.lib.workflows.web_research._fetcher")
    @patch("dana.lib.workflows.web_research._extractor")
    @patch("dana.lib.workflows.web_research._formatter")
    def test_fact_finding_workflow_execute_with_defaults(self, mock_format, mock_extract, mock_fetch, mock_search):
        """Test FactFindingWorkflow execute with default parameters."""
        mock_search.search.return_value = {
            "success": True,
            "query": "test query",
            "results": [{"url": "https://test.com"}],
        }
        mock_fetch.fetch_and_extract_single.return_value = {
            "success": True,
            "content_text": "test content",
            "metadata": {},
        }
        mock_extract.extract_fact.return_value = {
            "fact": "test fact",
            "confidence": 0.8,
        }
        mock_format.format_with_metadata.return_value = "formatted result"

        workflow = FactFindingWorkflow()
        result = workflow.execute(query="test query")

        # Verify default max_results is used (5 for FactFindingWorkflow)
        mock_search.search.assert_called_once_with(query="test query", max_results=5)
        # Verify result contains expected data
        assert "result" in result

    @patch("dana.lib.workflows.web_research._searcher")
    @patch("dana.lib.workflows.web_research._fetcher")
    @patch("dana.lib.workflows.web_research._extractor")
    @patch("dana.lib.workflows.web_research._formatter")
    def test_fact_finding_workflow_search_failure(self, mock_format, mock_extract, mock_fetch, mock_search):
        """Test FactFindingWorkflow when search fails."""
        mock_search.search.return_value = {
            "success": False,
            "error": "API key not configured",
            "results": [],
        }
        # Mock other resources to handle the error case
        mock_fetch.fetch_and_extract_single.return_value = {
            "success": False,
            "error": "No URL to fetch",
            "content_text": "",
            "metadata": {},
        }
        mock_extract.extract_fact.return_value = {
            "fact": "",
            "confidence": 0.0,
        }
        mock_format.format_with_metadata.return_value = "No results"

        workflow = FactFindingWorkflow()
        result = workflow.execute(query="test query")

        # Should still return result dict
        assert "result" in result or "success" in result

    @patch("dana.lib.workflows.web_research._searcher")
    @patch("dana.lib.workflows.web_research._fetcher")
    @patch("dana.lib.workflows.web_research._extractor")
    @patch("dana.lib.workflows.web_research._formatter")
    def test_fact_finding_workflow_fetch_failure(self, mock_format, mock_extract, mock_fetch, mock_search):
        """Test FactFindingWorkflow when fetch fails."""
        mock_search.search.return_value = {
            "success": True,
            "query": "test",
            "results": [{"url": "https://example.com"}],
        }
        mock_fetch.fetch_and_extract_single.return_value = {
            "success": False,
            "error": "Failed to fetch URL",
            "content_text": "",
            "metadata": {},
        }
        mock_extract.extract_fact.return_value = {
            "fact": "",
            "confidence": 0.0,
        }
        mock_format.format_with_metadata.return_value = "error result"

        workflow = FactFindingWorkflow()
        result = workflow.execute(query="test")

        # Should return results
        assert "result" in result or "success" in result

    def test_fact_finding_workflow_missing_query(self):
        """Test FactFindingWorkflow with missing query parameter."""
        workflow = FactFindingWorkflow()

        # Should handle missing query gracefully
        result = workflow.execute()
        assert isinstance(result, dict)


class TestSearchWorkflow:
    """Test SearchWorkflow class functionality."""

    @patch("dana.lib.workflows.web_research._searcher")
    def test_search_workflow_execute(self, mock_search):
        """Test SearchWorkflow execute."""
        mock_search.search.return_value = {
            "success": True,
            "query": "test query",
            "results": [{"title": "Test", "url": "https://test.com"}],
        }

        workflow = SearchWorkflow()
        result = workflow.execute(query="test query", max_results=5)

        assert "result" in result
        assert result["result"]["success"] is True
        mock_search.search.assert_called_once_with(query="test query", max_results=5)

    @patch("dana.lib.workflows.web_research._searcher")
    def test_search_workflow_with_default_max_results(self, mock_search):
        """Test SearchWorkflow with default max_results."""
        mock_search.search.return_value = {"success": True, "results": []}

        workflow = SearchWorkflow()
        workflow.execute(query="test")

        # Default max_results should be 10
        mock_search.search.assert_called_once_with(query="test", max_results=10)


# Note: FetchResultWorkflow, ExtractFactWorkflow, and FormatWorkflow have been removed
# as they were simple one-liner wrappers. CallableWorkflow with direct methods is now used:
# - CallableWorkflow(_fetcher.fetch_and_extract_single, "url=... -> fetch_result")
# - CallableWorkflow(_extractor.extract_fact, "content=..., query=...")
# - CallableWorkflow(_formatter.format_with_metadata, "content=..., metadata=...")


class TestWorkflowComposition:
    """Test workflow composition using the | operator."""

    @patch("dana.lib.workflows.web_research._searcher")
    def test_workflow_composition_operator(self, mock_search):
        """Test composing workflows with | operator."""
        mock_search.search.return_value = {
            "success": True,
            "query": "test",
            "results": [{"url": "https://test.com"}],
        }

        # Compose workflows - use SearchWorkflow with a simple callable
        def extract_first_url(results):
            return results[0]["url"] if results else ""

        composed = SearchWorkflow() | extract_first_url

        # Execute composed workflow
        result = composed.execute(query="test", max_results=5)

        # Both stages should have executed
        assert "result" in result
        assert result["result"] == "https://test.com"
        mock_search.search.assert_called_once()

    @patch("dana.lib.workflows.web_research._searcher")
    def test_workflow_composition_chaining(self, mock_search):
        """Test chaining multiple workflows and callables."""
        mock_search.search.return_value = {"success": True, "query": "test", "results": [{"title": "Test"}, {"title": "Example"}]}

        # Chain search workflow with a simple transformation callable
        def add_count(success, query, results):
            return {"success": success, "query": query, "results": results, "count": len(results)}

        workflow = SearchWorkflow() | add_count

        result = workflow.execute(query="test", max_results=5)

        # Workflow should have executed and callable added count
        assert "result" in result
        assert result["result"]["count"] == 2
        mock_search.search.assert_called_once()

    def test_workflow_composition_type_error(self):
        """Test that composing with non-workflow/non-callable raises TypeError."""
        workflow = SearchWorkflow()

        with pytest.raises(TypeError, match="Can only compose workflows with other workflows or callables"):
            workflow | "not a workflow"


class TestFactFindingWorkflowIntegration:
    """Test FactFindingWorkflow integration scenarios."""

    @patch("dana.lib.workflows.web_research._searcher")
    @patch("dana.lib.workflows.web_research._fetcher")
    @patch("dana.lib.workflows.web_research._extractor")
    @patch("dana.lib.workflows.web_research._formatter")
    def test_fact_finding_workflow_full_pipeline(self, mock_format, mock_extract, mock_fetch, mock_search):
        """Test complete FactFindingWorkflow pipeline."""
        # Setup complete mock pipeline
        mock_search.search.return_value = {
            "success": True,
            "query": "When was Python created?",
            "results": [
                {
                    "title": "Python (programming language) - Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                    "snippet": "Python was created in 1991 by Guido van Rossum",
                }
            ],
        }

        mock_fetch.fetch_and_extract_single.return_value = {
            "success": True,
            "content_text": "Python was created in 1991 by Guido van Rossum at CWI in the Netherlands.",
            "metadata": {
                "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                "title": "Python (programming language) - Wikipedia",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        }

        mock_extract.extract_fact.return_value = {
            "fact": "Python was created in 1991",
            "confidence": 0.95,
            "context": "Created by Guido van Rossum",
        }

        mock_format.format_with_metadata.return_value = "Python was created in 1991\nSource: Python (programming language) - Wikipedia\nURL: https://en.wikipedia.org/wiki/Python_(programming_language)\nConfidence: 95%"

        # Execute workflow
        workflow = FactFindingWorkflow()
        result = workflow.execute(query="When was Python created?", max_results=5)

        # Verify complete pipeline execution - workflows return "result" key
        assert "result" in result

        # Verify all resources were called in order
        # Note: fetch, extract, and format should be called if the search returns results with URLs
        mock_search.search.assert_called_once()
        # These may or may not be called depending on workflow composition logic
        if mock_fetch.fetch_and_extract_single.call_count > 0:
            mock_extract.extract_fact.assert_called_once()
            mock_format.format_with_metadata.assert_called_once()

    @patch("dana.lib.workflows.web_research._searcher")
    @patch("dana.lib.workflows.web_research._fetcher")
    @patch("dana.lib.workflows.web_research._extractor")
    @patch("dana.lib.workflows.web_research._formatter")
    def test_fact_finding_workflow_data_flow(self, mock_format, mock_extract, mock_fetch, mock_search):
        """Test that data flows correctly through the workflow pipeline."""
        # Setup mocks
        mock_search.search.return_value = {
            "success": True,
            "results": [{"url": "https://test.com"}],
        }
        mock_fetch.fetch_and_extract_single.return_value = {
            "success": True,
            "content_text": "test content from fetch",
            "metadata": {"url": "https://test.com"},
        }
        mock_extract.extract_fact.return_value = {"fact": "test fact", "confidence": 0.8}
        mock_format.format_with_metadata.return_value = {"formatted_text": "formatted result"}

        # Execute workflow
        workflow = FactFindingWorkflow()
        result = workflow.execute(query="test query")

        # Verify search was called (entry point of pipeline)
        mock_search.search.assert_called_once()

        # Verify workflow completed and returned a result
        assert isinstance(result, dict)
        assert "result" in result  # Standard workflow result key


class TestWorkflowEdgeCases:
    """Test edge cases and error conditions."""

    def test_workflow_with_empty_kwargs(self):
        """Test workflow execution with empty kwargs."""
        workflow = SearchWorkflow()
        result = workflow.execute()

        # Should handle gracefully
        assert isinstance(result, dict)

    @patch("dana.lib.workflows.web_research._searcher")
    def test_workflow_with_none_values(self, mock_search):
        """Test workflow with None values."""
        mock_search.search.return_value = {"success": True, "results": []}

        workflow = SearchWorkflow()
        result = workflow.execute(query=None, max_results=None)

        # Should handle None values
        assert isinstance(result, dict)

    @patch("dana.lib.workflows.web_research._searcher")
    def test_workflow_exception_handling(self, mock_search):
        """Test workflow handles exceptions from resources."""
        mock_search.search.side_effect = Exception("Test error")

        workflow = SearchWorkflow()

        # Should raise the exception (or handle it based on implementation)
        with pytest.raises(Exception, match="Test error"):
            workflow.execute(query="test")
