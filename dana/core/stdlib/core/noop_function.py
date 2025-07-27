"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

No-operation (identity) function for Dana.
This function is useful for parallel function composition where an identity operation is needed.
"""

from typing import Any

from dana.core.lang.sandbox_context import SandboxContext


def noop_function(
    context: SandboxContext,
    value: Any,
) -> Any:
    """No-operation function that returns its input unchanged (identity function).

    This function is primarily used in function composition scenarios where
    an identity operation is needed, particularly for parallel composition:

    pipeline = noop | [func1, func2, func3]

    Args:
        context: The execution context
        value: The value to return unchanged

    Returns:
        The same value that was passed in

    Examples:
        noop(42) -> 42
        noop("hello") -> "hello"
        noop([1, 2, 3]) -> [1, 2, 3]

        # In parallel composition:
        pipeline = noop | [double, square]
        result = pipeline(5)  # Returns [10, 25]
    """
    return value
