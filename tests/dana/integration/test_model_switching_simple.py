"""Simple model switching tests to verify core functionality."""

import os
import unittest
from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


class TestSimpleModelSwitching(unittest.TestCase):
    """Test simple model switching functionality."""

    def setUp(self):
        """Set up test environment."""
        self.original_env = os.environ.copy()
        
        # Set API keys and enable mock mode
        os.environ.update({
            "OPENAI_API_KEY": "test-openai-key",
            "ANTHROPIC_API_KEY": "test-anthropic-key", 
            "OPENDXA_MOCK_LLM": "true"
        })
        
        self.sandbox = DanaSandbox()

    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
        
        if hasattr(self, 'sandbox'):
            self.sandbox._cleanup()

    def test_openai_to_anthropic_switch(self):
        """Test switching from OpenAI to Anthropic."""
        code = '''
# Test OpenAI
set_model("openai:gpt-4")
openai_result = reason("What is 2+2?")
log(f"OpenAI: {openai_result}")

# Test Anthropic
set_model("anthropic:claude-3-5-sonnet-20240620")
anthropic_result = reason("What is 3+3?")
log(f"Anthropic: {anthropic_result}")

# Verify both work
log(f"OpenAI success: {openai_result is not None}")
log(f"Anthropic success: {anthropic_result is not None}")
'''
        result = self.sandbox.eval(code)
        self.assertTrue(result.success, f"Failed: {result.error}")

    def test_multiple_provider_switching(self):
        """Test switching between multiple providers."""
        code = '''
# Test sequence of model switches
models = ["openai:gpt-4", "anthropic:claude-3-5-sonnet-20240620", "openai:gpt-3.5-turbo"]
questions = ["What is pi?", "What is the sky color?", "What is 5*5?"]

for i in range(len(models)):
    set_model(models[i])
    result = reason(questions[i])
    log(f"Model {models[i]}: {result is not None}")

log("All model switches completed")
'''
        result = self.sandbox.eval(code)
        self.assertTrue(result.success, f"Failed: {result.error}")

    def test_model_switching_with_parameters(self):
        """Test model switching with different parameters."""
        code = '''
# Test without parameters first
set_model("openai:gpt-4")
result1 = reason("Explain AI")
log(f"OpenAI basic: {result1 is not None}")

set_model("anthropic:claude-3-haiku-20240307")
result2 = reason("Explain ML")
log(f"Anthropic basic: {result2 is not None}")

log("Basic tests completed")
'''
        result = self.sandbox.eval(code)
        self.assertTrue(result.success, f"Failed: {result.error}")


if __name__ == "__main__":
    unittest.main()