"""Pytest configuration for web search resource tests."""

import pytest
import os
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_environment_variables():
    """Mock environment variables for testing."""
    with patch.dict(
        os.environ,
        {
            "GOOGLE_SEARCH_API_KEY": "test_google_api_key_123456789",
            "GOOGLE_SEARCH_CX": "test_cse_id_123456789",
            "LLAMA_SEARCH_API_KEY": "test_llama_api_key_123456789",
            "OPENAI_API_KEY": "test_openai_api_key_123456789",
        },
    ):
        yield


@pytest.fixture
def mock_async_client():
    """Mock HTTP client for external API calls."""
    with patch("httpx.AsyncClient") as mock:
        yield mock


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    from dana.common.sys_resource.web_search.core.models import SearchResults, SearchSource

    return SearchResults(
        success=True,
        sources=[
            SearchSource(
                url="https://example.com/page1",
                content="Sample content from page 1 with technical specifications",
                full_content="Full detailed content from page 1",
            ),
            SearchSource(
                url="https://test.com/page2",
                content="Additional information and benchmarks from page 2",
                full_content="",
            ),
        ],
        raw_data="Sample raw search metadata",
    )


@pytest.fixture
def sample_failed_search_results():
    """Sample failed search results for testing."""
    from dana.common.sys_resource.web_search.core.models import SearchResults

    return SearchResults(
        success=False,
        sources=[],
        error_message="No results found for the given query",
    )
