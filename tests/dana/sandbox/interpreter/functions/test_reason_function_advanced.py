"""
Tests for advanced features of the reason function.

This module tests the new features added to reason_function including:
1. Model selection and caching
2. Raw prompt handling
3. LLMResource management
4. System resource integration
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from opendxa.common.config.config_loader import ConfigLoader
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest, BaseResponse
from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function
from opendxa.dana.sandbox.sandbox_context import SandboxContext


@pytest.fixture
def mock_env():
    """Set up mock environment for testing."""
    original_mock_env = os.environ.get("OPENDXA_MOCK_LLM")
    os.environ["OPENDXA_MOCK_LLM"] = "true"
    yield
    if original_mock_env is None:
        os.environ.pop("OPENDXA_MOCK_LLM", None)
    else:
        os.environ["OPENDXA_MOCK_LLM"] = original_mock_env


@pytest.fixture
def mock_config():
    """Mock configuration with test models."""
    config = {
        "preferred_models": [
            {"name": "gpt-4", "provider": "openai"},
            {"name": "gpt-3.5-turbo", "provider": "openai"},
            {"name": "claude-3-sonnet", "provider": "anthropic"},
        ]
    }
    with patch.object(ConfigLoader, "get_default_config", return_value=config):
        yield config


class TestReasonFunctionAdvanced:
    """Test advanced features of the reason function."""

    def setup_method(self):
        """Set up test environment."""
        self.context = SandboxContext()

        # Create mock LLMResource for system default
        self.mock_default_llm = MagicMock(spec=LLMResource)
        self.mock_default_llm.query.return_value = BaseResponse(success=True, content="Default LLM Response")
        self.mock_default_llm._is_available = True
        self.mock_default_llm.name = "default_llm"

        # Set default LLM in context
        self.context.set("system:llm_resource", self.mock_default_llm)

    def test_model_selection_exact_match(self, mock_env, mock_config):
        """Test selecting a specific model by exact name."""
        # Create mock LLMResource for specific model
        mock_gpt4 = MagicMock(spec=LLMResource)
        mock_gpt4.query.return_value = BaseResponse(success=True, content="GPT-4 Response")
        mock_gpt4._is_available = True
        mock_gpt4.name = "gpt-4"

        # Set up system resources
        self.context.set("system:llm_resources", {"gpt-4": mock_gpt4})

        # Test with exact model name
        result = reason_function("Test prompt", self.context, options={"model": "gpt-4", "enable_ipv": False}, use_mock=True)

        # Verify correct model was used
        assert result == "GPT-4 Response"
        mock_gpt4.query.assert_called_once()
        self.mock_default_llm.query.assert_not_called()

    def test_model_selection_partial_match(self, mock_env, mock_config):
        """Test selecting a model by partial name match."""
        # Create mock LLMResource for claude model
        mock_claude = MagicMock(spec=LLMResource)
        mock_claude.query.return_value = BaseResponse(success=True, content="Claude Response")
        mock_claude._is_available = True
        mock_claude.name = "claude-3-sonnet"

        # Set up system resources
        self.context.set("system:llm_resources", {"claude-3-sonnet": mock_claude})

        # Test with partial model name
        result = reason_function("Test prompt", self.context, options={"model": "claude", "enable_ipv": False}, use_mock=True)

        # Verify correct model was used
        assert result == "Claude Response"
        mock_claude.query.assert_called_once()
        self.mock_default_llm.query.assert_not_called()

    def test_model_caching(self, mock_env, mock_config):
        """Test that LLMResources are properly cached."""
        # First call with specific model
        result1 = reason_function("Test prompt 1", self.context, options={"model": "gpt-4", "enable_ipv": False}, use_mock=True)

        # Verify cache was created
        assert hasattr(self.context, "cached_llm_resources")
        assert "gpt-4" in self.context.cached_llm_resources

        # Second call with same model should use cached resource
        result2 = reason_function("Test prompt 2", self.context, options={"model": "gpt-4", "enable_ipv": False}, use_mock=True)

        # Verify same resource was used
        cached_resource = self.context.cached_llm_resources["gpt-4"]
        assert isinstance(cached_resource, LLMResource)
        assert cached_resource.name == "llm_resource_gpt-4"

    def test_raw_prompt_handling(self, mock_env):
        """Test raw prompt handling bypasses IPV."""
        result = reason_function("Raw test prompt", self.context, options={"raw_prompt": True}, use_mock=True)

        # Verify default LLM was used directly
        self.mock_default_llm.query.assert_called_once()
        request = self.mock_default_llm.query.call_args[0][0]
        assert isinstance(request, BaseRequest)
        assert request.arguments["prompt"] == "Raw test prompt"

    def test_model_fallback_behavior(self, mock_env, mock_config):
        """Test fallback to default LLM when requested model is not available."""
        # Request non-existent model
        result = reason_function("Test prompt", self.context, options={"model": "nonexistent-model", "enable_ipv": False}, use_mock=True)

        # Verify fallback to default LLM
        self.mock_default_llm.query.assert_called_once()
        assert result == "Default LLM Response"

    def test_model_initialization_from_config(self, mock_env, mock_config):
        """Test creating new LLMResource from config when not in system resources."""
        # Remove any existing resources
        self.context.set("system:llm_resources", {})

        # Request model from config
        result = reason_function("Test prompt", self.context, options={"model": "gpt-3.5-turbo", "enable_ipv": False}, use_mock=True)

        # Verify new resource was created and cached
        assert "gpt-3.5-turbo" in self.context.cached_llm_resources
        created_resource = self.context.cached_llm_resources["gpt-3.5-turbo"]
        assert isinstance(created_resource, LLMResource)
        assert created_resource.name == "llm_resource_gpt-3.5-turbo"

    def test_system_resources_integration(self, mock_env):
        """Test integration with system:llm_resources."""
        # Create multiple mock resources
        mock_gpt4 = MagicMock(spec=LLMResource)
        mock_gpt4.query.return_value = BaseResponse(success=True, content="GPT-4 Response")
        mock_gpt4._is_available = True
        mock_gpt4.name = "gpt-4"

        mock_claude = MagicMock(spec=LLMResource)
        mock_claude.query.return_value = BaseResponse(success=True, content="Claude Response")
        mock_claude._is_available = True
        mock_claude.name = "claude-3-sonnet"

        # Set up system resources
        self.context.set("system:llm_resources", {"gpt-4": mock_gpt4, "claude-3-sonnet": mock_claude})

        # Test switching between models
        result1 = reason_function("Test prompt 1", self.context, options={"model": "gpt-4", "enable_ipv": False}, use_mock=True)
        assert result1 == "GPT-4 Response"

        result2 = reason_function("Test prompt 2", self.context, options={"model": "claude", "enable_ipv": False}, use_mock=True)
        assert result2 == "Claude Response"

        # Verify both resources were used
        mock_gpt4.query.assert_called_once()
        mock_claude.query.assert_called_once()
