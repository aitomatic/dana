"""
Comprehensive tests for all supported Pythonic built-in functions.

These tests verify that all supported built-in functions work correctly
with various input types, edge cases, and error conditions.
"""

import pytest

from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.interpreter.functions.pythonic.function_factory import PythonicFunctionFactory
from opendxa.dana.sandbox.sandbox_context import SandboxContext


@pytest.mark.deep
class TestLenFunction:
    """Comprehensive tests for the len() function."""

    def test_len_with_lists(self):
        """Test len() with various list inputs."""
        factory = PythonicFunctionFactory()
        len_func = factory.create_function("len")
        context = SandboxContext()

        # Empty list
        assert len_func(context, []) == 0

        # Single element
        assert len_func(context, [1]) == 1

        # Multiple elements
        assert len_func(context, [1, 2, 3, 4, 5]) == 5

        # Mixed types
        assert len_func(context, [1, "hello", [1, 2], {"a": 1}]) == 4

    def test_len_with_strings(self):
        """Test len() with various string inputs."""
        factory = PythonicFunctionFactory()
        len_func = factory.create_function("len")
        context = SandboxContext()

        # Empty string
        assert len_func(context, "") == 0

        # Single character
        assert len_func(context, "a") == 1

        # Multiple characters
        assert len_func(context, "hello") == 5

        # Unicode characters
        assert len_func(context, "héllo") == 5

        # Whitespace
        assert len_func(context, "   ") == 3

    def test_len_with_dicts(self):
        """Test len() with various dictionary inputs."""
        factory = PythonicFunctionFactory()
        len_func = factory.create_function("len")
        context = SandboxContext()

        # Empty dict
        assert len_func(context, {}) == 0

        # Single key
        assert len_func(context, {"a": 1}) == 1

        # Multiple keys
        assert len_func(context, {"a": 1, "b": 2, "c": 3}) == 3

    def test_len_with_tuples(self):
        """Test len() with various tuple inputs."""
        factory = PythonicFunctionFactory()
        len_func = factory.create_function("len")
        context = SandboxContext()

        # Empty tuple
        assert len_func(context, ()) == 0

        # Single element
        assert len_func(context, (1,)) == 1

        # Multiple elements
        assert len_func(context, (1, 2, 3)) == 3

    def test_len_invalid_types(self):
        """Test len() with invalid input types."""
        factory = PythonicFunctionFactory()
        len_func = factory.create_function("len")
        context = SandboxContext()

        # Test with invalid types
        invalid_inputs = [42, 3.14, True, None]

        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError) as exc_info:
                len_func(context, invalid_input)
            assert "Invalid arguments for 'len'" in str(exc_info.value)


@pytest.mark.deep
class TestSumFunction:
    """Comprehensive tests for the sum() function."""

    def test_sum_with_lists(self):
        """Test sum() with various list inputs."""
        factory = PythonicFunctionFactory()
        sum_func = factory.create_function("sum")
        context = SandboxContext()

        # Empty list
        assert sum_func(context, []) == 0

        # Single element
        assert sum_func(context, [5]) == 5

        # Multiple integers
        assert sum_func(context, [1, 2, 3, 4, 5]) == 15

        # Multiple floats
        assert sum_func(context, [1.5, 2.5, 3.0]) == 7.0

        # Mixed numbers
        assert sum_func(context, [1, 2.5, 3]) == 6.5

        # Negative numbers
        assert sum_func(context, [-1, -2, -3]) == -6

        # Mix of positive and negative
        assert sum_func(context, [10, -5, 3, -2]) == 6

    def test_sum_with_tuples(self):
        """Test sum() with various tuple inputs."""
        factory = PythonicFunctionFactory()
        sum_func = factory.create_function("sum")
        context = SandboxContext()

        # Empty tuple
        assert sum_func(context, ()) == 0

        # Single element
        assert sum_func(context, (7,)) == 7

        # Multiple elements
        assert sum_func(context, (1, 2, 3, 4)) == 10

    def test_sum_invalid_types(self):
        """Test sum() with invalid input types."""
        factory = PythonicFunctionFactory()
        sum_func = factory.create_function("sum")
        context = SandboxContext()

        # Test with invalid container types
        invalid_containers = ["hello", {"a": 1}, 42]

        for invalid_input in invalid_containers:
            with pytest.raises(TypeError) as exc_info:
                sum_func(context, invalid_input)
            assert "Invalid arguments for 'sum'" in str(exc_info.value)

    def test_sum_invalid_content(self):
        """Test sum() with invalid content in valid containers."""
        factory = PythonicFunctionFactory()
        sum_func = factory.create_function("sum")
        context = SandboxContext()

        # Test with non-numeric content
        with pytest.raises(SandboxError) as exc_info:
            sum_func(context, ["hello", "world"])
        assert "Built-in function 'sum' failed" in str(exc_info.value)

        # Test with mixed valid and invalid content
        with pytest.raises(SandboxError) as exc_info:
            sum_func(context, [1, 2, "hello"])
        assert "Built-in function 'sum' failed" in str(exc_info.value)


@pytest.mark.deep
class TestMaxMinFunctions:
    """Comprehensive tests for max() and min() functions."""

    def test_max_with_lists(self):
        """Test max() with various list inputs."""
        factory = PythonicFunctionFactory()
        max_func = factory.create_function("max")
        context = SandboxContext()

        # Single element
        assert max_func(context, [5]) == 5

        # Multiple integers
        assert max_func(context, [1, 5, 3, 9, 2]) == 9

        # Multiple floats
        assert max_func(context, [1.5, 2.7, 1.2, 3.8]) == 3.8

        # Mixed numbers
        assert max_func(context, [1, 2.5, 3]) == 3

        # Negative numbers
        assert max_func(context, [-5, -2, -8, -1]) == -1

    def test_min_with_lists(self):
        """Test min() with various list inputs."""
        factory = PythonicFunctionFactory()
        min_func = factory.create_function("min")
        context = SandboxContext()

        # Single element
        assert min_func(context, [5]) == 5

        # Multiple integers
        assert min_func(context, [1, 5, 3, 9, 2]) == 1

        # Multiple floats
        assert min_func(context, [1.5, 2.7, 1.2, 3.8]) == 1.2

        # Mixed numbers
        assert min_func(context, [1, 2.5, 3]) == 1

        # Negative numbers
        assert min_func(context, [-5, -2, -8, -1]) == -8

    def test_max_min_with_tuples(self):
        """Test max() and min() with tuples."""
        factory = PythonicFunctionFactory()
        max_func = factory.create_function("max")
        min_func = factory.create_function("min")
        context = SandboxContext()

        # Test with tuples
        assert max_func(context, (1, 5, 3, 2)) == 5
        assert min_func(context, (1, 5, 3, 2)) == 1

    def test_max_min_empty_containers(self):
        """Test max() and min() with empty containers."""
        factory = PythonicFunctionFactory()
        max_func = factory.create_function("max")
        min_func = factory.create_function("min")
        context = SandboxContext()

        # Empty containers should raise errors
        with pytest.raises(SandboxError):
            max_func(context, [])

        with pytest.raises(SandboxError):
            min_func(context, ())

    def test_max_min_invalid_content(self):
        """Test max() and min() with invalid content."""
        factory = PythonicFunctionFactory()
        max_func = factory.create_function("max")
        min_func = factory.create_function("min")
        context = SandboxContext()

        # Non-comparable content
        with pytest.raises(SandboxError):
            max_func(context, ["hello", 42])

        with pytest.raises(SandboxError):
            min_func(context, [1, {"a": 1}])


class TestAbsRoundFunctions:
    """Comprehensive tests for abs() and round() functions."""

    def test_abs_with_integers(self):
        """Test abs() with integer inputs."""
        factory = PythonicFunctionFactory()
        abs_func = factory.create_function("abs")
        context = SandboxContext()

        # Positive integer
        assert abs_func(context, 5) == 5

        # Negative integer
        assert abs_func(context, -5) == 5

        # Zero
        assert abs_func(context, 0) == 0

    def test_abs_with_floats(self):
        """Test abs() with float inputs."""
        factory = PythonicFunctionFactory()
        abs_func = factory.create_function("abs")
        context = SandboxContext()

        # Positive float
        assert abs_func(context, 3.14) == 3.14

        # Negative float
        assert abs_func(context, -3.14) == 3.14

        # Zero float
        assert abs_func(context, 0.0) == 0.0

    def test_round_with_floats(self):
        """Test round() with float inputs."""
        factory = PythonicFunctionFactory()
        round_func = factory.create_function("round")
        context = SandboxContext()

        # Basic rounding
        assert round_func(context, 3.14) == 3
        assert round_func(context, 3.64) == 4
        assert round_func(context, 3.5) == 4  # Python's banker's rounding

        # Negative numbers
        assert round_func(context, -3.14) == -3
        assert round_func(context, -3.64) == -4

    def test_round_with_precision(self):
        """Test round() with precision parameter."""
        factory = PythonicFunctionFactory()
        round_func = factory.create_function("round")
        context = SandboxContext()

        # Round to specific decimal places
        assert round_func(context, 3.14159, 2) == 3.14
        assert round_func(context, 3.14159, 3) == 3.142

        # Round to negative precision (tens, hundreds, etc.)
        assert round_func(context, 1234.5, -1) == 1230.0
        assert round_func(context, 1234.5, -2) == 1200.0

    def test_round_with_integers(self):
        """Test round() with integer inputs."""
        factory = PythonicFunctionFactory()
        round_func = factory.create_function("round")
        context = SandboxContext()

        # Integers should return as-is
        assert round_func(context, 5) == 5
        assert round_func(context, -10) == -10


class TestTypeConversionFunctions:
    """Comprehensive tests for type conversion functions."""

    def test_int_conversion(self):
        """Test int() conversion function."""
        factory = PythonicFunctionFactory()
        int_func = factory.create_function("int")
        context = SandboxContext()

        # String to int
        assert int_func(context, "42") == 42
        assert int_func(context, "-17") == -17
        assert int_func(context, "0") == 0

        # Float to int (truncation)
        assert int_func(context, 3.14) == 3
        assert int_func(context, -3.99) == -3
        assert int_func(context, 0.0) == 0

        # Bool to int
        assert int_func(context, True) == 1
        assert int_func(context, False) == 0

    def test_int_conversion_errors(self):
        """Test int() conversion error cases."""
        factory = PythonicFunctionFactory()
        int_func = factory.create_function("int")
        context = SandboxContext()

        # Invalid string formats
        with pytest.raises(SandboxError):
            int_func(context, "hello")

        with pytest.raises(SandboxError):
            int_func(context, "3.14")  # Float string not allowed

        with pytest.raises(SandboxError):
            int_func(context, "")

    def test_float_conversion(self):
        """Test float() conversion function."""
        factory = PythonicFunctionFactory()
        float_func = factory.create_function("float")
        context = SandboxContext()

        # String to float
        assert float_func(context, "3.14") == 3.14
        assert float_func(context, "-2.5") == -2.5
        assert float_func(context, "0") == 0.0
        assert float_func(context, "42") == 42.0

        # Int to float
        assert float_func(context, 42) == 42.0
        assert float_func(context, -17) == -17.0
        assert float_func(context, 0) == 0.0

        # Bool to float
        assert float_func(context, True) == 1.0
        assert float_func(context, False) == 0.0

    def test_float_conversion_errors(self):
        """Test float() conversion error cases."""
        factory = PythonicFunctionFactory()
        float_func = factory.create_function("float")
        context = SandboxContext()

        # Invalid string formats
        with pytest.raises(SandboxError):
            float_func(context, "hello")

        with pytest.raises(SandboxError):
            float_func(context, "")

    def test_bool_conversion(self):
        """Test bool() conversion function."""
        factory = PythonicFunctionFactory()
        bool_func = factory.create_function("bool")
        context = SandboxContext()

        # String to bool
        assert bool_func(context, "hello") == True
        assert bool_func(context, "false") == True  # Non-empty string is True
        assert bool_func(context, "") == False

        # Int to bool
        assert bool_func(context, 1) == True
        assert bool_func(context, 42) == True
        assert bool_func(context, -1) == True
        assert bool_func(context, 0) == False

        # Float to bool
        assert bool_func(context, 3.14) == True
        assert bool_func(context, -2.5) == True
        assert bool_func(context, 0.0) == False

        # List to bool
        assert bool_func(context, [1, 2, 3]) == True
        assert bool_func(context, []) == False

        # Dict to bool
        assert bool_func(context, {"a": 1}) == True
        assert bool_func(context, {}) == False


class TestCollectionFunctions:
    """Comprehensive tests for collection manipulation functions."""

    def test_sorted_function(self):
        """Test sorted() function."""
        factory = PythonicFunctionFactory()
        sorted_func = factory.create_function("sorted")
        context = SandboxContext()

        # Sort list of integers
        result = sorted_func(context, [3, 1, 4, 1, 5, 9, 2, 6])
        assert result == [1, 1, 2, 3, 4, 5, 6, 9]

        # Sort list of floats
        result = sorted_func(context, [3.14, 1.41, 2.71])
        assert result == [1.41, 2.71, 3.14]

        # Sort list of strings
        result = sorted_func(context, ["banana", "apple", "cherry"])
        assert result == ["apple", "banana", "cherry"]

        # Sort tuple
        result = sorted_func(context, (3, 1, 4, 1, 5))
        assert result == [1, 1, 3, 4, 5]

        # Empty list
        result = sorted_func(context, [])
        assert result == []

    def test_reversed_function(self):
        """Test reversed() function."""
        factory = PythonicFunctionFactory()
        reversed_func = factory.create_function("reversed")
        context = SandboxContext()

        # Reverse list
        result = list(reversed_func(context, [1, 2, 3, 4, 5]))
        assert result == [5, 4, 3, 2, 1]

        # Reverse tuple
        result = list(reversed_func(context, (1, 2, 3)))
        assert result == [3, 2, 1]

        # Reverse string
        result = list(reversed_func(context, "hello"))
        assert result == ["o", "l", "l", "e", "h"]

        # Empty list
        result = list(reversed_func(context, []))
        assert result == []

    def test_enumerate_function(self):
        """Test enumerate() function."""
        factory = PythonicFunctionFactory()
        enumerate_func = factory.create_function("enumerate")
        context = SandboxContext()

        # Enumerate list
        result = list(enumerate_func(context, ["a", "b", "c"]))
        assert result == [(0, "a"), (1, "b"), (2, "c")]

        # Enumerate tuple
        result = list(enumerate_func(context, (10, 20, 30)))
        assert result == [(0, 10), (1, 20), (2, 30)]

        # Enumerate string
        result = list(enumerate_func(context, "hi"))
        assert result == [(0, "h"), (1, "i")]

        # Empty list
        result = list(enumerate_func(context, []))
        assert result == []


class TestLogicFunctions:
    """Comprehensive tests for logic functions."""

    def test_all_function(self):
        """Test all() function."""
        factory = PythonicFunctionFactory()
        all_func = factory.create_function("all")
        context = SandboxContext()

        # All True values
        assert all_func(context, [True, True, True]) == True
        assert all_func(context, [1, 2, 3]) == True
        assert all_func(context, ["a", "b", "c"]) == True

        # Some False values
        assert all_func(context, [True, False, True]) == False
        assert all_func(context, [1, 0, 3]) == False
        assert all_func(context, ["a", "", "c"]) == False

        # All False values
        assert all_func(context, [False, False, False]) == False
        assert all_func(context, [0, 0, 0]) == False

        # Empty container (vacuous truth)
        assert all_func(context, []) == True
        assert all_func(context, ()) == True

    def test_any_function(self):
        """Test any() function."""
        factory = PythonicFunctionFactory()
        any_func = factory.create_function("any")
        context = SandboxContext()

        # Some True values
        assert any_func(context, [True, False, False]) == True
        assert any_func(context, [0, 1, 0]) == True
        assert any_func(context, ["", "a", ""]) == True

        # All True values
        assert any_func(context, [True, True, True]) == True
        assert any_func(context, [1, 2, 3]) == True

        # All False values
        assert any_func(context, [False, False, False]) == False
        assert any_func(context, [0, 0, 0]) == False
        assert any_func(context, ["", "", ""]) == False

        # Empty container
        assert any_func(context, []) == False
        assert any_func(context, ()) == False


class TestRangeFunction:
    """Comprehensive tests for range() function."""

    def test_range_single_argument(self):
        """Test range() with single argument."""
        factory = PythonicFunctionFactory()
        range_func = factory.create_function("range")
        context = SandboxContext()

        # Basic range
        result = list(range_func(context, 5))
        assert result == [0, 1, 2, 3, 4]

        # Zero range
        result = list(range_func(context, 0))
        assert result == []

        # Single element
        result = list(range_func(context, 1))
        assert result == [0]

    def test_range_two_arguments(self):
        """Test range() with start and stop arguments."""
        factory = PythonicFunctionFactory()
        range_func = factory.create_function("range")
        context = SandboxContext()

        # Basic range with start
        result = list(range_func(context, 2, 7))
        assert result == [2, 3, 4, 5, 6]

        # Start equals stop
        result = list(range_func(context, 5, 5))
        assert result == []

        # Start greater than stop
        result = list(range_func(context, 7, 2))
        assert result == []

    def test_range_three_arguments(self):
        """Test range() with start, stop, and step arguments."""
        factory = PythonicFunctionFactory()
        range_func = factory.create_function("range")
        context = SandboxContext()

        # Basic range with step
        result = list(range_func(context, 0, 10, 2))
        assert result == [0, 2, 4, 6, 8]

        # Step of 1 (same as two-argument)
        result = list(range_func(context, 1, 5, 1))
        assert result == [1, 2, 3, 4]

        # Larger step
        result = list(range_func(context, 0, 20, 5))
        assert result == [0, 5, 10, 15]

        # Negative step
        result = list(range_func(context, 10, 0, -2))
        assert result == [10, 8, 6, 4, 2]


class TestFunctionFactoryMethods:
    """Test the factory's utility methods."""

    def test_get_available_functions(self):
        """Test getting list of available functions."""
        factory = PythonicFunctionFactory()
        available = factory.get_available_functions()

        # Check that all expected functions are available
        expected_functions = [
            "len",
            "sum",
            "max",
            "min",
            "abs",
            "round",
            "int",
            "float",
            "bool",
            "sorted",
            "reversed",
            "enumerate",
            "all",
            "any",
            "range",
        ]

        for func_name in expected_functions:
            assert func_name in available

    def test_get_function_info(self):
        """Test getting function information."""
        factory = PythonicFunctionFactory()

        # Test getting info for each function
        for func_name in factory.get_available_functions():
            info = factory.get_function_info(func_name)
            assert "func" in info
            assert "types" in info
            assert "doc" in info
            assert "signatures" in info
            assert isinstance(info["doc"], str)
            assert len(info["doc"]) > 0

    def test_is_supported(self):
        """Test checking if functions are supported."""
        factory = PythonicFunctionFactory()

        # Test supported functions
        assert factory.is_supported("len")
        assert factory.is_supported("sum")
        assert factory.is_supported("max")

        # Test unsupported functions
        assert not factory.is_supported("eval")
        assert not factory.is_supported("open")
        assert not factory.is_supported("unknown_function")

    def test_function_info_error(self):
        """Test error handling for function info."""
        factory = PythonicFunctionFactory()

        with pytest.raises(ValueError) as exc_info:
            factory.get_function_info("unknown_function")

        assert "Unknown function: unknown_function" in str(exc_info.value)
