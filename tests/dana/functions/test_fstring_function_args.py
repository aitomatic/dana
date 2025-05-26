"""
Tests for f-string evaluation in function arguments.

This module tests that f-strings are properly evaluated before being passed to functions
like reason(), ensuring consistency with other functions like print().
"""

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import parse_program
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_fstring_evaluation_in_print():
    """Test that f-strings are properly evaluated when passed to print()."""
    # Create a context and set a variable
    context = SandboxContext()
    context.set("local.message", "Hello world")

    # Create an interpreter
    interpreter = DanaInterpreter()

    # Capture output
    import sys
    from io import StringIO

    stdout_backup = sys.stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        # Execute print with f-string
        interpreter.execute_program(parse_program('print(f"{local.message}")'), context)

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

    # Create an interpreter
    interpreter = DanaInterpreter()

    # Use the real reason function with built-in mocking (use_mock=True)
    # We'll set an environment variable to force mocking
    import os

    original_mock_env = os.environ.get("OPENDXA_MOCK_LLM")
    os.environ["OPENDXA_MOCK_LLM"] = "true"

    try:
        # Execute reason with f-string - this should work without any patching
        result = interpreter.execute_program(parse_program('reason(f"{local.query}")'), context)

        # The key test: if f-string evaluation works, the function should execute successfully
        # If f-strings weren't evaluated, we'd get an error about FStringExpression not being a string
        assert result is not None, "Function should return a result"

        # The result could be a string or dict depending on the mock implementation
        # What matters is that it executed successfully, proving f-string was evaluated
        assert isinstance(result, (str, dict)), f"Result should be a string or dict, got {type(result)}"

    finally:
        # Restore original environment
        if original_mock_env is None:
            os.environ.pop("OPENDXA_MOCK_LLM", None)
        else:
            os.environ["OPENDXA_MOCK_LLM"] = original_mock_env


def test_consistency_between_print_and_reason():
    """Test that print() and reason() behave consistently with f-string arguments."""
    # Create a context and set a variable
    context = SandboxContext()
    context.set("local.value", 42)

    # Create an interpreter
    interpreter = DanaInterpreter()

    # Use environment variable to enable mocking for reason function
    import os

    original_mock_env = os.environ.get("OPENDXA_MOCK_LLM")
    os.environ["OPENDXA_MOCK_LLM"] = "true"

    # Capture print output
    import sys
    from io import StringIO

    stdout_backup = sys.stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        # Execute both functions with the same f-string
        interpreter.execute_program(parse_program('print(f"The answer is {local.value}")'), context)
        reason_result = interpreter.execute_program(parse_program('reason(f"The answer is {local.value}")'), context)

        # Get print output
        print_output = captured_output.getvalue().strip()

        # Both functions should handle f-strings consistently
        # Print should output the evaluated string
        assert print_output == "The answer is 42"

        # Reason should execute successfully (proving f-string was evaluated)
        assert reason_result is not None, "Reason should return a result"
        assert isinstance(reason_result, (str, dict)), "Reason should return a string or dict result"

        # The key test: both functions should work with the same f-string syntax
        # If f-string evaluation is inconsistent, one would fail

    finally:
        sys.stdout = stdout_backup
        # Restore original environment
        if original_mock_env is None:
            os.environ.pop("OPENDXA_MOCK_LLM", None)
        else:
            os.environ["OPENDXA_MOCK_LLM"] = original_mock_env
