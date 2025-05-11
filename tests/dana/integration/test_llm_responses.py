"""Test handling of different LLM response formats in the interpreter."""

import unittest

from opendxa.dana.language.ast import LogLevel
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter
from opendxa.dana.runtime.repl import REPL


class TestLLMResponseFormats(unittest.TestCase):
    """Test the interpreter's handling of different LLM response formats."""

    def setUp(self):
        """Set up the test environment."""
        self.context = RuntimeContext()
        self.interpreter = Interpreter(self.context)
        self.repl = REPL(log_level=LogLevel.INFO, context=self.context)

    def test_openai_style_response(self):
        """Test handling of OpenAI-style dictionary responses."""
        # Create a parse result for testing

        # Create an LLM integration object to test response processing directly
        from opendxa.dana.runtime.executor.context_manager import ContextManager
        from opendxa.dana.runtime.executor.llm_integration import LLMIntegration

        # Create a context manager
        context_manager = ContextManager(self.context)

        # Create the LLM integration to test
        llm_integration = LLMIntegration(context_manager)

        # Create a mock response in OpenAI format
        mock_content = {"choices": [{"message": {"content": "This is a test response"}}]}

        # Test the processor directly
        result = llm_integration._process_llm_response(mock_content)

        # Verify the result
        assert result == "This is a test response"

    def test_deepseek_style_response(self):
        """Test handling of DeepSeek-style object responses."""
        # Create a parse result for testing

        # Create an LLM integration object to test response processing directly
        from opendxa.dana.runtime.executor.context_manager import ContextManager
        from opendxa.dana.runtime.executor.llm_integration import LLMIntegration

        # Create a context manager
        context_manager = ContextManager(self.context)

        # Create the LLM integration to test
        llm_integration = LLMIntegration(context_manager)

        # Create a mock Choice object to simulate DeepSeek's response
        class MockMessage:
            def __init__(self):
                self.content = "This is a test response"

        class MockChoice:
            def __init__(self):
                self.message = MockMessage()

        mock_choice = MockChoice()

        # Create the response in DeepSeek format
        mock_content = {"choices": [mock_choice]}

        # Test the processor directly
        result = llm_integration._process_llm_response(mock_content)

        # The result should be the string "This is a test response"
        # Note: This might fail if the LLM integration doesn't handle object attributes correctly
        # In a real implementation, it would need to handle both dictionary access and attribute access
        assert str(result) == str(mock_choice.message.content)

    def test_direct_content_response(self):
        """Test handling of direct content responses."""
        # Create an LLM integration object to test response processing directly
        from opendxa.dana.runtime.executor.context_manager import ContextManager
        from opendxa.dana.runtime.executor.llm_integration import LLMIntegration

        # Create a context manager
        context_manager = ContextManager(self.context)

        # Create the LLM integration to test
        llm_integration = LLMIntegration(context_manager)

        # Create a mock response with direct content
        mock_content = {"content": "This is a test response"}

        # Test the processor directly
        result = llm_integration._process_llm_response(mock_content)

        # Verify the result
        assert result == "This is a test response"

    def test_fallback_response(self):
        """Test fallback handling for unexpected response formats."""
        # Create an LLM integration object to test response processing directly
        from opendxa.dana.runtime.executor.context_manager import ContextManager
        from opendxa.dana.runtime.executor.llm_integration import LLMIntegration

        # Create a context manager
        context_manager = ContextManager(self.context)

        # Create the LLM integration to test
        llm_integration = LLMIntegration(context_manager)

        # Create a simple string response
        mock_content = "This is a direct string response"

        # Test the processor directly
        result = llm_integration._process_llm_response(mock_content)

        # Verify the result
        assert result == "This is a direct string response"


if __name__ == "__main__":
    unittest.main()
