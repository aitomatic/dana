"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Custom exceptions for the DANA module.
"""

from typing import Any, Optional


class DanaError(Exception):
    """Base class for all DANA-related errors with unified formatting."""

    def __init__(self, message: str, line: int = 0, source_line: str = ""):
        self.message = message
        self.line = line
        self.source_line = source_line
        super().__init__(self.message)


class ParseError(DanaError):
    """Error during DANA program parsing."""

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
    """Error during DANA program validation."""

    pass


class SandboxError(DanaError):
    """Error during DANA program execution."""

    pass


class DANAError(Exception):
    """Base class for exceptions in the DANA module."""

    pass


class LanguageError(DANAError):
    """Base class for errors related to program language (parsing, validation)."""

    pass


class ProgramParsingError(LanguageError):
    """Raised when a program string cannot be parsed into an AST."""

    pass


class ProgramValidationError(LanguageError):
    """Raised when a parsed program AST fails validation checks."""

    pass


class DANARuntimeError(DANAError):
    """Base class for errors occurring during program execution."""

    pass


class ProgramExecutionError(DANARuntimeError):
    """Raised for general errors during program execution by the interpreter."""

    pass


class ResourceNotFoundError(DANARuntimeError, KeyError):
    """Raised when a required resource (tool, LLM) is not found in the context."""

    pass


class InvalidStateKeyError(DANARuntimeError, ValueError):
    """Raised when an invalid key is used for context state access (format or scope)."""

    pass


class SandboxViolationError(DANARuntimeError):
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


# Base exceptions for DANA


class StateError(DanaError):
    """Error related to RuntimeContext state access."""

    pass


class InterpretError(DanaError):
    """Error during DANA program interpretation/execution."""

    pass


class TypeError(Exception):
    """Custom error for type checking in DANA."""

    def __init__(self, message: str, node: Optional[Any] = None):
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
    """Handles errors in DANA programs."""

    def __init__(self):
        self.errors = []

    def add_error(self, error: DanaError):
        self.errors.append(error)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def get_errors(self) -> list[DanaError]:
        return self.errors
