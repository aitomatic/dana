"""
Consolidated Promise detection and utility functions.

This module provides centralized utilities for Promise detection and handling
to reduce code duplication across the Dana codebase.

Copyright © 2025 Aitomatic, Inc.
"""

from typing import Any

from dana.core.concurrency.base_promise import BasePromise
from dana.core.concurrency.eager_promise import EagerPromise
from dana.core.concurrency.lazy_promise import LazyPromise


def is_promise(obj: Any) -> bool:
    """Check if object is any type of Promise.

    Args:
        obj: Object to check

    Returns:
        True if object is a Promise (BasePromise subclass)
    """
    return isinstance(obj, BasePromise)


def is_eager_promise(obj: Any) -> bool:
    """Check if object is EagerPromise.

    Args:
        obj: Object to check

    Returns:
        True if object is an EagerPromise
    """
    return isinstance(obj, EagerPromise)


def is_lazy_promise(obj: Any) -> bool:
    """Check if object is LazyPromise.

    Args:
        obj: Object to check

    Returns:
        True if object is a LazyPromise
    """
    return isinstance(obj, LazyPromise)


def resolve_promise(promise: BasePromise) -> Any:
    """Resolve a Promise to its value.

    Args:
        promise: Promise to resolve

    Returns:
        The resolved value

    Raises:
        Original error if Promise failed
    """
    if not is_promise(promise):
        raise TypeError(f"Expected Promise, got {type(promise)}")

    return promise._wait_for_delivery()


def resolve_if_promise(obj: Any) -> Any:
    """Resolve object if it's a Promise, otherwise return as-is.

    Args:
        obj: Object to potentially resolve

    Returns:
        Resolved value if Promise, otherwise original object
    """
    if is_promise(obj):
        return resolve_promise(obj)
    return obj
