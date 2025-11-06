"""Tests for composed workflows in web_research.py"""

from unittest.mock import patch

from dana.lib.workflows.web_research import (
    GoogleLookupWorkflow,
    ResearchSynthesisWorkflow,
    StructuredDataNavigationWorkflow,
)


class TestGoogleLookupWorkflow:
    """Test GoogleLookupWorkflow composition."""

    @patch("dana.lib.workflows.web_research._extractor")
    @patch("dana.lib.workflows.web_research._searcher")
    def test_google_lookup_success(self, mock_search, mock_extractor):
        """Test GoogleLookupWorkflow successful execution."""
        # Mock search results
        mock_search.search.return_value = {
            "success": True,
            "query": "What is Python?",
            "results": [
                {
                    "title": "Python Programming Language",
                    "url": "https://python.org",
                    "snippet": "Python is a high-level programming language",
                }
            ],
        }

        # Mock extractor
        mock_extractor.extract_answer_from_search.return_value = {
            "success": True,
            "answer": "Python is a high-level programming language",
            "source": "python.org",
        }

        workflow = GoogleLookupWorkflow()
        result = workflow.execute(query="What is Python?")

        # Verify search was called
        mock_search.search.assert_called_once()

        # Verify result structure
        assert result["success"] is True
        assert result["answer"] == "Python is a high-level programming language"
        assert result["source"] == "python.org"

    @patch("dana.lib.workflows.web_research._extractor")
    @patch("dana.lib.workflows.web_research._searcher")
    def test_google_lookup_with_max_results(self, mock_search, mock_extractor):
        """Test GoogleLookupWorkflow with custom max_results."""
        mock_search.search.return_value = {
            "success": True,
            "query": "test",
            "results": [{"url": "https://test.com"}],
        }
        mock_extractor.extract_answer_from_search.return_value = {
            "success": True,
            "answer": "Test answer",
            "source": "test.com",
        }

        workflow = GoogleLookupWorkflow()
        workflow.execute(query="test query", max_results=3)

        # Verify max_results was passed through
        call_args = mock_search.search.call_args
        assert call_args.kwargs["max_results"] == 3

    @patch("dana.lib.workflows.web_research._extractor")
    @patch("dana.lib.workflows.web_research._searcher")
    def test_google_lookup_search_failure(self, mock_search, mock_extractor):
        """Test GoogleLookupWorkflow when search fails."""
        mock_search.search.return_value = {
            "success": False,
            "error": "API error",
            "results": [],
        }
        mock_extractor.extract_answer_from_search.return_value = {
            "success": False,
            "answer": "",
            "source": "",
        }

        workflow = GoogleLookupWorkflow()
        result = workflow.execute(query="test")

        assert result["success"] is False


class TestResearchSynthesisWorkflow:
    """Test ResearchSynthesisWorkflow composition."""

    @patch("dana.lib.workflows.web_research._synthesizer")
    @patch("dana.lib.workflows.web_research._fetcher")
    @patch("dana.lib.workflows.web_research._searcher")
    def test_research_synthesis_success(self, mock_search, mock_fetcher, mock_synthesizer):
        """Test ResearchSynthesisWorkflow successful execution."""
        # Mock search results
        mock_search.search.return_value = {
            "success": True,
            "query": "renewable energy",
            "results": [
                {"url": "https://energy1.com", "title": "Solar Power", "relevance": 0.9},
                {"url": "https://energy2.com", "title": "Wind Power", "relevance": 0.8},
            ],
        }

        # Mock ranking
        mock_search.rank_by_relevance.return_value = {
            "ranked_results": [
                {"url": "https://energy1.com", "title": "Solar Power", "relevance": 0.9},
                {"url": "https://energy2.com", "title": "Wind Power", "relevance": 0.8},
            ]
        }

        # Mock fetch
        mock_fetcher.fetch_and_extract.return_value = {
            "extractions": [
                {"content": "Solar power content", "url": "https://energy1.com"},
                {"content": "Wind power content", "url": "https://energy2.com"},
            ]
        }

        # Mock synthesis
        mock_synthesizer.synthesize_by_themes.return_value = {
            "success": True,
            "synthesis": "Renewable energy sources include solar and wind...",
            "themes": ["solar", "wind"],
            "confidence": 0.85,
        }

        workflow = ResearchSynthesisWorkflow()
        result = workflow.execute(query="renewable energy", max_sources=2)

        # Verify search was called with doubled max_results (pre_callable)
        call_args = mock_search.search.call_args
        assert call_args.kwargs["max_results"] == 4  # max_sources * 2

        # Verify result structure
        assert result["success"] is True
        assert "synthesis" in result
        assert "themes" in result

    @patch("dana.lib.workflows.web_research._synthesizer")
    @patch("dana.lib.workflows.web_research._fetcher")
    @patch("dana.lib.workflows.web_research._searcher")
    def test_research_synthesis_timeline_type(self, mock_search, mock_fetcher, mock_synthesizer):
        """Test ResearchSynthesisWorkflow with timeline synthesis."""
        mock_search.search.return_value = {
            "success": True,
            "query": "AI history",
            "results": [{"url": "https://ai.com"}],
        }
        mock_search.rank_by_relevance.return_value = {"ranked_results": [{"url": "https://ai.com"}]}
        mock_fetcher.fetch_and_extract.return_value = {"extractions": [{"content": "AI content"}]}

        # Mock timeline synthesis
        mock_synthesizer.synthesize_by_timeline.return_value = {
            "success": True,
            "synthesis": "Timeline of AI development...",
            "timeline": [{"year": 1950, "event": "Turing Test"}],
        }

        workflow = ResearchSynthesisWorkflow()
        result = workflow.execute(query="AI history", synthesis_type="timeline")

        # Verify timeline synthesizer was used
        mock_synthesizer.synthesize_by_timeline.assert_called_once()
        assert "timeline" in result

    @patch("dana.lib.workflows.web_research._synthesizer")
    @patch("dana.lib.workflows.web_research._fetcher")
    @patch("dana.lib.workflows.web_research._searcher")
    def test_research_synthesis_default_max_sources(self, mock_search, mock_fetcher, mock_synthesizer):
        """Test ResearchSynthesisWorkflow with default max_sources."""
        mock_search.search.return_value = {"success": True, "query": "test", "results": []}
        mock_search.rank_by_relevance.return_value = {"ranked_results": []}
        mock_fetcher.fetch_and_extract.return_value = {"extractions": []}
        mock_synthesizer.synthesize_by_themes.return_value = {"success": True, "synthesis": ""}

        workflow = ResearchSynthesisWorkflow()
        workflow.execute(query="test")

        # Verify default max_sources (5) results in max_results=10
        call_args = mock_search.search.call_args
        assert call_args.kwargs["max_results"] == 10  # default max_sources (5) * 2


class TestStructuredDataNavigationWorkflow:
    """Test StructuredDataNavigationWorkflow."""

    @patch("dana.lib.workflows.web_research._extractor")
    def test_structured_data_with_query(self, mock_extractor):
        """Test StructuredDataNavigationWorkflow with query."""
        mock_extractor.navigate_and_extract_structured.return_value = {
            "success": True,
            "tables": [{"headers": ["Name", "Value"], "rows": [["Test", "123"]]}],
            "lists": [["item1", "item2"]],
            "statistics": {"total_pages": 5},
        }

        workflow = StructuredDataNavigationWorkflow()
        result = workflow.execute(query="test query", max_pages=5)

        assert result["success"] is True
        assert len(result["tables"]) == 1
        assert len(result["lists"]) == 1
        assert result["statistics"]["total_pages"] == 5

    @patch("dana.lib.workflows.web_research._extractor")
    def test_structured_data_with_url(self, mock_extractor):
        """Test StructuredDataNavigationWorkflow with URL."""
        mock_extractor.navigate_and_extract_structured.return_value = {
            "success": True,
            "tables": [],
            "lists": [],
            "statistics": {},
        }

        workflow = StructuredDataNavigationWorkflow()
        result = workflow.execute(url="https://example.com", max_pages=10)

        mock_extractor.navigate_and_extract_structured.assert_called_once()
        assert result["success"] is True

    def test_structured_data_missing_query_and_url(self):
        """Test StructuredDataNavigationWorkflow without query or URL."""
        workflow = StructuredDataNavigationWorkflow()
        result = workflow.execute()

        # Should return validation error
        assert result["success"] is False
        assert result["error"] == "validation_error"
        assert "query" in result["message"] or "url" in result["message"]

    @patch("dana.lib.workflows.web_research._extractor")
    def test_structured_data_custom_options(self, mock_extractor):
        """Test StructuredDataNavigationWorkflow with custom extract options."""
        mock_extractor.navigate_and_extract_structured.return_value = {
            "success": True,
            "tables": [],
            "lists": [],
            "statistics": {},
        }

        workflow = StructuredDataNavigationWorkflow()
        workflow.execute(
            url="https://example.com",
            max_pages=20,
            extract_tables=False,
            extract_lists=True,
            rate_limit_sec=2.0,
        )

        # Verify parameters were passed through
        call_args = mock_extractor.navigate_and_extract_structured.call_args
        assert call_args.kwargs["max_pages"] == 20
        assert call_args.kwargs["extract_tables"] is False
        assert call_args.kwargs["extract_lists"] is True
        assert call_args.kwargs["rate_limit_sec"] == 2.0


class TestWorkflowCompositionIntegration:
    """Integration tests for workflow composition patterns."""

    @patch("dana.lib.workflows.web_research._extractor")
    @patch("dana.lib.workflows.web_research._searcher")
    def test_google_lookup_preserves_context(self, mock_search, mock_extractor):
        """Test that GoogleLookupWorkflow preserves input context."""
        mock_search.search.return_value = {
            "success": True,
            "query": "test",
            "results": [{"url": "https://test.com"}],
        }
        mock_extractor.extract_answer_from_search.return_value = {
            "success": True,
            "answer": "Test answer",
            "source": "test.com",
        }

        workflow = GoogleLookupWorkflow()
        # Pass extra context
        result = workflow.execute(query="test", custom_field="custom_value")

        # Context should be preserved in result
        assert result["custom_field"] == "custom_value"
        assert result["query"] == "test"

    @patch("dana.lib.workflows.web_research._synthesizer")
    @patch("dana.lib.workflows.web_research._fetcher")
    @patch("dana.lib.workflows.web_research._searcher")
    def test_research_synthesis_pre_callable_adjusts_params(self, mock_search, mock_fetcher, mock_synthesizer):
        """Test that ResearchSynthesisWorkflow pre_callable modifies params correctly."""
        mock_search.search.return_value = {"success": True, "query": "test", "results": []}
        mock_search.rank_by_relevance.return_value = {"ranked_results": []}
        mock_fetcher.fetch_and_extract.return_value = {"extractions": []}
        mock_synthesizer.synthesize_by_themes.return_value = {"success": True, "synthesis": ""}

        workflow = ResearchSynthesisWorkflow()

        # Test with max_sources=10
        workflow.execute(query="test", max_sources=10)

        # Verify pre_callable doubled max_sources to max_results
        call_args = mock_search.search.call_args
        assert call_args.kwargs["max_results"] == 20  # max_sources * 2
