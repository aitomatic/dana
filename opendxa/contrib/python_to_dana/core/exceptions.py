"""
Exception classes for Python-to-Dana Integration

Provides clear, specific exceptions for different types of failures
that can occur during Python-to-Dana calls.
"""


class DanaError(Exception):
    """Base exception for all Dana-related errors."""

    pass


class DanaCallError(DanaError):
    """Error during Dana function call execution."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class TypeConversionError(DanaError):
    """Error during type conversion between Python and Dana."""

    def __init__(self, message: str, python_type: type | None = None, dana_type: str | None = None):
        super().__init__(message)
        self.python_type = python_type
        self.dana_type = dana_type


class ResourceError(DanaError):
    """Error with resource management (LLM, etc.)."""

    pass


class SecurityError(DanaError):
    """Error related to sandbox security boundaries."""

    pass
