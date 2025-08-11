"""
Expression helper classes for Dana language parsing.

This module provides helper classes that can be used by the main ExpressionTransformer
to organize code by functionality while maintaining the original transformation flow.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from lark import Token, Tree

from dana.core.lang.ast import (
    BinaryExpression,
    BinaryOperator,
    LiteralExpression,
)


class OperatorHelper:
    """Helper class for operator-related transformations."""

    @staticmethod
    def extract_operator_string(op_token):
        """
        Extract the operator string from a parse tree node, token, or string.
        Handles comp_op, *_op, ADD_OP, MUL_OP, direct tokens, and plain strings.
        Also handles BinaryOperator enum values.
        """
        from dana.core.lang.ast import BinaryOperator

        if isinstance(op_token, Token):
            return op_token.value
        if isinstance(op_token, str):
            return op_token
        if isinstance(op_token, BinaryOperator):
            return op_token.value  # Return the value of the enum
        if isinstance(op_token, Tree):
            if getattr(op_token, "data", None) == "comp_op":
                op_str = " ".join(child.value for child in op_token.children if isinstance(child, Token))
                return op_str
            elif op_token.children and isinstance(op_token.children[0], Token):
                return op_token.children[0].value
        raise ValueError(f"Cannot extract operator string from: {op_token}")

    @staticmethod
    def op_tree_to_str(tree):
        """Convert an operator tree to its string representation."""
        if hasattr(tree, "data") and tree.data in ["not_in_op", "is_not_op"]:
            return " ".join(OperatorHelper.extract_operator_string(child) for child in tree.children)
        else:
            return str(tree)

    @staticmethod
    def left_associative_binop(items, operator_getter):
        """
        Helper for left-associative binary operations (e.g., a + b + c).
        Iterates over items, applying the operator from operator_getter to each pair.
        Used by or_expr, and_expr, comparison, sum_expr, and term.
        """
        if not items:
            raise ValueError("No items for binary operation")
        result = items[0]
        i = 1
        while i < len(items):
            op_token = items[i]
            # Special check to catch malformed parse trees early
            if isinstance(op_token, Tree) and hasattr(op_token, "data") and op_token.data.endswith("_op") and not op_token.children:
                raise ValueError(f"Malformed parse tree: operator node '{op_token.data}' has no children at index {i} in items: {items}")
            op_str = OperatorHelper.extract_operator_string(op_token)
            op = operator_getter(op_str)
            right = items[i + 1]
            left = result
            result = BinaryExpression(left, op, right)
            i += 2
        return result

    @staticmethod
    def get_binary_operator(op_str):
        """Convert operator string to BinaryOperator enum."""
        operator_map = {
            "+": BinaryOperator.ADD,
            "-": BinaryOperator.SUBTRACT,
            "*": BinaryOperator.MULTIPLY,
            "/": BinaryOperator.DIVIDE,
            "//": BinaryOperator.FLOOR_DIVIDE,
            "%": BinaryOperator.MODULO,
            "**": BinaryOperator.POWER,
            "==": BinaryOperator.EQUALS,
            "!=": BinaryOperator.NOT_EQUALS,
            "<": BinaryOperator.LESS_THAN,
            ">": BinaryOperator.GREATER_THAN,
            "<=": BinaryOperator.LESS_EQUALS,
            ">=": BinaryOperator.GREATER_EQUALS,
            "and": BinaryOperator.AND,
            "or": BinaryOperator.OR,
            "in": BinaryOperator.IN,
            "not in": BinaryOperator.NOT_IN,
            "is": BinaryOperator.IS,
            "is not": BinaryOperator.IS_NOT,
            "|": BinaryOperator.PIPE,
        }

        if op_str not in operator_map:
            raise ValueError(f"Unknown binary operator: {op_str}")

        return operator_map[op_str]


class LiteralHelper:
    """Helper class for literal-related transformations."""

    @staticmethod
    def atom_from_token(token):
        """Convert a token to an appropriate literal expression."""
        token_type = getattr(token, "type", None)
        value = getattr(token, "value", str(token))

        # Number literals
        if token_type == "NUMBER":
            if "." in value:
                return LiteralExpression(value=float(value))
            else:
                return LiteralExpression(value=int(value))

        # Boolean and None literals
        elif token_type in ["TRUE", "FALSE", "NONE"]:
            if value in ["True", "true", "TRUE"]:
                value = True
            elif value in ["False", "false", "FALSE"]:
                value = False
            elif value in ["None", "none", "NONE", "null", "NULL"]:
                value = None

        return LiteralExpression(value=value)

    @staticmethod
    def process_string_literal(item):
        """Process different types of string literals."""
        if isinstance(item, Token):
            # Regular string
            if item.type == "REGULAR_STRING":
                value = item.value[1:-1]  # Strip quotes
                return LiteralExpression(value)

            # Single-quoted string
            elif item.type == "SINGLE_QUOTED_STRING":
                value = item.value[1:-1]  # Strip single quotes
                return LiteralExpression(value)

            # Raw string
            elif item.type == "RAW_STRING":
                # Extract the raw string content (removing r" prefix and " suffix)
                if item.value.startswith('r"') and item.value.endswith('"'):
                    value = item.value[2:-1]
                elif item.value.startswith("r'") and item.value.endswith("'"):
                    value = item.value[2:-1]
                else:
                    value = item.value
                return LiteralExpression(value)

            # Multiline string
            elif item.type == "MULTILINE_STRING":
                if item.value.startswith('"""') and item.value.endswith('"""'):
                    value = item.value[3:-3]
                elif item.value.startswith("'''") and item.value.endswith("'''"):
                    value = item.value[3:-3]
                else:
                    value = item.value
                return LiteralExpression(value)

        return None


class CallHelper:
    """Helper class for function call and attribute access transformations."""

    @staticmethod
    def get_full_attribute_name(attr):
        """Recursively extract full dotted name from AttributeAccess chain."""
        from dana.core.lang.ast import AttributeAccess, Identifier

        parts = []
        while isinstance(attr, AttributeAccess):
            parts.append(attr.attribute)
            attr = attr.object
        if isinstance(attr, Identifier):
            parts.append(attr.name)
        else:
            parts.append(str(attr))
        return ".".join(reversed(parts))
