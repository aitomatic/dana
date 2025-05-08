"""Error handling utilities for the DANA interpreter.

This module provides utilities for error handling and reporting during execution.
"""

from typing import Any, Optional, Tuple

from opendxa.dana.exceptions import RuntimeError, StateError


def format_error_location(node: Any) -> str:
    """Format location information for error messages.

    Args:
        node: An AST node that may have location information

    Returns:
        A formatted string with location information, or an empty string if not available
    """
    if not hasattr(node, "location") or not node.location:
        return ""
    line, column, source_text = node.location
    # Add padding to align the column indicator
    padding = " " * (column - 1)
    return f"\nAt line {line}, column {column}:\n{source_text}\n{padding}^"


def create_runtime_error(message: str, node: Any, original_error: Optional[Exception] = None) -> RuntimeError:
    """Create a RuntimeError with location information.

    Args:
        message: The error message
        node: The AST node where the error occurred
        original_error: The original exception, if any

    Returns:
        A RuntimeError with enhanced location information
    """
    error_msg = message + format_error_location(node)

    error = RuntimeError(error_msg)
    if original_error:
        # Set the __cause__ attribute directly
        error.__cause__ = original_error
    return error


def create_state_error(message: str, node: Any, original_error: Optional[Exception] = None) -> StateError:
    """Create a StateError with location information.

    Args:
        message: The error message
        node: The AST node where the error occurred
        original_error: The original exception, if any

    Returns:
        A StateError with enhanced location information
    """
    error_msg = message + format_error_location(node)

    error = StateError(error_msg)
    if original_error:
        # Set the __cause__ attribute directly
        error.__cause__ = original_error
    return error


def handle_execution_error(e: Exception, node: Any, operation: str) -> Tuple[Exception, bool]:
    """Handle an error during execution.

    Args:
        e: The exception that occurred
        node: The AST node being executed
        operation: Description of the operation being performed

    Returns:
        A tuple of (error, is_passthrough) where error is the potentially
        wrapped error and is_passthrough indicates if it should be re-raised as is
    """
    # If it's already a RuntimeError or StateError, just pass it through
    if isinstance(e, (RuntimeError, StateError)):
        return e, True

    # Create an appropriate error based on the exception type
    error_msg = f"Error {operation}: {type(e).__name__}: {e}"

    if isinstance(e, (ValueError, TypeError, KeyError, IndexError, AttributeError)):
        return create_state_error(error_msg, node, e), False
    else:
        return create_runtime_error(error_msg, node, e), False
