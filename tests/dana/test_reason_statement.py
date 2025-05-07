"""Tests for the reason statement in the DANA REPL."""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch

from opendxa.common.resource.llm_resource import LLMResource
# REPL import not needed for this test
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.language.ast import LogLevel


@pytest.fixture
def runtime_context():
    """Create a runtime context for testing."""
    return RuntimeContext()


class TestReasonStatement:
    """Test the reason statement in the DANA REPL."""

    @pytest_asyncio.fixture
    async def mock_llm(self):
        """Create a mock LLM resource for testing."""
        from unittest.mock import AsyncMock
        
        # Create a MagicMock that supports await
        mock_llm = MagicMock(spec=LLMResource)
        
        # Mock the initialize method with AsyncMock
        mock_llm.initialize = AsyncMock(return_value=None)
        
        # Prepare a successful response
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = {"choices": [{"message": {"content": "This is a mock LLM response"}}]}
        
        # Mock the query method with AsyncMock
        mock_llm.query = AsyncMock(return_value=mock_response)
        
        return mock_llm

    def test_reason_statement_in_repl(self, runtime_context):
        """Test the reason statement in the DANA REPL."""
        # We'll use a simpler approach with the interpreter directly
        from opendxa.dana.runtime.interpreter import create_interpreter
        from opendxa.dana.language.parser import parse
        
        # Create an interpreter
        interpreter = create_interpreter(runtime_context)
        
        # Mock the LLM integration component
        with patch.object(interpreter.statement_executor.llm_integration, 'execute_direct_synchronous_reasoning') as mock_reasoning:
            # Mock the reasoning to return a fixed result
            mock_reasoning.return_value = "Paris"
            
            # Parse and execute a simple reason statement with assignment
            program = parse('private.result = reason("What is the capital of France?")')
            interpreter.execute_program(program)
            
            # Verify our mock was called with the right prompt
            mock_reasoning.assert_called_once()
            args, _ = mock_reasoning.call_args
            assert args[0] == "What is the capital of France?"
            
            # Verify the variable was set correctly
            assert interpreter.context.get("private.result") == "Paris"