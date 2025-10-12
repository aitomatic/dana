"""
Unit tests for the FactFindingWorkflow.
"""

from unittest.mock import patch

import pytest

from dana_agent.lib.workflows.web_research import (
    ExtractFactWorkflow,
    FactFindingWorkflow,
    FetchResultWorkflow,
    FormatWorkflow,
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

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    @patch("dana_agent.lib.workflows.web_research._extract_resource")
    @patch("dana_agent.lib.workflows.web_research._format_resource")
    def test_fact_finding_workflow_execute_success(self, mock_format, mock_extract, mock_fetch, mock_search):
        """Test FactFindingWorkflow execute with successful results."""
        # Setup mocks
        mock_search.search_web.return_value = {
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

        # Verify results
        assert "search_result" in result
        assert "fetch_result" in result
        assert "extracted_fact" in result
        assert "formatted_answer" in result
        assert result["search_result"]["success"] is True
        assert result["fetch_result"]["success"] is True

        # Verify resource calls
        mock_search.search_web.assert_called_once_with(query="What is the capital of France?", max_results=5)
        mock_extract.extract_fact.assert_called_once()
        mock_format.format_with_metadata.assert_called_once()

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_fact_finding_workflow_execute_with_defaults(self, mock_search):
        """Test FactFindingWorkflow execute with default parameters."""
        mock_search.search_web.return_value = {
            "success": True,
            "query": "test query",
            "results": [],
        }

        workflow = FactFindingWorkflow()
        workflow.execute(query="test query")

        # Verify default max_results is used (10)
        mock_search.search_web.assert_called_once_with(query="test query", max_results=10)

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_fact_finding_workflow_search_failure(self, mock_search):
        """Test FactFindingWorkflow when search fails."""
        mock_search.search_web.return_value = {
            "success": False,
            "error": "API key not configured",
        }

        workflow = FactFindingWorkflow()
        result = workflow.execute(query="test query")

        # Should still return result dict with error
        assert "search_result" in result
        assert result["search_result"]["success"] is False
        assert "error" in result["search_result"]

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    def test_fact_finding_workflow_fetch_failure(self, mock_fetch, mock_search):
        """Test FactFindingWorkflow when fetch fails."""
        mock_search.search_web.return_value = {
            "success": True,
            "query": "test",
            "results": [{"url": "https://example.com"}],
        }
        mock_fetch.fetch_and_extract_single.return_value = {
            "success": False,
            "error": "Failed to fetch URL",
        }

        workflow = FactFindingWorkflow()
        result = workflow.execute(query="test", url="https://example.com", purpose="test")

        # Should return results with fetch error
        assert "fetch_result" in result
        assert result["fetch_result"]["success"] is False

    def test_fact_finding_workflow_missing_query(self):
        """Test FactFindingWorkflow with missing query parameter."""
        workflow = FactFindingWorkflow()

        # Should handle missing query gracefully
        result = workflow.execute()
        assert isinstance(result, dict)


class TestSearchWorkflow:
    """Test SearchWorkflow class functionality."""

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_search_workflow_execute(self, mock_search):
        """Test SearchWorkflow execute."""
        mock_search.search_web.return_value = {
            "success": True,
            "query": "test query",
            "results": [{"title": "Test", "url": "https://test.com"}],
        }

        workflow = SearchWorkflow()
        result = workflow.execute(query="test query", max_results=5)

        assert "search_result" in result
        assert result["search_result"]["success"] is True
        mock_search.search_web.assert_called_once_with(query="test query", max_results=5)

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_search_workflow_with_default_max_results(self, mock_search):
        """Test SearchWorkflow with default max_results."""
        mock_search.search_web.return_value = {"success": True, "results": []}

        workflow = SearchWorkflow()
        workflow.execute(query="test")

        # Default max_results should be 10
        mock_search.search_web.assert_called_once_with(query="test", max_results=10)


class TestFetchResultWorkflow:
    """Test FetchResultWorkflow class functionality."""

    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    def test_fetch_result_workflow_execute(self, mock_fetch):
        """Test FetchResultWorkflow execute."""
        mock_fetch.fetch_and_extract_single.return_value = {
            "success": True,
            "content_text": "Test content",
            "metadata": {"url": "https://test.com"},
        }

        workflow = FetchResultWorkflow()
        result = workflow.execute(url="https://test.com", purpose="test purpose")

        assert "fetch_result" in result
        assert result["fetch_result"]["success"] is True
        mock_fetch.fetch_and_extract_single.assert_called_once_with(url="https://test.com", purpose="test purpose")

    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    def test_fetch_result_workflow_with_defaults(self, mock_fetch):
        """Test FetchResultWorkflow with default parameters."""
        mock_fetch.fetch_and_extract_single.return_value = {"success": True}

        workflow = FetchResultWorkflow()
        workflow.execute()

        # Should use empty string defaults
        mock_fetch.fetch_and_extract_single.assert_called_once_with(url="", purpose="")


class TestExtractFactWorkflow:
    """Test ExtractFactWorkflow class functionality."""

    @patch("dana_agent.lib.workflows.web_research._extract_resource")
    def test_extract_fact_workflow_execute(self, mock_extract):
        """Test ExtractFactWorkflow execute."""
        mock_extract.extract_fact.return_value = {
            "fact": "Paris is the capital of France",
            "confidence": 0.95,
        }

        workflow = ExtractFactWorkflow()
        result = workflow.execute(
            content="Paris is the capital and most populous city of France.",
            query="What is the capital of France?",
        )

        assert "extracted_fact" in result
        assert result["extracted_fact"]["fact"] == "Paris is the capital of France"
        assert result["extracted_fact"]["confidence"] == 0.95
        mock_extract.extract_fact.assert_called_once()


class TestFormatWorkflow:
    """Test FormatWorkflow class functionality."""

    @patch("dana_agent.lib.workflows.web_research._format_resource")
    def test_format_workflow_execute(self, mock_format):
        """Test FormatWorkflow execute."""
        mock_format.format_with_metadata.return_value = {"formatted_text": "Paris is the capital of France\nSource: Wikipedia"}

        workflow = FormatWorkflow()
        result = workflow.execute(
            content="Paris is the capital of France",
            metadata={"source": "Wikipedia"},
        )

        assert "formatted_answer" in result
        assert "Paris is the capital of France" in result["formatted_answer"]["formatted_text"]
        mock_format.format_with_metadata.assert_called_once_with(
            content="Paris is the capital of France",
            metadata={"source": "Wikipedia"},
        )

    @patch("dana_agent.lib.workflows.web_research._format_resource")
    def test_format_workflow_with_defaults(self, mock_format):
        """Test FormatWorkflow with default parameters."""
        mock_format.format_with_metadata.return_value = {"formatted_text": ""}

        workflow = FormatWorkflow()
        workflow.execute()

        # Should use empty defaults
        mock_format.format_with_metadata.assert_called_once_with(content="", metadata={})


class TestWorkflowComposition:
    """Test workflow composition using the | operator."""

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    def test_workflow_composition_operator(self, mock_fetch, mock_search):
        """Test composing workflows with | operator."""
        mock_search.search_web.return_value = {
            "success": True,
            "query": "test",
            "results": [{"url": "https://test.com"}],
        }
        mock_fetch.fetch_and_extract_single.return_value = {
            "success": True,
            "content_text": "test content",
        }

        # Compose workflows
        search_workflow = SearchWorkflow()
        fetch_workflow = FetchResultWorkflow()
        composed = search_workflow | fetch_workflow

        # Execute composed workflow
        result = composed.execute(query="test", max_results=5, url="https://test.com", purpose="test")

        # Both workflows should have executed
        assert "search_result" in result
        assert "fetch_result" in result
        assert result["search_result"]["success"] is True
        assert result["fetch_result"]["success"] is True

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    @patch("dana_agent.lib.workflows.web_research._extract_resource")
    def test_workflow_composition_chaining(self, mock_extract, mock_fetch, mock_search):
        """Test chaining multiple workflows."""
        mock_search.search_web.return_value = {"success": True, "results": []}
        mock_fetch.fetch_and_extract_single.return_value = {"success": True, "content_text": "test"}
        mock_extract.extract_fact.return_value = {"fact": "test fact", "confidence": 0.8}

        # Chain multiple workflows
        workflow = SearchWorkflow() | FetchResultWorkflow() | ExtractFactWorkflow()

        result = workflow.execute(query="test", url="https://test.com", purpose="test", content="test")

        # All three workflows should have executed
        assert "search_result" in result
        assert "fetch_result" in result
        assert "extracted_fact" in result

    def test_workflow_composition_type_error(self):
        """Test that composing with non-workflow raises TypeError."""
        workflow = SearchWorkflow()

        with pytest.raises(TypeError, match="Can only compose workflows with other workflows"):
            workflow | "not a workflow"


class TestFactFindingWorkflowIntegration:
    """Test FactFindingWorkflow integration scenarios."""

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    @patch("dana_agent.lib.workflows.web_research._extract_resource")
    @patch("dana_agent.lib.workflows.web_research._format_resource")
    def test_fact_finding_workflow_full_pipeline(self, mock_format, mock_extract, mock_fetch, mock_search):
        """Test complete FactFindingWorkflow pipeline."""
        # Setup complete mock pipeline
        mock_search.search_web.return_value = {
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

        mock_format.format_with_metadata.return_value = {
            "formatted_text": (
                "Python was created in 1991\n"
                "Source: Python (programming language) - Wikipedia\n"
                "URL: https://en.wikipedia.org/wiki/Python_(programming_language)\n"
                "Confidence: 95%"
            )
        }

        # Execute workflow
        workflow = FactFindingWorkflow()
        result = workflow.execute(query="When was Python created?", max_results=5)

        # Verify complete pipeline execution
        assert result["search_result"]["success"] is True
        assert result["fetch_result"]["success"] is True
        assert result["extracted_fact"]["fact"] == "Python was created in 1991"
        assert result["formatted_answer"]["formatted_text"] is not None

        # Verify all resources were called in order
        mock_search.search_web.assert_called_once()
        mock_fetch.fetch_and_extract_single.assert_called_once()
        mock_extract.extract_fact.assert_called_once()
        mock_format.format_with_metadata.assert_called_once()

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    @patch("dana_agent.lib.workflows.web_research._fetch_resource")
    @patch("dana_agent.lib.workflows.web_research._extract_resource")
    @patch("dana_agent.lib.workflows.web_research._format_resource")
    def test_fact_finding_workflow_data_flow(self, mock_format, mock_extract, mock_fetch, mock_search):
        """Test that data flows correctly through the workflow pipeline."""
        # Setup mocks to track data flow
        captured_extract_args = {}
        captured_format_args = {}

        def capture_extract(**kwargs):
            captured_extract_args.update(kwargs)
            return {"fact": "test fact", "confidence": 0.8}

        def capture_format(**kwargs):
            captured_format_args.update(kwargs)
            return {"formatted_text": "formatted result"}

        mock_search.search_web.return_value = {
            "success": True,
            "results": [{"url": "https://test.com"}],
        }
        mock_fetch.fetch_and_extract_single.return_value = {
            "success": True,
            "content_text": "test content from fetch",
            "metadata": {"url": "https://test.com"},
        }
        mock_extract.extract_fact.side_effect = capture_extract
        mock_format.format_with_metadata.side_effect = capture_format

        # Execute workflow
        workflow = FactFindingWorkflow()
        workflow.execute(query="test query")

        # Verify data flows from one stage to the next
        # Extract should receive content from fetch
        assert "content" in captured_extract_args
        # Format should receive content and metadata
        assert "content" in captured_format_args or "metadata" in captured_format_args


class TestWorkflowEdgeCases:
    """Test edge cases and error conditions."""

    def test_workflow_with_empty_kwargs(self):
        """Test workflow execution with empty kwargs."""
        workflow = SearchWorkflow()
        result = workflow.execute()

        # Should handle gracefully
        assert isinstance(result, dict)

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_workflow_with_none_values(self, mock_search):
        """Test workflow with None values."""
        mock_search.search_web.return_value = {"success": True, "results": []}

        workflow = SearchWorkflow()
        result = workflow.execute(query=None, max_results=None)

        # Should handle None values
        assert isinstance(result, dict)

    @patch("dana_agent.lib.workflows.web_research._search_resource")
    def test_workflow_exception_handling(self, mock_search):
        """Test workflow handles exceptions from resources."""
        mock_search.search_web.side_effect = Exception("Test error")

        workflow = SearchWorkflow()

        # Should raise the exception (or handle it based on implementation)
        with pytest.raises(Exception, match="Test error"):
            workflow.execute(query="test")
