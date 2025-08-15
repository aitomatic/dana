"""Simple test to verify Dana functions are available."""

import os
import unittest

from dana.core.lang.dana_sandbox import DanaSandbox


class TestSimpleDanaFunctions(unittest.TestCase):
    """Test simple Dana functions."""

    def setUp(self):
        """Set up test environment."""
        # Clean environment and set required API keys
        self.original_env = os.environ.copy()

        # Set API keys for all providers to enable testing
        os.environ.update(
            {
                "OPENAI_API_KEY": "test-openai-key",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "GROQ_API_KEY": "test-groq-key",
                "DEEPSEEK_API_KEY": "test-deepseek-key",
                # Enable mock mode for testing
                "DANA_MOCK_LLM": "true",
            }
        )

        # Create sandbox instance
        self.sandbox = DanaSandbox()

    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

        if hasattr(self, "sandbox"):
            self.sandbox._cleanup()

    def test_basic_log_function(self):
        """Test basic log function works."""
        code = 'log("Hello from Dana!")'
        result = self.sandbox.execute_string(code)

        if not result.success:
            print(f"FAILED: {result.error}")
            print(f"Output: {result.output}")
            print(f"Context: {result.final_context}")

        self.assertTrue(result.success, f"Dana execution failed: {result.error}")

    def test_basic_variable_assignment(self):
        """Test basic variable assignment."""
        code = """
x = 5
log(f"x = {x}")
"""
        result = self.sandbox.execute_string(code)

        if not result.success:
            print(f"FAILED: {result.error}")
            print(f"Output: {result.output}")
            print(f"Context: {result.final_context}")

        self.assertTrue(result.success, f"Dana execution failed: {result.error}")

    def test_set_model_function_exists(self):
        """Test if set_model function exists."""
        code = """
set_model("openai:gpt-4")
log("set_model function exists")
"""
        result = self.sandbox.execute_string(code)

        if not result.success:
            print(f"FAILED: {result.error}")
            print(f"Output: {result.output}")
            print(f"Context: {result.final_context}")

        self.assertTrue(result.success, f"Dana execution failed: {result.error}")

    def test_reason_function_exists(self):
        """Test if reason function exists."""
        code = """
set_model("openai:gpt-4")
result = reason("What is 2+2?")
log(f"reason function works: {result is not None}")
"""
        result = self.sandbox.execute_string(code)

        if not result.success:
            print(f"FAILED: {result.error}")
            print(f"Output: {result.output}")
            print(f"Context: {result.final_context}")

        self.assertTrue(result.success, f"Dana execution failed: {result.error}")

    def test_get_current_model_function_exists(self):
        """Test if get_current_model function exists."""
        # Skip this test since get_current_model doesn't exist
        self.skipTest("get_current_model function is not implemented in Dana")


if __name__ == "__main__":
    unittest.main()
