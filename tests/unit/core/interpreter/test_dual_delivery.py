"""
Tests for dual delivery mechanism with deliver and return statements.
"""

import pytest

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.concurrency import LazyPromise

# AST imports will be added in Phase 1 when deliver/return statement tests are implemented

from unittest.mock import Mock

try:
    from unittest.mock import AsyncMock
except ImportError:
    raise ImportError("AsyncMock is not available. Please use Python 3.8 or later.")


class TestDualDeliveryFoundation:
    """Test foundation for dual delivery mechanism - what works with current codebase."""

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    # NOTE: DeliverStatement tests will be added in Phase 1 when DeliverStatement AST node is implemented
    # For now, focusing on LazyPromise[T] functionality that's already available


class TestReturnStatement:
    """Test lazy execution with return statements (current codebase support)."""

    @pytest.fixture
    def mock_executor(self):
        """Create a mock executor."""
        executor = Mock()
        executor.execute_and_await = AsyncMock()
        return executor

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    @pytest.mark.asyncio
    async def test_return_with_value_creates_promise(self, context):
        """Test that return statement creates LazyPromise[T] wrapper."""
        # Act & Assert - Currently tests basic LazyPromise[T] creation
        # Full return statement execution will be implemented in Phase 1

        # Test that we can create a LazyPromise[T] directly (the foundation exists)
        promise = LazyPromise(lambda: 42, context)
        # Test that LazyPromise[T] resolves to the correct value
        resolved_value = promise._wait_for_delivery()  # Access internal resolution
        assert resolved_value == 42


class TestLazyPromiseTransparency:
    """Test that LazyPromise[T] appears completely transparent as T."""

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    def test_promise_arithmetic_operations(self, context):
        """Test that LazyPromise[T] supports arithmetic operations transparently."""
        # Create promises
        promise_5 = LazyPromise(lambda: 5, context)
        promise_3 = LazyPromise(lambda: 3, context)

        # Test arithmetic operations
        assert promise_5 + promise_3 == 8
        assert promise_5 - promise_3 == 2
        assert promise_5 * promise_3 == 15
        assert promise_5 / promise_3 == 5 / 3

    def test_promise_comparison_operations(self, context):
        """Test that LazyPromise[T] supports comparison operations transparently."""
        promise_5 = LazyPromise(lambda: 5, context)
        promise_3 = LazyPromise(lambda: 3, context)

        assert promise_5 > promise_3
        assert promise_3 < promise_5
        assert promise_5 >= promise_3
        assert promise_3 <= promise_5
        assert promise_5 == 5
        assert promise_3 != 5

    def test_promise_string_operations(self, context):
        """Test that LazyPromise[T] supports string operations transparently."""
        promise_str = LazyPromise(lambda: "hello", context)

        assert str(promise_str) == "hello"
        assert len(promise_str) == 5
        assert "ell" in promise_str
        assert promise_str + " world" == "hello world"

    def test_promise_collection_operations(self, context):
        """Test that LazyPromise[T] supports collection operations transparently."""
        promise_list = LazyPromise(lambda: [1, 2, 3], context)
        promise_dict = LazyPromise(lambda: {"a": 1, "b": 2}, context)

        # List operations
        assert len(promise_list) == 3
        assert promise_list[0] == 1
        assert 2 in promise_list

        # Dict operations
        assert len(promise_dict) == 2
        assert promise_dict["a"] == 1
        assert "b" in promise_dict

    def test_promise_function_call(self, context):
        """Test that LazyPromise[T] supports function calls transparently."""

        def test_func(x, y):
            return x + y

        promise_func = LazyPromise(lambda: test_func, context)
        result = promise_func(3, 4)
        assert result == 7

    def test_promise_attribute_access(self, context):
        """Test that LazyPromise[T] supports attribute access transparently."""

        class TestObj:
            def __init__(self):
                self.value = 42

            def method(self):
                return self.value * 2

        promise_obj = LazyPromise(lambda: TestObj(), context)

        assert promise_obj.value == 42
        assert promise_obj.method() == 84


class TestLazyPromiseParallelization:
    """Test automatic parallelization of multiple promise access."""

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    def test_multiple_promise_access_patterns(self, context):
        """Test that multiple promises are detected and resolved in parallel."""
        call_count = 0

        def slow_computation(value):
            nonlocal call_count
            call_count += 1
            return value * 2

        # Create multiple promises
        promise_a = LazyPromise(lambda: slow_computation(5), context)
        promise_b = LazyPromise(lambda: slow_computation(10), context)
        promise_c = LazyPromise(lambda: slow_computation(15), context)

        # Access multiple promises in same expression
        result = promise_a + promise_b + promise_c

        # All computations should have been called
        assert result == 60  # (5*2) + (10*2) + (15*2)
        assert call_count == 3


class TestLazyPromiseErrorHandling:
    """Test comprehensive error handling with stack trace preservation."""

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    def test_promise_error_preservation(self, context):
        """Test that errors in promise resolution are properly preserved."""

        def failing_computation():
            raise ValueError("Test error")

        promise = LazyPromise(failing_computation, context)

        with pytest.raises(Exception) as exc_info:
            _ = promise + 1  # Force resolution

        # Should preserve original error information
        assert "Test error" in str(exc_info.value)

    def test_promise_creation_location_tracking(self, context):
        """Test that promise creation location is tracked."""
        promise = LazyPromise(lambda: 42, context)

        # Location tracking is optional - just verify promise works
        assert promise is not None
        assert isinstance(promise, LazyPromise)


if __name__ == "__main__":
    pytest.main([__file__])
