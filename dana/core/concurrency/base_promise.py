"""
Abstract base Promise[T] class for Dana's promise system.

This module provides the abstract base class for all promise implementations,
defining the common interface and transparent proxy behavior.

Copyright © 2025 Aitomatic, Inc.
"""

import abc
import traceback

from dana.common.mixins.loggable import Loggable
from dana.core.lang.sandbox_context import SandboxContext


class PromiseError(Exception):
    """Errors from promise resolution with context preservation."""

    def __init__(self, original_error: Exception, creation_location: str, resolution_location: str):
        self.original_error = original_error
        self.creation_location = creation_location
        self.resolution_location = resolution_location
        super().__init__(f"Promise error: {original_error}")


class BasePromise(Loggable, abc.ABC):
    """
    Abstract base class for Promise implementations.

    Provides the common interface and transparent proxy behavior for all
    promise types (lazy, eager, etc.). Subclasses must implement the
    abstract methods to define their specific execution strategy.
    """

    def __init__(self, computation, context: SandboxContext):
        """
        Initialize a promise with a computation and context.

        Args:
            computation: Callable or coroutine that computes the value
            context: Execution context for the computation
        """
        super().__init__()
        self._computation = computation
        self._context = context
        self._resolved = False
        self._result = None
        self._error = None
        self._creation_location = self._get_creation_location()

    def _get_creation_location(self) -> str:
        """Get the location where this promise was created."""
        stack = traceback.extract_stack()
        # Skip Promise internal frames
        for frame in reversed(stack[:-3]):
            if not any(name in frame.filename for name in ["promise.py", "base_promise.py", "lazy_promise.py", "eager_promise.py"]):
                return f"{frame.filename}:{frame.lineno} in {frame.name}"
        return "unknown location"

    def _get_resolution_location(self) -> str:
        """Get the location where this promise is being resolved."""
        stack = traceback.extract_stack()
        for frame in reversed(stack[:-1]):
            if not any(name in frame.filename for name in ["promise.py", "base_promise.py", "lazy_promise.py", "eager_promise.py"]):
                return f"{frame.filename}:{frame.lineno} in {frame.name}"
        return "unknown location"

    @abc.abstractmethod
    def _ensure_resolved(self):
        """
        Ensure the promise is resolved and return the result.

        This is the key method that differentiates promise types:
        - LazyPromise: Executes computation on first call
        - EagerPromise: Waits for already-started computation

        Must be implemented by subclasses.
        """
        pass

    @abc.abstractmethod
    def _start_execution(self):
        """
        Start executing the computation.

        This method defines when and how the computation begins:
        - LazyPromise: Does nothing (defers until access)
        - EagerPromise: Starts execution immediately

        Must be implemented by subclasses.
        """
        pass

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

        result = self._ensure_resolved()
        return str(result)

    def __repr__(self):
        """Transparent representation."""
        if self._resolved:
            if self._error:
                return f"{self.__class__.__name__}[Error: {self._error.original_error}]"
            return repr(self._result)
        return f"{self.__class__.__name__}[<pending>]"

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

    def __instancecheck__(self, cls):
        """Support isinstance() checks."""
        result = self._ensure_resolved()
        return isinstance(result, cls)
