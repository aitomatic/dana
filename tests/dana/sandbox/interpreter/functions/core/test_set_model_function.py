"""Test the set_model function implementation."""

import os
import unittest
from unittest.mock import patch

from dana.common.exceptions import SandboxError
from dana.common.resource.llm.llm_resource import LLMResource
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.stdlib.core.set_model_function import set_model_function


class TestSetModelFunction(unittest.TestCase):
    """Test the set_model function."""

    def setUp(self):
        """Set up test fixtures."""
        self.context = SandboxContext()
        # Clear any existing environment variables for clean tests
        self.original_env = {}
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
            self.original_env[key] = os.environ.get(key)

    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_set_model_with_no_existing_llm_resource(self):
        """Test setting model when no LLM resource exists in context."""
        # Set up API key for testing
        os.environ["OPENAI_API_KEY"] = "test-key"

        result = set_model_function(self.context, "openai:gpt-4o")

        # Verify result
        self.assertEqual(result, "openai:gpt-4o")

        # Verify LLM resource was created and set in context
        llm_resource = self.context.get("system:llm_resource")
        self.assertIsNotNone(llm_resource)
        self.assertIsInstance(llm_resource, LLMResource)
        self.assertEqual(llm_resource.model, "openai:gpt-4o")

    def test_set_model_with_existing_llm_resource(self):
        """Test setting model when LLM resource already exists in context."""
        # Set up API keys
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

        # Create existing LLM resource
        existing_llm = LLMResource(name="existing_llm", model="openai:gpt-4o-mini")
        self.context.set("system:llm_resource", existing_llm)

        result = set_model_function(self.context, "anthropic:claude-3-5-sonnet-20241022")

        # Verify result
        self.assertEqual(result, "anthropic:claude-3-5-sonnet-20241022")

        # Verify the same LLM resource was updated (not replaced)
        updated_llm = self.context.get("system:llm_resource")
        self.assertIs(updated_llm, existing_llm)  # Same object
        self.assertEqual(updated_llm.model, "anthropic:claude-3-5-sonnet-20241022")

    def test_set_model_empty_string(self):
        """Test setting model with empty string raises error."""
        with self.assertRaises(SandboxError) as context:
            set_model_function(self.context, "")

        self.assertIn("non-empty model name", str(context.exception))

    def test_set_model_non_string_input(self):
        """Test setting model with non-string input raises error."""
        with self.assertRaises(SandboxError) as context:
            set_model_function(self.context, 123)  # type: ignore

        self.assertIn("Model name must be a string", str(context.exception))

    def test_set_model_invalid_model_name(self):
        """Test setting model without API keys succeeds (backward compatibility)."""
        # Don't set any API keys - LLM resources are designed to be permissive for testing
        with patch.dict(os.environ, {}, clear=True):  # Clear all env vars
            # This should succeed as LLM resources allow models without strict validation
            result = set_model_function(self.context, "invalid:model-name")
            self.assertEqual(result, "invalid:model-name")

            # Verify LLM resource was created despite no API keys
            llm_resource = self.context.get("system:llm_resource")
            self.assertIsNotNone(llm_resource)
            self.assertEqual(llm_resource.model, "invalid:model-name")

    def test_set_model_with_options_parameter(self):
        """Test that options parameter is accepted but unused."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        result = set_model_function(self.context, "openai:gpt-4o", options={"unused_option": "value"})

        self.assertEqual(result, "openai:gpt-4o")

    def test_set_model_none_options(self):
        """Test setting model with None options parameter."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        result = set_model_function(self.context, "openai:gpt-4o", options=None)

        self.assertEqual(result, "openai:gpt-4o")

    @patch("dana.core.stdlib.core.set_model_function.LLMResource")
    def test_set_model_llm_resource_creation_error(self, mock_llm_resource):
        """Test error handling when LLMResource creation fails."""
        # Mock LLMResource to raise an exception
        mock_llm_resource.side_effect = Exception("Resource creation failed")

        with self.assertRaises(SandboxError) as context:
            set_model_function(self.context, "openai:gpt-4o")

        self.assertIn("Unexpected error setting model", str(context.exception))
        self.assertIn("Resource creation failed", str(context.exception))

    def test_set_model_preserves_existing_llm_name(self):
        """Test that updating model preserves the existing LLM resource name."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        # Create existing LLM resource with custom name
        existing_llm = LLMResource(name="custom_llm_name", model="openai:gpt-4o-mini")
        self.context.set("system:llm_resource", existing_llm)

        set_model_function(self.context, "openai:gpt-4o")

        # Verify the name is preserved
        updated_llm = self.context.get("system:llm_resource")
        self.assertEqual(updated_llm.name, "custom_llm_name")
        self.assertEqual(updated_llm.model, "openai:gpt-4o")

    def test_fuzzy_matching_gpt4(self):
        """Test fuzzy matching for GPT-4 variants."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        # Test partial match "gpt-4" should match "openai:gpt-4o"
        result = set_model_function(self.context, "gpt-4")

        # Should match to a GPT-4 variant
        self.assertIn("gpt-4", result.lower())
        self.assertTrue(result.startswith("openai:"))

    def test_fuzzy_matching_claude(self):
        """Test fuzzy matching for Claude models."""
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

        # Test partial match "claude" should match an Anthropic Claude model
        result = set_model_function(self.context, "claude")

        # Should match to a Claude variant
        self.assertIn("claude", result.lower())
        self.assertTrue(result.startswith("anthropic:"))

    def test_fuzzy_matching_gemini(self):
        """Test fuzzy matching for Gemini models."""
        os.environ["GOOGLE_API_KEY"] = "test-key"

        # Test partial match "gemini" should match a Google Gemini model
        result = set_model_function(self.context, "gemini")

        # Should match to a Gemini variant
        self.assertIn("gemini", result.lower())
        self.assertTrue(result.startswith("google:"))

    def test_fuzzy_matching_deepseek(self):
        """Test fuzzy matching for DeepSeek models."""
        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        # Test partial match "deepseek" should match a DeepSeek model
        result = set_model_function(self.context, "deepseek")

        # Should match to a DeepSeek variant
        self.assertIn("deepseek", result.lower())
        self.assertTrue(result.startswith("deepseek:"))

    def test_exact_match_only_option(self):
        """Test exact match only option disables fuzzy matching."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        # With exact_match_only=True, partial matches should not work
        result = set_model_function(self.context, "gpt-4", options={"exact_match_only": True})

        # Should use the input as-is
        self.assertEqual(result, "gpt-4")

    def test_fuzzy_matching_case_insensitive(self):
        """Test that fuzzy matching is case insensitive."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        # Test case insensitive matching
        result = set_model_function(self.context, "GPT-4O")

        # Should match to the properly cased model
        self.assertIn("gpt-4o", result.lower())

    def test_fuzzy_matching_no_match(self):
        """Test fuzzy matching when no close match is found."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        # Test with a completely unrelated string
        result = set_model_function(self.context, "completely-unrelated-model")

        # Should use the input as-is when no good match is found
        self.assertEqual(result, "completely-unrelated-model")

    def test_fuzzy_matching_provider_specific(self):
        """Test fuzzy matching with provider-specific partial inputs."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        # Test "openai:gpt" should match to a specific OpenAI GPT model
        result = set_model_function(self.context, "openai:gpt")

        # Should match to an OpenAI GPT model
        self.assertTrue(result.startswith("openai:"))
        self.assertIn("gpt", result.lower())

    def test_fuzzy_matching_returns_different_model(self):
        """Test that fuzzy matching can return a different model name."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        # Use a partial match that should resolve to a different full name
        original_input = "gpt-4o"  # This should match to "openai:gpt-4o"
        result = set_model_function(self.context, original_input)

        # Result should be different from input (fuzzy matched)
        self.assertNotEqual(result, original_input)
        self.assertIn("gpt-4o", result.lower())
        self.assertTrue(result.startswith("openai:"))

    def test_get_available_model_names_helper(self):
        """Test the helper function that gets available model names."""
        from dana.core.stdlib.core.set_model_function import (
            _get_available_model_names,
        )

        models = _get_available_model_names()

        # Should return a list of model names
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)

        # Should contain common models
        model_str = " ".join(models).lower()
        self.assertIn("openai", model_str)
        self.assertIn("gpt", model_str)

    def test_find_closest_model_match_helper(self):
        """Test the fuzzy matching helper function directly."""
        from dana.core.stdlib.core.set_model_function import (
            _find_closest_model_match,
        )

        available_models = [
            "openai:gpt-4o",
            "openai:gpt-4o-mini",
            "anthropic:claude-3-5-sonnet-20241022",
            "google:gemini-1.5-pro",
        ]

        # Test exact match
        result = _find_closest_model_match("openai:gpt-4o", available_models)
        self.assertEqual(result, "openai:gpt-4o")

        # Test partial match
        result = _find_closest_model_match("gpt-4", available_models)
        self.assertIsNotNone(result)
        if result:
            self.assertIn("gpt-4", result)

        # Test case insensitive
        result = _find_closest_model_match("GPT-4O", available_models)
        self.assertEqual(result, "openai:gpt-4o")

        # Test no match
        result = _find_closest_model_match("nonexistent", available_models)
        self.assertIsNone(result)

    def test_set_model_no_parameters_no_current_model(self):
        """Test set_model() with no parameters when no current model is set."""
        # Redirect stdout to capture print statements
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            result = set_model_function(self.context)

            # Should return "None" when no model is set
            self.assertEqual(result, "None")

            # Should display current model and available options in concise format
            output = captured_output.getvalue()
            self.assertIn("Current model: None", output)
            # Could show either available models or no models message depending on API keys
            self.assertTrue("Available models:" in output or "No models available" in output)

        finally:
            sys.stdout = sys.__stdout__

    def test_set_model_no_parameters_with_current_model(self):
        """Test set_model() with no parameters when a current model is set."""
        # Set up a model first
        os.environ["OPENAI_API_KEY"] = "test-key"
        set_model_function(self.context, "openai:gpt-4o")

        # Redirect stdout to capture print statements
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            result = set_model_function(self.context)

            # Should return the current model
            self.assertEqual(result, "openai:gpt-4o")

            # Should display current model and available options in concise format
            output = captured_output.getvalue()
            self.assertIn("Current model: openai:gpt-4o", output)
            self.assertIn("Available models:", output)
            self.assertIn("✓ openai:gpt-4o", output)  # Should show current model with checkmark

        finally:
            sys.stdout = sys.__stdout__

    def test_set_model_no_parameters_displays_grouped_models(self):
        """Test that set_model() displays available models grouped by provider."""
        # Redirect stdout to capture print statements
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            result = set_model_function(self.context)

            # Should return current model status
            self.assertEqual(result, "None")

            # Should display available models or no models message
            output = captured_output.getvalue()
            self.assertTrue("Available models:" in output or "❌ No models available" in output)

            # If models are available, should show provider grouping
            if "Available models:" in output:
                self.assertIn(":", output)  # Should have provider sections like "OPENAI:"

        finally:
            sys.stdout = sys.__stdout__

    def test_set_model_no_parameters_shows_enhanced_examples(self):
        """Test that set_model() shows enhanced examples with emojis."""
        # Redirect stdout to capture print statements
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            set_model_function(self.context)

            # Should show enhanced examples if models are available
            output = captured_output.getvalue()
            if "Available models:" in output:
                self.assertIn("💡 Examples:", output)
                self.assertIn("fuzzy match →", output)
                self.assertIn("🔧 Pro tips:", output)
                self.assertIn("provider →", output)
            elif "❌ No models available" in output:
                self.assertIn("🔑 Check your API keys", output)
                self.assertIn("OPENAI_API_KEY", output)

        finally:
            sys.stdout = sys.__stdout__

    def test_enhanced_provider_fuzzy_matching(self):
        """Test that enhanced fuzzy matching works with provider intelligence."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        # Test provider-only input should return best model for that provider
        result = set_model_function(self.context, "openai")
        self.assertTrue(result.startswith("openai:"))
        self.assertIn("gpt", result.lower())

        # Test enhanced GPT matching should prefer OpenAI and latest versions
        result = set_model_function(self.context, "gpt-4")
        self.assertTrue(result.startswith("openai:"))
        self.assertIn("gpt-4", result.lower())

        # Test case insensitive still works
        result = set_model_function(self.context, "GPT-4O")
        self.assertIn("gpt-4o", result.lower())


if __name__ == "__main__":
    unittest.main()
