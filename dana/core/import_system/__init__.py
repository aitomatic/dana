"""
Dana Importing System

A unified importing system that provides consistent, Python-compatible import behavior
for Dana modules with proper lazy loading and circular import handling.

This module replaces the scattered importing logic across multiple modules with
a single, well-designed system that handles all fundamental import patterns.
"""

from .core.resolver import ModuleResolver
from .core.loader import ModuleLoader
from .core.registry import ModuleRegistry
from .core.lazy_loader import LazyLoader

from .patterns.absolute import AbsoluteImportHandler
from .patterns.relative import RelativeImportHandler
from .patterns.from_import import FromImportHandler
from .patterns.star_import import StarImportHandler

from .compatibility.python import PythonCompatibility
from .compatibility.dana import DanaCompatibility

from .utils.circular_detection import CircularImportDetector
from .utils.error_handling import ImportErrorHandler

__all__ = [
    # Core components
    "ModuleResolver",
    "ModuleLoader",
    "ModuleRegistry",
    "LazyLoader",

    # Pattern handlers
    "AbsoluteImportHandler",
    "RelativeImportHandler",
    "FromImportHandler",
    "StarImportHandler",

    # Compatibility
    "PythonCompatibility",
    "DanaCompatibility",

    # Utilities
    "CircularImportDetector",
    "ImportErrorHandler",
]



