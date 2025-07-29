"""
Enhanced error context tracking for Dana interpreter.

This module provides comprehensive error context tracking including
file location, line numbers, and execution stack information.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExecutionLocation:
    """Represents a location in the execution stack."""

    filename: str | None = None
    line: int | None = None
    column: int | None = None
    function_name: str | None = None
    source_line: str | None = None

    def __str__(self) -> str:
        """Format location for display."""
        parts = []
        if self.filename:
            parts.append(f'File "{self.filename}"')
        if self.line is not None:
            parts.append(f"line {self.line}")
        if self.column is not None:
            parts.append(f"column {self.column}")
        if self.function_name:
            parts.append(f"in {self.function_name}")
        return ", ".join(parts) if parts else "unknown location"


@dataclass
class ErrorContext:
    """Enhanced error context with file and location tracking."""

    # Current execution location
    current_location: ExecutionLocation = field(default_factory=ExecutionLocation)

    # Stack of execution locations
    execution_stack: list[ExecutionLocation] = field(default_factory=list)

    # Current file being executed
    current_file: str | None = None

    # Source code cache for error display
    source_cache: dict[str, list[str]] = field(default_factory=dict)

    def push_location(self, location: ExecutionLocation) -> None:
        """Push a new location onto the execution stack."""
        self.execution_stack.append(location)
        self.current_location = location

    def pop_location(self) -> ExecutionLocation | None:
        """Pop the top location from the execution stack."""
        if self.execution_stack:
            location = self.execution_stack.pop()
            self.current_location = self.execution_stack[-1] if self.execution_stack else ExecutionLocation()
            return location
        return None

    def set_file(self, filename: str | Path) -> None:
        """Set the current file being executed."""
        self.current_file = str(filename)
        self.current_location.filename = self.current_file

    def load_source(self, filename: str) -> list[str] | None:
        """Load source file lines for error display."""
        if filename not in self.source_cache:
            try:
                path = Path(filename)
                if path.exists():
                    with open(path) as f:
                        self.source_cache[filename] = f.readlines()
                else:
                    return None
            except Exception:
                return None
        return self.source_cache.get(filename)

    def get_source_line(self, filename: str, line_num: int) -> str | None:
        """Get a specific source line."""
        lines = self.load_source(filename)
        if lines and 0 < line_num <= len(lines):
            return lines[line_num - 1].rstrip()
        return None

    def format_stack_trace(self) -> str:
        """Format the execution stack as a traceback."""
        if not self.execution_stack:
            return ""

        lines = ["Traceback (most recent call last):"]
        for loc in self.execution_stack:
            lines.append(f"  {loc}")
            if loc.filename and loc.line:
                source_line = self.get_source_line(loc.filename, loc.line)
                if source_line:
                    lines.append(f"    {source_line}")
                    if loc.column:
                        lines.append(f"    {' ' * (loc.column - 1)}^")
        return "\n".join(lines)
