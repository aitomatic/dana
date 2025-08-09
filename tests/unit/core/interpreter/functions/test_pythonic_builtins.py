"""
Tests for Pythonic built-in functions using central dispatch.

These tests verify that the PythonicFunctionFactory correctly creates
and registers built-in functions with proper type validation and execution.
"""

import pytest

from dana.common.exceptions import SandboxError
from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.interpreter.executor.function_resolver import FunctionType
from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry
from dana.core.lang.sandbox_context import SandboxContext

# Import the real PythonicFunctionFactory
from dana.libs.corelib.py_builtins.register_py_builtins import PythonicBuiltinsFactory as PythonicFunctionFactory


def test_pythonic_function_factory_basic():
    """Test basic functionality of the PythonicFunctionFactory."""
    # Test getting available functions
    available = PythonicFunctionFactory.get_available_functions()
    assert "len" in available
    assert "sum" in available
    assert "max" in available
    assert "min" in available

    # Test getting function info
    len_info = PythonicFunctionFactory.get_function_info("len")
    assert len_info["doc"] == "Return the length of an object"
    assert len_info["func"] == len


def test_create_len_function():
    """Test creating and using the len function."""
    len_func = PythonicFunctionFactory.create_function("len")

    context = SandboxContext()

    # Test with list
    result = len_func(context, [1, 2, 3, 4])
    assert result == 4

    # Test with string
    result = len_func(context, "hello")
    assert result == 5

    # Test with dict
    result = len_func(context, {"a": 1, "b": 2})
    assert result == 2


def test_create_sum_function():
    """Test creating and using the sum function."""
    sum_func = PythonicFunctionFactory.create_function("sum")

    context = SandboxContext()

    # Test with list
    result = sum_func(context, [1, 2, 3, 4])
    assert result == 10

    # Test with tuple
    result = sum_func(context, (5, 10, 15))
    assert result == 30


def test_create_max_min_functions():
    """Test creating and using max/min functions."""
    max_func = PythonicFunctionFactory.create_function("max")
    min_func = PythonicFunctionFactory.create_function("min")

    context = SandboxContext()

    # Test max
    result = max_func(context, [1, 5, 3, 9, 2])
    assert result == 9

    # Test min
    result = min_func(context, [1, 5, 3, 9, 2])
    assert result == 1


def test_type_conversion_functions():
    """Test type conversion functions."""
    int_func = PythonicFunctionFactory.create_function("int")
    float_func = PythonicFunctionFactory.create_function("float")
    bool_func = PythonicFunctionFactory.create_function("bool")

    context = SandboxContext()

    # Test int conversion
    assert int_func(context, "42") == 42
    assert int_func(context, 3.14) == 3
    assert int_func(context, True) == 1

    # Test float conversion
    assert float_func(context, "3.14") == 3.14
    assert float_func(context, 42) == 42.0
    assert float_func(context, False) == 0.0

    # Test bool conversion
    assert bool_func(context, "hello")
    assert not bool_func(context, "")
    assert not bool_func(context, 0)
    assert bool_func(context, 1)


def test_type_validation():
    """Test that type validation works correctly."""
    len_func = PythonicFunctionFactory.create_function("len")

    context = SandboxContext()

    # This should work
    result = len_func(context, [1, 2, 3])
    assert result == 3

    # This should fail with TypeError
    with pytest.raises(TypeError) as exc_info:
        len_func(context, 42)  # int is not a valid type for len

    assert "Invalid arguments for 'len'" in str(exc_info.value)


def test_register_pythonic_builtins():
    """Test registering Pythonic built-ins in a function registry."""
    registry = FunctionRegistry()

    # Register the built-ins
    from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins

    do_register_py_builtins(registry)

    # Test that functions are registered
    assert registry.has("len")
    assert registry.has("sum")
    assert registry.has("max")
    assert registry.has("min")
    assert registry.has("int")
    assert registry.has("float")
    assert registry.has("bool")

    # Test calling through registry
    context = SandboxContext()
    result = registry.call("len", context, args=[[1, 2, 3, 4, 5]])
    assert result == 5


def test_function_lookup_order():
    """Test that built-in functions take precedence over custom functions."""
    registry = FunctionRegistry()

    # Register a custom function first
    def custom_len(context, obj):
        return 999  # Custom implementation

    from dana.core.lang.interpreter.functions.python_function import PythonFunction

    registry.register("len", PythonFunction(custom_len, trusted_for_context=True), func_type=FunctionType.PYTHON, overwrite=True)

    # Now register built-ins (should overwrite custom function for safety)
    from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins

    do_register_py_builtins(registry)

    # The built-in function should now take precedence
    context = SandboxContext()
    result = registry.call("len", context, args=[[1, 2, 3]])
    assert result == 3  # Built-in function, not custom


def test_integration_with_interpreter():
    """Test that built-ins work with the Dana interpreter."""
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # The interpreter should have built-ins registered
    assert interpreter.function_registry.has("len")
    assert interpreter.function_registry.has("sum")

    # Test calling through the interpreter
    result = interpreter.function_registry.call("len", context, args=["hello"])
    assert result == 5


def test_error_handling():
    """Test error handling in built-in functions."""
    sum_func = PythonicFunctionFactory.create_function("sum")

    context = SandboxContext()

    # Test with invalid argument type (caught by type validation)
    with pytest.raises(TypeError) as exc_info:
        sum_func(context, "not a list")  # sum() expects list or tuple

    assert "Invalid arguments for 'sum'" in str(exc_info.value)

    # Test with valid type but invalid content (caught by Python function)
    with pytest.raises(SandboxError) as exc_info:
        sum_func(context, ["not", "numbers"])  # sum() expects numbers

    assert "Built-in function 'sum' failed" in str(exc_info.value)


def test_unknown_function():
    """Test handling of unknown function names."""

    with pytest.raises(SandboxError) as exc_info:
        PythonicFunctionFactory.create_function("unknown_function")

    assert "not a recognized built-in function" in str(exc_info.value)


def test_type_function():
    """Test the supported type() function."""
    type_func = PythonicFunctionFactory.create_function("type")
    context = SandboxContext()
    assert type_func(context, 42) == "int"
    assert type_func(context, "hello") == "str"
    assert type_func(context, [1, 2, 3]) == "list"
    assert type_func(context, {"a": 1}) == "dict"
    assert type_func(context, 3.14) == "float"
    assert type_func(context, True) == "bool"
