"""
Test math functions in Dana standard library.
"""

import pytest

from dana.registry.function_registry import FunctionRegistry
from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers


class TestMathFunctions:
    """Test math functions registration and functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.registry = FunctionRegistry()
        register_py_wrappers(self.registry)

    def test_math_functions_registered(self):
        """Test that math functions are properly registered."""
        # Check that all math functions are registered in the system namespace
        assert "sum_range" in self.registry._functions["system"]
        assert "is_odd" in self.registry._functions["system"]
        assert "is_even" in self.registry._functions["system"]
        assert "factorial" in self.registry._functions["system"]

    def test_sum_range_function(self):
        """Test sum_range function."""
        func = self.registry._functions["system"]["sum_range"][0]

        # Test basic functionality
        result = func.execute(None, 1, 5)
        assert result == 15  # 1 + 2 + 3 + 4 + 5 = 15

        result = func.execute(None, 0, 3)
        assert result == 6  # 0 + 1 + 2 + 3 = 6

    def test_is_odd_function(self):
        """Test is_odd function."""
        func = self.registry._functions["system"]["is_odd"][0]

        # Test odd numbers
        assert func.execute(None, 1) is True
        assert func.execute(None, 3) is True
        assert func.execute(None, 5) is True

        # Test even numbers
        assert func.execute(None, 0) is False
        assert func.execute(None, 2) is False
        assert func.execute(None, 4) is False

    def test_is_even_function(self):
        """Test is_even function."""
        func = self.registry._functions["system"]["is_even"][0]

        # Test even numbers
        assert func.execute(None, 0) is True
        assert func.execute(None, 2) is True
        assert func.execute(None, 4) is True

        # Test odd numbers
        assert func.execute(None, 1) is False
        assert func.execute(None, 3) is False
        assert func.execute(None, 5) is False

    def test_factorial_function(self):
        """Test factorial function."""
        func = self.registry._functions["system"]["factorial"][0]

        # Test basic factorials
        assert func.execute(None, 0) == 1
        assert func.execute(None, 1) == 1
        assert func.execute(None, 2) == 2
        assert func.execute(None, 3) == 6
        assert func.execute(None, 4) == 24
        assert func.execute(None, 5) == 120

    def test_function_argument_validation(self):
        """Test that functions properly validate their arguments."""
        sum_range_func = self.registry._functions["system"]["sum_range"][0]
        is_odd_func = self.registry._functions["system"]["is_odd"][0]
        factorial_func = self.registry._functions["system"]["factorial"][0]

        # Test wrong argument types
        with pytest.raises(TypeError, match="sum_range arguments must be integers"):
            sum_range_func.execute(None, "1", 5)

        with pytest.raises(TypeError, match="is_odd argument must be an integer"):
            is_odd_func.execute(None, "1")

        with pytest.raises(TypeError, match="factorial argument must be an integer"):
            factorial_func.execute(None, "5")

        # Test negative factorial
        with pytest.raises(ValueError, match="factorial argument must be non-negative"):
            factorial_func.execute(None, -1)
