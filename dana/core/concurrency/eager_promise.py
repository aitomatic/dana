"""
Simple EagerPromise implementation for Dana.

Core Design Obligations:
1. NEVER block the caller
2. Auto-resolve in background
3. Provide clear access patterns

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


class EagerPromise(BasePromise):
    """
    Simple EagerPromise that never blocks the caller.

    Design:
    - Creation returns immediately
    - Background thread handles execution
    - Access before ready raises error
    - Access after ready returns result
    """

    def __init__(self, computation: Union[Callable[[], Any], Coroutine], context: SandboxContext, executor: ThreadPoolExecutor):
        """Initialize EagerPromise with immediate background execution.

        Args:
            computation: Function or coroutine to execute
            context: Execution context
            executor: ThreadPoolExecutor for background execution
        """
        super().__init__(computation, context)
        self._lock = threading.Lock()
        self._future = None
        self._executor = executor

        # Start background execution immediately
        self._start_execution()

    def _start_execution(self):
        """Start execution - calls background execution to fulfill abstract method."""
        self._start_background_execution()

    def _start_background_execution(self):
        """Start execution in background thread - never blocks caller."""

        def background_runner():
            """Run computation in background thread."""
            try:
                # Execute the computation
                result = self._computation()

                # If it's a coroutine, await it
                if inspect.iscoroutine(result):
                    result = asyncio.run(result)

                with self._lock:
                    self._result = result
                    self._resolved = True

            except Exception as e:
                with self._lock:
                    self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                    self._resolved = True

        # Submit to provided thread pool - returns immediately
        self._future = self._executor.submit(background_runner)

    def _ensure_resolved(self):
        """
        Ensure promise is resolved before accessing result.

        Returns:
            The resolved result if ready

        Raises:
            RuntimeError: If not ready yet
            Original error: If promise failed
        """
        with self._lock:
            if self._resolved:
                if self._error:
                    raise self._error.original_error
                return self._result

        # Not ready - wait for the background task to complete
        if self._future:
            # Block and wait for the task to complete
            self._future.result()  # This blocks until completion

            # Now check the result
            with self._lock:
                if self._resolved:
                    if self._error:
                        raise self._error.original_error
                    return self._result

        # Should not reach here, but just in case
        raise RuntimeError(f"EagerPromise failed to resolve.\nCreation location: {self._creation_location}")

    def is_ready(self) -> bool:
        """Check if promise is ready without blocking."""
        with self._lock:
            return self._resolved

    async def await_result(self):
        """
        Wait for promise to complete in async context.

        Returns:
            The resolved result

        Raises:
            Original error if promise failed
        """
        # If already resolved, return immediately
        with self._lock:
            if self._resolved:
                if self._error:
                    raise self._error.original_error
                return self._result

        # Wait for background completion
        if self._future:
            try:
                # Use run_in_executor to wait without blocking event loop
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._future.result)
            except Exception as e:
                # Check if error was recorded
                with self._lock:
                    if self._error:
                        raise self._error.original_error
                    else:
                        raise RuntimeError(f"EagerPromise failed: {e}")

        # Check result after waiting
        with self._lock:
            if self._resolved:
                if self._error:
                    raise self._error.original_error
                return self._result
            else:
                raise RuntimeError("EagerPromise task completed but not resolved")

    def __str__(self):
        """String representation showing status."""
        with self._lock:
            if self._resolved:
                if self._error:
                    return f"EagerPromise[Error: {self._error.original_error}]"
                return f"EagerPromise[{repr(self._result)}]"
            else:
                return "EagerPromise[<resolving>]"

    def __repr__(self):
        """Representation showing status."""
        with self._lock:
            if self._resolved:
                if self._error:
                    return f"EagerPromise[Error: {self._error.original_error}]"
                return f"EagerPromise[{repr(self._result)}]"
            return "EagerPromise[<resolving>]"

    @classmethod
    def create(
        cls, computation: Union[Callable[[], Any], Coroutine], context: SandboxContext, executor: ThreadPoolExecutor
    ) -> "EagerPromise":
        """Factory method to create EagerPromise.

        Args:
            computation: Function or coroutine to execute
            context: Execution context
            executor: ThreadPoolExecutor for background execution
        """
        return cls(computation, context, executor)


def is_eager_promise(obj: Any) -> bool:
    """Check if object is EagerPromise."""
    return isinstance(obj, EagerPromise)
