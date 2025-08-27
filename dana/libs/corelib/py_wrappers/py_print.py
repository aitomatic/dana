"""
Print function for Dana standard library.

This module provides the print function for outputting values.
"""

__all__ = ["py_print"]

from dana.core.lang.sandbox_context import SandboxContext


def py_print(
    context: SandboxContext,
    *values,
    sep: str = " ",
    end: str = "\n",
) -> None:
    """Print values to stdout.

    Args:
        context: The execution context
        *values: Values to print
        sep: Separator between values (default: " ")
        end: String appended after the last value (default: "\n")

    Returns:
        None

    Examples:
        print("Hello world") -> prints "Hello world"
        print(1, 2, 3) -> prints "1 2 3"
        print("a", "b", sep="-") -> prints "a-b"
    """
    # Convert all values to strings and join with separator
    output = sep.join(str(value) for value in values)

    # Add to output buffer if available
    if hasattr(context, "_interpreter") and hasattr(context._interpreter, "_executor"):
        context._interpreter._executor._output_buffer.append(output + end.rstrip("\n"))  # type: ignore
        print(output, end=end, flush=True)
    else:
        # Print to stdout instead
        print(output, end=end, flush=True)
