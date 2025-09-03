"""Tests for Llama search service implementation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from dana.common.sys_resource.web_search.core.models import (
    SearchRequest,
    SearchResults,
    SearchSource,
    SearchDepth,
)
from dana.common.sys_resource.web_search.llama_search_service import (
    LlamaSearchService,
    MockLlamaSearchService,
)


class TestLlamaSearchService:
    """Tests for LlamaSearchService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test_llama_api_key_12345"

    def test_llama_search_service_initialization(self):
        """Test LlamaSearchService initialization."""
        service = LlamaSearchService(api_key=self.api_key, timeout=120)

        assert service.api_key == self.api_key
        assert service.timeout == 120.0
        assert service._client is not None

    def test_llama_search_service_from_env(self):
        """Test LlamaSearchService initialization from environment."""
        with patch.dict("os.environ", {"LLAMA_SEARCH_API_KEY": self.api_key}):
            service = LlamaSearchService(timeout=90)

            assert service.api_key == self.api_key
            assert service.timeout == 90.0

    def test_llama_search_service_missing_api_key(self):
        """Test LlamaSearchService initialization with missing API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                LlamaSearchService()

    def test_llama_search_service_defaults(self):
        """Test LlamaSearchService with default parameters."""
        service = LlamaSearchService(api_key=self.api_key)

        assert service.timeout == 180.0  # Default timeout

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful Llama search."""
        # Mock the llama-search SDK response
        mock_source_1 = MagicMock()
        mock_source_1.url = "https://example.com/page1"
        mock_source_1.content = "Content about Intel i7-12700K specifications"
        mock_source_1.full_content = "Full detailed content"

        mock_source_2 = MagicMock()
        mock_source_2.url = "https://tech.com/review"
        mock_source_2.content = "Performance review and benchmarks"
        mock_source_2.full_content = None

        mock_result = MagicMock()
        mock_result.sources = [mock_source_1, mock_source_2]

        # Mock the AsyncLlamaSearch client
        with patch("dana.common.sys_resource.web_search.llama_search_service.AsyncLlamaSearch") as mock_llama_search:
            mock_client_instance = MagicMock()
            mock_client_instance.web_search = AsyncMock(return_value=mock_result)

            # Configure the context manager
            mock_llama_search.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_llama_search.return_value.__aexit__ = AsyncMock(return_value=None)

            service = LlamaSearchService(api_key=self.api_key)

            request = SearchRequest(
                query="Intel i7-12700K specifications",
                search_depth=SearchDepth.STANDARD,
                domain="hardware",
            )

            results = await service.search(request)

            # Verify results
            assert isinstance(results, SearchResults)
            assert results.success is True
            assert len(results.sources) == 2
            assert results.error_message == ""

            # Verify first source
            source1 = results.sources[0]
            assert isinstance(source1, SearchSource)
            assert source1.url == "https://example.com/page1"
            assert source1.content == "Content about Intel i7-12700K specifications"
            assert source1.full_content == "Full detailed content"

            # Verify second source (with None full_content)
            source2 = results.sources[1]
            assert source2.url == "https://tech.com/review"
            assert source2.content == "Performance review and benchmarks"
            assert source2.full_content == ""  # Should convert None to empty string

            # Verify SDK was called with correct parameters
            mock_client_instance.web_search.assert_called_once_with(
                query="Intel i7-12700K specifications",
                search_depth=SearchDepth.STANDARD,
                domain="hardware",
            )

    @pytest.mark.asyncio
    async def test_search_with_different_depths(self):
        """Test search with different search depths."""
        mock_result = MagicMock()
        mock_result.sources = [MagicMock(url="https://test.com", content="test", full_content="")]

        with patch("dana.common.sys_resource.web_search.llama_search_service.AsyncLlamaSearch") as mock_llama_search:
            mock_client_instance = MagicMock()
            mock_client_instance.web_search = AsyncMock(return_value=mock_result)
            mock_llama_search.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_llama_search.return_value.__aexit__ = AsyncMock(return_value=None)

            service = LlamaSearchService(api_key=self.api_key)

            for depth in [SearchDepth.BASIC, SearchDepth.STANDARD, SearchDepth.EXTENSIVE]:
                request = SearchRequest(
                    query="test query",
                    search_depth=depth,
                    domain="general",
                )

                results = await service.search(request)
                assert results.success is True

                # Verify correct depth was passed to SDK
                mock_client_instance.web_search.assert_called_with(
                    query="test query",
                    search_depth=depth,
                    domain="general",
                )

    @pytest.mark.asyncio
    async def test_search_api_key_error(self):
        """Test search with invalid API key."""
        with patch("dana.common.sys_resource.web_search.llama_search_service.AsyncLlamaSearch") as mock_llama_search:
            # Mock the client to raise an authentication error
            mock_client_instance = MagicMock()
            mock_client_instance.web_search = AsyncMock(side_effect=Exception("Invalid API key"))
            mock_llama_search.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_llama_search.return_value.__aexit__ = AsyncMock(return_value=None)

            service = LlamaSearchService(api_key=self.api_key)
            request = SearchRequest(query="test query")

            results = await service.search(request)

            assert results.success is False
            assert results.sources == []
            assert results.error_message == "Invalid API key"

    @pytest.mark.asyncio
    async def test_search_insufficient_credits_error(self):
        """Test search with insufficient credits."""
        with patch("dana.common.sys_resource.web_search.llama_search_service.AsyncLlamaSearch") as mock_llama_search:
            mock_client_instance = MagicMock()
            mock_client_instance.web_search = AsyncMock(side_effect=Exception("Insufficient credits"))
            mock_llama_search.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_llama_search.return_value.__aexit__ = AsyncMock(return_value=None)

            service = LlamaSearchService(api_key=self.api_key)
            request = SearchRequest(query="test query")

            results = await service.search(request)

            assert results.success is False
            assert results.error_message == "Insufficient credits"

    @pytest.mark.asyncio
    async def test_search_timeout_error(self):
        """Test search with timeout error."""
        with patch("dana.common.sys_resource.web_search.llama_search_service.AsyncLlamaSearch") as mock_llama_search:
            mock_client_instance = MagicMock()
            mock_client_instance.web_search = AsyncMock(side_effect=Exception("Request timeout"))
            mock_llama_search.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_llama_search.return_value.__aexit__ = AsyncMock(return_value=None)

            service = LlamaSearchService(api_key=self.api_key)
            request = SearchRequest(query="test query")

            results = await service.search(request)

            assert results.success is False
            assert results.error_message == "Request timeout"

    @pytest.mark.asyncio
    async def test_search_generic_error(self):
        """Test search with generic error."""
        error_message = "Some unexpected error occurred"

        with patch("dana.common.sys_resource.web_search.llama_search_service.AsyncLlamaSearch") as mock_llama_search:
            mock_client_instance = MagicMock()
            mock_client_instance.web_search = AsyncMock(side_effect=Exception(error_message))
            mock_llama_search.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_llama_search.return_value.__aexit__ = AsyncMock(return_value=None)

            service = LlamaSearchService(api_key=self.api_key)
            request = SearchRequest(query="test query")

            results = await service.search(request)

            assert results.success is False
            assert results.error_message == f"Llama search failed: {error_message}"

    def test_get_service_info(self):
        """Test service information method."""
        service = LlamaSearchService(api_key=self.api_key, timeout=150)
        info = service.get_service_info()

        assert isinstance(info, dict)
        assert info["service_type"] == "llama_search_sdk"
        assert info["timeout"] == 150.0
        assert "basic" in info["supported_depths"]
        assert "standard" in info["supported_depths"]
        assert "extensive" in info["supported_depths"]
        assert info["sdk_version"] == "official_llama_search_sdk"

    @pytest.mark.asyncio
    async def test_search_empty_sources(self):
        """Test search with empty sources from SDK."""
        mock_result = MagicMock()
        mock_result.sources = []

        with patch("dana.common.sys_resource.web_search.llama_search_service.AsyncLlamaSearch") as mock_llama_search:
            mock_client_instance = MagicMock()
            mock_client_instance.web_search = AsyncMock(return_value=mock_result)
            mock_llama_search.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_llama_search.return_value.__aexit__ = AsyncMock(return_value=None)

            service = LlamaSearchService(api_key=self.api_key)
            request = SearchRequest(query="empty results query")

            results = await service.search(request)

            assert results.success is True
            assert len(results.sources) == 0


class TestMockLlamaSearchService:
    """Tests for MockLlamaSearchService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = MockLlamaSearchService()

    def test_mock_llama_search_service_initialization(self):
        """Test MockLlamaSearchService initialization."""
        mock_service = MockLlamaSearchService(
            base_url="https://custom-mock.com",
            timeout=60,
        )

        assert mock_service.base_url == "https://custom-mock.com"
        assert mock_service.timeout == 60

    def test_mock_llama_search_service_defaults(self):
        """Test MockLlamaSearchService with default parameters."""
        assert self.mock_service.base_url == "https://mock-llama-search.com"
        assert self.mock_service.timeout == 120

    @pytest.mark.asyncio
    async def test_mock_search_basic_functionality(self):
        """Test mock search service basic functionality."""
        request = SearchRequest(
            query="Intel i7-12700K specifications",
            search_depth=SearchDepth.STANDARD,
            domain="hardware",
        )

        results = await self.mock_service.search(request)

        assert isinstance(results, SearchResults)
        assert results.success is True
        assert len(results.sources) == 2  # Standard depth returns 2 sources
        assert results.error_message == ""
        assert "Mock llama-search executed" in results.raw_data

        # Verify sources contain query-related content
        source1 = results.sources[0]
        assert "Intel i7-12700K specifications" in source1.content
        assert "Intel-i7-12700K-specifications" in source1.url

        source2 = results.sources[1]
        assert "Intel i7-12700K specifications" in source2.content
        assert "hardware" in source2.content  # Domain included in content

    @pytest.mark.asyncio
    async def test_mock_search_different_depths(self):
        """Test mock search with different search depths."""
        depth_limits = {"basic": 1, "standard": 2, "extensive": 3}

        for depth, expected_count in depth_limits.items():
            request = SearchRequest(
                query="test product",
                search_depth=getattr(SearchDepth, depth.upper()),
            )

            results = await self.mock_service.search(request)

            assert results.success is True
            assert len(results.sources) == expected_count
            assert all(isinstance(source, SearchSource) for source in results.sources)

    @pytest.mark.asyncio
    async def test_mock_search_with_full_content(self):
        """Test mock search with full content enabled."""
        request = SearchRequest(
            query="test product",
            with_full_content=True,
        )

        results = await self.mock_service.search(request)

        assert results.success is True
        for source in results.sources:
            assert source.full_content != ""
            assert "Extended mock content" in source.full_content

    @pytest.mark.asyncio
    async def test_mock_search_without_full_content(self):
        """Test mock search without full content."""
        request = SearchRequest(
            query="test product",
            with_full_content=False,
        )

        results = await self.mock_service.search(request)

        assert results.success is True
        for source in results.sources:
            assert source.full_content == ""

    @pytest.mark.asyncio
    async def test_mock_search_with_domain(self):
        """Test mock search with specific domain."""
        request = SearchRequest(
            query="test product",
            domain="electronics",
        )

        results = await self.mock_service.search(request)

        assert results.success is True
        # Check that domain appears in at least one source's content
        found_domain = any("electronics" in source.content for source in results.sources)
        assert found_domain

    @pytest.mark.asyncio
    async def test_mock_search_simulated_delay(self):
        """Test that mock search includes simulated API delay."""
        import time

        start_time = time.time()

        request = SearchRequest(query="test query")
        await self.mock_service.search(request)

        end_time = time.time()
        elapsed = end_time - start_time

        # Should have at least the simulated delay (0.2 seconds)
        assert elapsed >= 0.2

    @pytest.mark.asyncio
    async def test_mock_search_query_variations(self):
        """Test mock search with various query types."""
        queries = [
            "simple query",
            "query with spaces and special chars!",
            "very-long-query-with-many-words-and-hyphens-that-should-be-handled-properly",
            "",  # Empty query
        ]

        for query in queries:
            request = SearchRequest(query=query)
            results = await self.mock_service.search(request)

            assert results.success is True
            assert len(results.sources) >= 1

            if query:  # Non-empty query
                assert query in results.sources[0].content

    def test_mock_service_string_representation(self):
        """Test MockLlamaSearchService string representation."""
        service_str = str(self.mock_service)
        assert "MockLlamaSearchService" in service_str
        assert self.mock_service.base_url in service_str

    @pytest.mark.asyncio
    async def test_mock_search_results_structure(self):
        """Test that mock search results maintain proper structure."""
        request = SearchRequest(
            query="structure test",
            search_depth=SearchDepth.EXTENSIVE,
            domain="test_domain",
            with_full_content=True,
        )

        results = await self.mock_service.search(request)

        # Verify overall structure
        assert isinstance(results, SearchResults)
        assert hasattr(results, "success")
        assert hasattr(results, "sources")
        assert hasattr(results, "raw_data")
        assert hasattr(results, "error_message")

        # Verify sources structure
        for source in results.sources:
            assert isinstance(source, SearchSource)
            assert hasattr(source, "url")
            assert hasattr(source, "content")
            assert hasattr(source, "full_content")
            assert source.url.startswith("https://")
            assert len(source.content) > 0


if __name__ == "__main__":
    pytest.main([__file__])
