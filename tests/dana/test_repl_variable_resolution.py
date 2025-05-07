"""Test REPL variable resolution consistency between print and log statements."""

import io
import sys
import unittest
from unittest.mock import patch

from opendxa.dana.language.ast import (
    Identifier,
    Literal,
    LiteralExpression,
    LogLevel,
    LogStatement,
    PrintStatement,
)
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter, LogLevel


class TestReplVariableResolution(unittest.TestCase):
    """Test REPL variable resolution between print and log statements."""

    def setUp(self):
        """Set up a fresh context and interpreter for each test."""
        self.context = RuntimeContext()
        self.interpreter = Interpreter(self.context)
        # Ensure debug log level to see all log statements
        self.interpreter.set_log_level(LogLevel.DEBUG)
        
        # Set up test variables directly
        self.context.set('private.a', 5)
        self.context.set('private.obj', {'value': 10})
    
    def test_direct_variable_access(self):
        """Test direct variable access through expression evaluation."""
        # Use direct expression evaluation
        a_value = self.interpreter.evaluate_expression(Identifier(name='private.a'))
        assert a_value == 5, f"Expected a value to be 5, got {a_value}"
        
        # Test nested object reference
        obj_value = self.interpreter.evaluate_expression(Identifier(name='private.obj.value'))
        assert obj_value == 10, f"Expected obj.value to be 10, got {obj_value}"
        
    def test_print_variable_in_repl(self):
        """Test that print statements can access variables in REPL mode."""
        # Mock REPL execution
        from opendxa.dana.runtime.repl import REPL
        from unittest.mock import MagicMock
        
        # Create a simple REPL object with our context
        repl = REPL(MagicMock(), self.context)
        
        # Test print with variable
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            # Mute the debug logging that gets printed along with the output
            with patch.object(self.interpreter.statement_executor, '_log'):
                # Call the statement executor directly with existing variable
                print_node = PrintStatement(message=Identifier(name='private.a'))
                self.interpreter.statement_executor.execute_print_statement(print_node)
                
                # Check output (just the first line)
                output = mock_stdout.getvalue().split('\n')[0].strip()
                assert output == '5', f"Expected output to be '5', got '{output}'"
            
    def test_log_variable_in_repl(self):
        """Test that log statements can access variables in REPL mode."""
        # Test using the log statement directly
        with patch.object(self.interpreter.statement_executor, '_log') as mock_log:
            # Create and execute a log statement with a variable using the statement executor
            log_node = LogStatement(
                message=Identifier(name='private.a'),
                level=LogLevel.INFO
            )
            self.interpreter.statement_executor.execute_log_statement(log_node)
            
            # Check the output
            mock_log.assert_called()
            assert mock_log.call_args[0][0] == '5', f"Expected log call with '5', got {mock_log.call_args}"