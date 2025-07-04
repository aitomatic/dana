"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

String conversion function for Dana.
"""

from typing import Any

from dana.core.lang.sandbox_context import SandboxContext


def str_function(
    context: SandboxContext,
    value: Any,
    options: dict[str, Any] | None = None,
) -> str:
    """Convert a value to its string representation.

    Args:
        context: The execution context
        value: The value to convert to string
        options: Optional parameters (unused)

    Returns:
        String representation of the value

    Examples:
        str(42) -> "42"
        str(3.14) -> "3.14"
        str(True) -> "True"
        str([1, 2, 3]) -> "[1, 2, 3]"
    """
    try:
        return str(value)
    except Exception:
        # If conversion fails, return a safe representation
        return f"<{type(value).__name__} object>"
