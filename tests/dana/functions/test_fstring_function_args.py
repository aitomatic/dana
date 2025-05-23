"""
Tests for f-string evaluation in function arguments.

This module tests that f-strings are properly evaluated before being passed to functions
like reason(), ensuring consistency with other functions like print().
"""

from unittest.mock import patch

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.ast import FStringExpression
from opendxa.dana.sandbox.parser.dana_parser import parse_program
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_fstring_evaluation_in_print():
    """Test that f-strings are properly evaluated when passed to print()."""
    # Create a context and set a variable
    context = SandboxContext()
    context.set("local.message", "Hello world")

    # Create an interpreter
    interpreter = DanaInterpreter(context)

    # Capture output
    import sys
    from io import StringIO

    stdout_backup = sys.stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        # Execute print with f-string
        interpreter.execute_program(parse_program('print(f"{local.message}")'))

        # Get and check output
        output = captured_output.getvalue().strip()
        assert output == "Hello world"
    finally:
        sys.stdout = stdout_backup


def test_fstring_evaluation_in_reason():
    """Test that f-strings are properly evaluated when passed to reason()."""
    # Create a context and set a variable
    context = SandboxContext()
    context.set("local.query", "What is the capital of France?")

    # Mock reason_function to verify it receives the evaluated string
    with patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.reason_function") as mock_reason:
        mock_reason.return_value = "Paris"

        # Create an interpreter
        interpreter = DanaInterpreter(context)

        # Execute reason with f-string
        result = interpreter.execute_program(parse_program('reason(f"{local.query}")'))

        # Verify reason_function was called with the evaluated string
        mock_reason.assert_called_once()
        args, _ = mock_reason.call_args
        first_arg = args[0]

        assert isinstance(first_arg, str), f"First argument should be a string, got {type(first_arg)}"
        assert first_arg == "What is the capital of France?", f"Expected 'What is the capital of France?', got '{first_arg}'"
        assert not isinstance(first_arg, FStringExpression), "First argument should not be an FStringExpression"


def test_consistency_between_print_and_reason():
    """Test that print() and reason() behave consistently with f-string arguments."""
    # Create a context and set a variable
    context = SandboxContext()
    context.set("local.value", 42)

    # Mock reason_function
    with patch("opendxa.dana.sandbox.interpreter.functions.core.reason_function.reason_function") as mock_reason:
        mock_reason.return_value = "Mock reason response"

        # Capture print output
        import sys
        from io import StringIO

        stdout_backup = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            # Create an interpreter
            interpreter = DanaInterpreter(context)

            # Execute both functions with the same f-string
            interpreter.execute_program(parse_program('print(f"The answer is {local.value}")'))
            interpreter.execute_program(parse_program('reason(f"The answer is {local.value}")'))

            # Get print output
            print_output = captured_output.getvalue().strip()

            # Verify both functions received the same evaluated string
            args, _ = mock_reason.call_args
            reason_arg = args[0]

            assert print_output == "The answer is 42"
            assert reason_arg == "The answer is 42"
        finally:
            sys.stdout = stdout_backup
