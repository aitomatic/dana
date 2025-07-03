"""Test the list_models function implementation."""

import os
import unittest
from unittest.mock import patch

from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.interpreter.functions.core.list_models_function import list_models_function
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class TestListModelsFunction(unittest.TestCase):
    """Test the list_models function."""

    def setUp(self):
        """Set up test fixtures."""
        self.context = SandboxContext()
        # Clear any existing environment variables for clean tests
        self.original_env = {}
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "DEEPSEEK_API_KEY"]:
            if key in os.environ:
                self.original_env[key] = os.environ[key]
            os.environ[key] = "test-key"

    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "DEEPSEEK_API_KEY"]:
            if key in self.original_env:
                os.environ[key] = self.original_env[key]
            elif key in os.environ:
                del os.environ[key]

    def test_list_models_no_options(self):
        """Test listing models with no options."""
        result = list_models_function(self.context)

        # Should return a list of strings
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # All items should be strings
        for model in result:
            self.assertIsInstance(model, str)
            self.assertGreater(len(model), 0)

    def test_list_models_none_options(self):
        """Test listing models with None options."""
        result = list_models_function(self.context, options=None)

        # Should work the same as no options
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_list_models_empty_options(self):
        """Test listing models with empty options dict."""
        result = list_models_function(self.context, options={})

        # Should work the same as no options
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_filter_by_openai_provider(self):
        """Test filtering models by OpenAI provider."""
        result = list_models_function(self.context, options={"provider": "openai"})

        # Should return only OpenAI models
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        for model in result:
            self.assertTrue(model.startswith("openai:"), f"Model {model} should start with 'openai:'")

    def test_filter_by_anthropic_provider(self):
        """Test filtering models by Anthropic provider."""
        result = list_models_function(self.context, options={"provider": "anthropic"})

        # Should return only Anthropic models
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        for model in result:
            self.assertTrue(model.startswith("anthropic:"), f"Model {model} should start with 'anthropic:'")

    def test_filter_by_deepseek_provider(self):
        """Test filtering models by DeepSeek provider."""
        result = list_models_function(self.context, options={"provider": "deepseek"})

        # Should return only DeepSeek models
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        for model in result:
            self.assertTrue(model.startswith("deepseek:"), f"Model {model} should start with 'deepseek:'")

    def test_filter_by_case_insensitive_provider(self):
        """Test that provider filtering is case insensitive."""
        result_lower = list_models_function(self.context, options={"provider": "openai"})
        result_upper = list_models_function(self.context, options={"provider": "OPENAI"})
        result_mixed = list_models_function(self.context, options={"provider": "OpenAI"})

        # All should return the same results
        self.assertEqual(result_lower, result_upper)
        self.assertEqual(result_lower, result_mixed)

    def test_filter_by_nonexistent_provider(self):
        """Test filtering by a provider that doesn't exist."""
        result = list_models_function(self.context, options={"provider": "nonexistent"})

        # Should return empty list
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_models_are_in_preference_order(self):
        """Test that models are returned in preference order."""
        result = list_models_function(self.context)

        # The first model should be the top preferred model from the config
        # Based on opendxa_config.json, "openai:gpt-4o-mini" is the first preferred model
        self.assertEqual(result[0], "openai:gpt-4o-mini")

        # Check that another preferred model is also present
        self.assertIn("local", result)

    def test_openai_models_preference_order(self):
        """Test that OpenAI models are in the correct preference order."""
        result = list_models_function(self.context, options={"provider": "openai"})

        # Should have multiple OpenAI models
        self.assertGreater(len(result), 1)

        # The first OpenAI model should be the most preferred one
        self.assertEqual(result[0], "openai:gpt-4o-mini")

    def test_function_error_handling(self):
        """Test error handling in the function."""
        # Mock _get_available_model_names to raise an exception
        with patch("opendxa.dana.sandbox.interpreter.functions.core.list_models_function._get_available_model_names") as mock_get_models:
            mock_get_models.side_effect = Exception("Test error")

            with self.assertRaises(SandboxError) as context:
                list_models_function(self.context)

            self.assertIn("Unexpected error listing models", str(context.exception))

    def test_unknown_option_ignored(self):
        """Test that unknown options are ignored gracefully."""
        result = list_models_function(self.context, options={"unknown_option": "value"})

        # Should work normally, ignoring unknown options
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main()
