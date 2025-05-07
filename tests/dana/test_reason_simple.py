"""Simplified test for reason statements outside of asyncio."""

import pytest
from unittest.mock import MagicMock, patch

from opendxa.dana.runtime.context import RuntimeContext
# REPL import not needed for this test
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.language.ast import LogLevel


@pytest.fixture
def runtime_context():
    """Create a runtime context for testing."""
    return RuntimeContext()


@pytest.fixture
def mock_llm():
    """Create a mock LLM resource for testing."""
    mock_llm = MagicMock(spec=LLMResource)
    
    # Mock the initialize method
    mock_llm.initialize = MagicMock(return_value=None)
    
    # Mock the query method to return a successful response
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.content = {"choices": [{"message": {"content": "This is a mock LLM response"}}]}
    mock_llm.query = MagicMock(return_value=mock_response)
    
    return mock_llm


def test_reason_statement(runtime_context, mock_llm):
    """Test the reason statement outside of asyncio."""
    # We need to mock the LLM integration completely to avoid asyncio issues
    
    from opendxa.dana.runtime.interpreter import create_interpreter
    from opendxa.dana.language.parser import parse
    
    # Create an interpreter
    interpreter = create_interpreter(runtime_context)
    
    # Mock the LLM integration component
    with patch.object(interpreter.statement_executor.llm_integration, 'execute_direct_synchronous_reasoning') as mock_reasoning:
        # Mock the reasoning to return a fixed result
        mock_reasoning.return_value = "4"
        
        # Parse and execute a simple reason statement with assignment
        program = parse('private.result = reason("What is 2+2?")')
        interpreter.execute_program(program)
        
        # Verify our mock was called with the right prompt
        mock_reasoning.assert_called_once()
        args, _ = mock_reasoning.call_args
        assert args[0] == "What is 2+2?"
        
        # Verify the variable was set correctly
        assert interpreter.context.get("private.result") == "4"