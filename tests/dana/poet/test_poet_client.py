"""
Tests for POET Client functionality
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from opendxa.dana.poet.client import POETClient
from opendxa.dana.poet.types import POETConfig, POETResult, TranspiledFunction


class TestPOETClient:
    """Test POET Client functionality"""

    def setup_method(self):
        """Setup for each test"""
        # Use temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_env = {}

        # Save original environment variables
        for key in ["AITOMATIC_API_URL", "AITOMATIC_API_KEY"]:
            self.original_env[key] = os.environ.get(key)

    def teardown_method(self):
        """Cleanup after each test"""
        # Restore environment variables
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_client_initialization(self):
        client = POETClient()
        assert client.api_client is not None

    def test_client_remote_mode(self):
        with patch.dict("os.environ", {"AITOMATIC_API_URL": "http://test-service:8080"}):
            client = POETClient()
            assert client.service_uri == "http://test-service:8080"

    def test_transpile_function(self):
        with patch.dict("os.environ", {"AITOMATIC_API_URL": "http://test-service:8080"}):
            client = POETClient()
            mock_result = TranspiledFunction(code="def enhanced(): pass", language="python", metadata={"version": "1.0.0"})

            with patch("opendxa.dana.poet.client.APIClient") as mock_api_client:
                mock_api = Mock()
                mock_api.post.return_value = mock_result
                mock_api_client.return_value = mock_api

                config = POETConfig(domain="test")
                result = client.transpile_function("def test(): pass", config)
                assert result == mock_result
                mock_api.post.assert_called_once()

    def test_submit_feedback(self):
        with patch.dict("os.environ", {"AITOMATIC_API_URL": "http://test-service:8080"}):
            client = POETClient()
            feedback = {"execution_id": "123", "rating": 5}

            with patch("opendxa.dana.poet.client.APIClient") as mock_api_client:
                mock_api = Mock()
                mock_api.post.return_value = {"status": "success"}
                mock_api_client.return_value = mock_api

                result = client.submit_feedback(feedback)
                assert result["status"] == "success"
                mock_api.post.assert_called_once()

    def test_get_function_status(self):
        with patch.dict("os.environ", {"AITOMATIC_API_URL": "http://test-service:8080"}):
            client = POETClient()

            with patch("opendxa.dana.poet.client.APIClient") as mock_api_client:
                mock_api = Mock()
                mock_api.get.return_value = {"status": "active"}
                mock_api_client.return_value = mock_api

                result = client.get_function_status("test_function")
                assert result["status"] == "active"
                mock_api.get.assert_called_once()

    def test_error_handling(self):
        with patch.dict("os.environ", {"AITOMATIC_API_URL": "http://test-service:8080"}):
            client = POETClient()

            with patch("opendxa.dana.poet.client.APIClient") as mock_api_client:
                mock_api = Mock()
                mock_api.post.side_effect = Exception("API Error")
                mock_api_client.return_value = mock_api

                with pytest.raises(Exception):
                    config = POETConfig(domain="test")
                    client.transpile_function("def test(): pass", config)

    def test_health_check(self):
        with patch.dict("os.environ", {"AITOMATIC_API_URL": "http://test-service:8080"}):
            client = POETClient()

            with patch("opendxa.dana.poet.client.APIClient") as mock_api_client:
                mock_api = Mock()
                mock_api.get.return_value = {"status": "healthy"}
                mock_api_client.return_value = mock_api

                result = client.check_health()
                assert result["status"] == "healthy"
                mock_api.get.assert_called_once()


class TestPOETConfig:
    """Test POET Configuration"""

    def test_poet_config_defaults(self):
        """Test POETConfig default values"""
        config = POETConfig()

        assert config.domain is None
        assert config.optimize_for is None
        assert config.retries == 3
        assert config.timeout == 30.0
        assert config.enable_monitoring is True

    def test_poet_config_custom(self):
        """Test POETConfig with custom values"""
        config = POETConfig(domain="ml_monitoring", optimize_for="accuracy", retries=5, timeout=60.0, enable_monitoring=False)

        assert config.domain == "ml_monitoring"
        assert config.optimize_for == "accuracy"
        assert config.retries == 5
        assert config.timeout == 60.0
        assert config.enable_monitoring is False

    def test_poet_config_dict_conversion(self):
        """Test POETConfig dict conversion"""
        config = POETConfig(domain="test", optimize_for="speed")
        config_dict = config.dict()

        expected = {"domain": "test", "optimize_for": "speed", "retries": 3, "timeout": 30.0, "enable_monitoring": True}

        assert config_dict == expected

    def test_poet_config_from_dict(self):
        """Test POETConfig creation from dict"""
        data = {"domain": "api_operations", "optimize_for": "reliability", "retries": 7, "timeout": 120.0, "enable_monitoring": False}

        config = POETConfig.from_dict(data)

        assert config.domain == "api_operations"
        assert config.optimize_for == "reliability"
        assert config.retries == 7
        assert config.timeout == 120.0
        assert config.enable_monitoring is False


class TestPOETResult:
    """Test POET Result wrapper"""

    def test_poet_result_creation(self):
        """Test POETResult creation"""
        original_result = {"value": 42, "status": "success"}
        result = POETResult(original_result, "test_func", "v2")

        assert result._result == original_result
        assert result._poet["function_name"] == "test_func"
        assert result._poet["version"] == "v2"
        assert result._poet["enhanced"] is True
        assert "execution_id" in result._poet

    def test_poet_result_attribute_delegation(self):
        """Test POETResult delegates attributes to wrapped result"""
        original_result = Mock()
        original_result.some_attr = "test_value"

        result = POETResult(original_result, "test_func")

        assert result.some_attr == "test_value"

    def test_poet_result_item_access(self):
        """Test POETResult delegates item access to wrapped result"""
        original_result = {"key": "value", "number": 123}
        result = POETResult(original_result, "test_func")

        assert result["key"] == "value"
        assert result["number"] == 123

    def test_poet_result_item_assignment(self):
        """Test POETResult delegates item assignment to wrapped result"""
        original_result = {"existing": "value"}
        result = POETResult(original_result, "test_func")

        result["new_key"] = "new_value"

        assert original_result["new_key"] == "new_value"

    def test_poet_result_unwrap(self):
        """Test POETResult unwrap method"""
        original_result = {"data": [1, 2, 3]}
        result = POETResult(original_result, "test_func")

        unwrapped = result.unwrap()

        assert unwrapped is original_result
        assert unwrapped == {"data": [1, 2, 3]}

    def test_poet_result_str_repr(self):
        """Test POETResult string representations"""
        original_result = {"test": "data"}
        result = POETResult(original_result, "test_func")

        assert str(result) == str(original_result)
        assert "POETResult" in repr(result)
        assert str(original_result) in repr(result)
