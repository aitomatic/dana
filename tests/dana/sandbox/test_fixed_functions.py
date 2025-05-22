"""
Tests for the unified function execution in DANA using DanaExecutor.

These tests verify that function registration, resolution, and execution work correctly
with the unified DanaExecutor approach.
"""

import pytest

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.interpreter.executor.dana_executor import DanaExecutor
from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionMetadata, FunctionRegistry
from opendxa.dana.sandbox.parser.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    FStringExpression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    PrintStatement,
    Program,
)
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_function_registry_basic():
    """Test basic function registry operations."""
    registry = FunctionRegistry()

    # Register a function
    def foo(context, x):
        return x + 1

    registry.register("foo", foo)

    # Check if exists
    assert registry.has("foo")
    assert not registry.has("bar")

    # Resolve the function
    func, func_type, metadata = registry.resolve("foo")
    assert callable(func)
    assert func_type == "python"
    assert isinstance(metadata, FunctionMetadata)

    # Call the function
    context = SandboxContext()
    result = registry.call("foo", context, args=[41])
    assert result == 42


def test_evaluate_function_call():
    """Test evaluating function calls."""
    context = SandboxContext()
    # Create executor with proper context
    executor = DanaExecutor(context)

    # Register a function that doesn't take context as first param
    def add(a, b):
        return a + b

    registry = FunctionRegistry()
    registry.register("add", add)

    # Make function accessible to the evaluator through the context
    context.set_registry(registry)

    # Create a function call node
    func_call = FunctionCall(name="add", args={"0": LiteralExpression(17), "1": LiteralExpression(25)})

    # Evaluate the function call
    result = executor.execute(func_call, context)
    assert result == 42


def test_evaluate_expressions():
    """Test evaluating various expressions."""
    context = SandboxContext()
    # Create executor with proper context
    executor = DanaExecutor(context)

    # Literal
    assert executor.execute(LiteralExpression(42), context) == 42

    # Binary expression
    expr = BinaryExpression(
        left=LiteralExpression(17),
        operator=BinaryOperator.ADD,
        right=LiteralExpression(25),
    )
    assert executor.execute(expr, context) == 42

    # Identifier
    context.set("answer", 42)
    assert executor.execute(Identifier("answer"), context) == 42


def test_fstring_evaluation():
    """Test evaluating f-strings."""
    context = SandboxContext()
    # Create executor with proper context
    executor = DanaExecutor(context)

    # F-string
    fstring = FStringExpression(parts=["foo", LiteralExpression(42)])
    assert executor.execute(fstring, context) == "foo42"

    # Context variables in f-strings
    context.set("x", 17)
    context.set("y", 25)
    fstring = FStringExpression(
        parts=[
            "The answer is: ",
            Identifier("x"),
            " + ",
            Identifier("y"),
            " = ",
            BinaryExpression(Identifier("x"), BinaryOperator.ADD, Identifier("y")),
        ]
    )
    assert executor.execute(fstring, context) == "The answer is: 17 + 25 = 42"

    # New-style f-string with template and expressions
    fstring2 = FStringExpression(parts=[])
    fstring2.template = "The answer is: {x} + {y} = {result}"
    fstring2.expressions = {
        "{x}": Identifier("x"),
        "{y}": Identifier("y"),
        "{result}": BinaryExpression(Identifier("x"), BinaryOperator.ADD, Identifier("y")),
    }
    assert executor.execute(fstring2, context) == "The answer is: 17 + 25 = 42"


def test_assignment_and_print(capsys):
    """Test assignment and print execution."""
    context = SandboxContext()
    executor = DanaExecutor(context)

    # Set up interpreter
    interpreter = DanaInterpreter(context)
    executor.interpreter = interpreter

    # Assignment
    stmt = Assignment(target=Identifier("private.x"), value=LiteralExpression(99))
    result = executor.execute(stmt, context)
    assert result == 99
    assert context.get("private.x") == 99

    # Print
    stmt = PrintStatement(message=LiteralExpression("hello"))
    executor.execute(stmt, context)
    out, _ = capsys.readouterr()
    assert "hello" in out

    # Error case: unsupported node
    class Dummy:
        pass

    with pytest.raises(Exception):
        executor.execute(Dummy(), context)


def test_unified_interpreter_execution():
    """Test that the interpreter correctly uses the DanaExecutor."""
    context = SandboxContext()
    interpreter = DanaInterpreter(context)

    # Create and execute a program
    program = Program([Assignment(target=Identifier("private.y"), value=LiteralExpression(123))])
    result = interpreter.execute_program(program)
    assert result == 123
    assert context.get("private.y") == 123

    # Test expression evaluation
    expr = BinaryExpression(
        left=LiteralExpression(17),
        operator=BinaryOperator.ADD,
        right=LiteralExpression(25),
    )
    result = interpreter.evaluate_expression(expr, context)
    assert result == 42

    # Test statement execution
    stmt = Assignment(target=Identifier("private.z"), value=LiteralExpression(456))
    result = interpreter.execute_statement(stmt, context)
    assert result == 456
    assert context.get("private.z") == 456


def test_print_function_with_fstrings():
    """Test the print function's handling of f-strings."""
    import sys
    from io import StringIO

    from opendxa.dana.sandbox.interpreter.functions.core.print_function import print_function

    # Create a context with variables
    context = SandboxContext()
    context.set("x", 42)
    context.set("y", "hello")

    # Create an executor and set it on the context
    executor = DanaExecutor(context)
    interpreter = DanaInterpreter(context)
    interpreter._executor = executor  # Set the executor on the interpreter
    context.interpreter = interpreter  # Set the interpreter on the context

    # Create a simple f-string
    fstring = FStringExpression(parts=["Value: ", Identifier("x")])

    # Redirect stdout to capture print output
    original_stdout = sys.stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        # Call print function with f-string
        print_function(fstring, context=context)

        # Get the captured output
        output = captured_output.getvalue().strip()

        # Verify the output contains the evaluated f-string
        assert output == "Value: 42"

        # Test with multiple arguments including f-strings
        captured_output.truncate(0)
        captured_output.seek(0)

        # Create a more complex f-string
        complex_fstring = FStringExpression(
            parts=["x + 10 = ", BinaryExpression(Identifier("x"), BinaryOperator.ADD, LiteralExpression(10))]
        )

        # Print with multiple arguments
        print_function("Result:", complex_fstring, context=context)

        # Verify combined output
        combined_output = captured_output.getvalue().strip()
        assert combined_output == "Result: x + 10 = 52"

    finally:
        # Restore stdout
        sys.stdout = original_stdout
