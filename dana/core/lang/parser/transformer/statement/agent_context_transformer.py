"""
Agent and context transformer for Dana language parsing.

This module handles all agent and context statement transformations, including:
- Agent statements (agent())
- Use statements (use())
- With statements and context managers
- Mixed arguments and keyword arguments

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import cast

from lark import Token, Tree

from dana.core.lang.ast import (
    Expression,
    Identifier,
    WithStatement,
)
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer


class AgentContextTransformer(BaseTransformer):
    """
    Handles agent and context statement transformations for the Dana language.
    Converts agent/context parse trees into corresponding AST nodes.
    """

    def __init__(self, main_transformer):
        """Initialize with reference to main transformer for shared utilities."""
        super().__init__()
        self.main_transformer = main_transformer
        self.expression_transformer = main_transformer.expression_transformer

    # === Agent Statements ===

    # === Context Management (With Statements) ===

    def mixed_arguments(self, items):
        """Transform mixed_arguments rule into a structured list."""
        # items is a list of with_arg items
        return items

    def with_arg(self, items):
        """Transform with_arg rule - pass through the child (either kw_arg or expr)."""
        # items[0] is either a kw_arg Tree or an expression
        return items[0]

    def with_context_manager(self, items):
        """Transform with_context_manager rule - pass through the expression."""
        return self.expression_transformer.expression(items)

    def with_stmt(self, items):
        """Transform a with statement rule into a WithStatement node."""

        # Filter out None items
        filtered_items = [item for item in items if item is not None]

        # Initialize variables
        context_manager: str | Expression | None = None
        args = []
        kwargs = {}

        # First item is either a Token (NAME/USE), an Expression, or an Identifier
        first_item = filtered_items[0]

        # Handle direct expression case
        if isinstance(first_item, Tree) and first_item.data == "with_context_manager":
            expr = self.expression_transformer.expression([first_item.children[0]])
            if expr is not None:
                context_manager = cast(Expression, expr)
        # Handle direct object reference
        elif isinstance(first_item, Identifier):
            context_manager = cast(Expression, first_item)
            # Don't add local prefix if the identifier is already scoped
            if isinstance(context_manager.name, str) and not (
                context_manager.name.startswith("local:")
                or ":" in context_manager.name
                or context_manager.name.startswith("private:")
                or context_manager.name.startswith("public:")
                or context_manager.name.startswith("system:")
            ):
                context_manager = cast(Expression, Identifier(name=f"local:{context_manager.name}"))
        # Handle function call case
        elif isinstance(first_item, Token):
            # Keep the name as a string for function calls
            context_manager = first_item.value

            # Check if we have arguments
            if len(filtered_items) > 1 and filtered_items[1] is not None:
                # Process arguments
                arg_items = []
                for item in filtered_items[1:]:
                    # Handle both Tree form and already-transformed list form
                    if isinstance(item, Tree) and item.data == "mixed_arguments":
                        arg_items = item.children
                        break
                    elif isinstance(item, list):
                        # mixed_arguments was already transformed to a list
                        arg_items = item
                        break

                # Process each argument
                seen_kwarg = False
                for arg in arg_items:
                    if isinstance(arg, Tree) and arg.data == "kw_arg":
                        # Keyword argument
                        seen_kwarg = True
                        key = arg.children[0].value
                        value = self.expression_transformer.expression([arg.children[1]])
                        if value is not None:
                            kwargs[key] = value
                    else:
                        # Positional argument
                        if seen_kwarg:
                            raise SyntaxError("Positional argument follows keyword argument")
                        value = self.expression_transformer.expression([arg])
                        if value is not None:
                            args.append(value)

        # Find the 'as' variable name and block
        as_var = None
        block = None

        # Look for 'as' token to find variable name and block
        for i, item in enumerate(filtered_items):
            if hasattr(item, "value") and item.value == "as":
                # Next item should be the variable name
                if i + 1 < len(filtered_items):
                    as_var_token = filtered_items[i + 1]
                    as_var = as_var_token.value if hasattr(as_var_token, "value") else str(as_var_token)
                # Block should be the last item in the list (after filtering)
                for j in range(len(filtered_items) - 1, -1, -1):
                    if hasattr(filtered_items[j], "data") and filtered_items[j].data == "block":
                        block = self.main_transformer._transform_block(filtered_items[j])
                        break
                break

        if as_var is None:
            raise SyntaxError("Missing 'as' variable in with statement")
        if block is None:
            raise SyntaxError("Missing block in with statement")

        # Determine if this is a function call pattern or direct context manager
        context_manager_part = filtered_items[0]

        # If the first item is a simple token (NAME/USE), it's a function call
        if (
            hasattr(context_manager_part, "value")
            and isinstance(context_manager_part.value, str)
            and not hasattr(context_manager_part, "data")
        ):
            # Function call pattern: NAME [mixed_arguments] as var block
            context_manager_name = context_manager_part.value

            # Handle mixed_arguments - could be None (empty args) or a tree with arguments
            args: list[Expression] = []
            kwargs = {}
            seen_keyword_arg = False

            # Look for mixed_arguments (second item if it exists and is not 'as')
            if len(filtered_items) >= 2 and isinstance(filtered_items[1], list):
                # mixed_arguments has already been transformed into a list of expressions/trees
                args_list = filtered_items[1]

                # Process each item in the list
                for item in args_list:
                    if hasattr(item, "data") and item.data == "kw_arg":
                        # Keyword argument: NAME "=" expr
                        seen_keyword_arg = True
                        name = item.children[0].value
                        value = self.expression_transformer.expression([item.children[1]])
                        kwargs[name] = value
                    else:
                        # Positional argument: expr
                        if seen_keyword_arg:
                            raise SyntaxError("Positional argument follows keyword argument in with statement")
                        args.append(cast(Expression, item))
            elif len(filtered_items) >= 2 and hasattr(filtered_items[1], "data") and filtered_items[1].data == "mixed_arguments":
                mixed_args_tree = filtered_items[1]

                # mixed_arguments contains with_arg children
                for with_arg_tree in mixed_args_tree.children:
                    if hasattr(with_arg_tree, "data") and with_arg_tree.data == "with_arg":
                        # with_arg contains either kw_arg or expr
                        if len(with_arg_tree.children) > 0:
                            arg_content = with_arg_tree.children[0]
                            if hasattr(arg_content, "data") and arg_content.data == "kw_arg":
                                # Keyword argument: NAME "=" expr
                                seen_keyword_arg = True
                                name = arg_content.children[0].value
                                value = self.expression_transformer.expression([arg_content.children[1]])
                                kwargs[name] = value
                            else:
                                # Positional argument: expr
                                if seen_keyword_arg:
                                    raise SyntaxError("Positional argument follows keyword argument in with statement")
                                args.append(cast(Expression, self.expression_transformer.expression([arg_content])))

            return WithStatement(context_manager=context_manager_name, args=args, kwargs=kwargs, as_var=as_var, body=block)
        else:
            # Direct context manager pattern: with_context_manager as var block
            context_manager_expr = cast(Expression, self.expression_transformer.expression([context_manager_part]))
            return WithStatement(context_manager=context_manager_expr, args=[], kwargs={}, as_var=as_var, body=block)
