"""
LazyPromise: On-demand execution with transparent access.

This module implements lazy evaluation where computation is deferred until
first access, then cached for subsequent use. Leverages BasePromise for
comprehensive transparency.

Copyright © 2025 Aitomatic, Inc.
"""

import asyncio
import inspect
import threading
from collections.abc import Callable, Coroutine
from typing import Any, Union

from dana.core.concurrency.base_promise import BasePromise, PromiseError


class LazyPromise(BasePromise):
    """
    LazyPromise with on-demand execution and transparent access.

    Design Philosophy:
    - Creation returns immediately (never blocks)
    - No execution until first access (lazy evaluation)
    - First access triggers execution and blocks until completion
    - Subsequent access returns cached result immediately

    This lazy design is ideal for computations that may not be needed,
    allowing programs to defer expensive operations until actually required.
    """

    def __init__(self, computation: Union[Callable[[], Any], Coroutine], context=None):
        """Initialize LazyPromise without starting execution.

        Args:
            computation: Function or coroutine to execute on demand
            context: Ignored for compatibility (LazyPromise doesn't need context)
        """
        super().__init__(computation)
        self._lock = threading.Lock()
        # LAZY: No immediate execution - deferred until first access

    def _ensure_resolved(self) -> Any:
        """
        LAZY strategy: Execute computation on first access, return cached result after.

        - If already resolved: return cached result immediately
        - If not resolved: execute computation now and cache result

        Returns:
            The resolved result

        Raises:
            Original error: If computation failed
        """
        with self._lock:
            if self._resolved:
                # Already computed - return cached result immediately
                if self._error:
                    raise self._error.original_error
                return self._result

            # First access - execute computation now
            try:
                result = self._computation()

                # Handle coroutines by running them
                if inspect.iscoroutine(result):
                    result = asyncio.run(result)

                # Cache the result
                self._result = result
                self._resolved = True
                return result

            except Exception as e:
                # Cache the error too
                self._error = PromiseError(e)
                self._resolved = True
                raise self._error.original_error

    @classmethod
    def create(cls, computation: Union[Callable[[], Any], Coroutine], context=None) -> "LazyPromise":
        """Factory method to create LazyPromise.

        Args:
            computation: Function or coroutine to execute on demand
            context: Ignored for compatibility (LazyPromise doesn't need context)
        """
        return cls(computation)


def is_lazy_promise(obj: Any) -> bool:
    """Check if object is LazyPromise."""
    return isinstance(obj, LazyPromise)


# Stub implementations for backward compatibility
class PromiseGroup:
    """Stub PromiseGroup for backward compatibility."""

    def get_pending_promises(self):
        return []


def get_current_promise_group():
    """Stub function for backward compatibility."""
    return PromiseGroup()


def resolve_lazy_promise(promise):
    """Stub function for backward compatibility."""
    if hasattr(promise, "_ensure_resolved"):
        return promise._ensure_resolved()
    return promise


# Global for test compatibility
_current_promise_group = PromiseGroup()
