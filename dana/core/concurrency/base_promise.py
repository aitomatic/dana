"""
Abstract base Promise[T] class for Dana's promise system.

This module provides the abstract base class for all promise implementations,
defining the common interface and transparent proxy behavior.

Copyright © 2025 Aitomatic, Inc.
"""

import abc
from collections.abc import Callable
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
        self._delivered = False
        self._result = None
        self._error = None

        # Callback facility for on_delivery handlers
        self._on_delivery_callbacks: list[Callable[[Any], None]] = []

        # Safe metadata for display (never triggers resolution)
        self._promise_id = hex(id(self))
        self._promise_type = self.__class__.__name__

    @abc.abstractmethod
    def _wait_for_delivery(self) -> Any:
        """
        Ensure the promise has been delivered and return the result.

        This is the key method that differentiates promise types:
        - LazyPromise: Executes computation on first call
        - EagerPromise: Waits for already-started computation

        Must be implemented by subclasses.
        """
        pass

    def add_on_delivery_callback(self, callback: Callable[[Any], None]) -> None:
        """
        Add a callback to be executed when the Promise is delivered.

        If the Promise is already delivered, the callback is called immediately.

        Args:
            callback: Function to call with the delivered value when Promise is delivered
        """
        self._on_delivery_callbacks.append(callback)

        # If Promise is already delivered, call the callback immediately
        if self._delivered and not self._error:
            try:
                callback(self._result)
            except Exception as e:
                # Log callback errors but don't let them prevent Promise delivery
                self.logger.warning(f"Error in on_delivery callback: {e}")

    def remove_on_delivery_callback(self, callback: Callable[[Any], None]) -> bool:
        """
        Remove a callback from the delivered callbacks list.

        Args:
            callback: Function to remove from callbacks

        Returns:
            True if callback was found and removed, False otherwise
        """
        try:
            self._on_delivery_callbacks.remove(callback)
            return True
        except ValueError:
            return False

    def _trigger_on_delivery_callbacks(self, result: Any) -> None:
        """
        Trigger all on_delivery callbacks with the delivered value.

        This method should be called by subclasses when the Promise is delivered.

        Args:
            result: The delivered value to pass to callbacks
        """
        for callback in self._on_delivery_callbacks:
            try:
                callback(result)
            except Exception as e:
                # Log callback errors but don't let them prevent Promise delivery
                self.logger.warning(f"Error in on_delivery callback: {e}")

    def get_display_info(self) -> str:
        """
        Get safe display information about this Promise without triggering resolution.

        This method NEVER calls _wait_for_delivery() and is safe to use in REPL
        display contexts where we want to show Promise info without blocking.

        Returns:
            str: Human-readable Promise information
        """
        status = "delivered" if self._delivered else "pending"

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
        result = self._wait_for_delivery()
        return getattr(result, name)

    def __getitem__(self, key):
        """Transparent indexing."""
        result = self._wait_for_delivery()
        return result[key]

    def __setitem__(self, key, value):
        """Transparent item assignment."""
        result = self._wait_for_delivery()
        result[key] = value

    def __call__(self, *args, **kwargs):
        """Transparent function call."""
        result = self._wait_for_delivery()
        return result(*args, **kwargs)

    def __str__(self):
        """Transparent string conversion - show resolved value."""
        # Check if Promise has an error
        if self._delivered and self._error:
            return str(self._error)

        return str(self._wait_for_delivery())

    def __bool__(self):
        """Transparent boolean conversion."""
        return bool(self._wait_for_delivery())

    def __len__(self):
        """Transparent length."""
        return len(self._wait_for_delivery())

    def __iter__(self):
        """Transparent iteration."""
        return iter(self._wait_for_delivery())

    def __contains__(self, item):
        """Transparent containment check."""
        return item in self._wait_for_delivery()

    # === Arithmetic Operations ===
    def __add__(self, other):
        return self._wait_for_delivery() + other

    def __radd__(self, other):
        return other + self._wait_for_delivery()

    def __sub__(self, other):
        return self._wait_for_delivery() - other

    def __rsub__(self, other):
        return other - self._wait_for_delivery()

    def __mul__(self, other):
        return self._wait_for_delivery() * other

    def __rmul__(self, other):
        return other * self._wait_for_delivery()

    def __truediv__(self, other):
        return self._wait_for_delivery() / other

    def __rtruediv__(self, other):
        return other / self._wait_for_delivery()

    def __floordiv__(self, other):
        return self._wait_for_delivery() // other

    def __rfloordiv__(self, other):
        return other // self._wait_for_delivery()

    def __mod__(self, other):
        return self._wait_for_delivery() % other

    def __rmod__(self, other):
        return other % self._wait_for_delivery()

    def __pow__(self, other):
        return self._wait_for_delivery() ** other

    def __rpow__(self, other):
        return other ** self._wait_for_delivery()

    # === Comparison Operations ===
    def __eq__(self, other):
        return self._wait_for_delivery() == other

    def __ne__(self, other):
        return self._wait_for_delivery() != other

    def __lt__(self, other):
        return self._wait_for_delivery() < other

    def __le__(self, other):
        return self._wait_for_delivery() <= other

    def __gt__(self, other):
        return self._wait_for_delivery() > other

    def __ge__(self, other):
        return self._wait_for_delivery() >= other

    # === Bitwise Operations ===
    def __and__(self, other):
        return self._wait_for_delivery() & other

    def __rand__(self, other):
        return other & self._wait_for_delivery()

    def __or__(self, other):
        return self._wait_for_delivery() | other

    def __ror__(self, other):
        return other | self._wait_for_delivery()

    def __xor__(self, other):
        return self._wait_for_delivery() ^ other

    def __rxor__(self, other):
        return other ^ self._wait_for_delivery()

    # === Unary Operations ===
    def __neg__(self):
        return -self._wait_for_delivery()

    def __pos__(self):
        return +self._wait_for_delivery()

    def __abs__(self):
        return abs(self._wait_for_delivery())

    def __invert__(self):
        return ~self._wait_for_delivery()

    # === Type-related Operations ===
    def __hash__(self):
        """Make Promise hashable by using object identity."""
        return id(self)

    def __instancecheck__(self, cls):
        """Support isinstance() checks."""
        return isinstance(self._wait_for_delivery(), cls)

    # === Promise Status and Async Methods ===
    def _get_final_result(self):
        """Helper to get result or raise error after resolution."""
        if self._error:
            raise self._error
        return self._result

    async def await_result(self):
        """
        Wait for promise to complete in async context.

        Generic async implementation that works for all promise types.

        Returns:
            The delivered result

        Raises:
            Original error if promise failed
        """
        # If already delivered, return immediately
        if self._delivered:
            return self._get_final_result()

        # Generic async strategy: run _wait_for_delivery in thread pool
        import asyncio

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._wait_for_delivery)

        return self._get_final_result()
