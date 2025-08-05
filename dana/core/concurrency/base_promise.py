"""
Abstract base Promise[T] class for Dana's promise system.

This module provides the abstract base class for all promise implementations,
defining the common interface and transparent proxy behavior.

Copyright © 2025 Aitomatic, Inc.
"""

import abc
from typing import Any

from dana.common.mixins.loggable import Loggable


class PromiseError(Exception):
    """Errors from promise resolution."""

    def __init__(self, original_error: Exception):
        self.original_error = original_error
        super().__init__(f"Promise error: {original_error}")


class BasePromise(Loggable, abc.ABC):
    """
    Abstract base class for Promise implementations.

    Provides the common interface and transparent proxy behavior for all
    promise types (lazy, eager, etc.). Subclasses must implement the
    abstract methods to define their specific execution strategy.
    """

    def __init__(self, computation):
        """
        Initialize a promise with a computation.

        Args:
            computation: Callable or coroutine that computes the value
        """
        super().__init__()
        self._computation = computation
        self._resolved = False
        self._result = None
        self._error = None

        # Safe metadata for display (never triggers resolution)
        self._promise_id = hex(id(self))
        self._promise_type = self.__class__.__name__

    @abc.abstractmethod
    def _ensure_resolved(self) -> Any:
        """
        Ensure the promise is resolved and return the result.

        This is the key method that differentiates promise types:
        - LazyPromise: Executes computation on first call
        - EagerPromise: Waits for already-started computation

        Must be implemented by subclasses.
        """
        pass

    def get_display_info(self) -> str:
        """
        Get safe display information about this Promise without triggering resolution.

        This method NEVER calls _ensure_resolved() and is safe to use in REPL
        display contexts where we want to show Promise info without blocking.

        Returns:
            str: Human-readable Promise information
        """
        status = "resolved" if self._resolved else "pending"

        # Get computation description if safely available
        comp_info = ""
        if hasattr(self._computation, "__name__"):
            comp_info = f" computing {self._computation.__name__}()"
        elif hasattr(self._computation, "__qualname__"):
            comp_info = f" computing {self._computation.__qualname__}()"

        return f"<{self._promise_type} {self._promise_id} {status}{comp_info}>"

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
        """Transparent string conversion - show resolved value."""
        # Check if Promise has an error
        if self._resolved and self._error:
            return str(self._error.original_error)

        return str(self._ensure_resolved())

    def __bool__(self):
        """Transparent boolean conversion."""
        return bool(self._ensure_resolved())

    def __len__(self):
        """Transparent length."""
        return len(self._ensure_resolved())

    def __iter__(self):
        """Transparent iteration."""
        return iter(self._ensure_resolved())

    def __contains__(self, item):
        """Transparent containment check."""
        return item in self._ensure_resolved()

    # === Arithmetic Operations ===
    def __add__(self, other):
        return self._ensure_resolved() + other

    def __radd__(self, other):
        return other + self._ensure_resolved()

    def __sub__(self, other):
        return self._ensure_resolved() - other

    def __rsub__(self, other):
        return other - self._ensure_resolved()

    def __mul__(self, other):
        return self._ensure_resolved() * other

    def __rmul__(self, other):
        return other * self._ensure_resolved()

    def __truediv__(self, other):
        return self._ensure_resolved() / other

    def __rtruediv__(self, other):
        return other / self._ensure_resolved()

    def __floordiv__(self, other):
        return self._ensure_resolved() // other

    def __rfloordiv__(self, other):
        return other // self._ensure_resolved()

    def __mod__(self, other):
        return self._ensure_resolved() % other

    def __rmod__(self, other):
        return other % self._ensure_resolved()

    def __pow__(self, other):
        return self._ensure_resolved() ** other

    def __rpow__(self, other):
        return other ** self._ensure_resolved()

    # === Comparison Operations ===
    def __eq__(self, other):
        return self._ensure_resolved() == other

    def __ne__(self, other):
        return self._ensure_resolved() != other

    def __lt__(self, other):
        return self._ensure_resolved() < other

    def __le__(self, other):
        return self._ensure_resolved() <= other

    def __gt__(self, other):
        return self._ensure_resolved() > other

    def __ge__(self, other):
        return self._ensure_resolved() >= other

    # === Bitwise Operations ===
    def __and__(self, other):
        return self._ensure_resolved() & other

    def __rand__(self, other):
        return other & self._ensure_resolved()

    def __or__(self, other):
        return self._ensure_resolved() | other

    def __ror__(self, other):
        return other | self._ensure_resolved()

    def __xor__(self, other):
        return self._ensure_resolved() ^ other

    def __rxor__(self, other):
        return other ^ self._ensure_resolved()

    # === Unary Operations ===
    def __neg__(self):
        return -self._ensure_resolved()

    def __pos__(self):
        return +self._ensure_resolved()

    def __abs__(self):
        return abs(self._ensure_resolved())

    def __invert__(self):
        return ~self._ensure_resolved()

    # === Type-related Operations ===
    def __hash__(self):
        """Make Promise hashable by using object identity."""
        return id(self)

    def __instancecheck__(self, cls):
        """Support isinstance() checks."""
        return isinstance(self._ensure_resolved(), cls)

    # === Promise Status and Async Methods ===
    def _get_final_result(self):
        """Helper to get result or raise error after resolution."""
        if self._error:
            raise self._error.original_error
        return self._result

    async def await_result(self):
        """
        Wait for promise to complete in async context.

        Generic async implementation that works for all promise types.

        Returns:
            The resolved result

        Raises:
            Original error if promise failed
        """
        # If already resolved, return immediately
        if self._resolved:
            return self._get_final_result()

        # Generic async strategy: run _ensure_resolved in thread pool
        import asyncio

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._ensure_resolved)

        return self._get_final_result()
