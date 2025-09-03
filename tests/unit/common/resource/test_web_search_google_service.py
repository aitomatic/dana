"""Tests for Google search service implementation."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from dana.common.sys_resource.web_search.core.models import (
    SearchRequest,
    SearchResults,
    SearchSource,
    SearchDepth,
)
from dana.common.sys_resource.web_search.google.search_engine import (
    GoogleSearchEngine,
    GoogleResult,
    _sanitize_api_key,
)
from dana.common.sys_resource.web_search.google.config import (
    GoogleSearchConfig,
    load_google_config,
    _mask_api_key,
)
from dana.common.sys_resource.web_search.google.exceptions import (
    APIKeyError,
    ConfigurationError,
    GoogleSearchError,
    RateLimitError,
    ServiceUnavailableError,
)
from dana.common.sys_resource.web_search.google_search_service import (
    GoogleSearchService,
    MockGoogleSearchService,
    create_google_search_service,
)


class TestGoogleSearchConfig:
    """Tests for GoogleSearchConfig."""

    def test_google_config_creation(self):
        """Test basic GoogleSearchConfig creation."""
        config = GoogleSearchConfig(
            api_key="test_api_key_1234567890",
            cse_id="test_cse_id_123",
            max_results=5,
        )

        assert config.api_key == "test_api_key_1234567890"
        assert config.cse_id == "test_cse_id_123"
        assert config.max_results == 5
        assert config.enable_content_extraction is True

    def test_google_config_defaults(self):
        """Test GoogleSearchConfig with default values."""
        config = GoogleSearchConfig(
            api_key="test_key",
            cse_id="test_cse",
        )

        assert config.max_results == 10
        assert config.timeout_seconds == 30
        assert config.enable_content_extraction is True
        assert config.max_content_length == 50000

    def test_google_config_validation_missing_api_key(self):
        """Test configuration validation with missing API key."""
        with pytest.raises(ConfigurationError, match="Google Search API key is required"):
            GoogleSearchConfig(api_key="", cse_id="test_cse")

    def test_google_config_validation_missing_cse_id(self):
        """Test configuration validation with missing CSE ID."""
        with pytest.raises(ConfigurationError, match="Google Custom Search Engine ID is required"):
            GoogleSearchConfig(api_key="test_key", cse_id="")

    def test_google_config_validation_invalid_max_results(self):
        """Test configuration validation with invalid max_results."""
        with pytest.raises(ConfigurationError, match="max_results must be positive"):
            GoogleSearchConfig(
                api_key="test_key",
                cse_id="test_cse",
                max_results=0,
            )

        with pytest.raises(ConfigurationError, match="max_results cannot exceed 10"):
            GoogleSearchConfig(
                api_key="test_key",
                cse_id="test_cse",
                max_results=15,
            )

    def test_google_config_str_representation(self):
        """Test GoogleSearchConfig string representation masks sensitive data."""
        config = GoogleSearchConfig(
            api_key="test_api_key_1234567890",
            cse_id="test_cse_id_123456789",
        )

        config_str = str(config)
        assert "test_api_key_1234567890" not in config_str
        assert "test****7890" in config_str
        assert "test_cse_..." in config_str

    def test_mask_api_key_function(self):
        """Test API key masking utility function."""
        # Normal case
        masked = _mask_api_key("test_api_key_1234567890")
        assert masked == "test****7890"

        # Short key
        short_masked = _mask_api_key("short")
        assert short_masked == "****"

        # Empty key
        empty_masked = _mask_api_key("")
        assert empty_masked == "****"


class TestLoadGoogleConfig:
    """Tests for loading Google configuration from environment."""

    @patch.dict(
        "os.environ",
        {
            "GOOGLE_SEARCH_API_KEY": "env_api_key_123",
            "GOOGLE_SEARCH_CX": "env_cse_id_456",
        },
    )
    def test_load_google_config_from_env(self):
        """Test loading configuration from environment variables."""
        config = load_google_config()

        assert config.api_key == "env_api_key_123"
        assert config.cse_id == "env_cse_id_456"
        assert config.max_results == 10  # Default value

    @patch.dict("os.environ", {}, clear=True)
    def test_load_google_config_missing_api_key(self):
        """Test loading configuration with missing API key."""
        with pytest.raises(ConfigurationError, match="GOOGLE_SEARCH_API_KEY environment variable is required"):
            load_google_config()

    @patch.dict(
        "os.environ",
        {
            "GOOGLE_SEARCH_API_KEY": "test_key",
        },
    )
    def test_load_google_config_missing_cse_id(self):
        """Test loading configuration with missing CSE ID."""
        with pytest.raises(ConfigurationError, match="GOOGLE_SEARCH_CX environment variable is required"):
            load_google_config()

    @patch.dict(
        "os.environ",
        {
            "GOOGLE_SEARCH_API_KEY": "test_key",
            "GOOGLE_SEARCH_CX": "test_cse",
            "GOOGLE_SEARCH_MAX_RESULTS": "5",
            "GOOGLE_SEARCH_TIMEOUT": "45",
            "ENABLE_CONTENT_EXTRACTION": "false",
        },
    )
    def test_load_google_config_with_optional_params(self):
        """Test loading configuration with optional environment variables."""
        config = load_google_config()

        assert config.api_key == "test_key"
        assert config.cse_id == "test_cse"
        assert config.max_results == 5
        assert config.timeout_seconds == 45
        assert config.enable_content_extraction is False


class TestGoogleSearchEngine:
    """Tests for GoogleSearchEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = GoogleSearchConfig(
            api_key="test_api_key_123456789",
            cse_id="test_cse_id_123",
            max_results=5,
        )
        self.engine = GoogleSearchEngine(self.config)

    def test_google_search_engine_initialization(self):
        """Test GoogleSearchEngine initialization."""
        assert self.engine.config == self.config
        assert self.engine.base_url == "https://www.googleapis.com/customsearch/v1"

    def test_is_available(self):
        """Test GoogleSearchEngine availability check."""
        assert self.engine.is_available() is True

        # Test with missing credentials
        invalid_config = GoogleSearchConfig(api_key="", cse_id="test_cse")
        invalid_config.validate = MagicMock()  # Skip validation for this test
        invalid_engine = GoogleSearchEngine(invalid_config)
        assert invalid_engine.is_available() is False

    def test_optimize_query(self):
        """Test query optimization based on search depth."""
        base_query = "Intel CPU specifications"

        # Basic search
        basic_query = self.engine.optimize_query(base_query, "basic")
        assert basic_query == base_query

        # Standard search
        standard_query = self.engine.optimize_query(base_query, "standard")
        assert "with all specifications" in standard_query

        # Extensive search
        extensive_query = self.engine.optimize_query(base_query, "extensive")
        assert "with all specifications and relevant information" in extensive_query

    def test_create_fallback_queries(self):
        """Test fallback query creation."""
        base_query = "Intel i7-12700K"
        fallback_queries = self.engine.create_fallback_queries(base_query)

        assert len(fallback_queries) >= 4
        assert f"{base_query} datasheet" in fallback_queries
        assert f"{base_query} manual" in fallback_queries
        assert f"{base_query} specifications" in fallback_queries
        assert f"{base_query} filetype:pdf" in fallback_queries
        assert base_query in fallback_queries

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful Google search."""
        # Mock response data
        mock_response_data = {
            "items": [
                {
                    "link": "https://example.com/page1",
                    "title": "Intel i7-12700K Specifications",
                    "snippet": "Detailed specifications for Intel i7-12700K processor",
                    "displayLink": "example.com",
                },
                {
                    "link": "https://test.com/page2",
                    "title": "CPU Benchmarks",
                    "snippet": "Performance benchmarks and reviews",
                    "displayLink": "test.com",
                },
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            # Configure mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data

            mock_client_instance = MagicMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            # Execute search
            results = await self.engine.search("Intel i7-12700K", max_results=2)

            # Verify results
            assert len(results) == 2
            assert all(isinstance(r, GoogleResult) for r in results)
            assert results[0].url == "https://example.com/page1"
            assert results[0].title == "Intel i7-12700K Specifications"
            assert results[1].url == "https://test.com/page2"

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test Google search with no results."""
        mock_response_data = {}  # No "items" key

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data

            mock_client_instance = MagicMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            results = await self.engine.search("nonexistent query")
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_api_key_error(self):
        """Test Google search with API key error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"error": {"message": "Invalid API key provided"}}

            mock_client_instance = MagicMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(APIKeyError, match="Invalid Google API key"):
                await self.engine.search("test query")

    @pytest.mark.asyncio
    async def test_search_rate_limit_error(self):
        """Test Google search with rate limit error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 429

            mock_client_instance = MagicMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(RateLimitError, match="Google API rate limit exceeded"):
                await self.engine.search("test query")

    @pytest.mark.asyncio
    async def test_search_server_error(self):
        """Test Google search with server error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500

            mock_client_instance = MagicMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(ServiceUnavailableError, match="Google API server error"):
                await self.engine.search("test query")

    def test_sanitize_api_key(self):
        """Test API key sanitization in error messages."""
        api_key = "test_api_key_123456789"
        text_with_key = f"Error occurred with API key {api_key} in request"

        sanitized = _sanitize_api_key(text_with_key, api_key)
        assert api_key not in sanitized
        assert "test****6789" in sanitized

        # Test with short key
        short_key = "short"
        short_sanitized = _sanitize_api_key("Error with short key", short_key)
        assert short_sanitized == "Error with short key"


class TestGoogleSearchService:
    """Tests for GoogleSearchService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = GoogleSearchConfig(
            api_key="test_api_key_123456789",
            cse_id="test_cse_id_123",
        )

    @patch("dana.common.sys_resource.web_search.google_search_service.load_google_config")
    def test_google_search_service_initialization(self, mock_load_config):
        """Test GoogleSearchService initialization."""
        mock_load_config.return_value = self.config

        with patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = "test_openai_key"

            service = GoogleSearchService(enable_summarization=False)

            assert service.config == self.config
            assert service.search_engine is not None
            assert service.result_processor is not None
            assert service.content_processor is None

    @patch("dana.common.sys_resource.web_search.google_search_service.load_google_config")
    def test_google_search_service_with_summarization(self, mock_load_config):
        """Test GoogleSearchService with content processing enabled."""
        mock_load_config.return_value = self.config

        with patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = "test_openai_key"

            with patch("dana.common.sys_resource.web_search.utils.content_processor.ContentProcessor"):
                GoogleSearchService(enable_summarization=True)
                # ContentProcessor should be initialized when OPENAI_API_KEY is available

    def test_google_search_service_not_available(self):
        """Test GoogleSearchService initialization when not available."""
        invalid_config = GoogleSearchConfig(api_key="", cse_id="test_cse")
        invalid_config.validate = MagicMock()  # Skip validation

        with patch("dana.common.sys_resource.web_search.google.search_engine.GoogleSearchEngine.is_available") as mock_available:
            mock_available.return_value = False

            with pytest.raises(GoogleSearchError, match="Google Search service not available"):
                GoogleSearchService(config=invalid_config)

    @pytest.mark.asyncio
    async def test_search_basic_functionality(self):
        """Test basic search functionality."""
        # Mock all dependencies
        with patch.multiple(
            "dana.common.sys_resource.web_search.google_search_service",
            load_google_config=MagicMock(return_value=self.config),
        ):
            with patch("os.getenv") as mock_getenv:
                mock_getenv.return_value = None  # No OpenAI key

                service = GoogleSearchService(enable_summarization=False)

                # Mock search engine
                mock_google_results = [
                    GoogleResult(
                        url="https://example.com/page1",
                        title="Test Page 1",
                        snippet="Content from page 1",
                        display_link="example.com",
                    )
                ]

                service.search_engine.search = AsyncMock(return_value=mock_google_results)
                service.result_processor.process_and_score_results = MagicMock(return_value=mock_google_results)

                request = SearchRequest(
                    query="test query",
                    search_depth=SearchDepth.BASIC,
                )

                results = await service.search(request)

                assert isinstance(results, SearchResults)
                assert results.success is True
                assert len(results.sources) == 1
                assert results.sources[0].url == "https://example.com/page1"

    def test_is_available(self):
        """Test GoogleSearchService availability check."""
        with patch("dana.common.sys_resource.web_search.google_search_service.load_google_config"):
            with patch("os.getenv") as mock_getenv:
                mock_getenv.return_value = None

                service = GoogleSearchService(config=self.config, enable_summarization=False)
                assert service.is_available() is True

    def test_create_google_search_service_factory(self):
        """Test factory function for creating GoogleSearchService."""
        with patch("dana.common.sys_resource.web_search.google_search_service.load_google_config") as mock_load:
            mock_load.return_value = self.config

            with patch("os.getenv") as mock_getenv:
                mock_getenv.return_value = None

                # Test with override parameters
                service = create_google_search_service(
                    api_key="override_key",
                    cse_id="override_cse",
                    max_results=3,
                )

                assert isinstance(service, GoogleSearchService)


class TestMockGoogleSearchService:
    """Tests for MockGoogleSearchService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = MockGoogleSearchService()

    @pytest.mark.asyncio
    async def test_mock_search_basic(self):
        """Test mock search service basic functionality."""
        request = SearchRequest(
            query="Intel i7-12700K specifications",
            search_depth=SearchDepth.STANDARD,
        )

        results = await self.mock_service.search(request)

        assert isinstance(results, SearchResults)
        assert results.success is True
        assert len(results.sources) >= 2
        assert all(isinstance(source, SearchSource) for source in results.sources)
        assert "Intel i7-12700K specifications" in results.sources[0].content

    @pytest.mark.asyncio
    async def test_mock_search_with_full_content(self):
        """Test mock search service with full content enabled."""
        request = SearchRequest(
            query="test product",
            with_full_content=True,
        )

        results = await self.mock_service.search(request)

        assert results.success is True
        assert results.sources[0].full_content != ""

    @pytest.mark.asyncio
    async def test_mock_search_raw_data(self):
        """Test mock search service raw data."""
        request = SearchRequest(query="test query")
        results = await self.mock_service.search(request)

        assert results.raw_data != ""
        raw_data = json.loads(results.raw_data)
        assert raw_data["query"] == "test query"
        assert raw_data["mock_service"] is True


if __name__ == "__main__":
    pytest.main([__file__])
