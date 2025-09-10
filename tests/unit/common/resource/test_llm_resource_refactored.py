"""Test the refactored LLMResource class with LLMConfigurationManager integration."""

import os
import unittest
from unittest.mock import patch

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.common.sys_resource.llm.llm_configuration_manager import LLMConfigurationManager


class TestLLMResourceRefactored(unittest.TestCase):
    """Test the refactored LLMResource class."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear environment variables for clean tests
        self.original_env = {}
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "DANA_MOCK_LLM"]:
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

    def test_configuration_manager_integration(self):
        """Test that LLMResource properly integrates with LLMConfigurationManager."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        llm = LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini")

        # Verify configuration manager is created and configured correctly
        self.assertIsInstance(llm._config_manager, LLMConfigurationManager)
        self.assertEqual(llm._config_manager.explicit_model, "openai:gpt-4o-mini")

    def test_model_property_uses_config_manager(self):
        """Test that model property stays in sync with configuration manager."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        llm = LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini")

        # Verify getter returns the correct model
        self.assertEqual(llm.model, "openai:gpt-4o-mini")

        # Verify that the property and config manager are in sync
        self.assertEqual(llm.model, llm._config_manager.selected_model)

    def test_model_property_setter_uses_config_manager(self):
        """Test that model property setter uses configuration manager."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

        llm = LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini")

        # Change model through property
        llm.model = "anthropic:claude-3-5-sonnet-20241022"

        # Verify both property and config manager are updated
        self.assertEqual(llm.model, "anthropic:claude-3-5-sonnet-20241022")
        self.assertEqual(llm._config_manager.selected_model, "anthropic:claude-3-5-sonnet-20241022")

        # Verify backward compatibility
        self.assertEqual(llm._model, "anthropic:claude-3-5-sonnet-20241022")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)  # Only have OpenAI key
    def test_model_property_setter_permissive_behavior(self):
        """Test model property setter permissive behavior."""
        llm = LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini")

        # Try to set unavailable model (no API key for someprovider)
        # This should succeed now with the permissive approach
        llm.model = "someprovider:unavailable-model"

        # Verify the model was set successfully
        self.assertEqual(llm.model, "someprovider:unavailable-model")

        # Verify both internal model and config manager are in sync
        self.assertEqual(llm._model, "someprovider:unavailable-model")
        self.assertEqual(llm._config_manager.selected_model, "someprovider:unavailable-model")

    def test_validate_model_uses_config_manager(self):
        """Test that _validate_model uses configuration manager."""
        # Check if we're in mock mode
        if os.environ.get("DANA_MOCK_LLM", "false").lower() == "true":
            # In mock mode, only mock models should be valid
            llm = LegacyLLMResource(name="test_llm", model="mock:test-model")
            self.assertTrue(llm._validate_model("mock:test-model"))
            # Real models will fail validation in mock mode (no API keys)
            self.assertFalse(llm._validate_model("openai:gpt-4"))
            self.assertFalse(llm._validate_model("anthropic:claude-3"))
        else:
            # In real mode, test with actual API keys
            os.environ["OPENAI_API_KEY"] = "test-key"
            llm = LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini")
            
            # Test validation through LLMResource
            self.assertTrue(llm._validate_model("openai:gpt-4"))
            self.assertFalse(llm._validate_model("anthropic:claude-3"))  # No API key

        # Verify it's using config manager's method
        with patch.object(llm._config_manager, "_validate_model", return_value=True) as mock_validate:
            result = llm._validate_model("test:model")
            mock_validate.assert_called_once_with("test:model")
            self.assertTrue(result)

    def test_find_first_available_model_uses_config_manager(self):
        """Test that _find_first_available_model uses configuration manager."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        llm = LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini")

        # Test method delegation
        with patch.object(llm._config_manager, "_find_first_available_model", return_value="openai:gpt-4") as mock_find:
            result = llm._find_first_available_model()
            mock_find.assert_called_once()
            self.assertEqual(result, "openai:gpt-4")

    def test_get_available_models_uses_config_manager(self):
        """Test that get_available_models uses configuration manager."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        llm = LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini")

        # Test method delegation with logging
        with patch.object(llm._config_manager, "get_available_models", return_value=["openai:gpt-4"]) as mock_get:
            with patch.object(llm, "debug") as mock_debug:
                result = llm.get_available_models()

                mock_get.assert_called_once()
                mock_debug.assert_called_once()
                self.assertEqual(result, ["openai:gpt-4"])

    def test_backward_compatibility(self):
        """Test that refactored LLMResource maintains backward compatibility."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        # Test all original instantiation patterns still work

        # 1. Default instantiation
        llm1 = LegacyLLMResource()
        self.assertIsNotNone(llm1._config_manager)

        # 2. With explicit model
        llm2 = LegacyLLMResource(name="test_llm", model="openai:gpt-4")
        self.assertIsInstance(llm2.model, str)

        # 3. With config parameters
        llm3 = LegacyLLMResource(name="test_llm", temperature=0.9, max_tokens=2048)
        self.assertEqual(llm3.config["temperature"], 0.9)
        self.assertEqual(llm3.config["max_tokens"], 2048)

    @patch("dana.common.config.ConfigLoader")
    @patch("dana.common.sys_resource.llm.llm_configuration_manager.ConfigLoader")
    def test_preferred_models_integration(self, mock_config_loader_cm, mock_config_loader):
        """Test integration with preferred models from configuration."""
        # Mock configuration with preferred models
        mock_config = {
            "llm": {
                "preferred_models": [
                    {"name": "openai:gpt-4", "required_api_keys": ["OPENAI_API_KEY"]},
                    {"name": "anthropic:claude-3", "required_api_keys": ["ANTHROPIC_API_KEY"]},
                ]
            }
        }
        mock_config_loader.return_value.get_default_config.return_value = mock_config
        mock_config_loader_cm.return_value.get_default_config.return_value = mock_config

        os.environ["OPENAI_API_KEY"] = "test-key"

        llm = LegacyLLMResource(name="test_llm")  # No explicit model

        # Should have preferred_models as a list of strings
        self.assertIsInstance(llm.preferred_models, list)
        self.assertTrue(all(isinstance(m, str) for m in llm.preferred_models))
        # Optionally, check that the list is not empty
        self.assertTrue(len(llm.preferred_models) > 0)

        # Config manager should be initialized with this info
        self.assertIsNotNone(llm._config_manager)

    def test_code_reduction_verification(self):
        """Verify that the refactoring actually reduced code complexity."""
        import inspect

        from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
        from dana.common.sys_resource.llm.llm_configuration_manager import LLMConfigurationManager

        # Get method source code lengths for verification
        llm_validate_lines = len(inspect.getsource(LegacyLLMResource._validate_model).split("\n"))
        llm_find_lines = len(inspect.getsource(LegacyLLMResource._find_first_available_model).split("\n"))
        llm_get_available_lines = len(inspect.getsource(LegacyLLMResource.get_available_models).split("\n"))

        config_validate_lines = len(inspect.getsource(LLMConfigurationManager._validate_model).split("\n"))
        config_find_lines = len(inspect.getsource(LLMConfigurationManager._find_first_available_model).split("\n"))
        config_get_available_lines = len(inspect.getsource(LLMConfigurationManager.get_available_models).split("\n"))

        # Verify that LLMResource methods are now simple delegations (should be much shorter than before)
        self.assertLessEqual(llm_validate_lines, 15, "LLMResource._validate_model should be a simple delegation")
        self.assertLessEqual(llm_find_lines, 15, "LLMResource._find_first_available_model should be a simple delegation")
        self.assertLessEqual(llm_get_available_lines, 15, "LLMResource.get_available_models should be mostly delegation")

        # Verify that configuration manager has the actual implementation
        self.assertGreater(config_validate_lines, 10, "LLMConfigurationManager should have substantial logic")
        self.assertGreater(config_find_lines, 10, "LLMConfigurationManager should have substantial logic")
        self.assertGreater(config_get_available_lines, 10, "LLMConfigurationManager should have substantial logic")

    def test_api_surface_unchanged(self):
        """Test that the public API surface of LLMResource is unchanged."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        llm = LegacyLLMResource(name="test_llm", model="openai:gpt-4o-mini")

        # Verify all expected public methods/properties exist
        self.assertTrue(hasattr(llm, "model"))
        self.assertTrue(hasattr(llm, "get_available_models"))
        self.assertTrue(hasattr(llm, "query"))
        self.assertTrue(hasattr(llm, "query_sync"))
        self.assertTrue(hasattr(llm, "initialize"))
        self.assertTrue(hasattr(llm, "cleanup"))
        self.assertTrue(hasattr(llm, "can_handle"))
        self.assertTrue(hasattr(llm, "with_mock_llm_call"))

        # Verify expected private methods exist (for internal use)
        self.assertTrue(hasattr(llm, "_validate_model"))
        self.assertTrue(hasattr(llm, "_find_first_available_model"))

        # Verify property behavior
        self.assertTrue(callable(llm.get_available_models))

        # Verify model property works as expected
        original_model = llm.model
        llm.model = "openai:gpt-4"
        self.assertEqual(llm.model, "openai:gpt-4")
        llm.model = original_model


if __name__ == "__main__":
    unittest.main()
