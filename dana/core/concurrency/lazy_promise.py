"""
Lazy Promise[T] implementation for Dana's dual delivery mechanism.

This module implements transparent lazy evaluation where Promise[T] appears as T
but executes computation only when accessed. Supports automatic parallelization
when multiple promises are accessed together.

Copyright © 2025 Aitomatic, Inc.
"""

import asyncio
import inspect
import threading
import weakref
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Union

from dana.core.concurrency.base_promise import BasePromise, PromiseError
from dana.core.lang.sandbox_context import SandboxContext


class PromiseGroup:
    """Manages parallel execution of multiple promises."""

    def __init__(self):
        self._promises: set[weakref.ref] = set()
        self._lock = threading.Lock()

    def add_promise(self, promise: "LazyPromise"):
        """Add a promise to this group for potential parallel execution."""
        with self._lock:
            self._promises.add(weakref.ref(promise))
            print(f"🟡 PromiseGroup: Added promise, total: {len(self._promises)}")

    def get_pending_promises(self) -> list["LazyPromise"]:
        """Get all pending promises in this group."""
        with self._lock:
            pending = []
            # Clean up dead references
            dead_refs = set()
            for ref in self._promises:
                promise = ref()
                if promise is None:
                    dead_refs.add(ref)
                elif not promise._resolved:
                    pending.append(promise)
            self._promises -= dead_refs
            if pending:
                print(f"🟡 PromiseGroup: Found {len(pending)} pending promises")
            return pending

    async def resolve_all_pending(self):
        """Resolve all pending promises in parallel."""
        pending = self.get_pending_promises()
        if len(pending) > 1:
            print(f"🟡 PromiseGroup: Resolving {len(pending)} promises in parallel")
            await asyncio.gather(*[p._resolve_async() for p in pending], return_exceptions=True)
            print("🟡 PromiseGroup: Parallel resolution completed")


# Global promise group for automatic parallelization
_current_promise_group = threading.local()


def get_current_promise_group() -> PromiseGroup:
    """Get or create the current promise group for this thread."""
    if not hasattr(_current_promise_group, "group"):
        _current_promise_group.group = PromiseGroup()
    return _current_promise_group.group


class LazyPromise(BasePromise):
    """
    Lazy promise that defers execution until first access.

    LazyPromise[T] is completely transparent to users - it appears as T in all operations
    and type annotations, but defers computation until first access. Supports automatic
    parallelization when multiple promises are accessed together.
    """

    def __init__(self, computation: Union[Callable[[], Any], Coroutine], context: SandboxContext):
        """
        Initialize a lazy promise with deferred execution.

        Args:
            computation: Callable that returns the actual value, or coroutine
            context: Execution context for the computation
        """
        super().__init__(computation, context)
        self._lock = threading.Lock()

        self.info(f"🟡 LazyPromise CREATED at {self._creation_location}")

        # Add to current promise group for potential parallelization
        get_current_promise_group().add_promise(self)

        # Start execution (for lazy promise, this does nothing)
        self._start_execution()

    def _start_execution(self):
        """Start execution - for lazy promises, this does nothing."""
        # Lazy promises don't start execution until accessed
        self.info("🟡 LazyPromise _start_execution: Deferring execution until access")
        self.debug("LazyPromise created - execution deferred until access")

    async def _resolve_async(self):
        """Resolve the promise asynchronously."""
        self.info("🟡 LazyPromise _resolve_async() called")
        if self._resolved:
            self.info("🟡 LazyPromise _resolve_async: Already resolved")
            return

        with self._lock:
            if self._resolved:  # Double-check after acquiring lock
                self.info("🟡 LazyPromise _resolve_async: Already resolved (double-check)")
                return

            self.info("🟡 LazyPromise _resolve_async: Starting resolution")
            try:
                if inspect.iscoroutine(self._computation):
                    self.info("🟡 LazyPromise _resolve_async: Async computation")
                    self._result = await self._computation
                else:
                    self.info("🟡 LazyPromise _resolve_async: Sync computation in thread pool")
                    # Run sync computation in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor() as executor:
                        self._result = await loop.run_in_executor(executor, self._computation)

                self._resolved = True
                self.info(f"🟡 LazyPromise _resolve_async: Resolution COMPLETED, result: {type(self._result)}")

            except Exception as e:
                self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                self._resolved = True
                self.info(f"🟡 LazyPromise _resolve_async: Resolution FAILED: {e}")
                self.error(f"Promise resolution failed: {e}")
                raise  # Re-raise the exception

    def _resolve_sync(self):
        """Resolve the promise synchronously."""
        self.info("🟡 LazyPromise _resolve_sync() called")
        if self._resolved:
            self.info("🟡 LazyPromise _resolve_sync: Already resolved")
            return

        with self._lock:
            if self._resolved:  # Double-check after acquiring lock
                self.info("🟡 LazyPromise _resolve_sync: Already resolved (double-check)")
                return

            self.info("🟡 LazyPromise _resolve_sync: Starting resolution")
            try:
                # Check if we need to resolve other promises in parallel first
                group = get_current_promise_group()
                pending = group.get_pending_promises()

                if len(pending) > 1:
                    self.info(f"🟡 LazyPromise _resolve_sync: {len(pending)} pending promises, checking for parallel resolution")
                    # Multiple promises need resolution - use async execution
                    loop = None
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        pass

                    if loop is not None:
                        # We're in an async context - create task for parallel resolution
                        self.info("🟡 LazyPromise _resolve_sync: Creating parallel resolution task")
                        asyncio.create_task(group.resolve_all_pending())
                        # Continue with sync resolution for now

                if inspect.iscoroutine(self._computation):
                    # Cannot resolve async computation synchronously
                    self.info("🟡 LazyPromise _resolve_sync: ERROR - Cannot resolve async computation in sync context")
                    raise RuntimeError("Cannot resolve async computation in sync context")
                else:
                    self.info("🟡 LazyPromise _resolve_sync: Executing sync computation")
                    self._result = self._computation()

                self._resolved = True
                self.info(f"🟡 LazyPromise _resolve_sync: Resolution COMPLETED, result: {type(self._result)}")

            except Exception as e:
                self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                self._resolved = True
                self.info(f"🟡 LazyPromise _resolve_sync: Resolution FAILED: {e}")
                self.error(f"Promise resolution failed: {e}")
                raise  # Re-raise the exception

    def _ensure_resolved(self):
        """Ensure the promise is resolved and return the result."""
        self.info(f"🟡 LazyPromise _ensure_resolved() called at {self._get_resolution_location()}")

        if self._resolved:
            if self._error:
                self.info(f"🟡 LazyPromise _ensure_resolved: Already resolved with ERROR: {self._error.original_error}")
                raise self._error.original_error
            self.info(f"🟡 LazyPromise _ensure_resolved: Already resolved with SUCCESS: {type(self._result)}")
            return self._result

        # Resolve the promise
        self.info("🟡 LazyPromise _ensure_resolved: Starting resolution")
        try:
            from dana.common.utils.misc import Misc

            if asyncio.iscoroutine(self._computation):
                # Async computation
                self.info("🟡 LazyPromise _ensure_resolved: Using async resolution")
                Misc.safe_asyncio_run(self._resolve_async)
            else:
                # Sync computation
                self.info("🟡 LazyPromise _ensure_resolved: Using sync resolution")
                self._resolve_sync()

            self._resolved = True
            self.info(f"🟡 LazyPromise _ensure_resolved: Resolution COMPLETED, result: {type(self._result)}")
            return self._result

        except Exception as e:
            self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
            self._resolved = True
            self.info(f"🟡 LazyPromise _ensure_resolved: Resolution FAILED: {e}")
            self.error(f"Promise resolution failed: {e}")
            raise self._error.original_error

    @classmethod
    def create(cls, computation: Union[Callable[[], Any], Coroutine], context: SandboxContext) -> "LazyPromise":
        """
        Factory method to create a new LazyPromise[T].

        Args:
            computation: Callable that returns the actual value or coroutine
            context: Execution context

        Returns:
            LazyPromise[T] that appears as T but executes lazily
        """
        return cls(computation, context)

    # LazyPromise uses the transparent __str__ from BasePromise
    # This means str(lazy_promise) resolves to the actual value, not meta info

    def __repr__(self):
        """Show meta representation without resolving the promise."""
        if self._resolved:
            if self._error:
                return f"LazyPromise[Error: {self._error.original_error}]"
            return f"LazyPromise[{repr(self._result)}]"
        return "LazyPromise[<pending>]"


def is_lazy_promise(obj: Any) -> bool:
    """Check if an object is a LazyPromise."""
    return isinstance(obj, LazyPromise)


def resolve_lazy_promise(promise: LazyPromise) -> Any:
    """Force resolution of a lazy promise and return the result."""
    return promise._ensure_resolved()
