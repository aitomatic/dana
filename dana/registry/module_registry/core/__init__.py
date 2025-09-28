"""
Core importing components.

This module contains the fundamental building blocks of the importing system:
- Module resolution logic
- Module loading and execution
- Module registry and caching
- Lazy loading mechanism
"""

from .resolver import ModuleResolver
from .loader import ModuleLoader
from .registry import ModuleRegistry
from .lazy_loader import LazyLoader

__all__ = [
    "ModuleResolver",
    "ModuleLoader",
    "ModuleRegistry",
    "LazyLoader",
]



