"""Simplified Dana REPL tests for model switching.

These tests verify basic model switching functionality without complex Dana syntax.
"""

import os
import unittest

from dana.core.lang.dana_sandbox import DanaSandbox


class TestSimpleModelSwitching(unittest.TestCase):
    """Test simple model switching functionality."""

    def setUp(self):
        """Set up test environment."""
        self.original_env = os.environ.copy()

        # Set API keys and enable mock mode
        os.environ.update({"OPENAI_API_KEY": "test-openai-key", "ANTHROPIC_API_KEY": "test-anthropic-key", "DANA_MOCK_LLM": "true"})

        self.sandbox = DanaSandbox()

    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

        if hasattr(self, "sandbox"):
            self.sandbox._cleanup()

    def test_basic_model_switching_openai_to_anthropic(self):
        """Test basic model switching from OpenAI to Anthropic."""
        # Test OpenAI
        result = self.sandbox.execute_string('set_model("openai:gpt-4")')
        self.assertTrue(result.success)

        result = self.sandbox.execute_string('reason("What is 2+2?")')
        self.assertTrue(result.success)

        # Test Anthropic
        result = self.sandbox.execute_string('set_model("anthropic:claude-3-5-sonnet-20240620")')
        self.assertTrue(result.success)

        result = self.sandbox.execute_string('reason("What is 3+3?")')
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
