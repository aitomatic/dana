"""
Integration tests for built-in functions with Dana interpreter.

These tests verify that built-in functions work correctly when called
through the Dana interpreter with actual Dana code execution.
"""

import pytest

from dana.common.exceptions import SandboxError
from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext


@pytest.mark.deep
class TestBuiltinIntegrationBasic:
    """Basic integration tests for built-in functions."""

    def test_len_function_integration(self):
        """Test len() function through Dana interpreter."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test with list
        result = interpreter._eval("len([1, 2, 3, 4, 5])", context=context)
        assert result == 5

        # Test with string
        result = interpreter._eval('len("hello")', context=context)
        assert result == 5

        # Test with empty list
        result = interpreter._eval("len([])", context=context)
        assert result == 0

        # Test with dictionary
        result = interpreter._eval('len({"a": 1, "b": 2})', context=context)
        assert result == 2

    def test_sum_function_integration(self):
        """Test sum() function through Dana interpreter."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test with list of integers
        result = interpreter._eval("sum([1, 2, 3, 4, 5])", context=context)
        assert result == 15

        # Test with empty list
        result = interpreter._eval("sum([])", context=context)
        assert result == 0

        # Test with tuple
        result = interpreter._eval("sum((10, 20, 30))", context=context)
        assert result == 60

    def test_max_min_functions_integration(self):
        """Test max() and min() functions through Dana interpreter."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test max
        result = interpreter._eval("max([1, 5, 3, 9, 2])", context=context)
        assert result == 9

        # Test min
        result = interpreter._eval("min([1, 5, 3, 9, 2])", context=context)
        assert result == 1

        # Test with negative numbers
        result = interpreter._eval("max([-5, -2, -8, -1])", context=context)
        assert result == -1

        result = interpreter._eval("min([-5, -2, -8, -1])", context=context)
        assert result == -8

    def test_type_conversion_integration(self):
        """Test type conversion functions through Dana interpreter."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test int conversion
        result = interpreter._eval('int("42")', context=context)
        assert result == 42

        result = interpreter._eval("int(3.14)", context=context)
        assert result == 3

        # Test float conversion
        result = interpreter._eval('float("3.14")', context=context)
        assert result == 3.14

        result = interpreter._eval("float(42)", context=context)
        assert result == 42.0

        # Test bool conversion
        result = interpreter._eval('bool("hello")', context=context)
        assert result

        result = interpreter._eval('bool("")', context=context)
        assert not result

        result = interpreter._eval("bool(0)", context=context)
        assert not result

        result = interpreter._eval("bool(1)", context=context)
        assert result

    def test_abs_round_integration(self):
        """Test abs() and round() functions through Dana interpreter."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test abs
        result = interpreter._eval("abs(-5)", context=context)
        assert result == 5

        result = interpreter._eval("abs(3.14)", context=context)
        assert result == 3.14

        result = interpreter._eval("abs(-3.14)", context=context)
        assert result == 3.14

        # Test round
        result = interpreter._eval("round(3.14)", context=context)
        assert result == 3

        result = interpreter._eval("round(3.64)", context=context)
        assert result == 4

        result = interpreter._eval("round(3.14159, 2)", context=context)
        assert result == 3.14


@pytest.mark.deep
class TestBuiltinIntegrationAdvanced:
    """Advanced integration tests with complex expressions."""

    def test_nested_function_calls(self):
        """Test nested built-in function calls."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Nested len and sum
        result = interpreter._eval("len([sum([1, 2]), sum([3, 4]), sum([5, 6])])", context=context)
        assert result == 3

        # Nested max and abs
        result = interpreter._eval("max([abs(-5), abs(-2), abs(-8)])", context=context)
        assert result == 8

        # Complex nesting
        result = interpreter._eval("sum([len([1, 2, 3]), len([4, 5]), len([6])])", context=context)
        assert result == 6  # 3 + 2 + 1

    def test_function_calls_with_variables(self):
        """Test built-in functions with variables."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Set up variables and use them with built-ins
        code = """numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
count = len(numbers)
average = total / count"""
        interpreter._eval(code, context=context)

        # Check the results
        assert context.get("total") == 15
        assert context.get("count") == 5
        assert context.get("average") == 3.0

    def test_collection_functions_integration(self):
        """Test collection manipulation functions."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test sorted
        result = interpreter._eval("sorted([3, 1, 4, 1, 5])", context=context)
        assert result == [1, 1, 3, 4, 5]

        # Test reversed (convert to list for comparison)
        result = list(interpreter._eval("reversed([1, 2, 3, 4, 5])", context=context))
        assert result == [5, 4, 3, 2, 1]

        # Test enumerate (convert to list for comparison)
        result = list(interpreter._eval('enumerate(["a", "b", "c"])', context=context))
        assert result == [(0, "a"), (1, "b"), (2, "c")]

    def test_logic_functions_integration(self):
        """Test logic functions through interpreter."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test all
        result = interpreter._eval("all([True, True, True])", context=context)
        assert result

        result = interpreter._eval("all([True, False, True])", context=context)
        assert not result

        result = interpreter._eval("all([1, 2, 3])", context=context)
        assert result

        result = interpreter._eval("all([1, 0, 3])", context=context)
        assert not result

        # Test any
        result = interpreter._eval("any([False, True, False])", context=context)
        assert result

        result = interpreter._eval("any([False, False, False])", context=context)
        assert not result

        result = interpreter._eval("any([0, 1, 0])", context=context)
        assert result

    def test_range_function_integration(self):
        """Test range() function through interpreter."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test single argument range
        result = list(interpreter._eval("range(5)", context=context))
        assert result == [0, 1, 2, 3, 4]

        # Test two argument range
        result = list(interpreter._eval("range(2, 7)", context=context))
        assert result == [2, 3, 4, 5, 6]

        # Test three argument range
        result = list(interpreter._eval("range(0, 10, 2)", context=context))
        assert result == [0, 2, 4, 6, 8]


class TestBuiltinErrorHandling:
    """Test error handling for built-in functions through interpreter."""

    def test_type_validation_errors(self):
        """Test that type validation errors are properly handled."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test len with invalid type
        with pytest.raises((TypeError, SandboxError)):
            interpreter._eval("len(42)", context=context)

        # Test sum with invalid type
        with pytest.raises((TypeError, SandboxError)):
            interpreter._eval('sum("hello")', context=context)

        # Test max with invalid content
        with pytest.raises(SandboxError):
            interpreter._eval("max([])", context=context)

    def test_unsupported_function_errors(self):
        """Test that unsupported functions raise appropriate errors."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test eval is blocked
        with pytest.raises(SandboxError) as exc_info:
            interpreter._eval('eval("1 + 1")', context=context)
        assert "eval" in str(exc_info.value)
        assert "not found" in str(exc_info.value) or "not supported" in str(exc_info.value)

        # Test open is blocked
        with pytest.raises(SandboxError) as exc_info:
            interpreter._eval('open("test.txt")', context=context)
        assert "open" in str(exc_info.value)
        assert "not found" in str(exc_info.value) or "not supported" in str(exc_info.value)

        # Test exec is blocked
        with pytest.raises(SandboxError) as exc_info:
            interpreter._eval('exec("x = 1")', context=context)
        assert "exec" in str(exc_info.value)
        assert "not found" in str(exc_info.value) or "not supported" in str(exc_info.value)

    def test_runtime_errors(self):
        """Test runtime errors in built-in functions."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Test sum with non-numeric content
        with pytest.raises(SandboxError) as exc_info:
            interpreter._eval('sum(["hello", "world"])', context=context)
        assert "sum" in str(exc_info.value)
        assert "failed" in str(exc_info.value) or "not found" in str(exc_info.value)

        # Test int conversion with invalid string
        with pytest.raises(SandboxError) as exc_info:
            interpreter._eval('int("hello")', context=context)
        assert "int" in str(exc_info.value)
        assert "failed" in str(exc_info.value) or "not found" in str(exc_info.value)


class TestBuiltinFunctionPrecedence:
    """Test the precedence of built-in functions vs user-defined functions."""

    def test_core_function_precedence(self):
        """Test that core functions are available and can be called."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Core functions should be available
        result = interpreter._eval("len([1, 2, 3])", context=context)
        assert result == 3

    def test_user_function_precedence(self):
        """Test that built-in functions take precedence over user-defined functions."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Define a custom len function
        code = """def len(obj):
    return 999"""
        interpreter._eval(code, context=context)

        # According to Dana language design, registry functions (built-ins) have precedence
        # over user-defined functions, so the built-in len() should still be called
        result = interpreter._eval("len([1, 2, 3])", context=context)
        assert result == 3  # Built-in len() returns actual length, not user-defined 999

    def test_function_lookup_order(self):
        """Test the complete function lookup order."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Initially, built-in len should work
        result = interpreter._eval("len([1, 2, 3, 4])", context=context)
        assert result == 4

        # Define a user function with the same name
        code = """def len(obj):
    return 888"""
        interpreter._eval(code, context=context)

        # Registry functions have precedence over user-defined functions in Dana
        # This is the correct behavior according to the function resolution order:
        # 1. Function registry first (system functions)
        # 2. Context scope hierarchy (user functions)
        result = interpreter._eval("len([1, 2, 3, 4])", context=context)
        assert result == 4  # Built-in len() still returns actual length

        # However, the user-defined function should be accessible via explicit scoping
        user_len_result = interpreter._eval("local:len([1, 2, 3, 4])", context=context)
        assert user_len_result == 888  # User-defined function returns custom value


@pytest.mark.deep
class TestBuiltinRealWorldScenarios:
    """Test built-in functions in realistic scenarios."""

    def test_data_processing_scenario(self):
        """Test built-ins in a data processing scenario."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        code = """# Sample data processing
data = [10, 25, 30, 15, 40, 35, 20]

# Basic statistics
total = sum(data)
count = len(data)
average = total / count
maximum = max(data)
minimum = min(data)

# Data transformation
sorted_data = sorted(data)

# Simple boolean checks
all_positive = all([True, True, True])
any_large = any([True, False, True])"""

        interpreter._eval(code, context=context)

        # Verify results
        assert context.get("total") == 175
        assert context.get("count") == 7
        assert context.get("average") == 25.0
        assert context.get("maximum") == 40
        assert context.get("minimum") == 10
        assert context.get("sorted_data") == [10, 15, 20, 25, 30, 35, 40]
        assert context.get("all_positive")
        assert context.get("any_large")

    def test_mathematical_operations_scenario(self):
        """Test built-ins in mathematical operations."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        code = """# Mathematical operations using built-ins
val1 = abs(-3.7)
val2 = round(2.1)
val3 = round(-1.8, 1)

# Simple list operations
numbers = [1, 2, 3, 4, 5]
total_vals = sum(numbers)
max_val = max(numbers)
min_val = min(numbers)

# Range operations
indices = list(range(5))"""

        interpreter._eval(code, context=context)

        # Verify results
        assert context.get("val1") == 3.7
        assert context.get("val2") == 2
        assert context.get("val3") == -1.8
        assert context.get("total_vals") == 15
        assert context.get("max_val") == 5
        assert context.get("min_val") == 1
        assert context.get("indices") == [0, 1, 2, 3, 4]

    def test_string_processing_scenario(self):
        """Test built-ins in string processing."""
        interpreter = DanaInterpreter()
        context = SandboxContext()

        code = """# String processing
words = ["hello", "world", "python", "dana", "test"]

# Individual length checks
len1 = len("hello")
len2 = len("world")
len3 = len("python")

# Sorting
sorted_words = sorted(words)

# Boolean operations
all_non_empty = all([True, True, True])
any_long_words = any([False, True, False])"""

        interpreter._eval(code, context=context)

        # Verify results
        assert context.get("len1") == 5  # "hello"
        assert context.get("len2") == 5  # "world"
        assert context.get("len3") == 6  # "python"
        assert context.get("sorted_words") == ["dana", "hello", "python", "test", "world"]
        assert context.get("all_non_empty")
        assert context.get("any_long_words")


@pytest.mark.deep
class TestFStringFunctionArguments:
    """Test f-string evaluation in function arguments.

    Migrated from tests/dana/functions/test_fstring_function_args.py
    These tests ensure f-strings are properly evaluated before being passed to functions.
    """

    def test_fstring_evaluation_in_print(self, capsys):
        """Test that f-strings are properly evaluated when passed to print()."""
        # Create a context and set a variable
        context = SandboxContext()
        context.set("local:message", "Hello world")

        # Create an interpreter
        interpreter = DanaInterpreter()

        # Execute print with f-string
        interpreter._eval('print(f"{local:message}")', context=context)

        # Get and check output
        captured = capsys.readouterr()
        assert "Hello world" in captured.out

    def test_fstring_evaluation_in_reason(self):
        """Test that f-strings are properly evaluated when passed to reason()."""
        # Create a context and set a variable
        context = SandboxContext()
        context.set("local:query", "What is the capital of France?")

        # Create an interpreter
        interpreter = DanaInterpreter()

        # Use the real reason function with built-in mocking (use_mock=True)
        # We'll set an environment variable to force mocking
        import os

        original_mock_env = os.environ.get("DANA_MOCK_LLM")
        os.environ["DANA_MOCK_LLM"] = "true"

        try:
            # Execute reason with f-string - this should work without any patching
            result = interpreter._eval('reason(f"{local:query}")', context=context)

            # The key test: if f-string evaluation works, the function should execute successfully
            # If f-strings weren't evaluated, we'd get an error about FStringExpression not being a string
            assert result is not None, "Function should return a result"

            # The result could be a string or dict depending on the mock implementation
            # What matters is that it executed successfully, proving f-string was evaluated
            assert isinstance(result, str | dict), f"Result should be a string or dict, got {type(result)}"

        finally:
            # Restore original environment
            if original_mock_env is None:
                os.environ.pop("DANA_MOCK_LLM", None)
            else:
                os.environ["DANA_MOCK_LLM"] = original_mock_env

    def test_consistency_between_print_and_reason(self, capsys):
        """Test that print() and reason() behave consistently with f-string arguments."""
        # Create a context and set a variable
        context = SandboxContext()
        context.set("local:value", 42)

        # Create an interpreter
        interpreter = DanaInterpreter()

        # Use environment variable to enable mocking for reason function
        import os

        original_mock_env = os.environ.get("DANA_MOCK_LLM")
        os.environ["DANA_MOCK_LLM"] = "true"

        try:
            # Execute both functions with the same f-string
            interpreter._eval('print(f"The answer is {local:value}")', context=context)
            reason_result = interpreter._eval('reason(f"The answer is {local:value}")', context=context)

            # Get print output
            captured = capsys.readouterr()
            print_output = captured.out.strip()

            # Both functions should handle f-strings consistently
            # Print should output the evaluated string
            assert "The answer is 42" in print_output

            # Reason should execute successfully (proving f-string was evaluated)
            assert reason_result is not None, "Reason should return a result"
            assert isinstance(reason_result, str | dict), "Reason should return a string or dict result"

            # The key test: both functions should work with the same f-string syntax
            # If f-string evaluation is inconsistent, one would fail

        finally:
            # Restore original environment
            if original_mock_env is None:
                os.environ.pop("DANA_MOCK_LLM", None)
            else:
                os.environ["DANA_MOCK_LLM"] = original_mock_env

    def test_fstring_with_builtin_functions(self):
        """Test f-strings work correctly with built-in functions."""
        context = SandboxContext()
        context.set("local:numbers", [1, 2, 3, 4, 5])

        interpreter = DanaInterpreter()

        # Test f-string with len function
        result = interpreter._eval('f"Length: {len(local:numbers)}"', context=context)
        assert result == "Length: 5"

        # Test f-string with sum function
        result = interpreter._eval('f"Sum: {sum(local:numbers)}"', context=context)
        assert result == "Sum: 15"

        # Test f-string with max function
        result = interpreter._eval('f"Max: {max(local:numbers)}"', context=context)
        assert result == "Max: 5"

    def test_nested_fstring_function_calls(self):
        """Test nested f-strings with function calls."""
        context = SandboxContext()
        context.set("local:data", [10, 20, 30])

        interpreter = DanaInterpreter()

        # Test nested function calls in f-string
        result = interpreter._eval(
            'f"Stats: len={len(local:data)}, sum={sum(local:data)}, avg={sum(local:data)/len(local:data)}"', context=context
        )
        assert result == "Stats: len=3, sum=60, avg=20.0"
