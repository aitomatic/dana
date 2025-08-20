"""
Statement helper classes for Dana language parsing.

This module provides helper classes that can be used by the main StatementTransformer
to organize code by functionality while maintaining the original transformation flow.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import cast

from lark import Token, Tree

from dana.core.lang.ast import (
    AssertStatement,
    Assignment,
    BreakStatement,
    Conditional,
    ContinueStatement,
    Expression,
    ForLoop,
    Identifier,
    ImportFromStatement,
    ImportStatement,
    PassStatement,
    RaiseStatement,
    ReturnStatement,
    TypeHint,
    WhileLoop,
    WithStatement,
)


class AssignmentHelper:
    """Helper class for assignment-related transformations."""

    @staticmethod
    def create_assignment(target_tree, value_tree, expression_transformer, variable_transformer, type_hint=None):
        """Create an Assignment node with proper validation."""
        from lark import Tree

        # Handle different types of assignment targets
        if isinstance(target_tree, Tree) and hasattr(target_tree, "data"):
            # Check if this is a complex target (atom with trailers)
            if target_tree.data == "target":
                # target -> atom
                atom_tree = target_tree.children[0]
                if isinstance(atom_tree, Tree) and atom_tree.data == "atom":
                    # Check if atom has trailers (indicating subscript or attribute access)
                    if len(atom_tree.children) > 1:
                        # Complex target: use expression transformer to handle subscript/attribute access
                        target = expression_transformer.expression([target_tree])
                    else:
                        # Simple target: use variable transformer
                        target = variable_transformer.variable([target_tree])
                else:
                    # Fallback to variable transformer
                    target = variable_transformer.variable([target_tree])
            else:
                # Not a target rule, try expression transformer first
                try:
                    target = expression_transformer.expression([target_tree])
                except Exception:
                    # Fallback to variable transformer
                    target = variable_transformer.variable([target_tree])
        else:
            # Simple case: use variable transformer
            target = variable_transformer.variable([target_tree])

        # Validate target type
        from dana.core.lang.ast import AttributeAccess, Identifier, SubscriptExpression

        if not isinstance(target, Identifier | SubscriptExpression | AttributeAccess):
            raise TypeError(f"Assignment target must be Identifier, SubscriptExpression, or AttributeAccess, got {type(target)}")

        # Transform value
        value = expression_transformer.expression([value_tree])
        if isinstance(value, tuple):
            raise TypeError(f"Assignment value cannot be a tuple: {value}")

        # Type imports to match the original
        from dana.core.lang.ast import (
            BinaryExpression,
            DictLiteral,
            FStringExpression,
            FunctionCall,
            ListLiteral,
            LiteralExpression,
            ObjectFunctionCall,
            SetLiteral,
            TupleLiteral,
            UnaryExpression,
        )

        value_expr = cast(
            LiteralExpression
            | Identifier
            | BinaryExpression
            | UnaryExpression
            | FunctionCall
            | ObjectFunctionCall
            | TupleLiteral
            | DictLiteral
            | ListLiteral
            | SetLiteral
            | SubscriptExpression
            | AttributeAccess
            | FStringExpression,
            value,
        )

        return Assignment(target=target, value=value_expr, type_hint=type_hint)

    @staticmethod
    def create_type_hint(items):
        """Transform a basic_type rule into a TypeHint node."""
        if not items:
            raise ValueError("basic_type rule received empty items list")

        # Handle union types (basic_type -> union_type -> single_type (PIPE single_type)*)
        # items should contain a union_type Tree
        from lark import Tree

        if len(items) == 1 and isinstance(items[0], Tree) and items[0].data == "union_type":
            union_items = items[0].children

            # Extract type names from union
            type_names = []
            for union_item in union_items:
                type_name = AssignmentHelper._extract_type_name_from_single_type(union_item)
                if type_name:
                    type_names.append(type_name)

            # Join union types with " | "
            if len(type_names) > 1:
                type_name = " | ".join(type_names)
            else:
                type_name = type_names[0] if type_names else "unknown"
        else:
            # Handle legacy single type (fallback)
            item = items[0]
            if hasattr(item, "value"):
                type_name = item.value
            elif hasattr(item, "type") and item.type == "NAME":
                # This is a NAME token representing a user-defined struct type
                type_name = item.value
            else:
                type_name = str(item)

        return TypeHint(name=type_name)

    @staticmethod
    def _extract_type_name_from_single_type(single_type_item):
        """Extract type name from single_type grammar rule."""
        from lark import Tree

        if not isinstance(single_type_item, Tree) or single_type_item.data != "single_type":
            # Handle direct token case (legacy)
            if hasattr(single_type_item, "value"):
                return single_type_item.value
            elif hasattr(single_type_item, "type") and single_type_item.type == "NAME":
                return single_type_item.value
            else:
                return str(single_type_item)

        # single_type can be either generic_type or simple_type
        child = single_type_item.children[0]

        if isinstance(child, Tree):
            if child.data == "generic_type":
                # Handle generic_type: simple_type "[" type_argument_list "]"
                simple_type_tree = child.children[0]  # First child is simple_type
                base_type = AssignmentHelper._extract_type_name_from_simple_type(simple_type_tree)

                # For now, just return the base type (e.g., "list" from "list[str]")
                # In future phases, we'll parse the full generic type
                return base_type
            elif child.data == "simple_type":
                # Handle simple_type directly
                return AssignmentHelper._extract_type_name_from_simple_type(child)

        # Fallback
        return str(child)

    @staticmethod
    def _extract_type_name_from_simple_type(simple_type_tree):
        """Extract type name from simple_type grammar rule."""
        from lark import Tree

        if not isinstance(simple_type_tree, Tree) or simple_type_tree.data != "simple_type":
            return str(simple_type_tree)

        # simple_type contains a single token (INT_TYPE, STR_TYPE, NAME, etc.)
        type_token = simple_type_tree.children[0]

        if hasattr(type_token, "value"):
            return type_token.value
        elif hasattr(type_token, "type") and type_token.type == "NAME":
            return type_token.value
        else:
            return str(type_token)


class ControlFlowHelper:
    """Helper class for control flow statement transformations."""

    @staticmethod
    def create_conditional(condition_tree, body_tree, expression_transformer, statement_transformer, else_body_tree=None):
        """Create a Conditional node with proper validation."""
        condition = expression_transformer.expression([condition_tree])

        # Transform body
        body = statement_transformer._transform_block(body_tree)

        # Transform else body if present
        else_body = []
        if else_body_tree is not None:
            else_body = statement_transformer._transform_block(else_body_tree)

        line_num = getattr(condition, "line", 0) or 0
        return Conditional(condition=cast(Expression, condition), body=body, else_body=else_body, line_num=line_num)

    @staticmethod
    def create_while_loop(condition_tree, body_tree, expression_transformer, statement_transformer):
        """Create a WhileLoop node."""
        condition = expression_transformer.expression([condition_tree])

        body = statement_transformer._transform_block(body_tree)

        line_num = getattr(condition, "line", 0) or 0
        return WhileLoop(condition=cast(Expression, condition), body=body, line_num=line_num)

    @staticmethod
    def create_for_loop(target_tree, iterable_tree, body_tree, expression_transformer, variable_transformer, statement_transformer):
        """Create a ForLoop node."""
        target = variable_transformer.variable([target_tree])
        if not isinstance(target, Identifier):
            raise TypeError(f"For loop target must be Identifier, got {type(target)}")

        iterable = expression_transformer.expression([iterable_tree])

        body = statement_transformer._transform_block(body_tree)

        return ForLoop(target=target, iterable=cast(Expression, iterable), body=body)


class SimpleStatementHelper:
    """Helper class for simple statement transformations."""

    @staticmethod
    def create_return_statement(items, expression_transformer):
        """Create a ReturnStatement node."""
        value = expression_transformer.expression(items) if items else None
        if isinstance(value, tuple):
            raise TypeError(f"Return value cannot be a tuple: {value}")
        return ReturnStatement(value=value)

    @staticmethod
    def create_break_statement():
        """Create a BreakStatement node."""
        return BreakStatement()

    @staticmethod
    def create_continue_statement():
        """Create a ContinueStatement node."""
        return ContinueStatement()

    @staticmethod
    def create_pass_statement():
        """Create a PassStatement node."""
        return PassStatement()

    @staticmethod
    def create_raise_statement(items, expression_transformer):
        """Create a RaiseStatement node."""
        value = expression_transformer.expression([items[0]]) if items else None
        from_value = expression_transformer.expression([items[1]]) if len(items) > 1 else None
        if isinstance(value, tuple) or isinstance(from_value, tuple):
            raise TypeError(f"Raise statement values cannot be tuples: {value}, {from_value}")
        return RaiseStatement(value=value, from_value=from_value)

    @staticmethod
    def create_assert_statement(items, expression_transformer):
        """Create an AssertStatement node."""
        condition = expression_transformer.expression([items[0]])
        message = expression_transformer.expression([items[1]]) if len(items) > 1 else None
        if isinstance(condition, tuple) or isinstance(message, tuple):
            raise TypeError(f"Assert statement values cannot be tuples: {condition}, {message}")
        # Ensure condition and message are Expression or None
        condition_expr = cast(Expression, condition)
        message_expr = cast(Expression, message) if message is not None else None
        return AssertStatement(condition=condition_expr, message=message_expr)


class ImportHelper:
    """Helper class for import statement transformations."""

    @staticmethod
    def create_simple_import(module_path_tree, alias_name=None):
        """Create an ImportStatement node."""
        # Extract module path
        module = ImportHelper._extract_module_path(module_path_tree)
        alias = alias_name.value if alias_name and hasattr(alias_name, "value") else alias_name if alias_name else None
        return ImportStatement(module=module, alias=alias)

    @staticmethod
    def create_from_import(module_path_tree, name_token, alias_token=None):
        """Create an ImportFromStatement node."""
        # Handle relative_module_path (starts with dots) or regular module_path
        module = ImportHelper._extract_module_path_or_relative(module_path_tree)

        # Get the imported name
        name = name_token.value if hasattr(name_token, "value") else str(name_token)

        # Check for alias
        alias = None
        if alias_token is not None and hasattr(alias_token, "value"):
            alias = alias_token.value

        return ImportFromStatement(module=module, names=[(name, alias)])

    @staticmethod
    def _extract_module_path(module_path_tree):
        """Extract module path from a module_path tree."""
        if isinstance(module_path_tree, Tree) and getattr(module_path_tree, "data", None) == "module_path":
            parts = []
            for child in module_path_tree.children:
                if isinstance(child, Token):
                    parts.append(child.value)
                elif hasattr(child, "value"):
                    parts.append(child.value)
            return ".".join(parts)
        elif isinstance(module_path_tree, Token):
            return module_path_tree.value
        else:
            return str(module_path_tree)

    @staticmethod
    def _extract_module_path_or_relative(module_path_item):
        """Extract module path from either relative_module_path or module_path."""
        # Handle relative_module_path (starts with dots)
        if isinstance(module_path_item, Tree) and getattr(module_path_item, "data", None) == "relative_module_path":
            # Extract dots and optional module path
            dots = []
            module_parts = []

            for child in module_path_item.children:
                if isinstance(child, Token) and child.type == "DOT":
                    dots.append(".")
                elif isinstance(child, Tree) and getattr(child, "data", None) == "module_path":
                    # Extract module path parts
                    for subchild in child.children:
                        if isinstance(subchild, Token):
                            module_parts.append(subchild.value)
                        elif hasattr(subchild, "value"):
                            module_parts.append(subchild.value)
                elif isinstance(child, Token):
                    module_parts.append(child.value)

            # Build relative module name
            module = "".join(dots)
            if module_parts:
                module += ".".join(module_parts)
            return module
        else:
            # Handle absolute module_path (existing logic)
            return ImportHelper._extract_module_path(module_path_item)


class ContextHelper:
    """Helper class for context management statement transformations."""

    # Note: UseStatement functionality has been removed as part of grammar unification
    # @staticmethod
    # def create_use_statement(args, kwargs):
    #     """Create a UseStatement node."""
    #     return UseStatement(args=args, kwargs=kwargs)

    @staticmethod
    def create_with_statement(context_manager, as_var, body_tree, statement_transformer):
        """Create a WithStatement node."""
        body = statement_transformer._transform_block(body_tree)

        # Handle different types of context managers
        if isinstance(context_manager, str):
            # Function name
            return WithStatement(context_manager=context_manager, args=[], kwargs={}, as_var=as_var, body=body)
        else:
            # Expression
            return WithStatement(context_manager=context_manager, args=[], kwargs={}, as_var=as_var, body=body)
