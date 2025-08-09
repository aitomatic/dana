"""
No-op function for Dana standard library.

This module provides the noop function that returns exactly what was passed in.
"""

__all__ = ["py_noop"]

from dana.core.lang.sandbox_context import SandboxContext


def py_noop(
    context: SandboxContext,
    *args,
    **kwargs,
):
    """No-operation function that returns exactly what was passed in.

    This function accepts any arguments and returns them unchanged.
    If a single argument is passed, it returns that argument.
    If multiple arguments are passed, it returns a tuple of all arguments.
    Useful for testing, debugging, or as a pass-through function.

    Args:
        context: The execution context
        *args: Any positional arguments (returned unchanged)
        **kwargs: Any keyword arguments (ignored)

    Returns:
        The first argument if only one is provided, otherwise a tuple of all arguments

    Examples:
        noop(5) -> 5
        noop(1, 2, 3) -> (1, 2, 3)
        noop("hello") -> "hello"
    """
    if len(args) == 1:
        return args[0]
    elif len(args) > 1:
        return args
    else:
        return None
