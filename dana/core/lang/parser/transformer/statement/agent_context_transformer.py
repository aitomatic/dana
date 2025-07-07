"""
Agent and context transformer for Dana language parsing.

This module handles all agent and context statement transformations, including:
- Agent statements (agent(), agent_pool())
- Use statements (use())
- With statements and context managers
- Mixed arguments and keyword arguments

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import cast

from lark import Token, Tree

from dana.core.lang.ast import (
    AgentPoolStatement,
    AgentStatement,
    Expression,
    Identifier,
    UseStatement,
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

    # === Use Statements ===

    def use_stmt(self, items):
        """Transform a use_stmt rule into a UseStatement node.

        Grammar: use_stmt: USE "(" [mixed_arguments] ")"

        The grammar passes:
        - items[0] = USE token (ignored)
        - items[1] = result from mixed_arguments (None if no arguments, or list of arguments)
        """
        from lark import Tree

        # Initialize collections for arguments
        args = []  # List[Expression] for positional arguments
        kwargs = {}  # Dict[str, Expression] for keyword arguments

        # Handle the case where mixed_arguments is present
        # items[0] is the USE token, items[1] is the mixed_arguments result
        if len(items) > 1 and items[1] is not None:
            mixed_args_result = items[1]

            # Process mixed_arguments following with_stmt pattern
            seen_keyword_arg = False  # Track if we've seen any keyword arguments

            if isinstance(mixed_args_result, list):
                # Process each argument
                for arg_item in mixed_args_result:
                    if isinstance(arg_item, Tree) and arg_item.data == "kw_arg":
                        # Keyword argument: NAME "=" expr
                        seen_keyword_arg = True
                        name = arg_item.children[0].value
                        value = arg_item.children[1]  # Value is already processed
                        kwargs[name] = value
                    else:
                        # Positional argument: expr
                        if seen_keyword_arg:
                            # Error: positional argument after keyword argument
                            raise SyntaxError("Positional argument follows keyword argument in use statement")
                        args.append(cast(Expression, arg_item))
            else:
                # Single argument
                if isinstance(mixed_args_result, Tree) and mixed_args_result.data == "kw_arg":
                    # Keyword argument: NAME "=" expr
                    name = mixed_args_result.children[0].value
                    value = self.expression_transformer.expression([mixed_args_result.children[1]])
                    kwargs[name] = value
                else:
                    # Positional argument: expr
                    args.append(cast(Expression, mixed_args_result))

        return UseStatement(args=args, kwargs=kwargs)

    # === Agent Statements ===

    def agent_stmt(self, items):
        """Transform an agent_stmt rule into an AgentStatement node.

        Grammar: agent_stmt: AGENT "(" [mixed_arguments] ")"

        The grammar passes:
        - items[0] = AGENT token (ignored)
        - items[1] = result from mixed_arguments (None if no arguments, or list of arguments)
        """
        from lark import Tree

        # Initialize collections for arguments
        args = []  # List[Expression] for positional arguments
        kwargs = {}  # Dict[str, Expression] for keyword arguments

        # Handle the case where mixed_arguments is present
        # items[0] is the AGENT token, items[1] is the mixed_arguments result
        if len(items) > 1 and items[1] is not None:
            mixed_args_result = items[1]

            # Process mixed_arguments following use_stmt pattern
            seen_keyword_arg = False  # Track if we've seen any keyword arguments

            if isinstance(mixed_args_result, list):
                # Process each argument
                for arg_item in mixed_args_result:
                    if isinstance(arg_item, Tree) and arg_item.data == "kw_arg":
                        # Keyword argument: NAME "=" expr
                        seen_keyword_arg = True
                        name = arg_item.children[0].value
                        value = arg_item.children[1]  # Value is already processed
                        kwargs[name] = value
                    else:
                        # Positional argument: expr
                        if seen_keyword_arg:
                            # Error: positional argument after keyword argument
                            raise SyntaxError("Positional argument follows keyword argument in agent statement")
                        args.append(cast(Expression, arg_item))
            else:
                # Single argument
                if isinstance(mixed_args_result, Tree) and mixed_args_result.data == "kw_arg":
                    # Keyword argument: NAME "=" expr
                    name = mixed_args_result.children[0].value
                    value = self.expression_transformer.expression([mixed_args_result.children[1]])
                    kwargs[name] = value
                else:
                    # Positional argument: expr
                    args.append(cast(Expression, mixed_args_result))

        return AgentStatement(args=args, kwargs=kwargs)

    def agent_pool_stmt(self, items):
        """Transform an agent_pool_stmt rule into an AgentPoolStatement node.

        Grammar: agent_pool_stmt: AGENT_POOL "(" [mixed_arguments] ")"

        The grammar passes:
        - items[0] = AGENT_POOL token (ignored)
        - items[1] = result from mixed_arguments (None if no arguments, or list of arguments)
        """
        from lark import Tree

        # Initialize collections for arguments
        args = []  # List[Expression] for positional arguments
        kwargs = {}  # Dict[str, Expression] for keyword arguments

        # Handle the case where mixed_arguments is present
        # items[0] is the AGENT_POOL token, items[1] is the mixed_arguments result
        if len(items) > 1 and items[1] is not None:
            mixed_args_result = items[1]

            # Process mixed_arguments following use_stmt pattern
            seen_keyword_arg = False  # Track if we've seen any keyword arguments

            if isinstance(mixed_args_result, list):
                # Process each argument
                for arg_item in mixed_args_result:
                    if isinstance(arg_item, Tree) and arg_item.data == "kw_arg":
                        # Keyword argument: NAME "=" expr
                        seen_keyword_arg = True
                        name = arg_item.children[0].value
                        value = arg_item.children[1]  # Value is already processed
                        kwargs[name] = value
                    else:
                        # Positional argument: expr
                        if seen_keyword_arg:
                            # Error: positional argument after keyword argument
                            raise SyntaxError("Positional argument follows keyword argument in agent_pool statement")
                        args.append(cast(Expression, arg_item))
            else:
                # Single argument
                if isinstance(mixed_args_result, Tree) and mixed_args_result.data == "kw_arg":
                    # Keyword argument: NAME "=" expr
                    name = mixed_args_result.children[0].value
                    value = self.expression_transformer.expression([mixed_args_result.children[1]])
                    kwargs[name] = value
                else:
                    # Positional argument: expr
                    args.append(cast(Expression, mixed_args_result))

        return AgentPoolStatement(args=args, kwargs=kwargs)

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
        from dana.core.lang.ast import Expression

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
