"""
Tests for POET Client functionality
"""

import os
from unittest.mock import patch

import pytest

from opendxa.dana.poet.client import POETClient
from opendxa.dana.poet.types import POETConfig


@pytest.mark.poet
class TestPOETClient:
    """Test POET Client functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.original_env = os.environ.copy()

    def teardown_method(self):
        """Cleanup after each test"""
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch("opendxa.dana.poet.client.APIClient")
    def test_client_initialization_default_url(self, mock_api_client):
        """Test client initializes with default URL"""
        if "POET_API_URL" in os.environ:
            del os.environ["POET_API_URL"]

        POETClient()
        mock_api_client.assert_called_once_with("http://localhost:12345")

    @patch("opendxa.dana.poet.client.APIClient")
    def test_client_initialization_env_url(self, mock_api_client):
        """Test client initializes with URL from environment variable"""
        os.environ["POET_API_URL"] = "http://test-service:8888"
        POETClient()
        mock_api_client.assert_called_once_with("http://test-service:8888")

    @patch("opendxa.dana.poet.client.APIClient")
    def test_transpile_function(self, mock_api_client):
        """Test function transpilation"""
        mock_api_instance = mock_api_client.return_value
        mock_api_instance.post.return_value = {"enhanced_code": "def f(): pass"}

        client = POETClient()
        code = "def f(): ..."
        config = POETConfig(domain="test")
        result = client.transpile(code, config)

        assert result == {"enhanced_code": "def f(): pass"}
        mock_api_instance.post.assert_called_once_with("/poet/transpile", {"code": code, "config": config.dict()})
