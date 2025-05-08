"""Error handling system for DANA.

This module provides a unified error handling system that ensures consistent
error messages and proper error context preservation throughout the DANA runtime.
"""

from typing import Any, Optional


class ErrorContext:
    """Context information for error handling."""

    def __init__(self, operation: str, node: Optional[Any] = None):
        """Initialize error context.

        Args:
            operation: Description of the operation being performed
            node: Optional AST node where the error occurred
        """
        self.operation = operation
        self.node = node
        self.location = self._get_location(node) if node else None

    def _get_location(self, node: Any) -> Optional[str]:
        """Get formatted location information from a node.

        Args:
            node: AST node with location information

        Returns:
            Formatted location string or None if not available
        """
        if not hasattr(node, "location") or not node.location:
            return None
        line, column, source_text = node.location
        padding = " " * (column - 1)
        return f"{source_text}\n{padding}^"


class DanaError(Exception):
    """Base class for all DANA-related errors with unified formatting."""

    def __init__(self, message: str, original_error: Optional[Exception] = None, context: Optional[ErrorContext] = None):
        """Initialize a DANA error.

        Args:
            message: Primary error message
            original_error: Original exception that caused this error
            context: Additional context about where the error occurred
        """
        self.original_error = original_error
        self.context = context
        self.message = self._format_message(message, original_error, context)
        super().__init__(self.message)

    def _format_message(self, message: str, original_error: Optional[Exception], context: Optional[ErrorContext]) -> str:
        """Format the complete error message.

        Args:
            message: Primary error message
            original_error: Original exception
            context: Error context

        Returns:
            Formatted error message
        """
        parts = []

        # Add context information if available
        if context and context.location:
            parts.append(context.location)
        else:
            # Add the primary message only if we don't have location info
            parts.append(message)

        # Add original error information if available
        if original_error:
            if isinstance(original_error, DanaError):
                # If it's already a DanaError, just use its message
                parts.append(original_error.message)
            else:
                # For other errors, include the type and message
                parts.append(f"{type(original_error).__name__}: {str(original_error)}")

        return "\n".join(parts)


class ErrorHandler:
    """Handler for processing and formatting errors."""

    @staticmethod
    def handle_error(error: Exception, context: ErrorContext) -> DanaError:
        """Process an error and return a properly formatted DanaError.

        Args:
            error: The original exception
            context: Context about where the error occurred

        Returns:
            A properly formatted DanaError
        """
        if isinstance(error, DanaError):
            # If it's already a DanaError, just add the context
            if not error.context:
                error.context = context
            return error

        # Create a new DanaError with the original error and context
        return DanaError(message=f"Error during {context.operation}", original_error=error, context=context)


# Specific error types that extend DanaError
class RuntimeError(DanaError):
    """Error during program execution."""

    pass


class StateError(DanaError):
    """Error related to runtime state access."""

    pass


class ParseError(DanaError):
    """Error during program parsing."""

    pass


class ValidationError(DanaError):
    """Error during program validation."""

    pass


class InterpretError(DanaError):
    """Error during program interpretation."""

    pass
