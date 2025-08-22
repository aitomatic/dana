"""
Functional tests for deliver/return dual delivery mechanism.

NOTE: This test file is currently limited to LazyPromise[T] functionality that works
with the current codebase. Full deliver/return statement testing will be added
in Phase 1 when parser support and FunctionExecutor integration is implemented.
"""

import pytest

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext
from dana.core.concurrency import LazyPromise


class TestLazyPromiseFoundation:
    """Test LazyPromise[T] foundation that works with current codebase."""

    @pytest.fixture
    def interpreter(self):
        """Create a Dana interpreter for testing."""
        return DanaInterpreter()

    @pytest.fixture
    def context(self):
        """Create a test context."""
        return SandboxContext()

    def test_promise_transparency_basic(self, context):
        """Test basic LazyPromise[T] transparency."""
        # Test that LazyPromise[T] behaves like the wrapped type
        promise_int = LazyPromise(lambda: 42, context)
        promise_str = LazyPromise(lambda: "hello", context)

        # Basic arithmetic and operations
        assert promise_int + 8 == 50
        assert promise_str + " world" == "hello world"
        assert len(promise_str) == 5

    def test_promise_comparison_operations(self, context):
        """Test LazyPromise[T] comparison operations."""
        promise_5 = LazyPromise(lambda: 5, context)
        promise_3 = LazyPromise(lambda: 3, context)

        assert promise_5 > promise_3
        assert promise_3 < promise_5
        assert promise_5 == 5
        assert promise_3 != 5

    def test_promise_error_propagation(self, context):
        """Test that LazyPromise[T] error propagation works."""

        def failing_computation():
            raise ValueError("Test error message")

        promise = LazyPromise(failing_computation, context)

        # Error should surface when promise is accessed
        with pytest.raises((ValueError, RuntimeError, Exception)):
            _ = promise + 1

    # TODO Phase 1: Add deliver/return statement tests when parser support is added
    # def test_deliver_eager_execution(self):
    #     """Test that deliver executes immediately."""
    #     # Will test: deliver 42 returns concrete 42

    # def test_return_lazy_execution(self):
    #     """Test that return creates LazyPromise[T]."""
    #     # Will test: return 42 returns LazyPromise[42]

    # TODO Phase 1: Add Dana function LazyPromise[T] wrapping tests
    # def test_dana_function_promise_wrapping(self):
    #     """Test Dana functions automatically get LazyPromise[T] treatment."""
    #     # Will test FunctionExecutor wrapping Dana functions in LazyPromise[T]


if __name__ == "__main__":
    pytest.main([__file__])
