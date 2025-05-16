"""Simplified test for reason statements outside of asyncio."""

from unittest.mock import MagicMock, patch

import pytest

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser, ParseResult
from opendxa.dana.sandbox.sandbox_context import SandboxContext


@pytest.fixture
def runtime_context():
    """Create a runtime context for testing."""
    return SandboxContext()


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


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return DanaParser()


def test_reason_statement(runtime_context, mock_llm, parser):
    """Test the reason statement outside of asyncio."""
    # We need to mock the LLM integration completely to avoid asyncio issues

    # Create an interpreter
    interpreter = Interpreter.new(runtime_context)

    # Mock the LLM integration component
    with patch.object(interpreter.statement_executor.llm_integration, "execute_direct_synchronous_reasoning") as mock_reasoning:
        # Mock the reasoning to return a fixed result
        mock_reasoning.return_value = "4"

        # Parse and execute a simple reason statement with assignment
        program = parser.parse('private.result = reason("What is 2+2?")')
        interpreter.execute_program(program)

        # Verify our mock was called with the right prompt
        mock_reasoning.assert_called_once()
        args, _ = mock_reasoning.call_args
        assert args[0] == "What is 2+2?"

        # Verify the variable was set correctly
        assert interpreter.context.get("private.result") == "4"


def test_parse_simple_reason(parser):
    """Test parsing a simple reason statement."""
    program = parser.parse('private.result = reason("What is 2+2?")')
    assert isinstance(program, ParseResult)
    assert program.is_valid
    assert len(program.program.statements) == 1
