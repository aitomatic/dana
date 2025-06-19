"""
Tests for POET decorator Python functionality.

This module tests basic Python decorator functionality and integration patterns.
"""

from unittest.mock import Mock

import pytest

from opendxa.dana.poet.decorator import poet
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def create_test_context():
    """Create a test context for function calls."""
    context = SandboxContext()
    # Add a mock interpreter if needed for testing
    mock_interpreter = Mock()
    context._interpreter = mock_interpreter
    return context


class TestPOETDecoratorPython:
    """Test POET decorator functionality in pure Python context."""

    def test_poet_decorator_returns_function(self):
        """Test that POET decorator returns a callable function."""

        @poet(domain="test_domain", retries=2, timeout=10)
        def my_func(x):
            return x * 2

        assert callable(my_func)
        assert hasattr(my_func, "_poet_metadata")

        meta = my_func._poet_metadata
        assert "test_domain" in meta["domains"]
        assert meta["retries"] == 2
        assert meta["timeout"] == 10
        assert meta["namespace"] == "local"
        assert meta["overwrite"] is False

        # Test function execution
        result = my_func(3)
        assert result == 6

    def test_poet_decorator_retry_logic(self):
        """Test retry functionality of POET decorator."""

        calls = {"count": 0}

        @poet(domain="test_domain", retries=3)
        def sometimes_fails(x):
            calls["count"] += 1
            if calls["count"] < 2:
                raise ValueError("fail once")
            return x + 1

        result = sometimes_fails(5)
        assert result == 6
        assert calls["count"] == 2  # Should retry once

    def test_poet_decorator_metadata_fields(self):
        """Test that all metadata fields are properly set."""

        @poet(domain="my_domain", retries=4, timeout=7, namespace="custom", overwrite=True)
        def f(x):
            return x

        meta = f._poet_metadata
        assert "my_domain" in meta["domains"]
        assert meta["retries"] == 4
        assert meta["timeout"] == 7
        assert meta["namespace"] == "custom"
        assert meta["overwrite"] is True

    def test_poet_decorator_preserves_doc_and_name(self):
        """Test that function name and docstring are preserved."""

        @poet(domain="test_domain")
        def f(x):
            """This is a test docstring."""
            return x

        assert f.__name__ == "f"
        assert f.__doc__ == "This is a test docstring."

    def test_poet_decorator_with_context_parameter(self):
        """Test decorator with explicit context handling."""

        @poet(domain="context_test")
        def context_func(x: int) -> int:
            return x * 2

        # Function should work with or without explicit context
        result1 = context_func(5)
        assert result1 == 10

        # Should also work if context is available
        context = create_test_context()
        result2 = context_func(7)
        assert result2 == 14

    def test_poet_decorator_error_handling(self):
        """Test error handling in POET decorated functions."""

        @poet(domain="error_test", retries=1)
        def error_func(x):
            raise ValueError("Test error message")

        with pytest.raises(ValueError, match="Test error message"):
            error_func(5)

    @pytest.mark.skip(reason="DanaFunction mock integration issue - Mock execution chain needs debugging")
    def test_poet_decorator_with_dana_function_mock(self):
        """Test POET decorator applied to mock DanaFunction."""

        from opendxa.dana.sandbox.interpreter.functions.dana_function import DanaFunction

        # Create mock DanaFunction with all required attributes
        mock_dana_func = Mock(spec=DanaFunction)
        mock_dana_func.execute.return_value = 100
        mock_dana_func.__name__ = "mock_func"
        mock_dana_func.__annotations__ = {}  # Required for functools.wraps
        mock_dana_func.__doc__ = "Mock Dana function"
        mock_dana_func.__module__ = "test_module"
        mock_dana_func.__qualname__ = "mock_func"
        mock_dana_func.__type_params__ = ()  # Python 3.12+ compatibility

        # Apply POET decorator
        decorated_func = poet(domain="dana_test")(mock_dana_func)

        # Should be callable and preserve metadata
        assert callable(decorated_func)
        assert hasattr(decorated_func, "_poet_metadata")
        assert "dana_test" in decorated_func._poet_metadata["domains"]

        # Should work when called
        result = decorated_func(42)
        assert result == 100

        # Should have called the original function's execute method
        mock_dana_func.execute.assert_called_once()

    def test_poet_decorator_chaining_python(self):
        """Test chaining multiple POET decorators in Python."""

        @poet(domain="domain1")
        @poet(domain="domain2", retries=3)
        def chained_func(x):
            return x + 10

        assert callable(chained_func)
        meta = chained_func._poet_metadata

        # Should have both domains
        assert "domain1" in meta["domains"]
        assert "domain2" in meta["domains"]

        # Should work correctly
        result = chained_func(5)
        assert result == 15

    def test_poet_decorator_default_values(self):
        """Test default values for POET decorator parameters."""

        @poet(domain="defaults_test")
        def default_func(x):
            return x

        meta = default_func._poet_metadata
        assert meta["retries"] == 1
        assert meta["timeout"] is None
        assert meta["namespace"] == "local"
        assert meta["overwrite"] is False

    def test_poet_decorator_function_signature_preservation(self):
        """Test that function signatures are preserved for introspection."""

        @poet(domain="signature_test")
        def sig_func(a: int, b: str, c: float = 3.14) -> str:
            """Function with complex signature."""
            return f"{b}: {a + c}"

        # Function should work normally
        result = sig_func(10, "Result", 2.5)
        assert result == "Result: 12.5"

        # Should preserve original function attributes
        assert sig_func.__name__ == "sig_func"
        assert sig_func.__doc__ is not None and "complex signature" in sig_func.__doc__
