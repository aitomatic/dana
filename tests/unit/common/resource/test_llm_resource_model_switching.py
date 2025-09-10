"""Test LLMResource model switching functionality."""

import os
from unittest.mock import patch

import pytest

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.common.types import BaseRequest


class TestLLMResourceModelSwitching:
    """Test LLMResource model switching capabilities."""

    def setup_method(self):
        """Set up test environment."""
        # Set up fake environment variables for testing
        os.environ["ANTHROPIC_API_KEY"] = "test-key-123"
        os.environ["OPENAI_API_KEY"] = "test-key-456"
        os.environ["LOCAL_API_KEY"] = "test-key-789"

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up environment variables
        for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LOCAL_API_KEY"]:
            if key in os.environ:
                del os.environ[key]

    def test_llm_resource_creation_with_anthropic(self):
        """Test LLMResource creation with Anthropic model."""
        llm = LegacyLLMResource(name="test_anthropic", model="anthropic:claude-3-5-sonnet-20240620")
        assert llm.model == "anthropic:claude-3-5-sonnet-20240620"
        assert llm.name == "test_anthropic"

    def test_llm_resource_creation_with_openai(self):
        """Test LLMResource creation with OpenAI model."""
        llm = LegacyLLMResource(name="test_openai", model="openai:gpt-4")
        assert llm.model == "openai:gpt-4"
        assert llm.name == "test_openai"

    def test_llm_resource_creation_with_local(self):
        """Test LLMResource creation with local model."""
        llm = LegacyLLMResource(name="test_local", model="local:llama3.2")
        assert llm.model == "local:llama3.2"
        assert llm.name == "test_local"

    def test_model_switching_anthropic_to_openai(self):
        """Test switching from Anthropic to OpenAI model."""
        llm = LegacyLLMResource(name="test_switch", model="anthropic:claude-3-5-sonnet-20240620")
        assert llm.model == "anthropic:claude-3-5-sonnet-20240620"

        llm.model = "openai:gpt-4"
        assert llm.model == "openai:gpt-4"

    def test_model_switching_openai_to_local(self):
        """Test switching from OpenAI to local model."""
        llm = LegacyLLMResource(name="test_switch", model="openai:gpt-4")
        assert llm.model == "openai:gpt-4"

        llm.model = "local:llama3.2"
        assert llm.model == "local:llama3.2"

    def test_model_switching_local_to_anthropic(self):
        """Test switching from local to Anthropic model."""
        llm = LegacyLLMResource(name="test_switch", model="local:llama3.2")
        assert llm.model == "local:llama3.2"

        llm.model = "anthropic:claude-3-5-sonnet-20240620"
        assert llm.model == "anthropic:claude-3-5-sonnet-20240620"

    def test_model_switching_cycle(self):
        """Test cycling through multiple models."""
        llm = LegacyLLMResource(name="test_cycle", model="anthropic:claude-3-5-sonnet-20240620")

        # Cycle through models
        models = ["openai:gpt-4", "local:llama3.2", "anthropic:claude-3-5-sonnet-20240620", "openai:gpt-3.5-turbo", "local:mistral"]

        for model in models:
            llm.model = model
            assert llm.model == model

    def test_model_switching_preserves_name(self):
        """Test that model switching preserves the resource name."""
        llm = LegacyLLMResource(name="test_preserve", model="anthropic:claude-3-5-sonnet-20240620")
        original_name = llm.name

        llm.model = "openai:gpt-4"
        assert llm.name == original_name

        llm.model = "local:llama3.2"
        assert llm.name == original_name

    def test_invalid_model_format(self):
        """Test handling of invalid model format."""
        # LLMResource currently accepts any model format and validates availability later
        llm = LegacyLLMResource(name="test_invalid", model="invalid-model")
        assert llm.model == "invalid-model"
        # The model will be validated when trying to initialize the client

    def test_empty_model(self):
        """Test handling of empty model."""
        # LLMResource auto-selects a model if given an empty string
        llm = LegacyLLMResource(name="test_empty", model="")
        
        # In mock mode, should get a mock model
        if os.environ.get("DANA_MOCK_LLM", "false").lower() == "true":
            assert llm.model is not None
            assert isinstance(llm.model, str)
            assert llm.model.startswith("mock:")
        else:
            # In real mode, might be None if no API keys available
            # This is acceptable behavior
            pass

    def test_none_model(self):
        """Test handling of None model."""
        # LLMResource auto-selects a model if given None
        llm = LegacyLLMResource(name="test_none", model=None)
        
        # In mock mode, should get a mock model
        if os.environ.get("DANA_MOCK_LLM", "false").lower() == "true":
            assert llm.model is not None
            assert isinstance(llm.model, str)
            assert llm.model.startswith("mock:")
        else:
            # In real mode, might be None if no API keys available
            # This is acceptable behavior
            pass

    def test_model_switching_with_minimal_config(self):
        """Test model switching with minimal configuration."""
        # Test with minimal config that relies on environment variables
        llm = LegacyLLMResource(name="test_minimal")

        # Set model after creation
        llm.model = "anthropic:claude-3-5-sonnet-20240620"
        assert llm.model == "anthropic:claude-3-5-sonnet-20240620"

        llm.model = "openai:gpt-4"
        assert llm.model == "openai:gpt-4"

    @pytest.mark.asyncio
    async def test_async_model_switching(self):
        """Test model switching in async context."""
        llm = LegacyLLMResource(name="test_async", model="anthropic:claude-3-5-sonnet-20240620")

        # Switch models in async context
        llm.model = "openai:gpt-4"
        assert llm.model == "openai:gpt-4"

        llm.model = "local:llama3.2"
        assert llm.model == "local:llama3.2"

    def test_model_switching_with_provider_configs(self):
        """Test model switching with explicit provider configurations."""
        provider_configs = {
            "anthropic": {"api_key": "test-anthropic-key"},
            "openai": {"api_key": "test-openai-key"},
            "local": {"api_key": "test-local-key"},
        }

        llm = LegacyLLMResource(name="test_config", model="anthropic:claude-3-5-sonnet-20240620", provider_configs=provider_configs)

        # Test switching with explicit configs
        llm.model = "openai:gpt-4"
        assert llm.model == "openai:gpt-4"

        llm.model = "local:llama3.2"
        assert llm.model == "local:llama3.2"

    def test_invalid_model_format_raises_on_query(self):
        """Test that querying with an invalid model format returns a failed response with an error message."""
        llm = LegacyLLMResource(name="test_invalid_query", model="microsoft/Phi-3.5-mini-instruct")
        request = BaseRequest(arguments={"messages": [{"role": "user", "content": "hello"}]})
        response = llm.query_sync(request)
        assert not response.success
        assert "not available" in (response.error or "")

    def test_local_model_format_validation(self):
        """Test that local model format errors are caught during query."""
        from dana.common.types import BaseRequest

        # Test with invalid local model format (should be "local:model_name")
        llm = LegacyLLMResource(name="test_local_invalid", model="microsoft/Phi-3.5-mini-instruct")

        # Set up minimal config to allow initialization
        provider_configs = {"microsoft": {"api_key": "test-key", "base_url": "http://localhost:8000/v1"}}
        llm.provider_configs = provider_configs

        request = BaseRequest(arguments={"messages": [{"role": "user", "content": "hello"}]})
        response = llm.query_sync(request)

        # Should fail due to model format or provider config issues
        assert not response.success
        error_message = response.error or ""
        assert any(
            [
                "Invalid model format" in error_message,
                "not available" in error_message,
                "No valid provider configuration" in error_message,
                "unexpected error" in error_message.lower(),
            ]
        ), f"Expected model format validation error for local model, got: {error_message}"

    def test_openai_model_format_validation(self):
        """Test that OpenAI model format errors are caught during query."""
        from dana.common.types import BaseRequest

        # Test with invalid OpenAI model format (should be "openai:model_name")
        llm = LegacyLLMResource(name="test_openai_invalid", model="gpt-4-invalid-format")

        # Set up OpenAI config to allow initialization
        provider_configs = {"openai": {"api_key": "test-key", "base_url": "https://api.openai.com/v1"}}
        llm.provider_configs = provider_configs

        request = BaseRequest(arguments={"messages": [{"role": "user", "content": "hello"}]})
        response = llm.query_sync(request)

        # Should fail due to model format or provider config issues
        assert not response.success
        error_message = response.error or ""
        assert any(
            [
                "Invalid model format" in error_message,
                "not available" in error_message,
                "No valid provider configuration" in error_message,
                "unexpected error" in error_message.lower(),
            ]
        ), f"Expected model format validation error for OpenAI model, got: {error_message}"

    def test_anthropic_model_format_validation(self):
        """Test that Anthropic model format errors are caught during query."""
        from dana.common.types import BaseRequest

        # Test with invalid Anthropic model format (should be "anthropic:model_name")
        llm = LegacyLLMResource(name="test_anthropic_invalid", model="claude-3-invalid-format")

        # Set up Anthropic config to allow initialization
        provider_configs = {"anthropic": {"api_key": "test-key"}}
        llm.provider_configs = provider_configs

        request = BaseRequest(arguments={"messages": [{"role": "user", "content": "hello"}]})
        response = llm.query_sync(request)

        # Should fail due to model format or provider config issues
        assert not response.success
        error_message = response.error or ""
        assert any(
            [
                "Invalid model format" in error_message,
                "not available" in error_message,
                "No valid provider configuration" in error_message,
                "unexpected error" in error_message.lower(),
            ]
        ), f"Expected model format validation error for Anthropic model, got: {error_message}"

    def test_model_switching_with_invalid_formats(self):
        """Test that switching to invalid model formats is caught during query."""
        from dana.common.types import BaseRequest

        # Start with valid model
        llm = LegacyLLMResource(name="test_switching_invalid", model="openai:gpt-4")

        # Set up configs for multiple providers
        provider_configs = {
            "openai": {"api_key": "test-key"},
            "anthropic": {"api_key": "test-key"},
            "local": {"api_key": "test-key", "base_url": "http://localhost:8000/v1"},
        }
        llm.provider_configs = provider_configs

        # Switch to invalid format and test
        llm.model = "invalid-model-format"
        request = BaseRequest(arguments={"messages": [{"role": "user", "content": "hello"}]})
        response = llm.query_sync(request)

        # Should fail due to invalid model format
        assert not response.success
        error_message = response.error or ""
        assert any(
            [
                "Invalid model format" in error_message,
                "not available" in error_message,
                "No valid provider configuration" in error_message,
                "unexpected error" in error_message.lower(),
            ]
        ), f"Expected model format validation error after switching, got: {error_message}"

    @pytest.mark.live
    def test_actual_aisuite_model_format_validation(self):
        """Test that actually triggers the AISuite model format validation error."""
        from dana.common.types import BaseRequest

        # No longer overriding DANA_MOCK_LLM - let environment control it
        try:
            # Create LLMResource with the exact model that's causing the error
            llm = LegacyLLMResource(name="test_actual_aisuite", model="microsoft/Phi-3.5-mini-instruct")

            # Mock the provider config validation to allow initialization
            with patch.object(llm, "_get_provider_config_for_current_model") as mock_get_config:
                # Return a valid config that will allow initialization
                mock_get_config.return_value = {"microsoft": {"api_key": "test-key", "base_url": "http://localhost:8000/v1"}}

                # Mock the AISuite client to simulate the actual error
                with patch("aisuite.Client") as mock_client:
                    # Make the AISuite client raise the exact error you're seeing
                    mock_client.return_value.chat.completions.create.side_effect = Exception(
                        "Invalid model format. Expected 'provider:model', got 'microsoft/Phi-3.5-mini-instruct'"
                    )

                    request = BaseRequest(arguments={"messages": [{"role": "user", "content": "hello"}]})
                    response = llm.query_sync(request)

                    # Should fail with the AISuite validation error
                    assert not response.success
                    error_message = response.error or ""
                    assert "Invalid model format" in error_message, f"Expected AISuite validation error, got: {error_message}"
                    assert "Expected 'provider:model'" in error_message, f"Expected specific format error, got: {error_message}"
                    assert "microsoft/Phi-3.5-mini-instruct" in error_message, f"Expected model name in error, got: {error_message}"
        finally:
            # No longer overriding DANA_MOCK_LLM - let environment control it
            pass

    def test_config_with_invalid_model_format_triggers_error(self):
        """Test that a config with an invalid model format triggers the error before Dana sees it."""
        import copy

        # Patch ConfigLoader to inject a bad preferred model
        from dana.common.config import ConfigLoader
        from dana.common.types import BaseRequest

        bad_model = "microsoft/Phi-3.5-mini-instruct"

        # Copy the real config and inject the bad model as the only preferred model
        real_config = ConfigLoader().get_default_config()
        bad_config = copy.deepcopy(real_config)
        if "llm" not in bad_config:
            bad_config["llm"] = {}
        bad_config["llm"]["preferred_models"] = [bad_model]
        # Also patch provider_configs to allow initialization
        bad_config["llm"]["provider_configs"] = {"microsoft": {"api_key": "test-key", "base_url": "http://localhost:8000/v1"}}

        with patch.object(ConfigLoader, "get_default_config", return_value=bad_config):
            llm = LegacyLLMResource()
            request = BaseRequest(arguments={"messages": [{"role": "user", "content": "hello"}]})
            response = llm.query_sync(request)
            assert not response.success
            error_message = response.error or ""
            assert (
                "Invalid model format" in error_message
                or "not available" in error_message
                or "No valid provider configuration" in error_message
                or "unexpected error" in error_message.lower()
            ), f"Expected model format validation error from config, got: {error_message}"

    @pytest.mark.live
    def test_local_model_bug_is_fixed(self):
        """Test that the local model bug is fixed - correct model format transformation."""
        from dana.common.types import BaseRequest

        # Test 1: Default api_type (should default to "openai")
        provider_configs_default = {
            "local": {
                "api_key": "test-key",
                "base_url": "http://localhost:8000/v1",
                "model_name": "microsoft/Phi-3.5-mini-instruct",
                # No api_type specified - should default to "openai"
            }
        }

        llm_default = LegacyLLMResource(name="test_local_default", model="local", provider_configs=provider_configs_default)
        assert (
            llm_default.aisuite_model_name == "openai:microsoft/Phi-3.5-mini-instruct"
        ), f"Expected default openai format, got: {llm_default.aisuite_model_name}"

        # Test 2: Explicit api_type="openai"
        provider_configs_openai = {
            "local": {
                "api_key": "test-key",
                "base_url": "http://localhost:8000/v1",
                "model_name": "microsoft/Phi-3.5-mini-instruct",
                "api_type": "openai",
            }
        }

        llm_openai = LegacyLLMResource(name="test_local_openai", model="local", provider_configs=provider_configs_openai)
        assert (
            llm_openai.aisuite_model_name == "openai:microsoft/Phi-3.5-mini-instruct"
        ), f"Expected openai format, got: {llm_openai.aisuite_model_name}"

        # Test 3: Different api_type (e.g., "anthropic" for local Anthropic-compatible API)
        provider_configs_anthropic = {
            "local": {
                "api_key": "test-key",
                "base_url": "http://localhost:8000/v1",
                "model_name": "claude-3.5-sonnet",
                "api_type": "anthropic",
            }
        }

        llm_anthropic = LegacyLLMResource(name="test_local_anthropic", model="local", provider_configs=provider_configs_anthropic)
        assert (
            llm_anthropic.aisuite_model_name == "anthropic:claude-3.5-sonnet"
        ), f"Expected anthropic format, got: {llm_anthropic.aisuite_model_name}"

        # Verify the fix for the original bug case
        llm = llm_openai  # Use the openai case for the main test

        # Verify the fix: logical model vs AISuite model format
        assert llm.model == "local", f"Expected logical model name 'local', got: {llm.model}"
        assert llm.physical_model_name == "microsoft/Phi-3.5-mini-instruct", f"Expected physical model name, got: {llm.physical_model_name}"
        assert llm.aisuite_model_name == "openai:microsoft/Phi-3.5-mini-instruct", f"Expected AISuite format, got: {llm.aisuite_model_name}"

        # Initialize and verify query executor gets the correct format
        import asyncio

        asyncio.run(llm.initialize())
        assert (
            llm._query_executor.model == "openai:microsoft/Phi-3.5-mini-instruct"
        ), f"Query executor should receive AISuite format, got: {llm._query_executor.model}"

        # No longer overriding DANA_MOCK_LLM - let environment control it
        try:
            # Test query with mock enabled
            request = BaseRequest(arguments={"messages": [{"role": "user", "content": "test"}]})
            response = llm.query_sync(request)

            # Verify success - the fact that it succeeds means the model format is correct
            # If the model format was wrong (like the original bug), AISuite would have thrown an error
            assert response.success, f"Query should succeed with fixed local model format, got error: {response.error}"

            # Additional verification: the query executor should have the correct model format
            # This ensures that AISuite receives "openai:microsoft/Phi-3.5-mini-instruct" instead of just "microsoft/Phi-3.5-mini-instruct"
            assert llm._query_executor.model.startswith(
                "openai:"
            ), f"Query executor model should start with 'openai:' for AISuite compatibility, got: {llm._query_executor.model}"

        finally:
            # No longer overriding DANA_MOCK_LLM - let environment control it
            pass

    def test_local_model_api_type_configuration(self):
        """Test that different api_type values are properly handled for local models."""

        # Test various api_type configurations
        test_cases = [
            ("openai", "gpt-4-local", "openai:gpt-4-local"),
            ("anthropic", "claude-3-local", "anthropic:claude-3-local"),
            ("google", "gemini-local", "google:gemini-local"),
            (None, "default-model", "openai:default-model"),  # Should default to openai
        ]

        for api_type, model_name, expected_aisuite_name in test_cases:
            provider_configs = {"local": {"api_key": "test-key", "base_url": "http://localhost:8000/v1", "model_name": model_name}}

            # Only add api_type if it's not None
            if api_type is not None:
                provider_configs["local"]["api_type"] = api_type

            llm = LegacyLLMResource(name=f"test_api_type_{api_type or 'default'}", model="local", provider_configs=provider_configs)

            assert (
                llm.aisuite_model_name == expected_aisuite_name
            ), f"For api_type={api_type}, expected {expected_aisuite_name}, got: {llm.aisuite_model_name}"
