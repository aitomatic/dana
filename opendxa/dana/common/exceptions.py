"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Custom exceptions for the Dana module.
"""

from typing import Any


class DanaError(Exception):
    """Base class for all Dana-related errors with unified formatting.

    This is the primary exception class for all Dana-related errors.
    It supports location information, error context, and original error chaining.
    """

    def __init__(
        self, message: str, line: int = 0, source_line: str = "", original_error: Exception | None = None, context: Any | None = None
    ):
        """Initialize a Dana error.

        Args:
            message: Primary error message
            line: Line number where error occurred (0 if unknown)
            source_line: Source code line where error occurred
            original_error: Original exception that caused this error
            context: Additional context about where the error occurred
        """
        self.message = message
        self.line = line
        self.source_line = source_line
        self.original_error = original_error
        self.context = context
        super().__init__(self.message)


class ParseError(DanaError):
    """Error during Dana program parsing."""

    def __init__(self, message: str, line_num: int | None = None, line_content: str | None = None):
        self.line_num = line_num
        self.line_content = line_content
        # Set self.line for compatibility with DanaError and tests
        line = line_num if line_num is not None else 0
        source_line = line_content or ""
        full_message = message
        if line_content is not None:
            # Find the position of the error in the line
            line_with_caret = line_content.rstrip()
            error_pos = 0

            if "=" in line_with_caret:
                # For assignment errors, point after the equals sign
                error_pos = line_with_caret.find("=") + 1
                # Skip any whitespace after the equals
                while error_pos < len(line_with_caret) and line_with_caret[error_pos].isspace():
                    error_pos += 1
            else:
                # For other errors, point to the end of the content
                error_pos = len(line_with_caret.strip())

            # Don't point into comments
            if "#" in line_with_caret:
                error_pos = min(error_pos, line_with_caret.index("#") - 1)

            # Insert the caret at the error position
            full_message = f"{full_message}\n{line_with_caret}\n{' ' * error_pos}^"
        super().__init__(full_message, line, source_line)

    def __len__(self) -> int:
        """Return 1 to indicate this is a single error."""
        return 1


class ValidationError(DanaError):
    """Error during Dana program validation."""

    pass


class SandboxError(DanaError):
    """Error during Dana program execution."""

    pass


class FunctionRegistryError(SandboxError):
    """Error related to function registry operations (registration, lookup, execution)."""

    def __init__(
        self,
        message: str,
        function_name: str = "",
        namespace: str = "",
        operation: str = "",
        calling_function: str = "",
        call_stack: list | None = None,
        **kwargs,
    ):
        """Initialize a function registry error.

        Args:
            message: Primary error message
            function_name: Name of the function involved in the error
            namespace: Namespace where the error occurred
            operation: Operation that failed (e.g., 'resolve', 'call', 'register')
            calling_function: Name of the function that was trying to call this function
            call_stack: List of function names in the call stack
            **kwargs: Additional arguments passed to parent DanaError
        """
        self.function_name = function_name
        self.namespace = namespace
        self.operation = operation
        self.calling_function = calling_function
        self.call_stack = call_stack or []

        # Enhance the message with context
        enhanced_message = message
        if calling_function:
            enhanced_message = f"{message} (called from '{calling_function}')"
        if call_stack and len(call_stack) > 1:
            stack_str = " -> ".join(call_stack)
            enhanced_message = f"{enhanced_message}\nCall stack: {stack_str}"

        super().__init__(enhanced_message, **kwargs)


class LanguageError(DanaError):
    """Base class for errors related to program language (parsing, validation)."""

    pass


class ProgramParsingError(LanguageError):
    """Raised when a program string cannot be parsed into an AST."""

    pass


class ProgramValidationError(LanguageError):
    """Raised when a parsed program AST fails validation checks."""

    pass


class DanaRuntimeError(DanaError):
    """Base class for errors occurring during program execution."""

    pass


class ProgramExecutionError(DanaRuntimeError):
    """Raised for general errors during program execution by the interpreter."""

    pass


class ResourceNotFoundError(DanaRuntimeError, KeyError):
    """Raised when a required resource (tool, LLM) is not found in the context."""

    pass


class InvalidStateKeyError(DanaRuntimeError, ValueError):
    """Raised when an invalid key is used for context state access (format or scope)."""

    pass


class SandboxViolationError(DanaRuntimeError):
    """Raised if an operation violates configured sandbox constraints."""

    pass


class TranscoderError(Exception):
    """Base class for errors during NL <-> Program conversion."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class CompilationError(TranscoderError):
    """Raised when the compiler (GMA) fails to generate a valid program."""

    pass


class NarrationError(TranscoderError):
    """Raised when the narrator fails to explain a program."""

    pass


class StateError(DanaError):
    """Error related to RuntimeContext state access."""

    pass


class InterpretError(DanaError):
    """Error during Dana program interpretation/execution."""

    pass


class TypeError(Exception):
    """Custom error for type checking in Dana."""

    def __init__(self, message: str, node: Any | None = None):
        self.message = message
        self.node = node
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.node:
            return f"{self.message} at {self.node}"
        return self.message


class KBError(DanaError):
    """Error related to Knowledge Base access or loading."""

    pass


# Moved from opendxa/dana/error_handling.py
class ErrorContext:
    """Context for error handling."""

    def __init__(self, message: str, line: int = 0, source_line: str = ""):
        self.message = message
        self.line = line
        self.source_line = source_line


class ErrorHandler:
    """Handles errors in Dana programs."""

    def __init__(self):
        self.errors = []

    def add_error(self, error: DanaError):
        self.errors.append(error)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def get_errors(self) -> list[DanaError]:
        return self.errors
