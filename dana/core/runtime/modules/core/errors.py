"""
Dana Dana Module System - Error Types

This module defines the error hierarchy for Dana's module system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModuleError(Exception):
    """Base class for all module-related errors."""

    message: str
    module_name: str | None = None
    file_path: str | Path | None = None
    line_number: int | None = None
    source_line: str | None = None

    def __str__(self) -> str:
        """Format the error message with context."""
        parts = [self.message]

        if self.module_name:
            parts.append(f"Module: {self.module_name}")

        if self.file_path:
            parts.append(f"File: {self.file_path}")

        if self.line_number is not None:
            parts.append(f"Line {self.line_number}")
            if self.source_line:
                parts.append(f"\n{self.source_line}")

        return " | ".join(parts)


class ModuleNotFoundError(ModuleError):
    """Raised when a module cannot be found during import."""

    def __init__(self, name: str, searched_paths: list[str] | None = None, message: str | None = None):
        self.searched_paths = searched_paths or []
        super().__init__(message or f"No module named '{name}'", module_name=name)


class ImportError(ModuleError):
    """Raised when there's an error importing a module."""

    pass


class CircularImportError(ImportError):
    """Raised when a circular import is detected."""

    def __init__(self, cycle: list[str]):
        self.cycle = cycle
        super().__init__(f"Circular import detected: {' -> '.join(cycle)}", module_name=cycle[0] if cycle else None)


class VersionError(ModuleError):
    """Raised when there's a version incompatibility."""

    def __init__(self, module_name: str, required_version: str, current_version: str):
        self.required_version = required_version
        self.current_version = current_version
        super().__init__(
            f"Version mismatch for module '{module_name}': requires {required_version}, but current version is {current_version}",
            module_name=module_name,
        )


class SyntaxError(ModuleError):
    """Raised when there's a syntax error in a module."""

    pass


class CompileError(ModuleError):
    """Raised when there's an error compiling a module."""

    pass


class LinkageError(ModuleError):
    """Raised when there's an error linking module dependencies."""

    pass


class SecurityError(ModuleError):
    """Raised when there's a security violation in module operations."""

    pass


class ResourceError(ModuleError):
    """Raised when there's an error accessing module resources."""

    pass
