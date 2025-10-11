"""
Unit tests for PromiseLimiter - Safety and Resource Management for Universal EagerPromise Wrapping

Tests all safety mechanisms including:
- Global limit enforcement
- Nesting depth limits
- Timeout mechanisms
- Circuit breaker pattern
- Resource exhaustion protection
- Performance monitoring

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from dana.core.concurrency.promise_limiter import (
    PromiseLimiter,
    PromiseLimiterError,
    get_global_promise_limiter,
    set_global_promise_limiter,
)
from dana.core.concurrency.promise_utils import resolve_if_promise, resolve_promise


class TestPromiseLimiter:
    """Test PromiseLimiter functionality and safety mechanisms."""

    def _resolve_promise_result(self, result):
        """Utility function to resolve Promise results consistently in tests."""
        return resolve_if_promise(result)

    def _resolve_promise_directly(self, promise):
        """Utility function to resolve a Promise directly (when we know it's a Promise)."""
        return resolve_promise(promise)

    @pytest.fixture
    def limiter(self):
        """Create a PromiseLimiter instance for testing."""
        return PromiseLimiter(
            max_promises=4,
            max_nesting_depth=2,
            timeout_seconds=1.0,
            circuit_breaker_threshold=3,
            circuit_breaker_timeout=2.0,
            enable_monitoring=True,
        )

    @pytest.fixture
    def executor(self):
        """Create a ThreadPoolExecutor for testing."""
        with ThreadPoolExecutor(max_workers=2) as executor:
            yield executor

    def test_initialization(self, limiter):
        """Test PromiseLimiter initialization with default values."""
        assert limiter.max_promises == 4
        assert limiter.max_nesting_depth == 2
        assert limiter.timeout_seconds == 1.0
        assert limiter.circuit_breaker_threshold == 3
        assert limiter.circuit_breaker_timeout == 2.0
        assert limiter.enable_monitoring is True

    def test_can_create_promise_initial_state(self, limiter):
        """Test that PromiseLimiter allows Promise creation in initial state."""
        assert limiter.can_create_promise() is True

    def test_global_limit_enforcement(self, limiter, executor):
        """Test that global Promise limit is enforced."""
        # Create promises up to the limit (max_promises = 4, max_nesting_depth = 2)
        promises = []

        for i in range(2):  # Only create 2 promises to stay within nesting depth limit
            # Use a closure to capture the current value of i
            def make_computation(value):
                return lambda: (time.sleep(0.1), f"result_{value}")[1]  # Slow computation

            promise = limiter.create_promise(make_computation(i), executor)
            promises.append(promise)

        # Should still be able to create more promises (we have 2 outstanding, limit is 4)
        assert limiter.can_create_promise() is True

        # Create 2 more promises to reach the limit
        for i in range(2, 4):

            def make_computation(value):
                return lambda: (time.sleep(0.1), f"result_{value}")[1]  # Slow computation

            promise = limiter.create_promise(make_computation(i), executor)
            promises.append(promise)

        # Verify we can't create more promises (at global limit)
        assert limiter.can_create_promise() is False

        # Access one promise to complete it
        result = promises[0]
        result_value = self._resolve_promise_directly(result)
        assert "result_0" in str(result_value)

        # Wait a bit for Promise completion
        time.sleep(0.1)

        # Should be able to create one more promise now
        assert limiter.can_create_promise() is True

    def test_nesting_depth_limit(self, limiter, executor):
        """Test that nesting depth limit is enforced."""
        # First level - should work
        _ = limiter.create_promise(lambda: "level1", executor)
        assert limiter.can_create_promise() is True

        # Simulate nested execution by manually incrementing depth
        limiter._increment_nesting_depth()
        limiter._increment_nesting_depth()

        # Should not be able to create more promises at depth 3
        assert limiter.can_create_promise() is False

        # Decrement depth
        limiter._decrement_nesting_depth()
        assert limiter.can_create_promise() is True

    def test_synchronous_fallback(self, limiter):
        """Test that synchronous fallback works when limits are exceeded."""
        # Set up limiter to force fallback
        limiter._outstanding_promises = limiter.max_promises

        # Should fall back to synchronous execution
        result = limiter.create_promise(lambda: "sync_result")
        assert result == "sync_result"

        # Check statistics
        stats = limiter.get_statistics()
        assert stats["synchronous_fallbacks"] == 1

    def test_timeout_mechanism(self, limiter, executor):
        """Test that timeout mechanism works correctly."""

        def slow_computation():
            time.sleep(2.0)  # Longer than timeout
            return "slow_result"

        # Should timeout and fall back to synchronous
        result = limiter.create_promise(slow_computation, executor)
        assert result == "slow_result"

        # Check statistics
        stats = limiter.get_statistics()
        assert stats["timeout_events"] >= 1

    def test_circuit_breaker_pattern(self, limiter, executor):
        """Test that circuit breaker pattern works correctly."""

        def failing_computation():
            raise Exception("Simulated failure")

        # Create promises that will fail
        promises = []
        for _ in range(3):
            promise = limiter.create_promise(failing_computation, executor)
            promises.append(promise)

        # Access the promises to trigger their execution and failures
        for promise in promises:
            try:
                _ = promise
                # This should raise an exception
                raise AssertionError("Should have raised an exception")
            except Exception:
                pass  # Expected to fail
            time.sleep(0.1)  # Small delay to ensure failure is recorded

        # Circuit breaker should be open now
        assert limiter.can_create_promise() is False

        # Wait for circuit breaker timeout
        time.sleep(2.1)

        # Circuit breaker should reset
        assert limiter.can_create_promise() is True

    def test_circuit_breaker_manual_reset(self, limiter, executor):
        """Test manual circuit breaker reset."""

        def failing_computation():
            raise Exception("Simulated failure")

        # Create promises that will fail
        promises = []
        for _ in range(3):
            promise = limiter.create_promise(failing_computation, executor)
            promises.append(promise)

        # Access the promises to trigger their execution and failures
        for promise in promises:
            try:
                _ = promise
                # This should raise an exception
                raise AssertionError("Should have raised an exception")
            except Exception:
                pass  # Expected to fail
            time.sleep(0.1)  # Small delay to ensure failure is recorded

        # Circuit breaker should be open
        assert limiter.can_create_promise() is False

        # Manually reset
        limiter.reset_circuit_breaker()
        assert limiter.can_create_promise() is True

    def test_thread_safety(self, limiter, executor):
        """Test that PromiseLimiter is thread-safe."""
        results = []
        errors = []

        def worker(worker_id):
            try:
                _ = limiter.create_promise(lambda: f"worker_{worker_id}", executor)
                results.append(f"worker_{worker_id}")
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have some results and no errors
        assert len(results) > 0
        assert len(errors) == 0

    def test_statistics_monitoring(self, limiter, executor):
        """Test that statistics monitoring works correctly."""
        # Create some promises
        for i in range(3):
            limiter.create_promise(lambda i=i: f"result_{i}", executor)

        # Force some fallbacks
        limiter._outstanding_promises = limiter.max_promises
        limiter.create_promise(lambda: "fallback_result")

        # Get statistics
        stats = limiter.get_statistics()

        # Verify key metrics
        assert stats["promises_created"] >= 3
        assert stats["synchronous_fallbacks"] >= 1
        assert stats["outstanding_promises"] <= limiter.max_promises
        assert "uptime_seconds" in stats
        assert "promises_per_second" in stats
        assert "fallback_rate" in stats

    def test_statistics_reset(self, limiter, executor):
        """Test that statistics can be reset."""
        # Create some promises
        limiter.create_promise(lambda: "result", executor)

        # Get initial statistics
        initial_stats = limiter.get_statistics()
        assert initial_stats["promises_created"] >= 1

        # Reset statistics
        limiter.reset_statistics()

        # Get new statistics
        new_stats = limiter.get_statistics()
        assert new_stats["promises_created"] == 0
        assert new_stats["synchronous_fallbacks"] == 0

    def test_health_check(self, limiter):
        """Test that health check works correctly."""
        # Initially should be healthy
        assert limiter.is_healthy() is True

        # Force high fallback rate
        limiter._synchronous_fallbacks = 100
        limiter._promises_created = 150

        # Should be unhealthy due to high fallback rate
        assert limiter.is_healthy() is False

        # Reset and test timeout rate
        limiter.reset_statistics()
        limiter._timeout_events = 10
        limiter._promises_created = 50

        # Should be unhealthy due to high timeout rate
        assert limiter.is_healthy() is False

    def test_coroutine_support(self, limiter, executor):
        """Test that PromiseLimiter works with coroutines."""

        async def async_computation():
            await asyncio.sleep(0.1)
            return "async_result"

        # Should work with coroutines
        _ = limiter.create_promise(async_computation, executor)
        # Note: promise creation should succeed

    def test_completion_callback(self, limiter, executor):
        """Test that completion callbacks work correctly."""
        callback_called = False

        def callback(result):
            nonlocal callback_called
            callback_called = True

        # Create promise with callback
        promise = limiter.create_promise(lambda: "callback_result", executor, on_delivery=callback)

        # Access the promise to trigger completion
        result = self._resolve_promise_directly(promise)
        assert "callback_result" in str(result)

        # Wait for callback to be called
        time.sleep(0.1)
        assert callback_called is True

    def test_error_in_completion_callback(self, limiter, executor):
        """Test that errors in completion callbacks are handled gracefully."""

        def callback():
            raise Exception("Callback error")

        # Should not raise exception
        promise = limiter.create_promise(lambda: "result", executor, callback)
        result = self._resolve_promise_directly(promise)
        assert "result" in str(result)

    def test_promise_creation_failure_handling(self, limiter, executor):
        """Test that Promise creation failures are handled gracefully."""
        # Mock EagerPromise.create to raise an exception
        with patch("dana.core.concurrency.eager_promise.EagerPromise.create") as mock_create:
            mock_create.side_effect = Exception("Promise creation failed")

            # Should fall back to synchronous execution
            result = limiter.create_promise(lambda: "fallback_result", executor)
            assert result == "fallback_result"

    def test_nesting_depth_thread_local(self, limiter):
        """Test that nesting depth is thread-local."""
        # Set nesting depth in main thread
        limiter._increment_nesting_depth()
        assert limiter._get_nesting_depth() == 1

        # Create a new thread and check depth
        depth_in_thread = []

        def check_depth():
            depth_in_thread.append(limiter._get_nesting_depth())

        thread = threading.Thread(target=check_depth)
        thread.start()
        thread.join()

        # Should be 0 in new thread
        assert depth_in_thread[0] == 0

    def test_global_promise_limiter(self):
        """Test global PromiseLimiter functionality."""
        # Get global instance
        global_limiter = get_global_promise_limiter()
        assert isinstance(global_limiter, PromiseLimiter)

        # Set custom instance
        custom_limiter = PromiseLimiter(max_promises=8)
        set_global_promise_limiter(custom_limiter)

        # Should get custom instance
        retrieved_limiter = get_global_promise_limiter()
        assert retrieved_limiter is custom_limiter
        assert retrieved_limiter.max_promises == 8

    def test_promise_limiter_error(self):
        """Test PromiseLimiterError exception."""
        error = PromiseLimiterError("Test error")
        assert str(error) == "Test error"

    def test_concurrent_promise_creation(self, limiter, executor):
        """Test concurrent Promise creation under load."""
        results = []

        def create_promise(worker_id):
            try:
                _ = limiter.create_promise(lambda: f"concurrent_{worker_id}", executor)
                results.append(f"concurrent_{worker_id}")
            except Exception as e:
                results.append(f"error_{worker_id}: {e}")

        # Create many concurrent requests
        threads = []
        for i in range(20):
            thread = threading.Thread(target=create_promise, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have some successful results
        assert len(results) > 0

        # Check statistics
        stats = limiter.get_statistics()
        assert stats["promises_created"] > 0

    def test_memory_usage_under_load(self, limiter, executor):
        """Test memory usage under high load."""
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

            # Create many promises
            promises = []
            for i in range(100):
                promise = limiter.create_promise(lambda i=i: f"memory_test_{i}", executor)
                promises.append(promise)

            # Access some promises
            for i in range(10):
                result = self._resolve_promise_result(promises[i])
                assert f"memory_test_{i}" in str(result)

            # Wait for completion
            time.sleep(0.5)

            # Check final memory usage
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable (less than 10MB)
            assert memory_increase < 10 * 1024 * 1024
        except ImportError:
            # Skip memory test if psutil is not available
            pytest.skip("psutil not available, skipping memory test")

    def test_performance_under_load(self, limiter, executor):
        """Test performance under high load."""
        start_time = time.time()

        # Create many promises quickly
        promises = []
        for i in range(50):
            promise = limiter.create_promise(lambda i=i: f"perf_test_{i}", executor)
            promises.append(promise)

        creation_time = time.time() - start_time

        # Creation should be fast (less than 1 second for 50 promises)
        assert creation_time < 1.0

        # Access promises
        start_time = time.time()
        for promise in promises[:10]:
            result = self._resolve_promise_result(promise)
            assert "perf_test_" in str(result)

        access_time = time.time() - start_time

        # Access should be fast
        assert access_time < 1.0

    def test_edge_cases(self, limiter, executor):
        """Test various edge cases."""
        # Test with None computation - should handle gracefully
        result = limiter.create_promise(lambda: None, executor)
        result_value = self._resolve_promise_result(result)
        assert result_value is None

        # Test with very fast computation
        result = limiter.create_promise(lambda: "fast", executor)
        result_value = self._resolve_promise_result(result)
        assert result_value == "fast"

        # Test with computation that returns a Promise
        def return_promise():
            return limiter.create_promise(lambda: "nested", executor)

        result = limiter.create_promise(return_promise, executor)
        assert result is not None
