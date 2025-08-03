"""
Eager Promise[T] wrapper system for Dana.

This module implements eager evaluation where Promise[T] starts executing
immediately upon creation, rather than waiting for first access.

Copyright © 2025 Aitomatic, Inc.
"""

import asyncio
import inspect
import threading
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Union

from dana.core.concurrency.base_promise import BasePromise, PromiseError
from dana.core.lang.sandbox_context import SandboxContext

# Shared thread pool for all EagerPromise instances to prevent deadlocks
_shared_executor = None
_executor_lock = threading.Lock()


def _get_shared_executor() -> ThreadPoolExecutor:
    """Get the shared thread pool executor for EagerPromise instances."""
    global _shared_executor
    if _shared_executor is None:
        with _executor_lock:
            if _shared_executor is None:
                _shared_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="EagerPromise")
    return _shared_executor


class EagerPromise(BasePromise):
    """
    Eager evaluation promise that starts execution immediately upon creation.

    Unlike the lazy Promise, EagerPromise begins executing its computation
    as soon as it's created, making it suitable for scenarios where you want
    to start async operations immediately.
    """

    def __init__(self, computation: Union[Callable[[], Any], Coroutine], context: SandboxContext):
        """
        Initialize an eager promise that starts execution immediately.

        Args:
            computation: Callable that returns the actual value, or coroutine
            context: Execution context for the computation
        """
        super().__init__(computation, context)
        self._task = None  # Store the asyncio task
        self._future = None  # Store the concurrent.futures.Future for sync execution
        self._lock = threading.Lock()
        self._delayed_coroutine = False

        # Start execution immediately
        self._start_execution()

    def _start_execution(self):
        """Start executing the computation immediately."""
        if inspect.iscoroutine(self._computation):
            # For coroutines, create an asyncio task
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._execute_async())
            except RuntimeError:
                # No running loop - for now, we'll delay execution until access
                # This prevents issues with REPL and other environments
                self.debug("No event loop available, delaying coroutine execution until access")
                self._delayed_coroutine = True
                return
        else:
            # For sync computations, execute immediately to avoid deadlocks
            # This is simpler and avoids the thread pool complexity
            try:
                self._result = self._computation()
                self._resolved = True
                self.debug(f"Eager promise resolved immediately: {type(self._result)}")
            except Exception as e:
                self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                self._resolved = True
                self.error(f"Eager promise immediate execution failed: {e}")

    async def _execute_async(self):
        """Execute the async computation."""
        with self._lock:
            if self._resolved:
                return

            try:
                self._result = await self._computation
                self._resolved = True
                self.debug(f"Eager promise resolved asynchronously: {type(self._result)}")
            except Exception as e:
                self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                self._resolved = True
                self.error(f"Eager promise async execution failed: {e}")

    def _execute_sync(self):
        """Execute the sync computation."""
        with self._lock:
            if self._resolved:
                return

            try:
                self._result = self._computation()
                self._resolved = True
                self.debug(f"Eager promise resolved synchronously: {type(self._result)}")
            except Exception as e:
                self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                self._resolved = True
                self.error(f"Eager promise sync execution failed: {e}")

    def _ensure_resolved(self):
        """Ensure the promise is resolved and return the result."""
        # If execution was somehow not started, start it now
        if not self._resolved and not self._task and not self._future and not hasattr(self, "_delayed_coroutine"):
            self.debug("Execution was not started, starting now")
            self._start_execution()

        # Handle delayed coroutine execution
        if hasattr(self, "_delayed_coroutine") and self._delayed_coroutine and not self._resolved:
            # Execute the coroutine now
            from dana.common.utils.misc import Misc

            try:
                Misc.safe_asyncio_run(self._execute_async())
            except Exception as e:
                self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                self._resolved = True
                raise self._error.original_error

        # If we have a task, wait for it
        if self._task and not self._resolved:
            try:
                # Check if task is done first
                if not self._task.done():
                    from dana.common.utils.misc import Misc

                    Misc.safe_asyncio_run(self._wait_for_task())
            except Exception:
                # Task might have completed in the meantime
                pass

        # Wait for sync computations (if using thread pool)
        if self._future and not self._resolved:
            try:
                # Get result from future (this will block if not done)
                self._future.result()
                # The _execute_sync method already set _result and _resolved
            except Exception:
                # Future might have completed with error
                pass

        # Spin wait for any remaining cases with timeout
        timeout_count = 0
        max_timeout = 5000  # 5 seconds (5000 * 0.001)
        while not self._resolved and timeout_count < max_timeout:
            threading.Event().wait(0.001)  # Small sleep to avoid busy waiting
            timeout_count += 1

        if not self._resolved:
            # If still not resolved after timeout, there's likely a deadlock
            error_msg = "EagerPromise timed out after 5 seconds. This suggests a deadlock or synchronization issue."
            self._error = PromiseError(RuntimeError(error_msg), self._creation_location, self._get_resolution_location())
            self._resolved = True

        if self._error:
            raise self._error.original_error
        return self._result

    async def _wait_for_task(self):
        """Wait for the async task to complete."""
        if self._task:
            await self._task

    # Override __str__ to show execution status for eager promises
    def __str__(self):
        """String representation showing EagerPromise meta info."""
        # Don't call _ensure_resolved() to avoid deadlocks
        if self._resolved:
            if self._error:
                return f"EagerPromise[Error: {self._error.original_error}]"
            else:
                return f"EagerPromise[{repr(self._result)}]"
        elif self._task or self._future:
            return "EagerPromise[<executing>]"
        else:
            return "EagerPromise[<pending>]"

    def __repr__(self):
        """Transparent representation."""
        if self._resolved:
            if self._error:
                return f"EagerPromise[Error: {self._error.original_error}]"
            return f"EagerPromise[{repr(self._result)}]"
        return "EagerPromise[<executing>]"

    @classmethod
    def create(cls, computation: Union[Callable[[], Any], Coroutine], context: SandboxContext) -> "EagerPromise":
        """
        Factory method to create a new EagerPromise[T].

        Args:
            computation: Callable that returns the actual value or coroutine
            context: Execution context

        Returns:
            EagerPromise[T] that executes immediately and blocks on access
        """
        return cls(computation, context)


def is_eager_promise(obj: Any) -> bool:
    """Check if an object is an EagerPromise."""
    return isinstance(obj, EagerPromise)
