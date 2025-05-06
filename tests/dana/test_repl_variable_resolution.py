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
        
    def test_variable_resolution_consistency(self):
        """Test that variable resolution is consistent in log and print statements."""
        # Test direct variable access with print statement
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            # Create a PrintStatement node directly
            print_node = PrintStatement(
                message=Identifier(name='a')
            )
            # Visit the node
            self.interpreter.visit_print_statement(print_node)
            # Check output
            output = mock_stdout.getvalue().strip()
            self.assertTrue(output.startswith('5'), f"Print output didn't start with '5': {output}")
        
        # Test direct variable access with log statement
        with patch.object(self.interpreter, '_log') as mock_log:
            # Create a LogStatement node directly
            log_node = LogStatement(
                message=Identifier(name='a'),
                level=LogLevel.INFO
            )
            # Visit the node
            self.interpreter.visit_log_statement(log_node)
            # Check that _log was called with the value '5'
            mock_log.assert_called_with('5', LogLevel.INFO)
            
    def test_complex_variable_resolution(self):
        """Test resolution with nested variable references."""
        # Test direct access to nested variables with print
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            # Create a PrintStatement node directly with a complex path
            print_node = PrintStatement(
                message=Identifier(name='obj.value')
            )
            # Visit the node
            self.interpreter.visit_print_statement(print_node)
            # Check output
            output = mock_stdout.getvalue().strip()
            self.assertTrue(output.startswith('10'), f"Print output didn't start with '10': {output}")
        
        # Test direct access to nested variables with log
        with patch.object(self.interpreter, '_log') as mock_log:
            # Create a LogStatement node directly with a complex path
            log_node = LogStatement(
                message=Identifier(name='obj.value'),
                level=LogLevel.INFO
            )
            # Visit the node
            self.interpreter.visit_log_statement(log_node)
            # Check that _log was called with the value '10'
            mock_log.assert_called_with('10', LogLevel.INFO)
            
    def test_unprefixed_variable_access(self):
        """Test direct access to unprefixed variables."""
        # Test that we can directly access 'a' without prefix in both print and log statements
        
        # For print statement
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            # Create custom context with unprefixed variable
            custom_context = {'a': 5}
            # Create a PrintStatement node
            print_node = PrintStatement(
                message=Identifier(name='a')
            )
            # Visit the node with custom context
            self.interpreter.visit_print_statement(print_node, custom_context)
            # Check output
            output = mock_stdout.getvalue().strip()
            self.assertTrue(output.startswith('5'), f"Print output didn't start with '5': {output}")
        
        # For log statement
        with patch.object(self.interpreter, '_log') as mock_log:
            # Create custom context with unprefixed variable
            custom_context = {'a': 5}
            # Create a LogStatement node
            log_node = LogStatement(
                message=Identifier(name='a'),
                level=LogLevel.INFO
            )
            # Visit the node with custom context
            self.interpreter.visit_log_statement(log_node, custom_context)
            # Check that _log was called with the value '5'
            mock_log.assert_called_with('5', LogLevel.INFO)