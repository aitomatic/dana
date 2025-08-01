"""
Promise[T] wrapper system for Dana's dual delivery mechanism.

This module implements transparent lazy evaluation where Promise[T] appears as T
but executes computation only when accessed. Supports automatic parallelization
when multiple promises are accessed together.

Copyright © 2025 Aitomatic, Inc.
"""

import asyncio
import inspect
import threading
import traceback
import weakref
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Union

from dana.common.mixins.loggable import Loggable
from dana.core.lang.sandbox_context import SandboxContext


class PromiseError(Exception):
    """Errors from promise resolution with context preservation."""

    def __init__(self, original_error: Exception, creation_location: str, resolution_location: str):
        self.original_error = original_error
        self.creation_location = creation_location
        self.resolution_location = resolution_location
        super().__init__(f"Promise error: {original_error}")


class PromiseGroup:
    """Manages parallel execution of multiple promises."""

    def __init__(self):
        self._promises: set[weakref.ref] = set()
        self._lock = threading.Lock()

    def add_promise(self, promise: "Promise"):
        """Add a promise to this group for potential parallel execution."""
        with self._lock:
            self._promises.add(weakref.ref(promise))

    def get_pending_promises(self) -> list["Promise"]:
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
            return pending

    async def resolve_all_pending(self):
        """Resolve all pending promises in parallel."""
        pending = self.get_pending_promises()
        if len(pending) > 1:
            await asyncio.gather(*[p._resolve_async() for p in pending], return_exceptions=True)


# Global promise group for automatic parallelization
_current_promise_group = threading.local()


def get_current_promise_group() -> PromiseGroup:
    """Get or create the current promise group for this thread."""
    if not hasattr(_current_promise_group, "group"):
        _current_promise_group.group = PromiseGroup()
    return _current_promise_group.group


class Promise(Loggable):
    """
    Transparent wrapper that appears as T but executes lazily.

    Promise[T] is completely transparent to users - it appears as T in all operations
    and type annotations, but defers computation until first access.
    """

    def __init__(self, computation: Union[Callable[[], Any], Coroutine], context: SandboxContext):
        """
        Initialize a promise with a computation and context.

        Args:
            computation: Callable that returns the actual value, or coroutine
            context: Execution context for the computation
        """
        super().__init__()
        self._computation = computation
        self._context = context
        self._resolved = False
        self._result = None
        self._error = None

        # Debug logging
        self.debug(f"Promise created with computation: {type(computation)}")
        self.debug(f"Promise initial state: _resolved={self._resolved}, _result={self._result}")

        self._lock = threading.Lock()
        self._creation_location = self._get_creation_location()

        # Add to current promise group for potential parallelization
        get_current_promise_group().add_promise(self)

    def _get_creation_location(self) -> str:
        """Get the location where this promise was created."""
        stack = traceback.extract_stack()
        # Skip Promise internal frames
        for frame in reversed(stack[:-3]):
            if "promise.py" not in frame.filename:
                return f"{frame.filename}:{frame.lineno} in {frame.name}"
        return "unknown location"

    def _get_resolution_location(self) -> str:
        """Get the location where this promise is being resolved."""
        stack = traceback.extract_stack()
        for frame in reversed(stack[:-1]):
            if "promise.py" not in frame.filename:
                return f"{frame.filename}:{frame.lineno} in {frame.name}"
        return "unknown location"

    async def _resolve_async(self):
        """Resolve the promise asynchronously."""
        if self._resolved:
            return

        with self._lock:
            if self._resolved:  # Double-check after acquiring lock
                return

            try:
                if inspect.iscoroutine(self._computation):
                    self._result = await self._computation
                else:
                    # Run sync computation in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor() as executor:
                        self._result = await loop.run_in_executor(executor, self._computation)

                self._resolved = True
                self.debug(f"Promise resolved successfully: {type(self._result)}")

            except Exception as e:
                self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                self._resolved = True
                self.error(f"Promise resolution failed: {e}")

    def _resolve_sync(self):
        """Resolve the promise synchronously."""
        if self._resolved:
            self.debug("Promise already resolved in _resolve_sync")
            return

        with self._lock:
            if self._resolved:  # Double-check after acquiring lock
                self.debug("Promise already resolved in _resolve_sync (after lock)")
                return

            self.debug("Starting promise resolution in _resolve_sync")
            try:
                # Check if we need to resolve other promises in parallel first
                group = get_current_promise_group()
                pending = group.get_pending_promises()

                if len(pending) > 1:
                    self.debug(f"Found {len(pending)} pending promises")
                    # Multiple promises need resolution - use async execution
                    loop = None
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        pass

                    if loop is not None:
                        # We're in an async context - create task for parallel resolution
                        asyncio.create_task(group.resolve_all_pending())
                        # Continue with sync resolution for now

                self.debug("About to execute computation")
                if inspect.iscoroutine(self._computation):
                    # Cannot resolve async computation synchronously
                    raise RuntimeError("Cannot resolve async computation in sync context")
                else:
                    self.debug("Executing computation function")
                self._result = self._computation()
                self.debug(f"Computation result: {self._result}")

                self._resolved = True
                self.debug(f"Promise resolved synchronously: {type(self._result)}")

            except Exception as e:
                self._error = PromiseError(e, self._creation_location, self._get_resolution_location())
                self._resolved = True
                self.error(f"Promise resolution failed: {e}")

    def _ensure_resolved(self):
        """Ensure the promise is resolved, throwing any errors."""
        if not self._resolved:
            self.debug("Promise._ensure_resolved: Resolving promise")

            # Check if we have an async computation
            if inspect.iscoroutine(self._computation):
                self.debug("Promise._ensure_resolved: Using safe_asyncio_run for async computation")
                # Use safe_asyncio_run to handle async computations
                from dana.common.utils.misc import Misc

                Misc.safe_asyncio_run(self._resolve_async)
                # _resolve_async sets self._result and self._resolved
            else:
                self._resolve_sync()
        else:
            self.debug("Promise._ensure_resolved: Promise already resolved")

        if self._error:
            # Re-raise the original error for transparent error handling
            raise self._error.original_error

        return self._result

    # === Transparent Operations ===
    # Make Promise[T] behave exactly like T for all operations

    def __getattr__(self, name: str):
        """Transparent attribute access."""
        result = self._ensure_resolved()
        return getattr(result, name)

    def __getitem__(self, key):
        """Transparent indexing."""
        result = self._ensure_resolved()
        return result[key]

    def __setitem__(self, key, value):
        """Transparent item assignment."""
        result = self._ensure_resolved()
        result[key] = value

    def __call__(self, *args, **kwargs):
        """Transparent function call."""
        result = self._ensure_resolved()
        return result(*args, **kwargs)

    def __str__(self):
        """Transparent string conversion."""
        result = self._ensure_resolved()
        return str(result)

    def __repr__(self):
        """Transparent representation."""
        if self._resolved:
            if self._error:
                return f"Promise[Error: {self._error.original_error}]"
            return repr(self._result)
        return "Promise[<pending>]"

    def __bool__(self):
        """Transparent boolean conversion."""
        result = self._ensure_resolved()
        return bool(result)

    def __len__(self):
        """Transparent length."""
        result = self._ensure_resolved()
        return len(result)

    def __iter__(self):
        """Transparent iteration."""
        result = self._ensure_resolved()
        return iter(result)

    def __contains__(self, item):
        """Transparent containment check."""
        result = self._ensure_resolved()
        return item in result

    # === Arithmetic Operations ===
    def __add__(self, other):
        result = self._ensure_resolved()
        return result + other

    def __radd__(self, other):
        result = self._ensure_resolved()
        return other + result

    def __sub__(self, other):
        result = self._ensure_resolved()
        return result - other

    def __rsub__(self, other):
        result = self._ensure_resolved()
        return other - result

    def __mul__(self, other):
        result = self._ensure_resolved()
        return result * other

    def __rmul__(self, other):
        result = self._ensure_resolved()
        return other * result

    def __truediv__(self, other):
        result = self._ensure_resolved()
        return result / other

    def __rtruediv__(self, other):
        result = self._ensure_resolved()
        return other / result

    def __floordiv__(self, other):
        result = self._ensure_resolved()
        return result // other

    def __rfloordiv__(self, other):
        result = self._ensure_resolved()
        return other // result

    def __mod__(self, other):
        result = self._ensure_resolved()
        return result % other

    def __rmod__(self, other):
        result = self._ensure_resolved()
        return other % result

    def __pow__(self, other):
        result = self._ensure_resolved()
        return result**other

    def __rpow__(self, other):
        result = self._ensure_resolved()
        return other**result

    # === Comparison Operations ===
    def __eq__(self, other):
        result = self._ensure_resolved()
        return result == other

    def __ne__(self, other):
        result = self._ensure_resolved()
        return result != other

    def __lt__(self, other):
        result = self._ensure_resolved()
        return result < other

    def __le__(self, other):
        result = self._ensure_resolved()
        return result <= other

    def __gt__(self, other):
        result = self._ensure_resolved()
        return result > other

    def __ge__(self, other):
        result = self._ensure_resolved()
        return result >= other

    # === Bitwise Operations ===
    def __and__(self, other):
        result = self._ensure_resolved()
        return result & other

    def __rand__(self, other):
        result = self._ensure_resolved()
        return other & result

    def __or__(self, other):
        result = self._ensure_resolved()
        return result | other

    def __ror__(self, other):
        result = self._ensure_resolved()
        return other | result

    def __xor__(self, other):
        result = self._ensure_resolved()
        return result ^ other

    def __rxor__(self, other):
        result = self._ensure_resolved()
        return other ^ result

    # === Unary Operations ===
    def __neg__(self):
        result = self._ensure_resolved()
        return -result

    def __pos__(self):
        result = self._ensure_resolved()
        return +result

    def __abs__(self):
        result = self._ensure_resolved()
        return abs(result)

    def __invert__(self):
        result = self._ensure_resolved()
        return ~result

    # === Type-related Operations ===
    def __hash__(self):
        """Make Promise hashable by using object identity."""
        return id(self)

    def __class__(self):
        """Return the class of the resolved value for isinstance checks."""
        if self._resolved and not self._error:
            return self._result.__class__
        return Promise

    def __instancecheck__(self, cls):
        """Support isinstance() checks."""
        result = self._ensure_resolved()
        return isinstance(result, cls)


def create_promise(computation: Union[Callable[[], Any], Coroutine], context: SandboxContext) -> Promise:
    """
    Create a new Promise[T] wrapper.

    Args:
        computation: Callable that returns the actual value or coroutine
        context: Execution context

    Returns:
        Promise[T] that appears as T but executes lazily
    """
    return Promise(computation, context)


def is_promise(obj: Any) -> bool:
    """Check if an object is a Promise."""
    return isinstance(obj, Promise)


def resolve_promise(promise: Promise) -> Any:
    """Force resolution of a promise and return the result."""
    return promise._ensure_resolved()
