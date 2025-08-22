"""
Math functions for Dana standard library.

This module provides mathematical utility functions including:
- sum_range: Sum numbers in a range (inclusive)
- is_odd: Check if a number is odd
- is_even: Check if a number is even
- factorial: Calculate factorial of a number
"""

__all__ = ["py_sum_range", "py_is_odd", "py_is_even", "py_factorial"]

from dana.core.lang.sandbox_context import SandboxContext


def py_sum_range(
    context: SandboxContext,
    start: int,
    end: int,
) -> int:
    """Sum numbers in a range (inclusive).

    Args:
        context: The execution context
        start: Start of the range (inclusive)
        end: End of the range (inclusive)

    Returns:
        Sum of all numbers from start to end (inclusive)

    Examples:
        sum_range(1, 5) -> 15  # 1 + 2 + 3 + 4 + 5
        sum_range(0, 3) -> 6   # 0 + 1 + 2 + 3
    """
    if not isinstance(start, int) or not isinstance(end, int):
        raise TypeError("sum_range arguments must be integers")

    total = 0
    i = start
    while i <= end:
        total = total + i
        i = i + 1
    return total


def py_is_odd(
    context: SandboxContext,
    n: int,
) -> bool:
    """Check if a number is odd.

    Args:
        context: The execution context
        n: The number to check

    Returns:
        True if the number is odd, False otherwise

    Examples:
        is_odd(1) -> True
        is_odd(2) -> False
        is_odd(3) -> True
    """
    if not isinstance(n, int):
        raise TypeError("is_odd argument must be an integer")

    return n % 2 == 1


def py_is_even(
    context: SandboxContext,
    n: int,
) -> bool:
    """Check if a number is even.

    Args:
        context: The execution context
        n: The number to check

    Returns:
        True if the number is even, False otherwise

    Examples:
        is_even(0) -> True
        is_even(1) -> False
        is_even(2) -> True
    """
    if not isinstance(n, int):
        raise TypeError("is_even argument must be an integer")

    return n % 2 == 0


def py_factorial(
    context: SandboxContext,
    n: int,
) -> int:
    """Calculate factorial of a number.

    Args:
        context: The execution context
        n: The number to calculate factorial for

    Returns:
        The factorial of n (n!)

    Examples:
        factorial(0) -> 1
        factorial(1) -> 1
        factorial(5) -> 120
    """
    if not isinstance(n, int):
        raise TypeError("factorial argument must be an integer")

    if n < 0:
        raise ValueError("factorial argument must be non-negative")

    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
