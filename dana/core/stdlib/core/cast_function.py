"""
Cast function for Dana - identity function that preserves type context.

This function is used to preserve type context in expressions like:
cast(TaskSignature, reason(prompt))

The actual type conversion is handled by Dana's POET system through
context detection and semantic coercion. This function just returns
the value as-is to maintain the type context.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any
from dana.core.lang.sandbox_context import SandboxContext


def cast_function(context: SandboxContext, target_type: Any, value: Any) -> Any:
    """
    Identity function that preserves type context for POET system.

    This function is used in expressions like `cast(TaskSignature, reason(prompt))`
    to preserve the type context so that Dana's POET system can automatically
    handle the type conversion through context detection and semantic coercion.

    Args:
        context: The execution context
        target_type: The target type (used by context detector)
        value: The value to return (usually from reason())

    Returns:
        The value as-is (identity function)
    """
    # DEBUG: Print information about the cast call
    print(f"DEBUG: cast() called with target_type: {target_type} (type: {type(target_type)})")
    print(f"DEBUG: cast() value type: {type(value)}")

    # If the value is a string (likely from reason()), set the context for POET system
    if isinstance(value, str) and isinstance(target_type, str):
        # Set the type context so that the POET system can detect it
        context.set("system:__current_assignment_type", target_type)
        print(f"DEBUG: cast() set context type to: {target_type}")

    # This is an identity function - just return the value
    # The POET system will handle the actual type conversion based on context
    return value
