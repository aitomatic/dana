"""
Tests for POET Client functionality
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

from opendxa.dana.poet.client import POETClient
from opendxa.dana.poet.types import POETConfig, POETResult, POETServiceError


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

    def test_client_local_mode_default(self):
        """Test client defaults to local mode"""
        # Clear environment variables
        os.environ.pop("AITOMATIC_API_URL", None)
        os.environ.pop("AITOMATIC_API_KEY", None)

        with patch("opendxa.dana.poet.transpiler.LocalPOETTranspiler") as mock_transpiler:
            client = POETClient()
            assert client.local_mode is True
            assert client.service_uri == "local"

    def test_client_local_mode_explicit(self):
        """Test client with explicit local mode"""
        os.environ["AITOMATIC_API_URL"] = "local"

        with patch("opendxa.dana.poet.transpiler.LocalPOETTranspiler") as mock_transpiler:
            client = POETClient()
            assert client.local_mode is True
            assert client.service_uri == "local"

    def test_client_remote_mode(self):
        """Test client with remote service URL"""
        os.environ["AITOMATIC_API_URL"] = "http://localhost:8080"
        os.environ["AITOMATIC_API_KEY"] = "test-key"

        with patch("opendxa.dana.poet.client.APIClient") as mock_api_client:
            mock_client = Mock()
            mock_client.health_check.return_value = True
            mock_api_client.return_value = mock_client

            client = POETClient()
            assert client.local_mode is False
            assert client.service_uri == "http://localhost:8080"
            assert client.api_key == "test-key"

    def test_client_remote_mode_health_check_fails(self):
        """Test client with failed health check"""
        os.environ["AITOMATIC_API_URL"] = "http://localhost:8080"

        with patch("opendxa.dana.poet.client.APIClient") as mock_api_client:
            mock_client = Mock()
            mock_client.health_check.return_value = False
            mock_api_client.return_value = mock_client

            with pytest.raises(POETServiceError, match="POET service not available"):
                POETClient()

    def test_transpile_function_local(self):
        """Test function transpilation in local mode"""
        os.environ["AITOMATIC_API_URL"] = "local"

        with patch("opendxa.dana.poet.transpiler.LocalPOETTranspiler") as mock_transpiler_class:
            mock_transpiler = Mock()
            mock_result = Mock()
            mock_transpiler.transpile_function.return_value = mock_result
            mock_transpiler_class.return_value = mock_transpiler

            client = POETClient()
            config = POETConfig(domain="test")

            result = client.transpile_function("def test(): pass", config)

            assert result == mock_result
            mock_transpiler.transpile_function.assert_called_once_with("def test(): pass", config, None)

    def test_transpile_function_remote(self):
        """Test function transpilation in remote mode"""
        os.environ["AITOMATIC_API_URL"] = "http://localhost:8080"

        with patch("opendxa.dana.poet.client.APIClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client.health_check.return_value = True
            mock_api_client.post.return_value = {
                "poet_implementation": {"code": "enhanced code", "language": "python"},
                "metadata": {"test": "data"},
            }
            mock_api_client_class.return_value = mock_api_client

            client = POETClient()
            config = POETConfig(domain="test")

            result = client.transpile_function("def test(): pass", config)

            assert result.code == "enhanced code"
            assert result.language == "python"
            assert result.metadata == {"test": "data"}

            mock_api_client.post.assert_called_once_with(
                "/poet/transpile", {"function_code": "def test(): pass", "language": "python", "config": config.dict()}
            )

    def test_feedback_local(self):
        """Test feedback submission in local mode"""
        os.environ["AITOMATIC_API_URL"] = "local"

        with patch("opendxa.dana.poet.transpiler.LocalPOETTranspiler") as mock_transpiler:
            with patch("opendxa.dana.poet.feedback.AlphaFeedbackSystem") as mock_feedback_class:
                mock_feedback_system = Mock()
                mock_feedback_class.return_value = mock_feedback_system

                client = POETClient()
                result = POETResult({"test": "data"}, "test_func")

                client.feedback(result, "test feedback")

                mock_feedback_system.feedback.assert_called_once_with(result, "test feedback")

    def test_feedback_remote(self):
        """Test feedback submission in remote mode"""
        os.environ["AITOMATIC_API_URL"] = "http://localhost:8080"

        with patch("opendxa.dana.poet.client.APIClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client.health_check.return_value = True
            mock_api_client.post.return_value = {"status": "success"}
            mock_api_client_class.return_value = mock_api_client

            client = POETClient()
            result = POETResult({"test": "data"}, "test_func")

            client.feedback(result, "test feedback")

            mock_api_client.post.assert_called_once_with(
                "/poet/feedback",
                {"execution_id": result._poet["execution_id"], "function_name": "test_func", "feedback_payload": "test feedback"},
            )

    def test_feedback_invalid_result(self):
        """Test feedback with invalid result type"""
        os.environ["AITOMATIC_API_URL"] = "local"

        with patch("opendxa.dana.poet.transpiler.LocalPOETTranspiler") as mock_transpiler:
            client = POETClient()

            with pytest.raises(POETServiceError, match="result must be a POETResult instance"):
                client.feedback("invalid", "test feedback")

    def test_get_function_status_local(self):
        """Test function status check in local mode"""
        os.environ["AITOMATIC_API_URL"] = "local"

        with patch("opendxa.dana.poet.transpiler.LocalPOETTranspiler") as mock_transpiler:
            with patch("opendxa.dana.poet.client.Path") as mock_path:
                # Mock directory structure
                mock_poet_dir = Mock()
                mock_current_link = Mock()
                mock_current_link.exists.return_value = True
                mock_current_link.is_symlink.return_value = True
                mock_current_link.readlink.return_value = Path("v1")

                mock_poet_dir.exists.return_value = True
                mock_poet_dir.__truediv__ = Mock(return_value=mock_current_link)

                # Mock the entire path construction chain
                mock_poet_base = Mock()
                mock_poet_base.__truediv__ = Mock(return_value=mock_poet_dir)
                mock_path.return_value = mock_poet_base

                client = POETClient()
                status = client.get_function_status("test_func")

                assert status["status"] == "available"
                assert status["function_name"] == "test_func"
                assert status["current_version"] == "v1"

    def test_get_function_status_not_found(self):
        """Test function status check for non-existent function"""
        os.environ["AITOMATIC_API_URL"] = "local"

        with patch("opendxa.dana.poet.transpiler.LocalPOETTranspiler") as mock_transpiler:
            with patch("opendxa.dana.poet.client.Path") as mock_path:
                mock_poet_dir = Mock()
                mock_poet_dir.exists.return_value = False

                mock_poet_base = Mock()
                mock_poet_base.__truediv__ = Mock(return_value=mock_poet_dir)
                mock_path.return_value = mock_poet_base

                client = POETClient()
                status = client.get_function_status("nonexistent_func")

                assert status["status"] == "not_found"
                assert status["function_name"] == "nonexistent_func"


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
