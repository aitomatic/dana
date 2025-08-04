"""
Text utility functions for Dana standard library.

This module provides text processing functions including:
- capitalize_words: Capitalize each word in the text
- title_case: Convert text to title case
"""

__all__ = ["py_capitalize_words", "py_title_case"]

from dana.core.lang.sandbox_context import SandboxContext


def py_capitalize_words(
    context: SandboxContext,
    text: str,
) -> str:
    """Capitalize each word in the text.

    Args:
        context: The execution context
        text: The text to capitalize

    Returns:
        Text with each word capitalized

    Examples:
        capitalize_words("hello world") -> "Hello World"
        capitalize_words("dana language") -> "Dana Language"
    """
    if not isinstance(text, str):
        raise TypeError("capitalize_words argument must be a string")

    return text.title()


def py_title_case(
    context: SandboxContext,
    text: str,
) -> str:
    """Convert text to title case.

    Args:
        context: The execution context
        text: The text to convert

    Returns:
        Text in title case

    Examples:
        title_case("hello world") -> "Hello World"
        title_case("dana language") -> "Dana Language"
    """
    if not isinstance(text, str):
        raise TypeError("title_case argument must be a string")

    return text.title()
