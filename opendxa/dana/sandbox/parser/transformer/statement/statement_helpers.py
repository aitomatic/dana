"""
Statement helper classes for Dana language parsing.

This module provides helper classes that can be used by the main StatementTransformer
to organize code by functionality while maintaining the original transformation flow.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, cast

from lark import Token, Tree

from opendxa.dana.sandbox.parser.ast import (
    Assignment,
    AssertStatement,
    BreakStatement,
    Conditional,
    ContinueStatement,
    Expression,
    FunctionDefinition,
    Identifier,
    ImportFromStatement,
    ImportStatement,
    Parameter,
    PassStatement,
    RaiseStatement,
    ReturnStatement,
    TypeHint,
    UseStatement,
    WhileLoop,
    ForLoop,
    TryBlock,
    ExceptBlock,
    WithStatement,
)


class AssignmentHelper:
    """Helper class for assignment-related transformations."""

    @staticmethod
    def create_assignment(target_tree, value_tree, type_hint=None, expression_transformer=None, variable_transformer=None):
        """Create an Assignment node with proper validation."""
        # Get target identifier
        target = variable_transformer.variable([target_tree])
        if not isinstance(target, Identifier):
            raise TypeError(f"Assignment target must be Identifier, got {type(target)}")

        # Transform value
        value = expression_transformer.expression([value_tree])
        if isinstance(value, tuple):
            raise TypeError(f"Assignment value cannot be a tuple: {value}")
        
        # Type imports to match the original
        from opendxa.dana.sandbox.parser.ast import (
            AttributeAccess, BinaryExpression, DictLiteral, FStringExpression,
            FunctionCall, ListLiteral, LiteralExpression, ObjectFunctionCall,
            SetLiteral, SubscriptExpression, TupleLiteral, UnaryExpression
        )
        
        AllowedAssignmentValue = (
            LiteralExpression, Identifier, BinaryExpression, UnaryExpression,
            FunctionCall, ObjectFunctionCall, TupleLiteral, DictLiteral,
            ListLiteral, SetLiteral, SubscriptExpression, AttributeAccess,
            FStringExpression, UseStatement
        )
        
        value_expr = cast(AllowedAssignmentValue, value)

        return Assignment(target=target, value=value_expr, type_hint=type_hint)

    @staticmethod
    def create_type_hint(items):
        """Transform a basic_type rule into a TypeHint node."""
        if not items:
            raise ValueError("basic_type rule received empty items list")

        type_name = items[0].value if hasattr(items[0], "value") else str(items[0])
        return TypeHint(name=type_name)


class ControlFlowHelper:
    """Helper class for control flow statement transformations."""

    @staticmethod
    def create_conditional(condition_tree, body_tree, else_body_tree=None, expression_transformer=None, statement_transformer=None):
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
    def create_while_loop(condition_tree, body_tree, expression_transformer=None, statement_transformer=None):
        """Create a WhileLoop node."""
        condition = expression_transformer.expression([condition_tree])
        
        body = statement_transformer._transform_block(body_tree)
        
        line_num = getattr(condition, "line", 0) or 0
        return WhileLoop(condition=cast(Expression, condition), body=body, line_num=line_num)

    @staticmethod
    def create_for_loop(target_tree, iterable_tree, body_tree, expression_transformer=None, variable_transformer=None, statement_transformer=None):
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
    def create_return_statement(items, expression_transformer=None):
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
    def create_raise_statement(items, expression_transformer=None):
        """Create a RaiseStatement node."""
        value = expression_transformer.expression([items[0]]) if items else None
        from_value = expression_transformer.expression([items[1]]) if len(items) > 1 else None
        if isinstance(value, tuple) or isinstance(from_value, tuple):
            raise TypeError(f"Raise statement values cannot be tuples: {value}, {from_value}")
        return RaiseStatement(value=value, from_value=from_value)

    @staticmethod
    def create_assert_statement(items, expression_transformer=None):
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
        alias = alias_name.value if hasattr(alias_name, 'value') else alias_name if alias_name else None
        return ImportStatement(module=module, alias=alias)

    @staticmethod
    def create_from_import(module_path_tree, name_token, alias_token=None):
        """Create an ImportFromStatement node."""
        # Handle relative_module_path (starts with dots) or regular module_path
        module = ImportHelper._extract_module_path_or_relative(module_path_tree)
        
        # Get the imported name
        name = name_token.value if hasattr(name_token, 'value') else str(name_token)
        
        # Check for alias
        alias = None
        if alias_token is not None and hasattr(alias_token, 'value'):
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

    @staticmethod
    def create_use_statement(args, kwargs):
        """Create a UseStatement node."""
        return UseStatement(args=args, kwargs=kwargs)

    @staticmethod
    def create_with_statement(context_manager, as_var, body_tree, statement_transformer=None):
        """Create a WithStatement node."""
        body = statement_transformer._transform_block(body_tree)
        
        # Handle different types of context managers
        if isinstance(context_manager, str):
            # Function name
            return WithStatement(
                context_manager=context_manager,
                args=[],
                kwargs={},
                as_var=as_var,
                body=body
            )
        else:
            # Expression
            return WithStatement(
                context_manager=context_manager,
                args=[],
                kwargs={},
                as_var=as_var,
                body=body
            )