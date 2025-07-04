"""Test the LLMConfigurationManager class."""

import os
import unittest
from unittest.mock import patch

from dana.common.exceptions import LLMError
from dana.common.resource.llm_configuration_manager import LLMConfigurationManager


class TestLLMConfigurationManager(unittest.TestCase):
    """Test the LLMConfigurationManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing environment variables for clean tests
        self.original_env = {}
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
            self.original_env[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_explicit_model_initialization(self):
        """Test configuration manager with explicit model."""
        config_manager = LLMConfigurationManager(explicit_model="openai:gpt-4", config={"temperature": 0.8})

        self.assertEqual(config_manager.explicit_model, "openai:gpt-4")
        self.assertEqual(config_manager.config["temperature"], 0.8)

    def test_model_validation_with_api_keys(self):
        """Test model validation with various API key scenarios."""
        config_manager = LLMConfigurationManager()

        # Test with no API keys
        self.assertFalse(config_manager._validate_model("openai:gpt-4"))
        self.assertFalse(config_manager._validate_model("anthropic:claude-3"))

        # Test with OpenAI API key
        os.environ["OPENAI_API_KEY"] = "test-key"
        self.assertTrue(config_manager._validate_model("openai:gpt-4"))
        self.assertTrue(config_manager._validate_model("openai:gpt-4o-mini"))

        # Test with Anthropic API key
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        self.assertTrue(config_manager._validate_model("anthropic:claude-3"))

        # Test unknown provider (should return False since provider not in config)
        self.assertFalse(config_manager._validate_model("unknown:model"))

    def test_selected_model_property(self):
        """Test the selected_model property with validation."""
        # Set up environment for OpenAI
        os.environ["OPENAI_API_KEY"] = "test-key"

        config_manager = LLMConfigurationManager(explicit_model="openai:gpt-4o-mini")

        # Test getter
        self.assertEqual(config_manager.selected_model, "openai:gpt-4o-mini")

        # Test setter with valid model
        config_manager.selected_model = "openai:gpt-4"
        self.assertEqual(config_manager.selected_model, "openai:gpt-4")

        # Test setter with invalid model (should raise LLMError)
        with self.assertRaises(LLMError):
            config_manager.selected_model = "anthropic:claude-3"  # No ANTHROPIC_API_KEY

    @patch("opendxa.common.resource.llm_configuration_manager.ConfigLoader")
    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables for this test
    def test_find_first_available_model(self, mock_config_loader):
        """Test finding the first available model from configuration."""
        # Mock configuration
        mock_config = {
            "llm": {
                "preferred_models": [
                    "anthropic:claude-3",  # No API key
                    "openai:gpt-4",  # Will have API key
                    "google:gemini-1.5-pro",  # No API key
                ],
                "provider_configs": {
                    "anthropic": {"api_key": "env:ANTHROPIC_API_KEY", "api_type": "anthropic"},
                    "openai": {"api_key": "env:OPENAI_API_KEY", "api_type": "openai"},
                    "google": {"api_key": "env:GOOGLE_API_KEY", "api_type": "openai"},
                },
            }
        }
        mock_config_loader.return_value.get_default_config.return_value = mock_config

        # Set up OpenAI API key only
        os.environ["OPENAI_API_KEY"] = "test-key"

        config_manager = LLMConfigurationManager()

        # Should find the first available model from preferred_models list
        result = config_manager._find_first_available_model()
        # With OPENAI_API_KEY set, openai:gpt-4 is the first available model in the list
        self.assertEqual(result, "openai:gpt-4")

    @patch("opendxa.common.resource.llm_configuration_manager.ConfigLoader")
    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables for this test
    def test_find_first_available_model_none_available(self, mock_config_loader):
        """Test when no models are available."""
        # Mock configuration with models that need API keys we don't have
        mock_config = {
            "llm": {
                "preferred_models": ["someprovider:nonexistent-model", "anotherprovider:missing-model"],
                "provider_configs": {
                    # Note: someprovider and anotherprovider are intentionally not in the config
                },
            }
        }
        mock_config_loader.return_value.get_default_config.return_value = mock_config

        config_manager = LLMConfigurationManager()

        # Should return None when no models are available
        result = config_manager._find_first_available_model()
        self.assertIsNone(result)

    @patch("opendxa.common.resource.llm_configuration_manager.ConfigLoader")
    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables for this test
    def test_get_available_models(self, mock_config_loader):
        """Test getting list of available models."""
        # Mock configuration including provider_configs
        mock_config = {
            "llm": {
                "preferred_models": [
                    "openai:gpt-4o",
                    "openai:gpt-4o-mini",
                    "someprovider:unavailable-model",
                    "anotherprovider:missing-model",
                ],
                "provider_configs": {
                    "openai": {"api_key": "env:OPENAI_API_KEY", "api_type": "openai"}
                    # Note: someprovider and anotherprovider are intentionally not in the config
                },
            }
        }
        mock_config_loader.return_value.get_default_config.return_value = mock_config

        # Set up only OpenAI API key
        os.environ["OPENAI_API_KEY"] = "test-key"

        config_manager = LLMConfigurationManager()

        available_models = config_manager.get_available_models()

        # Should only return OpenAI models (models with available API keys)
        self.assertIn("openai:gpt-4o", available_models)
        self.assertIn("openai:gpt-4o-mini", available_models)
        self.assertNotIn("someprovider:unavailable-model", available_models)
        self.assertNotIn("anotherprovider:missing-model", available_models)

    @patch("opendxa.common.resource.llm_configuration_manager.ConfigLoader")
    def test_get_model_config(self, mock_config_loader):
        """Test getting model-specific configuration."""
        # Mock configuration
        mock_config = {"llm": {"model_configs": {"openai:gpt-4": {"max_tokens": 8192, "temperature": 0.7, "timeout": 60}}}}
        mock_config_loader.return_value.get_default_config.return_value = mock_config

        config_manager = LLMConfigurationManager()

        # Test getting config for configured model
        config = config_manager.get_model_config("openai:gpt-4")
        self.assertEqual(config["max_tokens"], 8192)
        self.assertEqual(config["temperature"], 0.7)

        # Test getting config for unconfigured model (should return defaults)
        default_config = config_manager.get_model_config("anthropic:claude-3")
        self.assertEqual(default_config["max_tokens"], 4096)
        self.assertEqual(default_config["temperature"], 0.7)

    @patch("opendxa.common.resource.llm_configuration_manager.ConfigLoader")
    @patch.dict(os.environ, {"OPENDXA_MOCK_LLM": "false", "OPENAI_API_KEY": "test-key"}, clear=True)
    def test_determine_model_explicit(self, mock_config_loader):
        """Test model determination with explicit model."""
        # Mock configuration with provider configs
        mock_config = {
            "llm": {
                "preferred_models": ["openai:gpt-4"],
                "provider_configs": {"openai": {"api_key": "env:OPENAI_API_KEY", "api_type": "openai"}},
            }
        }
        mock_config_loader.return_value.get_default_config.return_value = mock_config

        config_manager = LLMConfigurationManager(explicit_model="openai:gpt-4")

        # Should use explicit model
        model = config_manager._determine_model()
        self.assertEqual(model, "openai:gpt-4")

    @patch("opendxa.common.resource.llm_configuration_manager.ConfigLoader")
    @patch.dict(os.environ, {"OPENDXA_MOCK_LLM": "false"}, clear=True)  # Clear all env vars and disable mock mode
    def test_determine_model_explicit_unavailable(self, mock_config_loader):
        """Test model determination with unavailable explicit model."""
        # Mock configuration
        mock_config = {
            "llm": {
                "preferred_models": ["openai:gpt-4"],
                "provider_configs": {
                    "openai": {"api_key": "env:OPENAI_API_KEY", "api_type": "openai"}
                    # Note: someprovider is intentionally not in the config
                },
            }
        }
        mock_config_loader.return_value.get_default_config.return_value = mock_config

        # Use a model that requires an API key we don't have
        config_manager = LLMConfigurationManager(explicit_model="someprovider:unavailable-model")

        # Should raise error for unavailable explicit model
        with self.assertRaises(LLMError) as context:
            config_manager._determine_model()

        self.assertIn("not available", str(context.exception))

    @patch("opendxa.common.resource.llm_configuration_manager.ConfigLoader")
    @patch.dict(os.environ, {"OPENDXA_MOCK_LLM": "false", "OPENAI_API_KEY": "test-key"}, clear=True)
    def test_determine_model_auto_selection(self, mock_config_loader):
        """Test model determination with auto-selection."""
        # Mock configuration
        mock_config = {
            "llm": {
                "preferred_models": ["openai:gpt-4"],
                "default_model": "openai:gpt-4o-mini",
                "provider_configs": {"openai": {"api_key": "env:OPENAI_API_KEY", "api_type": "openai"}},
            }
        }
        mock_config_loader.return_value.get_default_config.return_value = mock_config

        config_manager = LLMConfigurationManager()  # No explicit model

        # Should auto-select first available
        model = config_manager._determine_model()
        self.assertEqual(model, "openai:gpt-4")

    @patch.dict(os.environ, {"OPENDXA_MOCK_LLM": "false"})
    def test_error_handling_with_config_errors(self):
        """Test graceful error handling when config files are corrupt or missing."""
        with patch("opendxa.common.resource.llm_configuration_manager.ConfigLoader") as mock_config_loader:
            # Make config loader raise an exception
            mock_config_loader.return_value.get_default_config.side_effect = FileNotFoundError("Config not found")

            config_manager = LLMConfigurationManager()

            # Should handle gracefully and return empty list
            available_models = config_manager.get_available_models()
            self.assertEqual(available_models, [])

            # Test get_model_config with explicit model to avoid selected_model issues
            model_config = config_manager.get_model_config("openai:gpt-4")
            self.assertEqual(model_config["max_tokens"], 4096)

            # Test that determine_model raises appropriate error when no models available
            with self.assertRaises(LLMError) as context:
                config_manager._determine_model()
            self.assertIn("No available LLM models found", str(context.exception))

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        config_manager = LLMConfigurationManager()

        # Test empty model name
        self.assertFalse(config_manager._validate_model(""))
        self.assertFalse(config_manager._validate_model(None))  # type: ignore

        # Test model without provider prefix
        os.environ["OPENAI_API_KEY"] = "test-key"
        self.assertTrue(config_manager._validate_model("gpt-4"))  # Defaults to openai


class TestLLMConfigurationManagerIntegration(unittest.TestCase):
    """Integration tests for LLMConfigurationManager with LLMResource."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear environment variables for clean tests
        self.original_env = {}
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            self.original_env[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_llm_resource_uses_configuration_manager(self):
        """Test that LLMResource properly uses LLMConfigurationManager."""
        from dana.common.resource.llm_resource import LLMResource

        # Set up API key
        os.environ["OPENAI_API_KEY"] = "test-key"

        # Create LLMResource with explicit model
        llm = LLMResource(name="test_llm", model="openai:gpt-4o-mini")

        # Verify configuration manager is created
        self.assertIsNotNone(llm._config_manager)
        self.assertIsInstance(llm._config_manager, LLMConfigurationManager)

        # Verify model property uses configuration manager
        self.assertEqual(llm.model, "openai:gpt-4o-mini")

        # Verify model validation uses configuration manager
        self.assertTrue(llm._validate_model("openai:gpt-4"))
        self.assertFalse(llm._validate_model("anthropic:claude-3"))  # No API key

        # Verify available models uses configuration manager
        available = llm.get_available_models()
        self.assertIsInstance(available, list)

    def test_model_setting_through_property(self):
        """Test setting model through property."""
        from dana.common.resource.llm_resource import LLMResource

        # Set up API keys
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

        llm = LLMResource(name="test_llm", model="openai:gpt-4o-mini")

        # Change model through property
        llm.model = "anthropic:claude-3-5-sonnet-20241022"
        self.assertEqual(llm.model, "anthropic:claude-3-5-sonnet-20241022")

        # Verify backward compatibility - _model should also be updated
        self.assertEqual(llm._model, "anthropic:claude-3-5-sonnet-20241022")


if __name__ == "__main__":
    unittest.main()
