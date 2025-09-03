"""Tests for WebSearchResource main implementation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from dana.common.exceptions import ResourceError
from dana.common.sys_resource.web_search.web_search_resource import WebSearchResource
from dana.common.sys_resource.web_search.core.models import (
    SearchRequest,
    SearchResults,
    SearchSource,
    SearchDepth,
)


class TestWebSearchResource:
    """Tests for WebSearchResource."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock both search services to prevent actual initialization
        self.google_service_patcher = patch("dana.common.sys_resource.web_search.web_search_resource.GoogleSearchService")
        self.llama_service_patcher = patch("dana.common.sys_resource.web_search.web_search_resource.LlamaSearchService")

        self.mock_google_service_class = self.google_service_patcher.start()
        self.mock_llama_service_class = self.llama_service_patcher.start()

        # Create mock instances
        self.mock_google_service = MagicMock()
        self.mock_llama_service = MagicMock()

        self.mock_google_service_class.return_value = self.mock_google_service
        self.mock_llama_service_class.return_value = self.mock_llama_service

    def teardown_method(self):
        """Clean up after tests."""
        self.google_service_patcher.stop()
        self.llama_service_patcher.stop()

    def test_web_search_resource_initialization_google(self):
        """Test WebSearchResource initialization with Google service."""
        resource = WebSearchResource(
            service_type="google",
            name="test_google_search",
            description="Test Google search resource",
        )

        assert resource.name == "test_google_search"
        assert "Google" in resource.description
        assert resource._search_service == self.mock_google_service
        assert resource._is_ready is False

        # Verify Google service was instantiated
        self.mock_google_service_class.assert_called_once()

    def test_web_search_resource_initialization_llama(self):
        """Test WebSearchResource initialization with Llama service."""
        resource = WebSearchResource(
            service_type="llama-search",
            name="test_llama_search",
        )

        assert resource.name == "test_llama_search"
        assert "llama-search" in resource.description
        assert resource._search_service == self.mock_llama_service

        # Verify Llama service was instantiated
        self.mock_llama_service_class.assert_called_once()

    def test_web_search_resource_initialization_default_service(self):
        """Test WebSearchResource initialization with default service (fallback to Llama)."""
        resource = WebSearchResource(service_type="unknown_service")

        # Should fallback to LlamaSearchService for unknown service types
        assert resource._search_service == self.mock_llama_service
        self.mock_llama_service_class.assert_called_once()

    def test_web_search_resource_initialization_empty_service_type(self):
        """Test WebSearchResource initialization with empty service type."""
        resource = WebSearchResource(service_type="")

        # Should fallback to LlamaSearchService for empty service type
        assert resource._search_service == self.mock_llama_service
        self.mock_llama_service_class.assert_called_once()

    def test_web_search_resource_default_parameters(self):
        """Test WebSearchResource with default parameters."""
        resource = WebSearchResource()

        assert resource.name == "web_search"
        assert "Web Search Resource using " in resource.description
        assert resource._search_service == self.mock_llama_service  # Default fallback

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful WebSearchResource initialization."""
        # Mock service availability check
        self.mock_google_service.is_available.return_value = True

        resource = WebSearchResource(service_type="google")

        # Mock base class initialization
        with patch("dana.common.sys_resource.base_sys_resource.BaseSysResource.initialize") as mock_base_init:
            mock_base_init.return_value = None

            await resource.initialize()

            assert resource._is_ready is True
            mock_base_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_service_unavailable(self):
        """Test initialization failure when service is unavailable."""
        # Mock service availability check to return False
        self.mock_google_service.is_available.return_value = False

        resource = WebSearchResource(service_type="google")

        with patch("dana.common.sys_resource.base_sys_resource.BaseSysResource.initialize"):
            with pytest.raises(ResourceError, match="Search service.*is not available"):
                await resource.initialize()

    @pytest.mark.asyncio
    async def test_initialize_service_no_availability_check(self):
        """Test initialization when service doesn't have is_available method."""
        # Remove is_available method from mock
        delattr(self.mock_llama_service, "is_available")

        resource = WebSearchResource(service_type="llama-search")

        with patch("dana.common.sys_resource.base_sys_resource.BaseSysResource.initialize"):
            # Should not raise an error - services without is_available are assumed available
            await resource.initialize()
            assert resource._is_ready is True

    @pytest.mark.asyncio
    async def test_search_basic_functionality(self):
        """Test basic search functionality."""
        # Mock search results
        mock_sources = [
            SearchSource(
                url="https://example.com/result1",
                content="Content about Intel processor specifications",
            ),
            SearchSource(
                url="https://tech.com/result2",
                content="Performance benchmarks and reviews",
            ),
        ]

        mock_results = SearchResults(
            success=True,
            sources=mock_sources,
            raw_data="Mock search metadata",
        )

        self.mock_google_service.search = AsyncMock(return_value=mock_results)

        resource = WebSearchResource(service_type="google")
        resource._is_ready = True  # Skip initialization

        results = await resource.search(
            query="Intel i7-12700K specifications",
            search_depth=SearchDepth.STANDARD,
            domain="hardware",
            with_full_content=False,
        )

        # Verify results
        assert isinstance(results, SearchResults)
        assert results.success is True
        assert len(results.sources) == 2
        assert results.sources[0].url == "https://example.com/result1"

        # Verify search service was called with correct parameters
        expected_request = SearchRequest(
            query="Intel i7-12700K specifications",
            search_depth=SearchDepth.STANDARD,
            domain="hardware",
            with_full_content=False,
        )

        self.mock_google_service.search.assert_called_once()
        actual_request = self.mock_google_service.search.call_args[0][0]
        assert actual_request.query == expected_request.query
        assert actual_request.search_depth == expected_request.search_depth
        assert actual_request.domain == expected_request.domain
        assert actual_request.with_full_content == expected_request.with_full_content

    @pytest.mark.asyncio
    async def test_search_with_different_depths(self):
        """Test search with different search depths."""
        mock_results = SearchResults(
            success=True,
            sources=[SearchSource(url="https://test.com", content="Test content")],
        )

        self.mock_llama_service.search = AsyncMock(return_value=mock_results)

        resource = WebSearchResource(service_type="llama-search")
        resource._is_ready = True

        # Test different search depths
        for depth in [SearchDepth.BASIC, SearchDepth.STANDARD, SearchDepth.EXTENSIVE]:
            await resource.search(
                query="test query",
                search_depth=depth,
            )

            # Verify correct depth was passed
            call_args = self.mock_llama_service.search.call_args[0][0]
            assert call_args.search_depth == depth

    @pytest.mark.asyncio
    async def test_search_auto_initialize(self):
        """Test that search auto-initializes if not ready."""
        mock_results = SearchResults(
            success=True,
            sources=[SearchSource(url="https://test.com", content="Content")],
        )

        self.mock_llama_service.search = AsyncMock(return_value=mock_results)

        resource = WebSearchResource(service_type="llama-search")
        assert resource._is_ready is False

        with patch.object(resource, "initialize", new_callable=AsyncMock) as mock_initialize:
            await resource.search("test query")

            mock_initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_full_content(self):
        """Test search with full content enabled."""
        mock_source = SearchSource(
            url="https://example.com",
            content="Brief content",
            full_content="Full detailed content with complete information",
        )

        mock_results = SearchResults(success=True, sources=[mock_source])
        self.mock_google_service.search = AsyncMock(return_value=mock_results)

        resource = WebSearchResource(service_type="google")
        resource._is_ready = True

        await resource.search(
            query="detailed information",
            with_full_content=True,
        )

        # Verify with_full_content was passed correctly
        call_args = self.mock_google_service.search.call_args[0][0]
        assert call_args.with_full_content is True

    @pytest.mark.asyncio
    async def test_search_default_parameters(self):
        """Test search with default parameters."""
        mock_results = SearchResults(
            success=True,
            sources=[SearchSource(url="https://test.com", content="Test")],
        )

        self.mock_llama_service.search = AsyncMock(return_value=mock_results)

        resource = WebSearchResource()
        resource._is_ready = True

        await resource.search("simple query")

        # Verify default parameters
        call_args = self.mock_llama_service.search.call_args[0][0]
        assert call_args.query == "simple query"
        assert call_args.search_depth == SearchDepth.STANDARD
        assert call_args.domain == ""
        assert call_args.with_full_content is False

    @pytest.mark.asyncio
    async def test_search_service_exception_handling(self):
        """Test search with service exception handling."""
        # Mock service to raise an exception
        self.mock_google_service.search = AsyncMock(side_effect=Exception("Service unavailable"))

        resource = WebSearchResource(service_type="google")
        resource._is_ready = True

        with pytest.raises(ResourceError, match="Search failed: Service unavailable"):
            await resource.search("test query")

    @pytest.mark.asyncio
    async def test_search_failed_results(self):
        """Test search with failed search results."""
        failed_results = SearchResults(
            success=False,
            sources=[],
            error_message="No results found for query",
        )

        self.mock_llama_service.search = AsyncMock(return_value=failed_results)

        resource = WebSearchResource(service_type="llama-search")
        resource._is_ready = True

        results = await resource.search("nonexistent query")

        # Should return the failed results without raising an exception
        assert results.success is False
        assert results.error_message == "No results found for query"

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Test search with empty query."""
        mock_results = SearchResults(
            success=True,
            sources=[SearchSource(url="https://test.com", content="Default content")],
        )

        self.mock_llama_service.search = AsyncMock(return_value=mock_results)

        resource = WebSearchResource()
        resource._is_ready = True

        # Should handle empty query gracefully
        results = await resource.search("")
        assert isinstance(results, SearchResults)

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self):
        """Test search with special characters in query."""
        special_query = "Intel® Core™ i7-12700K (LGA1700) ~$400"

        mock_results = SearchResults(
            success=True,
            sources=[SearchSource(url="https://test.com", content="Special char content")],
        )

        self.mock_google_service.search = AsyncMock(return_value=mock_results)

        resource = WebSearchResource(service_type="google")
        resource._is_ready = True

        await resource.search(special_query)

        # Verify special characters are preserved
        call_args = self.mock_google_service.search.call_args[0][0]
        assert call_args.query == special_query

    def test_search_parameter_combinations(self):
        """Test various parameter combinations for search method."""
        WebSearchResource(service_type="google")

        # Test that all parameter combinations are accepted without errors
        test_combinations = [
            {"query": "test", "search_depth": SearchDepth.BASIC},
            {"query": "test", "domain": "tech", "with_full_content": True},
            {"query": "test", "search_depth": SearchDepth.EXTENSIVE, "domain": "science"},
            {"query": "test", "search_depth": SearchDepth.STANDARD, "with_full_content": False},
        ]

        for params in test_combinations:
            # Should not raise any exceptions during parameter validation
            request = SearchRequest(
                query=params["query"],
                search_depth=params.get("search_depth", SearchDepth.STANDARD),
                domain=params.get("domain", ""),
                with_full_content=params.get("with_full_content", False),
            )
            assert isinstance(request, SearchRequest)

    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        """Test multiple concurrent search requests."""
        import asyncio

        mock_results = SearchResults(
            success=True,
            sources=[SearchSource(url="https://test.com", content="Concurrent content")],
        )

        self.mock_llama_service.search = AsyncMock(return_value=mock_results)

        resource = WebSearchResource(service_type="llama-search")
        resource._is_ready = True

        # Execute multiple searches concurrently
        queries = ["query1", "query2", "query3"]
        tasks = [resource.search(query) for query in queries]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 3
        assert all(result.success for result in results)

        # Service should have been called for each query
        assert self.mock_llama_service.search.call_count == 3


class TestWebSearchResourceIntegration:
    """Integration tests for WebSearchResource with real-like scenarios."""

    def setup_method(self):
        """Set up integration test fixtures."""
        # Use real service classes but with mocked dependencies
        pass

    @pytest.mark.asyncio
    async def test_full_google_workflow_simulation(self):
        """Test complete Google search workflow simulation."""
        with patch("dana.common.sys_resource.web_search.google_search_service.load_google_config") as mock_config:
            with patch("os.getenv") as mock_getenv:
                # Mock configuration
                from dana.common.sys_resource.web_search.google.config import GoogleSearchConfig

                mock_config.return_value = GoogleSearchConfig(
                    api_key="test_key_123456789",
                    cse_id="test_cse_id",
                )
                mock_getenv.return_value = None  # No OpenAI key

                # Mock Google search engine
                with patch("dana.common.sys_resource.web_search.google.search_engine.GoogleSearchEngine") as mock_engine_class:
                    mock_engine = MagicMock()
                    mock_engine.is_available.return_value = True
                    mock_engine_class.return_value = mock_engine

                    # Mock other dependencies
                    with patch("dana.common.sys_resource.web_search.google.result_processor.ResultProcessor"):
                        with patch("dana.common.sys_resource.web_search.google.reference_extractor.ReferenceExtractor"):
                            resource = WebSearchResource(service_type="google")

                            # Mock the actual search method
                            expected_results = SearchResults(
                                success=True,
                                sources=[
                                    SearchSource(
                                        url="https://intel.com/specs",
                                        content="Intel i7-12700K: 12 cores, 3.6 GHz base frequency",
                                    )
                                ],
                            )

                            resource._search_service.search = AsyncMock(return_value=expected_results)

                            # Execute search
                            results = await resource.search(
                                query="Intel i7-12700K specifications",
                                search_depth=SearchDepth.EXTENSIVE,
                            )

                            # Verify results
                            assert results.success is True
                            assert len(results.sources) == 1
                            assert "Intel i7-12700K" in results.sources[0].content

    @pytest.mark.asyncio
    async def test_full_llama_workflow_simulation(self):
        """Test complete Llama search workflow simulation."""
        with patch("dana.common.sys_resource.web_search.llama_search_service.AsyncLlamaSearch") as mock_llama_class:
            # Mock SDK client
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_source = MagicMock()
            mock_source.url = "https://example.com/llama-result"
            mock_source.content = "Llama search result content"
            mock_source.full_content = "Full Llama content"
            mock_result.sources = [mock_source]

            mock_client.web_search = AsyncMock(return_value=mock_result)
            mock_llama_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_llama_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Set up environment
            with patch.dict("os.environ", {"LLAMA_SEARCH_API_KEY": "test_llama_key"}):
                resource = WebSearchResource(service_type="llama-search")

                results = await resource.search(
                    query="machine learning models",
                    search_depth=SearchDepth.STANDARD,
                    domain="ai",
                )

                # Verify results
                assert results.success is True
                assert len(results.sources) == 1
                assert results.sources[0].url == "https://example.com/llama-result"
                assert results.sources[0].content == "Llama search result content"


if __name__ == "__main__":
    pytest.main([__file__])
