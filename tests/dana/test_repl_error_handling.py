"""Test REPL error handling for undefined variables in log/print statements."""

import io
import sys
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import LogLevel
from opendxa.dana.runtime.repl import REPL


@pytest.mark.asyncio
class TestReplErrorHandling:
    """Test how the REPL handles errors with unprefixed variables."""
    
    @pytest_asyncio.fixture
    async def context(self):
        """Create a context for testing."""
        return RuntimeContext()
    
    @pytest_asyncio.fixture
    async def mock_llm(self):
        """Create a mock LLM resource for testing."""
        # Create a MagicMock that supports await
        from unittest.mock import AsyncMock, MagicMock
        
        mock_llm = MagicMock(spec=LLMResource)
        
        # Mock the initialize method with AsyncMock
        mock_llm.initialize = AsyncMock(return_value=None)
        
        # Prepare a successful response with a properly structured message
        # This is crucial for both reasoning and transcoding
        mock_message = MagicMock()
        mock_message.content = "This is a mock LLM response"
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = {"choices": [mock_choice]}
        
        # Mock the query method with AsyncMock
        mock_llm.query = AsyncMock(return_value=mock_response)
        
        return mock_llm
    
    @pytest_asyncio.fixture
    async def repl(self, context, mock_llm):
        """Set up a fresh REPL with a context for each test."""
        repl = REPL(context=context, llm_resource=mock_llm, log_level=LogLevel.DEBUG)
        # Set up a variable for all tests
        await repl.execute("a = 10")
        return repl
        
    async def test_undefined_var_in_print(self, repl):
        """Test that print with undefined variable works."""
        # Now test print with the variable
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            await repl.execute("print(a)")
            output = mock_stdout.getvalue().strip()
            assert output.startswith('10'), f"Output '{output}' doesn't contain '10'"
            
    async def test_undefined_var_in_log(self, repl):
        """Test that log with undefined variable works."""
        # We need to use a direct parsing path and skip the transcoder
        with patch.object(repl, 'transcoder', None):
            with patch.object(repl.interpreter, '_log') as mock_log:
                await repl.execute("log(a)")
                # Check that log was called (no exception was raised)
                assert mock_log.called, "Log method was not called"
            
    async def test_binary_expr_with_var(self, repl):
        """Test that binary expressions with variables work."""
        # We need to use a direct parsing path and skip the transcoder
        with patch.object(repl, 'transcoder', None):
            # Now test log with a binary expression including the variable
            with patch.object(repl.interpreter, '_log') as mock_log:
                await repl.execute("log(a + 2)")
                # Check that log was called (no exception was raised)
                assert mock_log.called, "Log method was not called"
            
    async def test_log_level_with_var(self, repl):
        """Test that log.error with a variable works."""
        # We need to use a direct parsing path and skip the transcoder
        with patch.object(repl, 'transcoder', None):
            # Now test log.error with a variable
            with patch.object(repl.interpreter, '_log') as mock_log:
                await repl.execute("log.error(a)")
                # Get the calls to _log and check if any have the expected arguments
                calls = mock_log.call_args_list
                assert any(call[0][0] == '10' and call[0][1] == LogLevel.ERROR for call in calls), \
                    "No call to _log with '10' and ERROR level was made"
                
    async def test_reason_statement(self, repl):
        """Test that reason statement works in REPL."""
        # Patch the _visit_reason_statement_sync method to avoid actual LLM calls
        with patch.object(repl.interpreter, '_visit_reason_statement_sync') as mock_reason:
            # Set up a side effect that simulates adding result to context
            def reason_side_effect(node, context=None):
                # Log the mock response directly
                repl.interpreter._log("Reasoning result: This is a mock LLM response", LogLevel.INFO)
                return None
            
            mock_reason.side_effect = reason_side_effect
            
            # Run a reason statement with a simple prompt
            with patch.object(repl.interpreter, '_log') as mock_log:
                await repl.execute('reason("What is 2+2?")')
                
                # Check that log was called with the mock response
                calls = mock_log.call_args_list
                assert any("mock LLM response" in call[0][0] for call in calls), \
                    "Expected log to contain the mock LLM response"
                
    async def test_reason_with_variable(self, repl):
        """Test that reason statement with variables works in REPL."""
        # Patch the _visit_reason_statement_sync method to avoid actual LLM calls
        with patch.object(repl.interpreter, '_visit_reason_statement_sync') as mock_reason:
            # Set up a side effect that simulates adding result to context
            def reason_side_effect(node, context=None):
                # Log the mock response directly
                repl.interpreter._log("Reasoning result: This is a mock LLM response", LogLevel.INFO)
                return None
            
            mock_reason.side_effect = reason_side_effect
            
            # Run a reason statement with a variable
            with patch.object(repl.interpreter, '_log') as mock_log:
                await repl.execute('reason(f"What is {a} + 2?")')
                
                # Check that log was called with the mock response
                calls = mock_log.call_args_list
                assert any("mock LLM response" in call[0][0] for call in calls), \
                    "Expected log to contain the mock LLM response"