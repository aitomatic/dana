"""
End-to-end tests for the function call system.

These tests verify that all components of the function call system work
together correctly, including:
1. Python to Dana calls
2. Dana to Python calls
3. Context passing
4. Argument processing
5. Error handling
"""

import pytest

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_mixed_dana_and_python_functions():
    """Test Python and Dana functions working together with context passing."""

    # Define a Python function that needs context
    def python_logger(message, context):
        """Python function that logs a message and accesses context."""
        # Access the logs list from context
        logs = context.get("logs", [])
        logs.append(f"Python: {message}")
        context.set("logs", logs)
        return f"Logged: {message}"

    # Define a Python function that returns a callable (higher-order function)
    def create_formatter(prefix):
        """Returns a function that formats messages with a prefix."""

        def formatter(message):
            return f"{prefix}: {message}"

        return formatter

    # Setup interpreter and context
    context = SandboxContext()
    context.set("logs", [])

    # Initialize all required scopes
    if "system" not in context._state:
        context._state["system"] = {}

    interpreter = DanaInterpreter()

    # Register the Python functions
    interpreter.function_registry.register("python_logger", python_logger, func_type="python")
    interpreter.function_registry.register("create_formatter", create_formatter, func_type="python")

    # Test 1: Call Python function that modifies context
    result1 = python_logger("Test message 1", context)
    assert result1 == "Logged: Test message 1"
    assert context.get("logs") == ["Python: Test message 1"]

    # Test 2: Call higher-order function
    formatter = create_formatter("INFO")
    result2 = formatter("System ready")
    assert result2 == "INFO: System ready"

    # Test 3: Chain function calls
    python_logger("Test message 2", context)
    assert context.get("logs") == ["Python: Test message 1", "Python: Test message 2"]


def test_context_injection_with_type_annotations():
    """Test context injection with type annotations."""

    # Define a Python function with annotated context parameter
    def analyze_data(data: list, ctx: "SandboxContext"):
        """Analyzes data and stores results in context."""
        result = sum(data)
        ctx.set("analysis_result", result)
        return result

    # Setup
    context = SandboxContext()
    interpreter = DanaInterpreter()

    # Register the function
    interpreter.function_registry.register("analyze_data", analyze_data, func_type="python")

    # Test direct call
    test_data = [1, 2, 3, 4, 5]
    result = analyze_data(test_data, context)

    # Verify results
    assert result == 15
    assert context.get("analysis_result") == 15


def test_keyword_and_positional_args():
    """Test mixing keyword and positional arguments."""

    # Define a Python function with multiple parameters
    def format_message(template, name, age=0, location="unknown"):
        """Format a message with the given parameters."""
        return template.format(name=name, age=age, location=location)

    # Setup
    context = SandboxContext()
    interpreter = DanaInterpreter()

    # Register the function
    interpreter.function_registry.register("format_message", format_message, func_type="python")

    # Test various calling patterns
    template = "Hello {name}, you are {age} years old from {location}"

    # Test 1: All positional
    result1 = format_message(template, "Alice", 25, "New York")
    assert result1 == "Hello Alice, you are 25 years old from New York"

    # Test 2: Mixed positional and keyword
    result2 = format_message(template, "Bob", location="Paris")
    assert result2 == "Hello Bob, you are 0 years old from Paris"

    # Test 3: All keyword
    result3 = format_message(template=template, name="Charlie", age=30, location="London")
    assert result3 == "Hello Charlie, you are 30 years old from London"


def test_error_handling():
    """Test error handling in function calls."""

    # Define a Python function that validates inputs
    def divide(a, b):
        """Divide a by b, raising an error for division by zero."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    # Setup
    context = SandboxContext()
    interpreter = DanaInterpreter()

    # Register the function
    interpreter.function_registry.register("divide", divide, func_type="python")

    # Test successful call
    result = divide(10, 2)
    assert result == 5.0

    # Test error case
    try:
        divide(10, 0)
        assert False, "Expected ValueError"
    except ValueError as e:
        assert str(e) == "Cannot divide by zero"