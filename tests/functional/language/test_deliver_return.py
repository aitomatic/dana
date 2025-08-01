"""
Functional tests for deliver/return dual delivery mechanism.

NOTE: This test file is currently limited to Promise[T] functionality that works
with the current codebase. Full deliver/return statement testing will be added
in Phase 1 when parser support and FunctionExecutor integration is implemented.
"""

import pytest

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.runtime.promise import Promise


class TestPromiseFoundation:
    """Test Promise[T] foundation that works with current codebase."""

    @pytest.fixture
    def interpreter(self):
        """Create a Dana interpreter for testing."""
        return DanaInterpreter()

    @pytest.fixture
    def context(self):
        """Create a test context."""
        return SandboxContext()

    def test_promise_transparency_basic(self, context):
        """Test basic Promise[T] transparency."""
        # Test that Promise[T] behaves like the wrapped type
        promise_int = Promise(lambda: 42, context)
        promise_str = Promise(lambda: "hello", context)

        # Basic arithmetic and operations
        assert promise_int + 8 == 50
        assert promise_str + " world" == "hello world"
        assert len(promise_str) == 5

    def test_promise_comparison_operations(self, context):
        """Test Promise[T] comparison operations."""
        promise_5 = Promise(lambda: 5, context)
        promise_3 = Promise(lambda: 3, context)

        assert promise_5 > promise_3
        assert promise_3 < promise_5
        assert promise_5 == 5
        assert promise_3 != 5

    def test_promise_error_propagation(self, context):
        """Test that Promise[T] error propagation works."""

        def failing_computation():
            raise ValueError("Test error message")

        promise = Promise(failing_computation, context)

        # Error should surface when promise is accessed
        with pytest.raises((ValueError, RuntimeError, Exception)):
            _ = promise + 1

    # TODO Phase 1: Add deliver/return statement tests when parser support is added
    # def test_deliver_eager_execution(self):
    #     """Test that deliver executes immediately."""
    #     # Will test: deliver 42 returns concrete 42

    # def test_return_lazy_execution(self):
    #     """Test that return creates Promise[T]."""
    #     # Will test: return 42 returns Promise[42]

    # TODO Phase 1: Add Dana function Promise[T] wrapping tests
    # def test_dana_function_promise_wrapping(self):
    #     """Test Dana functions automatically get Promise[T] treatment."""
    #     # Will test FunctionExecutor wrapping Dana functions in Promise[T]


if __name__ == "__main__":
    pytest.main([__file__])
