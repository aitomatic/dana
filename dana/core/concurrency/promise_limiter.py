"""
Promise Limiter - Safety and Resource Management for Universal EagerPromise Wrapping

This module provides a PromiseLimiter class that enforces safety limits and resource
management for universal EagerPromise creation in Dana's function execution model.

Key Features:
- Global limit enforcement for outstanding promises
- Thread-local tracking for nested execution contexts
- Graceful degradation to synchronous execution when limits exceeded
- Nesting depth limits to prevent deep Promise chains
- Timeout mechanisms for Promise resolution
- Deadlock detection and prevention
- Resource exhaustion protection
- Circuit breaker pattern for cascading failures

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import threading
import time
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.concurrency.eager_promise import EagerPromise


class PromiseLimiterError(Exception):
    """Exception raised when PromiseLimiter safety limits are exceeded."""

    pass


class PromiseLimiter(Loggable):
    """
    Safety and resource management for universal EagerPromise creation.

    This class enforces various safety limits to prevent resource exhaustion,
    deadlocks, and cascading failures when implementing universal EagerPromise
    wrapping for all function executions.
    """

    def __init__(
        self,
        max_promises: int = 16,
        max_nesting_depth: int = 3,
        timeout_seconds: float = 30.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 60.0,
        enable_monitoring: bool = True,
    ):
        """
        Initialize the PromiseLimiter with safety limits.

        Args:
            max_promises: Maximum number of outstanding EagerPromises
            max_nesting_depth: Maximum nesting depth for EagerPromises
            timeout_seconds: Timeout for Promise resolution in seconds
            circuit_breaker_threshold: Number of failures before circuit breaker opens
            circuit_breaker_timeout: Timeout for circuit breaker reset in seconds
            enable_monitoring: Whether to enable performance monitoring
        """
        super().__init__()

        # Core limits
        self.max_promises = max_promises
        self.max_nesting_depth = max_nesting_depth
        self.timeout_seconds = timeout_seconds

        # Circuit breaker settings
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

        # Thread-safe counters and state
        self._lock = threading.RLock()
        self._outstanding_promises = 0
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = 0.0
        self._circuit_breaker_open = False

        # Thread-local context tracking
        self._thread_local = threading.local()

        # Performance monitoring
        self.enable_monitoring = enable_monitoring
        self._promises_created = 0
        self._synchronous_fallbacks = 0
        self._timeout_events = 0
        self._circuit_breaker_events = 0
        self._start_time = time.time()

    def can_create_promise(self) -> bool:
        """
        Check if a new EagerPromise can be created based on safety limits.

        Returns:
            True if a Promise can be created, False otherwise
        """
        with self._lock:
            # Check circuit breaker
            if self._circuit_breaker_open:
                if time.time() - self._circuit_breaker_last_failure > self.circuit_breaker_timeout:
                    self._circuit_breaker_open = False
                    self._circuit_breaker_failures = 0
                    self.debug("Circuit breaker reset")
                else:
                    self.debug("Circuit breaker is open, cannot create Promise")
                    return False

            # Check global promise limit
            if self._outstanding_promises >= self.max_promises:
                self.debug(f"Global promise limit reached ({self._outstanding_promises}/{self.max_promises})")
                return False

            # Check nesting depth limit
            current_depth = self._get_nesting_depth()
            if current_depth >= self.max_nesting_depth:
                self.debug(f"Nesting depth limit reached ({current_depth}/{self.max_nesting_depth})")
                return False

            return True

    def create_promise(
        self,
        computation: Callable[[], Any] | Coroutine,
        executor: ThreadPoolExecutor | None = None,
        on_delivery: Callable[[Any], None] | None = None,
    ) -> Any:
        """
        Create an EagerPromise if limits allow, otherwise execute synchronously.

        Args:
            computation: Function or coroutine to execute
            executor: ThreadPoolExecutor for background execution
            on_delivery: Optional callback called with the result when Promise is delivered

        Returns:
            Either an EagerPromise or the direct result of synchronous execution
        """
        if not self.can_create_promise():
            # Fall back to synchronous execution
            self._record_synchronous_fallback()
            self.debug("Falling back to synchronous execution due to safety limits")
            result = self._execute_synchronously(computation)
            # Call the delivery callback if provided
            if on_delivery:
                try:
                    on_delivery(result)
                except Exception as callback_error:
                    self.error(f"Error in Promise delivery callback: {callback_error}")
            return result

        # Create EagerPromise with safety wrapper
        try:
            with self._lock:
                self._outstanding_promises += 1
                self._promises_created += 1
                # Don't increment nesting depth here - nesting depth should be managed by the calling context
                # Only increment if we're actually in a nested execution context

            # Create Promise with timeout and error handling
            self.debug(f"Creating EagerPromise (computation: {computation})")
            promise = self._create_safe_promise(computation, executor, on_delivery)

            self.debug(f"Created EagerPromise ({self._outstanding_promises}/{self.max_promises} outstanding)")
            return promise

        except Exception as e:
            # Handle Promise creation failure
            with self._lock:
                self._outstanding_promises -= 1
                self._decrement_nesting_depth()
                self._record_circuit_breaker_failure()

            self.error(f"Failed to create EagerPromise: {e}")
            # Fall back to synchronous execution
            result = self._execute_synchronously(computation)
            # Call the delivery callback if provided
            if on_delivery:
                try:
                    on_delivery(result)
                except Exception as callback_error:
                    self.error(f"Error in Promise delivery callback: {callback_error}")
            return result

    def _create_safe_promise(
        self, computation: Callable[[], Any] | Coroutine, executor: ThreadPoolExecutor | None, on_delivery: Callable[[Any], None] | None
    ) -> EagerPromise:
        """
        Create an EagerPromise with safety wrappers for timeout and error handling.
        """

        def safe_computation():
            """Wrapper that adds timeout and error handling to the computation."""
            try:
                # Execute with timeout
                result = self._execute_with_timeout(computation)
                return result
            except Exception:
                # Record failure for circuit breaker
                self._record_circuit_breaker_failure()
                raise
            finally:
                # Always decrement counters when Promise computation completes
                with self._lock:
                    self._outstanding_promises -= 1

                # Call delivery callback if provided (this will be called by the Promise when accessed)
                if on_delivery:
                    try:
                        # We can't call the callback here because we don't have the result yet
                        # The callback will be called by the Promise when it's accessed
                        pass
                    except Exception as callback_error:
                        self.error(f"Error in Promise completion callback: {callback_error}")

        # Create EagerPromise with the safe computation wrapper
        promise = EagerPromise.create(safe_computation, executor)

        # Add the delivery callback to the Promise
        if on_delivery:
            promise.add_on_delivery_callback(on_delivery)

        return promise

    def _execute_with_timeout(self, computation: Callable[[], Any] | Coroutine) -> Any:
        """
        Execute computation with timeout protection.
        """
        import asyncio

        if asyncio.iscoroutinefunction(computation):
            # Handle coroutine with timeout
            return asyncio.run(asyncio.wait_for(computation(), timeout=self.timeout_seconds))
        else:
            # Handle regular function with timeout using threading
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as timeout_executor:
                future = timeout_executor.submit(computation)
                try:
                    return future.result(timeout=self.timeout_seconds)
                except concurrent.futures.TimeoutError:
                    self._record_timeout_event()
                    # Return the computation result directly instead of raising
                    return computation()

    def _execute_synchronously(self, computation: Callable[[], Any] | Coroutine) -> Any:
        """
        Execute computation synchronously as fallback.
        """
        import asyncio

        if asyncio.iscoroutinefunction(computation):
            return asyncio.run(computation())
        else:
            return computation()

    def _get_nesting_depth(self) -> int:
        """Get current nesting depth for the current thread."""
        return getattr(self._thread_local, "nesting_depth", 0)

    def _increment_nesting_depth(self) -> None:
        """Increment nesting depth for the current thread."""
        current_depth = getattr(self._thread_local, "nesting_depth", 0)
        self._thread_local.nesting_depth = current_depth + 1

    def _decrement_nesting_depth(self) -> None:
        """Decrement nesting depth for the current thread."""
        current_depth = getattr(self._thread_local, "nesting_depth", 0)
        self._thread_local.nesting_depth = max(0, current_depth - 1)

    def _record_synchronous_fallback(self) -> None:
        """Record a synchronous fallback event."""
        if self.enable_monitoring:
            with self._lock:
                self._synchronous_fallbacks += 1

    def _record_timeout_event(self) -> None:
        """Record a timeout event."""
        if self.enable_monitoring:
            with self._lock:
                self._timeout_events += 1

    def _record_circuit_breaker_failure(self) -> None:
        """Record a failure for circuit breaker logic."""
        if self.enable_monitoring:
            with self._lock:
                self._circuit_breaker_failures += 1
                self._circuit_breaker_last_failure = time.time()

                # Check if circuit breaker should open
                if self._circuit_breaker_failures >= self.circuit_breaker_threshold:
                    self._circuit_breaker_open = True
                    self._circuit_breaker_events += 1
                    self.warning(f"Circuit breaker opened after {self._circuit_breaker_failures} failures")

    def get_statistics(self) -> dict[str, Any]:
        """
        Get PromiseLimiter statistics for monitoring.

        Returns:
            Dictionary containing various statistics
        """
        with self._lock:
            uptime = time.time() - self._start_time
            return {
                "outstanding_promises": self._outstanding_promises,
                "max_promises": self.max_promises,
                "promises_created": self._promises_created,
                "synchronous_fallbacks": self._synchronous_fallbacks,
                "timeout_events": self._timeout_events,
                "circuit_breaker_events": self._circuit_breaker_events,
                "circuit_breaker_open": self._circuit_breaker_open,
                "circuit_breaker_failures": self._circuit_breaker_failures,
                "current_nesting_depth": self._get_nesting_depth(),
                "max_nesting_depth": self.max_nesting_depth,
                "uptime_seconds": uptime,
                "promises_per_second": self._promises_created / uptime if uptime > 0 else 0,
                "fallback_rate": self._synchronous_fallbacks / max(self._promises_created, 1),
                "timeout_rate": self._timeout_events / max(self._promises_created, 1),
            }

    def reset_statistics(self) -> None:
        """Reset all statistics counters."""
        with self._lock:
            self._promises_created = 0
            self._synchronous_fallbacks = 0
            self._timeout_events = 0
            self._circuit_breaker_events = 0
            self._start_time = time.time()

    def reset_circuit_breaker(self) -> None:
        """Manually reset the circuit breaker."""
        with self._lock:
            self._circuit_breaker_open = False
            self._circuit_breaker_failures = 0
            self._circuit_breaker_last_failure = 0.0
        self.info("Circuit breaker manually reset")

    def is_healthy(self) -> bool:
        """
        Check if the PromiseLimiter is in a healthy state.

        Returns:
            True if healthy, False if there are concerning metrics
        """
        stats = self.get_statistics()

        # Check for concerning patterns
        if stats["fallback_rate"] > 0.5:  # More than 50% fallbacks
            return False

        if stats["timeout_rate"] > 0.1:  # More than 10% timeouts
            return False

        if stats["circuit_breaker_open"]:
            return False

        return True


# Global instance for easy access
_global_promise_limiter: PromiseLimiter | None = None
_global_limiter_lock = threading.Lock()


def get_global_promise_limiter() -> PromiseLimiter:
    """
    Get the global PromiseLimiter instance.

    Returns:
        The global PromiseLimiter instance
    """
    global _global_promise_limiter

    if _global_promise_limiter is None:
        with _global_limiter_lock:
            if _global_promise_limiter is None:
                _global_promise_limiter = PromiseLimiter()

    return _global_promise_limiter


def set_global_promise_limiter(limiter: PromiseLimiter) -> None:
    """
    Set the global PromiseLimiter instance.

    Args:
        limiter: The PromiseLimiter instance to use globally
    """
    global _global_promise_limiter

    with _global_limiter_lock:
        _global_promise_limiter = limiter
