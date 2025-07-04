"""
Tests for the function context handling methods.

These tests verify the functionality of the context preparation, restoration,
and injection methods in the function classes.
"""

from dana.core.lang.interpreter.functions.dana_function import DanaFunction
from dana.core.lang.interpreter.functions.python_function import PythonFunction
from dana.core.lang.sandbox_context import SandboxContext


def test_dana_function_context_methods():
    """Test the context handling methods in DanaFunction."""
    # Create test data
    context = SandboxContext()
    context.set("existing_var", "original_value")

    args = ["arg_value"]
    kwargs = {"kwarg_name": "kwarg_value"}

    # Create a DanaFunction with mock body
    function = DanaFunction([], ["param1", "kwarg_name"], context)

    # Test prepare_context
    prepared_context = function.prepare_context(context, args, kwargs)

    # Check that original variables are preserved
    assert prepared_context.get("existing_var") == "original_value"

    # Check that args and kwargs are mapped to parameters
    assert prepared_context.get("param1") == "arg_value"
    assert prepared_context.get("kwarg_name") == "kwarg_value"

    # Test restore_context
    function.restore_context(prepared_context, context)

    # Verify that the context is restored
    assert not hasattr(prepared_context, "_original_locals")


def test_python_function_context_methods():
    """Test the context handling methods in PythonFunction."""
    # Create test data
    context = SandboxContext()
    context.set("test_var", "test_value")

    # Create a test function
    def test_func(ctx, x, y):
        return x + y

    # Create a PythonFunction
    function = PythonFunction(test_func, context)

    # Test prepare_context
    prepared_context = function.prepare_context(context, [], {})

    # Check that the context is a copy
    assert prepared_context is not context
    assert prepared_context.get("test_var") == "test_value"

    # Test restore_context
    function.restore_context(prepared_context, context)

    # Test context injection
    kwargs = {"existing_arg": "value"}
    result = function.inject_context(context, kwargs)

    # Check that context is injected
    assert "ctx" in result
    assert result["ctx"] is context
    assert result["existing_arg"] == "value"

    # Test that existing values aren't overwritten
    kwargs = {"ctx": "existing_value"}
    result = function.inject_context(context, kwargs)

    # Context should not overwrite existing kwargs
    assert result["ctx"] == "existing_value"


def test_python_function_no_context_injection():
    """Test that PythonFunction doesn't inject context when not wanted."""
    context = SandboxContext()

    # Define a function that doesn't want context
    def test_func(x, y):
        return x + y

    # Create a PythonFunction
    function = PythonFunction(test_func, context)

    kwargs = {"arg": "value"}
    result = function.inject_context(context, kwargs)

    # Check that context is not injected
    assert "ctx" not in result
    assert result == {"arg": "value"}
