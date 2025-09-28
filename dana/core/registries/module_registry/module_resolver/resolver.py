"""
Module Resolver for Dana importing system.

This module provides the ModuleResolver class for resolving module paths
to file system paths and determining appropriate loaders.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Union
from .path import ModulePath, parse_module_path, PathType, Language


class ModuleNotFoundError(Exception):
    """Raised when a module cannot be found."""
    pass


class InvalidPathError(Exception):
    """Raised when a module path is invalid."""
    pass


class LanguageMismatchError(Exception):
    """Raised when there's a language detection mismatch."""
    pass


class ModuleResolver:
    """
    Resolves module paths to file system paths and determines loaders.

    This class handles the resolution of module paths according to Dana's
    importing specification, supporting both Dana and Python modules.
    """

    def __init__(self, search_paths: Optional[List[str]] = None):
        """
        Initialize the module resolver.

        Args:
            search_paths: List of directories to search for modules.
                         If None, uses sys.path
        """
        self.search_paths = search_paths or sys.path.copy()

    def resolve(self, module_path: Union[str, ModulePath],
                current_module_path: Optional[str] = None) -> Tuple[str, str]:
        """
        Resolve a module path to a file system path and loader type.

        Args:
            module_path: The module path to resolve (string or ModulePath)
            current_module_path: Path of the current module (for relative resolution)

        Returns:
            Tuple of (file_path, loader_type) where:
            - file_path: Absolute file system path to the module
            - loader_type: Either 'dana' or 'python'

        Raises:
            ModuleNotFoundError: If the module cannot be found
            InvalidPathError: If the path syntax is invalid
        """
        # Parse the module path if it's a string
        if isinstance(module_path, str):
            try:
                parsed_path = parse_module_path(module_path)
            except ValueError as e:
                raise InvalidPathError(f"Invalid module path '{module_path}': {e}")
        else:
            parsed_path = module_path

        # Resolve the path based on its type
        if parsed_path.is_absolute:
            return self._resolve_absolute_path(parsed_path)
        elif parsed_path.is_relative or parsed_path.is_pure_dotted:
            return self._resolve_relative_path(parsed_path, current_module_path)
        else:
            raise InvalidPathError(f"Unknown path type: {parsed_path.path_type}")

    def _resolve_absolute_path(self, parsed_path: ModulePath) -> Tuple[str, str]:
        """Resolve an absolute module path."""
        # Build the file path
        file_path = parsed_path.to_file_path()

        # Search in each search path
        for search_path in self.search_paths:
            full_path = os.path.join(search_path, file_path)
            if os.path.exists(full_path):
                return os.path.abspath(full_path), parsed_path.language.value

        # If not found, raise error
        raise ModuleNotFoundError(f"Module '{parsed_path.original}' not found in search paths")

    def _resolve_relative_path(self, parsed_path: ModulePath,
                              current_module_path: Optional[str]) -> Tuple[str, str]:
        """Resolve a relative module path."""
        if current_module_path is None:
            raise InvalidPathError("Relative path requires current module path")

        # Get the directory of the current module
        current_dir = os.path.dirname(current_module_path)

        # Handle pure dotted paths
        if parsed_path.is_pure_dotted:
            # Navigate up the directory hierarchy
            target_dir = current_dir
            for _ in range(parsed_path.dots):
                target_dir = os.path.dirname(target_dir)

            # For pure dotted paths, we're looking for __init__ files
            if parsed_path.is_dana:
                init_file = os.path.join(target_dir, "__init__.na")
            else:  # Python
                init_file = os.path.join(target_dir, "__init__.py")

            if os.path.exists(init_file):
                return os.path.abspath(init_file), parsed_path.language.value
            else:
                raise ModuleNotFoundError(f"Package '{parsed_path.original}' not found")

        # Handle relative paths with segments
        # Navigate up the directory hierarchy
        target_dir = current_dir
        for _ in range(parsed_path.dots):
            target_dir = os.path.dirname(target_dir)

        # Build the file path
        file_path = parsed_path.to_file_path()
        # If the file path already contains parent directory navigation, use current_dir
        if file_path.startswith('../'):
            full_path = os.path.join(current_dir, file_path)
        else:
            full_path = os.path.join(target_dir, file_path)

        if os.path.exists(full_path):
            return os.path.abspath(full_path), parsed_path.language.value
        else:
            raise ModuleNotFoundError(f"Module '{parsed_path.original}' not found")

    def add_search_path(self, path: str) -> None:
        """Add a search path to the resolver."""
        if path not in self.search_paths:
            self.search_paths.append(path)

    def remove_search_path(self, path: str) -> None:
        """Remove a search path from the resolver."""
        if path in self.search_paths:
            self.search_paths.remove(path)

    def get_search_paths(self) -> List[str]:
        """Get the current search paths."""
        return self.search_paths.copy()

    def find_module(self, module_name: str,
                   current_module_path: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """
        Find a module without raising exceptions.

        Args:
            module_name: Name of the module to find
            current_module_path: Path of the current module

        Returns:
            Tuple of (file_path, loader_type) if found, None otherwise
        """
        try:
            return self.resolve(module_name, current_module_path)
        except (ModuleNotFoundError, InvalidPathError):
            return None


# Convenience functions
def resolve_module(module_path: str,
                  current_module_path: Optional[str] = None,
                  search_paths: Optional[List[str]] = None) -> Tuple[str, str]:
    """
    Convenience function to resolve a module path.

    Args:
        module_path: The module path to resolve
        current_module_path: Path of the current module
        search_paths: Optional search paths

    Returns:
        Tuple of (file_path, loader_type)
    """
    resolver = ModuleResolver(search_paths)
    return resolver.resolve(module_path, current_module_path)


def parse_and_validate_path(module_path: str) -> ModulePath:
    """
    Parse and validate a module path.

    Args:
        module_path: The module path to parse

    Returns:
        ModulePath object

    Raises:
        InvalidPathError: If the path is invalid
    """
    try:
        return parse_module_path(module_path)
    except ValueError as e:
        raise InvalidPathError(f"Invalid module path '{module_path}': {e}")
