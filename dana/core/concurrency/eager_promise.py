"""
EagerPromise: Transparent concurrency through immediate background execution.

High-Level Design Behavior:
EagerPromise implements "eager" execution where computations begin immediately
upon promise creation, running in background threads while providing transparent
access semantics to the caller.

Key Characteristics:
- **Immediate Execution**: Computation starts in background thread upon creation
- **Transparent Access**: Promises behave like regular values - accessing them
  blocks if not ready, returns immediately if delivered
- **Multiple Access Patterns**: Supports sync blocking, async await, and status checking
- **Thread Safety**: All operations are thread-safe with internal locking
- **Error Transparency**: Background exceptions are captured and re-raised on access

This enables "fire-and-forget" concurrent programming where you can create promises
for expensive operations and continue other work, knowing that accessing the promise
later will seamlessly provide the result when needed.

Copyright © 2025 Aitomatic, Inc.
"""

import asyncio
import inspect
import threading
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Union

from dana.core.concurrency.base_promise import BasePromise, PromiseError


class EagerPromise(BasePromise):
    """
    EagerPromise with transparent concurrency through blocking-on-access.

    Design Philosophy:
    - Creation returns immediately (never blocks)
    - Background thread handles execution
    - Access before ready blocks until resolution (ensures transparency)
    - Access after ready returns result immediately

    This blocking-on-access design is intentional to provide transparent
    concurrency - users can work with promises as if they were regular
    values, and the system handles synchronization automatically.
    """

    def __init__(self, computation: Union[Callable[[], Any], Coroutine], executor: ThreadPoolExecutor):
        """Initialize EagerPromise with immediate background execution.

        Args:
            computation: Function or coroutine to execute
            executor: ThreadPoolExecutor for background execution
        """
        super().__init__(computation)
        self._lock = threading.Lock()
        self._executor = executor

        # EAGER: Start background execution immediately in constructor
        def background_runner():
            """Run computation in background thread."""
            try:
                result = self._computation()
                # Handle coroutines
                if inspect.iscoroutine(result):
                    result = asyncio.run(result)
                with self._lock:
                    self._result = result
                    self._delivered = True
                # Trigger callbacks after successful resolution
                self._trigger_on_delivery_callbacks(result)
            except Exception as e:
                with self._lock:
                    self._error = PromiseError(e)
                    self._delivered = True

        # Submit to thread pool - returns immediately (never blocks constructor)
        self._future = self._executor.submit(background_runner)

    def _wait_for_delivery(self) -> Any:
        """
        EAGER strategy: Block waiting for background thread, return cached result.

        - If already delivered: return cached result immediately
        - If not delivered: block until background thread completes

        Returns:
            The delivered result

        Raises:
            Error: If promise computation failed
        """
        with self._lock:
            if self._delivered:
                if self._error:
                    raise self._error.original_error
                return self._result

        # Block waiting for background thread to complete
        if self._future:
            self._future.result()  # This blocks until completion

            # Result should now be cached
            with self._lock:
                if self._delivered:
                    if self._error:
                        raise self._error.original_error
                    return self._result

        # Should not reach here
        raise RuntimeError("EagerPromise failed to be delivered.")

    @classmethod
    def create(cls, computation: Union[Callable[[], Any], Coroutine], executor: ThreadPoolExecutor | None = None) -> "EagerPromise":
        """Factory method to create EagerPromise.

        Args:
            computation: Function or coroutine to execute
            executor: ThreadPoolExecutor for background execution. If None, uses Dana's shared thread pool.
        """
        if executor is None:
            # Use Dana's shared thread pool
            from dana.core.runtime.dana_thread_pool import DanaThreadPool

            executor = DanaThreadPool.get_instance().get_executor()

        return cls(computation, executor)


def is_eager_promise(obj: Any) -> bool:
    """Check if object is EagerPromise."""
    return isinstance(obj, EagerPromise)
