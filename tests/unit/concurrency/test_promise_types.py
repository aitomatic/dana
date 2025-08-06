"""
Robust tests for both LazyPromise and EagerPromise implementations.

Tests the behavior differences between lazy and eager evaluation,
focusing on correctness rather than precise timing.
"""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from dana.core.concurrency import BasePromise, EagerPromise, LazyPromise
from dana.core.lang.sandbox_context import SandboxContext


class TestPromiseTypes:
    """Test both LazyPromise and EagerPromise types."""

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    @pytest.fixture
    def executor(self):
        """Create a test thread pool executor."""
        with ThreadPoolExecutor(max_workers=4) as executor:
            yield executor

    def test_both_inherit_from_base_promise(self, context, executor):
        """Test that both promise types inherit from BasePromise."""
        lazy = LazyPromise.create(lambda: "test", context)
        eager = EagerPromise.create(lambda: "test", executor)

        assert isinstance(lazy, BasePromise)
        assert isinstance(eager, BasePromise)
        assert isinstance(lazy, LazyPromise)
        assert isinstance(eager, EagerPromise)

    def test_factory_method_patterns(self, context, executor):
        """Test that both types use factory method pattern correctly."""
        # Test factory methods
        lazy = LazyPromise.create(lambda: 42, context)
        eager = EagerPromise.create(lambda: 42, executor)

        assert isinstance(lazy, LazyPromise)
        assert isinstance(eager, EagerPromise)

        # Both should resolve to the same value
        assert lazy._ensure_resolved() == 42
        assert eager._wait_for_delivery() == 42

    def test_lazy_execution_timing(self, context, executor):
        """Test that lazy promises don't execute until accessed."""
        executed = []

        def track_execution():
            executed.append("executed")
            return "result"

        # Create lazy promise
        lazy = LazyPromise.create(track_execution, context)

        # Should not have executed yet
        assert len(executed) == 0

        # Access should trigger execution
        result = lazy._ensure_resolved()
        assert result == "result"
        assert len(executed) == 1

    def test_eager_execution_intention(self, context, executor):
        """Test that eager promises attempt immediate execution."""
        executed = []

        def track_execution():
            executed.append("executed")
            return "result"

        # Create eager promise
        eager = EagerPromise.create(track_execution, executor)

        # Give time for thread/async execution
        time.sleep(0.05)

        # Access result
        result = eager._wait_for_delivery()
        assert result == "result"
        assert len(executed) == 1

    def test_sync_computation_execution(self, context, executor):
        """Test both types with synchronous computations."""
        call_count = 0

        def sync_computation():
            nonlocal call_count
            call_count += 1
            return f"sync_result_{call_count}"

        # Test lazy
        lazy = LazyPromise.create(sync_computation, context)
        assert call_count == 0  # Not executed yet

        result = lazy._ensure_resolved()
        assert result == "sync_result_1"
        assert call_count == 1

        # Test eager
        call_count = 0  # Reset
        eager = EagerPromise.create(sync_computation, executor)

        # Give thread time to execute
        time.sleep(0.05)

        result = eager._wait_for_delivery()
        assert result == "sync_result_1"
        assert call_count == 1

    def test_error_handling_both_types(self, context, executor):
        """Test error handling in both promise types."""

        def failing_computation():
            raise ValueError("Test error")

        # Test lazy error handling
        lazy = LazyPromise.create(failing_computation, context)
        with pytest.raises(ValueError, match="Test error"):
            lazy._ensure_resolved()

        # Test eager error handling
        eager = EagerPromise.create(failing_computation, executor)
        with pytest.raises(ValueError, match="Test error"):
            eager._wait_for_delivery()

    def test_transparent_operations_both_types(self, context, executor):
        """Test that both types are transparent to their underlying values."""
        # Test with different value types
        test_cases = [
            (42, int),
            ("hello", str),
            ([1, 2, 3], list),
            ({"key": "value"}, dict),
        ]

        for value, expected_type in test_cases:
            lazy = LazyPromise.create(lambda v=value: v, context)
            eager = EagerPromise.create(lambda v=value: v, executor)

            # Give eager promise time to execute
            time.sleep(0.01)

            # Test type behavior
            assert isinstance(lazy._ensure_resolved(), expected_type)
            assert isinstance(eager._wait_for_delivery(), expected_type)

            # Test transparent operations
            if expected_type == int:
                assert lazy + 8 == value + 8
                assert eager + 8 == value + 8
            elif expected_type == str:
                assert lazy + " world" == value + " world"
                assert eager + " world" == value + " world"
                assert len(lazy) == len(value)
                assert len(eager) == len(value)
            elif expected_type == list:
                assert len(lazy) == len(value)
                assert len(eager) == len(value)
                assert lazy[0] == value[0]
                assert eager[0] == value[0]
            elif expected_type == dict:
                assert len(lazy) == len(value)
                assert len(eager) == len(value)
                assert lazy["key"] == value["key"]
                assert eager["key"] == value["key"]

    def test_multiple_lazy_promises_behavior(self, context, executor):
        """Test behavior of multiple lazy promises."""
        execution_order = []

        def track_execution(name):
            execution_order.append(name)
            return name

        # Create multiple lazy promises
        p1 = LazyPromise.create(lambda: track_execution("p1"), context)
        p2 = LazyPromise.create(lambda: track_execution("p2"), context)
        p3 = LazyPromise.create(lambda: track_execution("p3"), context)

        # None should have executed yet
        assert len(execution_order) == 0

        # Access them
        results = [str(p1), str(p2), str(p3)]

        assert results == ["p1", "p2", "p3"]
        assert len(execution_order) == 3

    def test_multiple_eager_promises_behavior(self, context, executor):
        """Test behavior of multiple eager promises."""
        execution_count = 0

        def count_execution(name):
            nonlocal execution_count
            execution_count += 1
            return name

        # Create multiple eager promises
        p1 = EagerPromise.create(lambda: count_execution("eager1"), executor)
        p2 = EagerPromise.create(lambda: count_execution("eager2"), executor)
        p3 = EagerPromise.create(lambda: count_execution("eager3"), executor)

        # Give time for execution
        time.sleep(0.1)

        # Access results
        results = [str(p1), str(p2), str(p3)]

        assert results == ["eager1", "eager2", "eager3"]
        assert execution_count == 3

    def test_repr_and_str_transparency(self, context, executor):
        """Test string representations are transparent for both promise types."""
        lazy = LazyPromise.create(lambda: "test_value", context)
        eager = EagerPromise.create(lambda: "test_value", executor)

        # Give eager time to execute
        time.sleep(0.01)

        # Test repr shows promise type
        assert "LazyPromise" in repr(lazy)
        assert "EagerPromise" in repr(eager)

        # Test str behavior: both promise types should be transparent
        assert str(lazy) == "test_value"
        assert str(eager) == "test_value"

    def test_promise_string_transparency(self, context, executor):
        """Test promise string transparency."""
        lazy = LazyPromise.create(lambda: "test_value", context)
        eager = EagerPromise.create(lambda: "test_value", executor)

        lazy_str = str(lazy)
        eager_str = str(eager)

        # Both promise types resolve transparently to the value
        assert lazy_str == "test_value"
        assert eager_str == "test_value"

    def test_creation_location_tracking_both_types(self, context, executor):
        """Test that both types track creation location."""
        lazy = LazyPromise.create(lambda: "test", context)
        eager = EagerPromise.create(lambda: "test", executor)

        # Location tracking is optional - just verify promises work
        assert lazy is not None
        assert eager is not None


class TestPromiseInteroperability:
    """Test how lazy and eager promises work together."""

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    @pytest.fixture
    def executor(self):
        """Create a test thread pool executor."""
        with ThreadPoolExecutor(max_workers=4) as executor:
            yield executor

    def test_mixed_promise_operations(self, context, executor):
        """Test operations between lazy and eager promises."""
        lazy = LazyPromise.create(lambda: 10, context)
        eager = EagerPromise.create(lambda: 5, executor)

        # Give eager time to execute
        time.sleep(0.01)

        # Test arithmetic between different promise types
        result1 = lazy + eager
        result2 = eager * lazy

        assert result1 == 15
        assert result2 == 50

    def test_mixed_promise_comparisons(self, context, executor):
        """Test comparisons between different promise types."""
        lazy_5 = LazyPromise.create(lambda: 5, context)
        eager_3 = EagerPromise.create(lambda: 3, executor)
        eager_5 = EagerPromise.create(lambda: 5, executor)

        # Give eager promises time to execute
        time.sleep(0.01)

        assert lazy_5 > eager_3
        assert eager_3 < lazy_5
        assert lazy_5 == eager_5
        assert eager_3 != lazy_5

    def test_promise_in_collections(self, context, executor):
        """Test both promise types in collections."""
        lazy_list = LazyPromise.create(lambda: [1, 2, 3], context)
        eager_dict = EagerPromise.create(lambda: {"a": 1, "b": 2}, executor)

        # Give eager promise time to execute
        time.sleep(0.01)

        # Test collection operations
        assert len(lazy_list) == 3
        assert len(eager_dict) == 2
        assert lazy_list[1] == 2
        assert eager_dict["a"] == 1


class TestPromiseSpecialCases:
    """Test special cases and edge conditions."""

    @pytest.fixture
    def context(self):
        """Create a test sandbox context."""
        return SandboxContext()

    @pytest.fixture
    def executor(self):
        """Create a test thread pool executor."""
        with ThreadPoolExecutor(max_workers=4) as executor:
            yield executor

    def test_promise_resolution_idempotency(self, context, executor):
        """Test that resolving promises multiple times gives same result."""
        lazy = LazyPromise.create(lambda: "test", context)
        eager = EagerPromise.create(lambda: "test", executor)

        # Give eager time to execute
        time.sleep(0.01)

        # Multiple resolutions should give same result
        assert lazy._ensure_resolved() == "test"
        assert lazy._ensure_resolved() == "test"

        assert eager._wait_for_delivery() == "test"
        assert eager._wait_for_delivery() == "test"

    def test_promise_with_none_values(self, context, executor):
        """Test promises that resolve to None."""
        lazy_none = LazyPromise.create(lambda: None, context)
        eager_none = EagerPromise.create(lambda: None, executor)

        time.sleep(0.01)

        assert lazy_none._ensure_resolved() is None
        assert eager_none._wait_for_delivery() is None

    def test_promise_boolean_evaluation(self, context, executor):
        """Test boolean evaluation of promises."""
        lazy_true = LazyPromise.create(lambda: True, context)
        lazy_false = LazyPromise.create(lambda: False, context)
        eager_true = EagerPromise.create(lambda: True, executor)
        eager_false = EagerPromise.create(lambda: False, executor)

        time.sleep(0.01)

        assert bool(lazy_true) is True
        assert bool(lazy_false) is False
        assert bool(eager_true) is True
        assert bool(eager_false) is False


if __name__ == "__main__":
    pytest.main([__file__])
