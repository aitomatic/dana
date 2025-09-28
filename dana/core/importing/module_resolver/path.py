"""
Module Path representation and parsing.

This module provides the ModulePath class for representing and parsing
module paths according to Dana's importing specification.
"""

from enum import Enum
from typing import List, Optional, Union
from dataclasses import dataclass


class PathType(Enum):
    """Types of module paths."""
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    PURE_DOTTED = "pure_dotted"


class Language(Enum):
    """Module languages."""
    DANA = "dana"
    PYTHON = "python"


@dataclass
class ModulePath:
    """
    Represents a parsed module path with all its components.

    Attributes:
        path_type: Whether the path is absolute, relative, or pure dotted
        language: Whether the module is Dana or Python
        segments: List of path segments (excluding dots)
        dots: Number of parent directory navigations
        suffix: File suffix (.py for Python, None for Dana)
        original: Original path string
    """
    path_type: PathType
    language: Language
    segments: List[str]
    dots: int
    suffix: Optional[str]
    original: str

    def __post_init__(self):
        """Validate the module path after initialization."""
        if self.path_type == PathType.PURE_DOTTED and self.segments:
            raise ValueError("Pure dotted paths cannot have segments")
        if self.language == Language.PYTHON and not self.suffix:
            raise ValueError("Python modules must have .py suffix")
        if self.language == Language.DANA and self.suffix:
            raise ValueError("Dana modules cannot have .py suffix")

    @property
    def is_absolute(self) -> bool:
        """Check if this is an absolute path."""
        return self.path_type == PathType.ABSOLUTE

    @property
    def is_relative(self) -> bool:
        """Check if this is a relative path."""
        return self.path_type == PathType.RELATIVE

    @property
    def is_pure_dotted(self) -> bool:
        """Check if this is a pure dotted path."""
        return self.path_type == PathType.PURE_DOTTED

    @property
    def is_dana(self) -> bool:
        """Check if this is a Dana module."""
        return self.language == Language.DANA

    @property
    def is_python(self) -> bool:
        """Check if this is a Python module."""
        return self.language == Language.PYTHON

    @property
    def file_extension(self) -> str:
        """Get the file extension for this module."""
        if self.is_python:
            return ".py"
        return ".na"

    def to_file_path(self) -> str:
        """Convert to file system path."""
        if self.is_pure_dotted:
            # Pure dotted paths are special - they represent directory navigation
            # For Python pure dotted paths, we include the .py suffix
            if self.is_python:
                return "." * self.dots + ".py"
            else:
                return "." * self.dots

        # Build path from segments
        path_parts = self.segments.copy()

        # Add parent directory navigation
        if self.dots > 0:
            # For relative paths, dots represent parent directory navigation
            # But we need to handle the case where dots == 1 (current directory)
            if self.dots == 1:
                # Current directory - add ./ prefix
                path_parts = ["."] + path_parts
            else:
                # Parent directory navigation - add .. for dots > 1
                path_parts = [".."] * (self.dots - 1) + path_parts

        # Join and add extension
        if path_parts:
            return "/".join(path_parts) + self.file_extension
        else:
            return self.file_extension

    def __str__(self) -> str:
        """String representation of the module path."""
        return self.original

    def __repr__(self) -> str:
        """Detailed representation of the module path."""
        return (f"ModulePath(type={self.path_type.value}, "
                f"language={self.language.value}, "
                f"segments={self.segments}, "
                f"dots={self.dots}, "
                f"suffix={self.suffix})")


def parse_module_path(path: str) -> ModulePath:
    """
    Parse a module path string into a ModulePath object.

    Args:
        path: The module path string to parse

    Returns:
        ModulePath object representing the parsed path

    Raises:
        ValueError: If the path syntax is invalid
    """
    if not path:
        raise ValueError("Module path cannot be empty")

    # Handle pure dotted paths (only dots, possibly with language suffix)
    if path.startswith('.') and path == '.' * len(path):
        # Count consecutive dots at the beginning
        dots = 0
        for char in path:
            if char == '.':
                dots += 1
            else:
                break

        return ModulePath(
            path_type=PathType.PURE_DOTTED,
            language=Language.DANA,
            segments=[],
            dots=dots,
            suffix=None,
            original=path
        )

    # Handle Python pure dotted paths (dots + .py)
    if path.startswith('.') and path.endswith('.py') and path.count('.') >= 1 and path.count('.py') == 1:
        # Check if this is a pure dotted path by ensuring no alphanumeric characters between dots and .py
        dots_part = path[:path.rfind('.py')]
        if dots_part == '.' * len(dots_part):
            # Count consecutive dots at the beginning (excluding the .py suffix)
            dots = len(dots_part)

            return ModulePath(
                path_type=PathType.PURE_DOTTED,
                language=Language.PYTHON,
                segments=[],
                dots=dots,
                suffix='.py',
                original=path
            )

    # Handle relative paths (start with dots but have segments)
    if path.startswith('.'):
        # Count consecutive dots at the beginning
        dots = 0
        for char in path:
            if char == '.':
                dots += 1
            else:
                break

        # Parse the remaining path
        remaining = path[dots:]
        if not remaining:
            raise ValueError(f"Invalid relative path: {path}")

        # Check for language suffix
        if remaining.endswith('.py'):
            language = Language.PYTHON
            suffix = '.py'
            # Remove .py suffix to get segments
            path_without_suffix = remaining[:-3]
        else:
            language = Language.DANA
            suffix = None
            path_without_suffix = remaining

        # Split into segments
        if path_without_suffix:
            segments = path_without_suffix.split('.')
        else:
            segments = []

        return ModulePath(
            path_type=PathType.RELATIVE,
            language=language,
            segments=segments,
            dots=dots,
            suffix=suffix,
            original=path
        )

    # Handle absolute paths
    # Check for language suffix
    if path.endswith('.py'):
        language = Language.PYTHON
        suffix = '.py'
        # Remove .py suffix to get segments
        path_without_suffix = path[:-3]
    else:
        language = Language.DANA
        suffix = None
        path_without_suffix = path

    # Split into segments
    if path_without_suffix:
        segments = path_without_suffix.split('.')
    else:
        segments = []

    return ModulePath(
        path_type=PathType.ABSOLUTE,
        language=language,
        segments=segments,
        dots=0,
        suffix=suffix,
        original=path
    )
