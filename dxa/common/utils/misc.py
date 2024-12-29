"""Miscellaneous utilities."""

from importlib import import_module
from typing import Type, Any

def get_class_by_name(class_path: str) -> Type[Any]:
    """Get class by its fully qualified name.
    
    Example:
        get_class_by_name("dxa.common.graph.traversal.Cursor")
    """
    module_path, class_name = class_path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, class_name) 