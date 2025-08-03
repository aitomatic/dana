"""
Eager Promise[T] wrapper system for Dana.

This module implements eager evaluation where Promise[T] starts executing
immediately upon creation, rather than waiting for first access.

Copyright © 2025 Aitomatic, Inc.
"""

import asyncio
import inspect
import threading
import time
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

    def __init__(self, computation: Union[Callable[[], Any], Coroutine], context: SandboxContext, timeout_seconds: float = 10.0):
        """
        Initialize an eager promise that starts execution immediately.

        Args:
            computation: Callable that returns the actual value, or coroutine
            context: Execution context for the computation
            timeout_seconds: Timeout in seconds for async operations (default: 10.0)
        """
        super().__init__(computation, context)
        self._task = None  # Store the asyncio task
        self._future = None  # Store the concurrent.futures.Future for sync execution (legacy)
        self._lock = threading.Lock()
        self._timeout_seconds = timeout_seconds

        # Start execution immediately
        self._start_execution()

    def _start_execution(self):
        """Start executing the computation immediately."""
        if inspect.iscoroutine(self._computation):
            # For coroutines, check if we're in a running event loop
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()

                # CRITICAL FIX: Don't run LLM tasks on the main event loop
                # Use thread pool to prevent blocking prompt-toolkit
                async def run_in_thread():
                    """Run the coroutine in a separate thread to avoid blocking the main event loop."""
                    try:
                        # Create a new event loop in the thread and run the computation
                        import concurrent.futures

                        def thread_runner():
                            return asyncio.run(self._computation)

                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(thread_runner)
                            result = future.result()

                        with self._lock:
                            self._result = result
                            self._resolved = True
                            self.debug(f"Eager promise resolved in thread: {type(self._result)}")
                        return result
                    except Exception as e:
                        with self._lock:
                            self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                            self._resolved = True
                            self.error(f"Eager promise thread execution failed: {e}")
                        raise

                # Create task that runs in thread pool
                self._task = loop.create_task(run_in_thread())
                self.debug("Created async task using thread pool to avoid event loop blocking")

            except RuntimeError:
                # No running loop - execute immediately using asyncio.run()
                self.debug("No event loop available, executing immediately")
                self._execute_async_immediately()
        else:
            # For sync computations, wrap them as async tasks using run_in_executor
            # This prevents main-thread blocking while maintaining async compatibility
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()

                # We're in a running loop - wrap sync computation as async task
                async def sync_as_async():
                    try:
                        result = await loop.run_in_executor(_get_shared_executor(), self._computation)
                        with self._lock:
                            self._result = result
                            self._resolved = True
                        return result
                    except Exception as e:
                        with self._lock:
                            self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                            self._resolved = True
                        raise

                self._task = loop.create_task(sync_as_async())
                self.debug("Created async task for sync computation using run_in_executor")
            except RuntimeError:
                # No running loop - execute immediately (fallback for non-async contexts)
                self.debug("No event loop available, executing sync computation immediately")
                try:
                    self._result = self._computation()
                    self._resolved = True
                    self.debug(f"Eager promise resolved immediately: {type(self._result)}")
                except Exception as e:
                    self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                    self._resolved = True
                    self.error(f"Eager promise immediate execution failed: {e}")

    def _is_potential_async_deadlock(self, loop) -> bool:
        """Check if creating an async task might cause a deadlock."""
        # Check if there are already pending tasks that might depend on this one
        pending_tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]

        # If there are many pending tasks, there's a higher risk of deadlock
        if len(pending_tasks) > 10:
            self.debug(f"Many pending tasks ({len(pending_tasks)}), avoiding potential deadlock")
            return True

        # Check if we're in a nested async context
        current_task = asyncio.current_task(loop)
        if current_task and current_task in pending_tasks:
            # We're already in an async task, creating another might cause deadlock
            self.debug("Already in async task context, avoiding potential deadlock")
            return True

        return False

    def _execute_async_immediately(self):
        """Execute async computation immediately to avoid deadlocks."""
        try:
            import asyncio

            # This method should only be called when there's no running event loop
            # Check if we're in a running event loop (this should not happen)
            try:
                loop = asyncio.get_running_loop()
                # This shouldn't happen - we should have created a task instead
                self.error("Unexpected: _execute_async_immediately called with running event loop")
                self._task = loop.create_task(self._execute_async())
                return
            except RuntimeError:
                # No running loop, use asyncio.run()
                self._result = asyncio.run(self._computation)
                self._resolved = True
                self.debug(f"Eager promise async executed immediately: {type(self._result)}")
        except Exception as e:
            self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
            self._resolved = True
            self.error(f"Eager promise async immediate execution failed: {e}")

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
        """
        Ensure the promise is resolved before accessing the result.

        This method handles both sync and async contexts intelligently:
        - In sync context: Uses busy wait (legacy behavior)
        - In async context: Raises helpful error directing to await_result()
        """
        with self._lock:
            if self._resolved:
                if self._error:
                    raise self._error.original_error
                return self._result

        # Check if we're in an async context
        try:
            # If this succeeds, we're in a running event loop
            asyncio.get_running_loop()

            # We're in an async context - we should NOT block the event loop
            # The caller should use async methods instead
            if self._task and not self._task.done():
                # Async task is still running, don't block the event loop
                error_msg = (
                    "EagerPromise cannot be resolved synchronously in async context while task is executing.\n"
                    "SOLUTION: Use 'await promise.await_result()' instead of accessing .result directly.\n"
                    "This prevents blocking the prompt_toolkit event loop."
                )
                self.debug(f"Blocking sync resolution in async context: {error_msg}")
                raise RuntimeError(error_msg)
            elif not self._resolved:
                # No task but not resolved - something went wrong
                error_msg = (
                    "EagerPromise not resolved and no async task found.\n"
                    "SOLUTION: Use 'await promise.await_result()' for async-safe resolution."
                )
                self.debug(f"Promise not resolved in async context: {error_msg}")
                raise RuntimeError(error_msg)

        except RuntimeError as e:
            if "no running event loop" in str(e):
                # We're in sync context - use the original busy wait behavior
                self.debug("No event loop detected, using sync resolution")
                pass  # Continue to sync waiting below
            else:
                # Re-raise our custom RuntimeErrors with helpful messages
                raise

        # Legacy sync context handling - only reached if no event loop
        # Handle legacy sync futures (from old thread-based execution)
        if self._future and not self._future.done():
            try:
                # Wait for thread-based future to complete
                result = self._future.result(timeout=self._timeout_seconds)
                with self._lock:
                    self._result = result
                    self._resolved = True
                    return self._result
            except Exception:
                # Future might have completed with error
                pass

        # Final sync busy wait for any remaining cases (legacy compatibility)
        # Only reached in sync context without running event loop
        timeout_count = 0
        max_timeout = int(self._timeout_seconds * 1000)  # Convert to milliseconds
        self.debug(f"Starting sync busy wait with timeout {self._timeout_seconds}s")

        while not self._resolved and timeout_count < max_timeout:
            time.sleep(0.001)  # Small sleep to avoid busy waiting
            timeout_count += 1

        if not self._resolved:
            # If still not resolved after timeout, there's likely a deadlock
            error_msg = f"EagerPromise timed out after {self._timeout_seconds} seconds. This suggests a deadlock or synchronization issue."
            self.error(error_msg)
            self._error = PromiseError(RuntimeError(error_msg), self._creation_location, self._get_resolution_location())
            self._resolved = True

        if self._error:
            raise self._error.original_error
        return self._result

    async def _wait_for_task(self):
        """Wait for the async task to complete."""
        if self._task:
            await self._task

    async def await_result(self):
        """
        Safely await the EagerPromise result in async contexts.

        This is the recommended method for accessing EagerPromise results
        from within prompt_toolkit or other async contexts to avoid blocking
        the main event loop.

        Returns:
            The resolved value of the promise

        Raises:
            The original error if the promise failed
        """
        # If already resolved, return immediately
        with self._lock:
            if self._resolved:
                if self._error:
                    raise self._error.original_error
                return self._result

        # Wait for the task to complete if we have one
        if self._task:
            await self._task

        # Check again after waiting
        with self._lock:
            if self._resolved:
                if self._error:
                    raise self._error.original_error
                return self._result
            else:
                # This shouldn't happen, but handle gracefully
                raise RuntimeError("EagerPromise task completed but promise not resolved")

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
    def create(
        cls, computation: Union[Callable[[], Any], Coroutine], context: SandboxContext, timeout_seconds: float = 10.0
    ) -> "EagerPromise":
        """
        Factory method to create a new EagerPromise[T].

        Args:
            computation: Callable that returns the actual value or coroutine
            context: Execution context
            timeout_seconds: Timeout in seconds for async operations (default: 10.0)

        Returns:
            EagerPromise[T] that executes immediately and blocks on access
        """
        return cls(computation, context, timeout_seconds)


def is_eager_promise(obj: Any) -> bool:
    """Check if an object is an EagerPromise."""
    return isinstance(obj, EagerPromise)
