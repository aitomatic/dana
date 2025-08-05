"""
Promise[T] wrapper system for Dana's dual delivery mechanism - backward compatibility.

This module provides backward compatibility for the original promise.py module.
The actual implementation has been moved to dana.core.concurrency.

Copyright © 2025 Aitomatic, Inc.
"""

# Import everything from the new location for backward compatibility
from dana.core.concurrency.base_promise import PromiseError
from dana.core.concurrency.lazy_promise import (
    LazyPromise,
    PromiseGroup,
    get_current_promise_group,
    is_lazy_promise as is_promise,
    resolve_lazy_promise as resolve_promise,
)


# Re-export everything with LazyPromise names
__all__ = [
    "LazyPromise",
    "PromiseError",
    "PromiseGroup",
    "get_current_promise_group",
    "is_promise",
    "resolve_promise",
]
