"""
Utility functions for statement transformation.

This module provides shared utility functions used across statement transformers.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from lark import Token, Tree

from dana.core.lang.parser.utils.tree_utils import TreeTraverser


class StatementTransformationUtils:
    """Utility class containing shared statement transformation methods."""

    @staticmethod
    def filter_relevant_items(items: list[Any]) -> list[Any]:
        """
        Filter out irrelevant items from parse tree items.
        Removes None values, comment tokens, and other non-semantic elements.
        """
        relevant = []
        for item in items:
            # Skip None values (optional grammar elements that weren't present)
            if item is None:
                continue
            # Skip comment tokens
            if hasattr(item, "type") and item.type == "COMMENT":
                continue
            # Skip empty tokens or whitespace-only tokens
            if isinstance(item, Token) and (not item.value or item.value.isspace()):
                continue
            # Keep everything else
            relevant.append(item)
        return relevant

    @staticmethod
    def filter_body(items: list[Any]) -> list[Any]:
        """
        Utility to filter out Token and None from a list of items.
        Used to clean up statement bodies extracted from parse trees, removing indentation tokens and empty lines.
        """
        return [item for item in items if not (isinstance(item, Token) or item is None)]

    @staticmethod
    def transform_block(block: Any, statement_transformer) -> list[Any]:
        """Recursively transform a block (list, Tree, or node) into a flat list of AST nodes."""
        result = []
        if block is None:
            return result
        if isinstance(block, list):
            for item in block:
                result.extend(StatementTransformationUtils.transform_block(item, statement_transformer))
        elif isinstance(block, Tree):
            # If this is a block or statements node, flatten children
            if getattr(block, "data", None) in {"block", "statements"}:
                for child in block.children:
                    result.extend(StatementTransformationUtils.transform_block(child, statement_transformer))
            else:
                # Try to dispatch to a transformer method if available
                method = getattr(statement_transformer, block.data, None)
                if method:
                    transformed = method(block.children)
                    # If the result is a list, flatten it
                    if isinstance(transformed, list):
                        result.extend(transformed)
                    else:
                        result.append(transformed)
                else:
                    # Fallback: try with tree traverser
                    try:
                        tree_traverser = TreeTraverser()

                        def custom_transform(node):
                            if isinstance(node, Tree):
                                rule = getattr(node, "data", None)
                                if isinstance(rule, str) and hasattr(statement_transformer, rule):
                                    method = getattr(statement_transformer, rule)
                                    return method(node.children)
                            return node

                        transformed = tree_traverser.transform_tree(block, custom_transform)
                        if transformed is not block:
                            result.append(transformed)
                        else:
                            # Last resort: treat as leaf
                            result.append(block)
                    except Exception:
                        # Fallback: treat as leaf
                        result.append(block)
        else:
            result.append(block)
        return result

    @staticmethod
    def transform_item(item: Any, statement_transformer):
        """Transform a single item into an AST node."""
        # Use TreeTraverser to help with traversal
        if isinstance(item, Tree):
            # Try to use a specific method for this rule
            rule_name = getattr(item, "data", None)
            if isinstance(rule_name, str):
                method = getattr(statement_transformer, rule_name, None)
                if method:
                    return method(item.children)

            # If no specific method, fall back to expression transformer
            return statement_transformer.expression_transformer.expression([item])
        elif isinstance(item, list):
            result = []
            for subitem in item:
                transformed = StatementTransformationUtils.transform_item(subitem, statement_transformer)
                if transformed is not None:
                    result.append(transformed)
            return result
        else:
            # For basic tokens, use the expression transformer
            return statement_transformer.expression_transformer.expression([item])
