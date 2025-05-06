"""Test handling of different LLM response formats in the interpreter."""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest
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
        
        # Register a mock LLM resource
        self.mock_llm = MagicMock(spec=LLMResource)
        self.context.register_resource("reason_llm", self.mock_llm)

    def test_openai_style_response(self):
        """Test handling of OpenAI-style dictionary responses."""
        # Create a response structure with OpenAI-style format
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response"
                    }
                }
            ]
        }
        
        # Set up the async mock for LLM query
        async def mock_initialize():
            return None
        self.mock_llm.initialize = mock_initialize
        
        async def mock_query(*args, **kwargs):
            return mock_response
        self.mock_llm.query = mock_query
        
        # Create a reason statement
        literal = Literal("test prompt")
        expr = LiteralExpression(literal)
        reason_stmt = ReasonStatement(expr, None, None, {})
        
        # Patch the _log method to check the output
        with patch.object(self.interpreter, '_log') as mock_log:
            # Execute the reason statement synchronously
            self.interpreter._visit_reason_statement_sync(reason_stmt)
            
            # Check that the right content was extracted and logged
            calls = mock_log.call_args_list
            assert any("This is a test response" in str(call) for call in calls), \
                "Expected log to contain the test response"

    def test_deepseek_style_response(self):
        """Test handling of DeepSeek-style object responses."""
        # Create a mock Choice object to simulate DeepSeek's response
        class MockMessage:
            def __init__(self):
                self.content = "This is a test response"

        class MockChoice:
            def __init__(self):
                self.message = MockMessage()

        mock_choice = MockChoice()
        
        # Create the response
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = {
            "choices": [mock_choice]
        }
        
        # Set up the async mock for LLM query
        async def mock_initialize():
            return None
        self.mock_llm.initialize = mock_initialize
        
        async def mock_query(*args, **kwargs):
            return mock_response
        self.mock_llm.query = mock_query
        
        # Create a reason statement
        literal = Literal("test prompt")
        expr = LiteralExpression(literal)
        reason_stmt = ReasonStatement(expr, None, None, {})
        
        # Patch the _log method to check the output
        with patch.object(self.interpreter, '_log') as mock_log:
            # Execute the reason statement synchronously
            self.interpreter._visit_reason_statement_sync(reason_stmt)
            
            # Check that the right content was extracted and logged
            calls = mock_log.call_args_list
            assert any("This is a test response" in str(call) for call in calls), \
                "Expected log to contain the test response"

    def test_direct_content_response(self):
        """Test handling of direct content responses."""
        # Create a response with direct content field
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = {
            "content": "This is a test response"
        }
        
        # Set up the async mock for LLM query
        async def mock_initialize():
            return None
        self.mock_llm.initialize = mock_initialize
        
        async def mock_query(*args, **kwargs):
            return mock_response
        self.mock_llm.query = mock_query
        
        # Create a reason statement
        literal = Literal("test prompt")
        expr = LiteralExpression(literal)
        reason_stmt = ReasonStatement(expr, None, None, {})
        
        # Patch the _log method to check the output
        with patch.object(self.interpreter, '_log') as mock_log:
            # Execute the reason statement synchronously
            self.interpreter._visit_reason_statement_sync(reason_stmt)
            
            # Check that the right content was extracted and logged
            calls = mock_log.call_args_list
            assert any("This is a test response" in str(call) for call in calls), \
                "Expected log to contain the test response"

    def test_fallback_response(self):
        """Test fallback handling for unexpected response formats."""
        # Create an unexpected response format (direct string)
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = "This is a direct string response"
        
        # Set up the async mock for LLM query
        async def mock_initialize():
            return None
        self.mock_llm.initialize = mock_initialize
        
        async def mock_query(*args, **kwargs):
            return mock_response
        self.mock_llm.query = mock_query
        
        # Create a reason statement
        literal = Literal("test prompt")
        expr = LiteralExpression(literal)
        reason_stmt = ReasonStatement(expr, None, None, {})
        
        # Patch the _log method to check the output
        with patch.object(self.interpreter, '_log') as mock_log:
            # Execute the reason statement synchronously
            self.interpreter._visit_reason_statement_sync(reason_stmt)
            
            # Check that the response was handled correctly
            calls = mock_log.call_args_list
            assert any("This is a direct string response" in str(call) for call in calls), \
                "Expected log to contain the direct string response"


if __name__ == '__main__':
    unittest.main()