"""
Decorator transformer for Dana language parsing.

This module provides specialized transformation for decorators and decorator-related constructs.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from lark import Tree

from dana.core.lang.ast import Decorator


class DecoratorTransformer:
    """Specialized transformer for decorator constructs."""

    def __init__(self, expression_transformer):
        """Initialize with expression transformer dependency."""
        self.expression_transformer = expression_transformer

    def transform_decorators(self, decorators_tree: Tree) -> list[Decorator]:
        """Transform decorators tree into list of Decorator nodes."""
        if hasattr(decorators_tree, "children"):
            return [self.transform_decorator(child) for child in decorators_tree.children if child is not None]
        return []

    def transform_decorator(self, decorator_tree: Any) -> Decorator:
        """Transform a single decorator tree into a Decorator node."""
        # If it's already a Decorator object, return it as-is
        if hasattr(decorator_tree, "name") and hasattr(decorator_tree, "args") and hasattr(decorator_tree, "kwargs"):
            return decorator_tree

        # Otherwise, transform it
        if hasattr(decorator_tree, "children"):
            return self.transform_decorator_from_items(decorator_tree.children)
        elif hasattr(decorator_tree, "data") and decorator_tree.data == "decorator":
            return self.transform_decorator_from_items(decorator_tree.children)
        else:
            # Handle direct items
            return self.transform_decorator_from_items([decorator_tree])

    def transform_decorator_from_items(self, items: list[Any]) -> Decorator:
        """Transform decorator items into a Decorator node."""
        from dana.core.lang.parser.transformer.statement.statement_utils import StatementTransformationUtils

        relevant_items = StatementTransformationUtils.filter_relevant_items(items)
        if not relevant_items:
            raise ValueError("decorator rule received empty relevant items list")

        # Based on raw parse tree: decorator -> @ NAME [arguments]
        # items[0] should be AT token (@)
        # items[1] should be NAME token (decorator name)
        # items[2] should be arguments (optional)

        # Skip the AT token and get the NAME token
        decorator_name = None
        arguments_tree = None

        for _, item in enumerate(relevant_items):
            if hasattr(item, "value") and item.value != "@":
                # This should be the decorator name
                decorator_name = item.value
            elif hasattr(item, "type") and item.type == "NAME":
                # This should be the decorator name
                decorator_name = str(item)
            elif hasattr(item, "data") and item.data == "arguments":
                # This should be the arguments
                arguments_tree = item

        if not decorator_name:
            raise ValueError("Could not find decorator name in items")

        # Check for arguments (optional)
        args = []
        kwargs = {}

        if arguments_tree:
            args, kwargs = self.parse_decorator_arguments(arguments_tree)

        return Decorator(name=decorator_name, args=args, kwargs=kwargs)

    def parse_decorator_arguments(self, arguments_tree: Tree) -> tuple[list[Any], dict[str, Any]]:
        """Parse decorator arguments into args and kwargs lists."""
        args = []
        kwargs = {}

        if hasattr(arguments_tree, "children"):
            for child in arguments_tree.children:
                if hasattr(child, "data") and child.data == "kw_arg":
                    # Keyword argument: name = value
                    if len(child.children) >= 2:
                        key_name = child.children[0].value if hasattr(child.children[0], "value") else str(child.children[0])
                        value_expr = self.expression_transformer.expression([child.children[1]])
                        kwargs[key_name] = value_expr
                else:
                    # Positional argument
                    arg_expr = self.expression_transformer.expression([child])
                    args.append(arg_expr)

        return args, kwargs
