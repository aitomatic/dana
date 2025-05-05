"""Test handling of different LLM response formats in the interpreter."""

import unittest
from unittest.mock import patch, MagicMock

from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter, LogLevel
from opendxa.dana.language.ast import ReasonStatement, Literal, LiteralExpression


class TestLLMResponseFormats(unittest.TestCase):
    """Test the interpreter's handling of different LLM response formats."""

    def setUp(self):
        """Set up the test environment."""
        self.context = RuntimeContext()
        self.interpreter = Interpreter(self.context)
        self.interpreter.set_log_level(LogLevel.INFO)

    @patch('opendxa.dana.runtime.interpreter.Interpreter._perform_reasoning')
    def test_openai_style_response(self, mock_reasoning):
        """Test handling of OpenAI-style dictionary responses."""
        # Mock the _perform_reasoning method to return a dictionary response
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response"
                    }
                }
            ]
        }
        mock_reasoning.return_value = mock_response

        # Create a reason statement
        literal = Literal("test prompt")
        expr = LiteralExpression(literal)
        reason_stmt = ReasonStatement(expr, None, None, {})

        # Execute the reason statement synchronously to avoid asyncio issues
        self.interpreter._visit_reason_statement_sync(reason_stmt)

        # Verify the reasoning was called
        mock_reasoning.assert_called_once()

    @patch('opendxa.dana.runtime.interpreter.Interpreter._perform_reasoning')
    @patch('json.dumps')
    def test_deepseek_style_response(self, mock_dumps, mock_reasoning):
        """Test handling of DeepSeek-style object responses."""
        # Create a mock Choice object to simulate DeepSeek's response
        class MockMessage:
            def __init__(self):
                self.content = "This is a test response"

        class MockChoice:
            def __init__(self):
                self.message = MockMessage()

        mock_choice = MockChoice()
        
        # Mock the response
        mock_response = {
            "choices": [mock_choice]
        }
        
        # Mock the json.dumps function to avoid serialization issues
        mock_dumps.return_value = '{"mocked": "response"}'
        
        mock_reasoning.return_value = mock_response

        # Create a reason statement
        literal = Literal("test prompt")
        expr = LiteralExpression(literal)
        reason_stmt = ReasonStatement(expr, None, None, {})

        # Execute the reason statement synchronously to avoid asyncio issues
        self.interpreter._visit_reason_statement_sync(reason_stmt)

        # Verify the reasoning was called
        mock_reasoning.assert_called_once()

    @patch('opendxa.dana.runtime.interpreter.Interpreter._perform_reasoning')
    def test_direct_content_response(self, mock_reasoning):
        """Test handling of direct content responses."""
        # Mock the _perform_reasoning method to return a direct content response
        mock_response = {
            "content": "This is a test response"
        }
        mock_reasoning.return_value = mock_response

        # Create a reason statement
        literal = Literal("test prompt")
        expr = LiteralExpression(literal)
        reason_stmt = ReasonStatement(expr, None, None, {})

        # Execute the reason statement synchronously to avoid asyncio issues
        self.interpreter._visit_reason_statement_sync(reason_stmt)

        # Verify the reasoning was called
        mock_reasoning.assert_called_once()

    @patch('opendxa.dana.runtime.interpreter.Interpreter._perform_reasoning')
    def test_fallback_response(self, mock_reasoning):
        """Test fallback handling for unexpected response formats."""
        # Mock the _perform_reasoning method to return an unexpected response
        mock_response = "This is a direct string response"
        mock_reasoning.return_value = mock_response

        # Create a reason statement
        literal = Literal("test prompt")
        expr = LiteralExpression(literal)
        reason_stmt = ReasonStatement(expr, None, None, {})

        # Execute the reason statement synchronously to avoid asyncio issues
        self.interpreter._visit_reason_statement_sync(reason_stmt)

        # Verify the reasoning was called
        mock_reasoning.assert_called_once()


if __name__ == '__main__':
    unittest.main()