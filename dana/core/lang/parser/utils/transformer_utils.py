"""
Transformer utility functions for Dana language parsing.

This module provides common utilities for AST transformers,
including tree traversal and node manipulation functions.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from lark import Token, Tree

from dana.core.lang.ast import ASTNode


def get_leaf_node(item: Tree | Token | ASTNode) -> Token | ASTNode:
    """Recursively unwrap a Tree until an AST node or token is reached.

    Args:
        item: Tree, Token, or ASTNode to unwrap

    Returns:
        The leaf node (Token or ASTNode)
    """
    while hasattr(item, "children") and len(item.children) == 1:
        item = item.children[0]
    return item  # type: ignore


def flatten_items(items: list) -> list:
    """Recursively flatten lists and Tree nodes, returning a flat list of AST nodes or tokens.

    Useful for collection and statement flattening.

    Args:
        items: List of items to flatten

    Returns:
        Flattened list of AST nodes or tokens
    """
    flat = []
    for item in items:
        if isinstance(item, list):
            flat.extend(flatten_items(item))
        elif isinstance(item, Tree) and hasattr(item, "children"):
            flat.extend(flatten_items(item.children))
        elif item is not None:
            flat.append(item)
    return flat


def unwrap_single_child_tree(item: Any, stop_at: set[str] | None = None) -> Any:
    """Recursively unwrap single-child Tree nodes, stopping at rule names in stop_at.

    If stop_at is None, unwrap all single-child Trees.

    Args:
        item: Item to unwrap
        stop_at: Set of rule names to stop unwrapping at

    Returns:
        Unwrapped item
    """
    stop_at = stop_at or set()

    while isinstance(item, Tree) and len(item.children) == 1 and getattr(item, "data", None) not in stop_at:
        item = item.children[0]
    return item


def extract_token_value(item: Token | Tree | Any) -> Any:
    """Extract the value from a Token, Tree, or other item, converting to appropriate type.

    Args:
        item: Item to extract value from (Token, Tree, or other)

    Returns:
        The extracted value, converted to the appropriate type if possible
    """
    if isinstance(item, Token):
        value = item.value

        # Try to convert numeric values
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except (ValueError, TypeError):
            pass

        # Handle boolean and None values
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif value.lower() == "none":
            return None

        # Default: return as string
        return value
    elif isinstance(item, Tree) and item.children:
        # For Trees, try to extract from first child recursively
        return extract_token_value(item.children[0])
    else:
        return str(item)


def is_tree_with_data(item: Any, data_name: str) -> bool:
    """Check if an item is a Tree with specific data name.

    Args:
        item: Item to check
        data_name: Expected data name

    Returns:
        True if item is a Tree with the specified data name
    """
    return isinstance(item, Tree) and getattr(item, "data", None) == data_name


def get_tree_children_safe(item: Any) -> list:
    """Safely get children from a Tree, returning empty list if not a Tree.

    Args:
        item: Item to get children from

    Returns:
        List of children or empty list
    """
    if isinstance(item, Tree) and hasattr(item, "children"):
        return item.children
    return []


def extract_name_from_token_or_tree(item: Token | Tree | Any) -> str:
    """Extract a name/identifier from a Token, Tree, or AST node.

    Args:
        item: Item to extract name from

    Returns:
        Extracted name as string
    """
    if isinstance(item, Token):
        return item.value
    elif isinstance(item, Tree):
        # For Trees, recursively look for a name token
        for child in item.children:
            if isinstance(child, Token) and child.type == "NAME":
                return child.value
        # Fallback to first child
        if item.children:
            return extract_name_from_token_or_tree(item.children[0])
    elif hasattr(item, "name"):
        # AST nodes with name attribute
        name = item.name
        return name if isinstance(name, str) else str(name)

    # Fallback to string representation
    return str(item)
