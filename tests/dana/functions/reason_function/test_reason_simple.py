"""Simplified test for reason statements outside of asyncio."""

from unittest.mock import MagicMock

import pytest

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser, Program
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
    # Set the mock LLM in the context so the interpreter will use it
    runtime_context.set("system.__reason_llm", mock_llm)
    interpreter = Interpreter.new(runtime_context)

    # Parse and execute a simple reason statement with assignment
    program = parser.parse('private:result = reason("What is 2+2?")')
    interpreter.execute_program(program)

    # Verify our mock was called
    mock_llm.query.assert_called_once()

    # Verify the variable was set correctly
    assert interpreter.context.get("private:result") == "4"


def test_parse_simple_reason(parser):
    """Test parsing a simple reason statement."""
    program = parser.parse('private:result = reason("What is 2+2?")')
    assert isinstance(program, Program)
    assert len(program.statements) == 1
