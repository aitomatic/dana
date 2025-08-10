"""
Operator transformer for Dana language parsing.

This module handles all operator expressions including:
- Binary operators (arithmetic, comparison, logical)
- Unary operators (not, negation)
- Pipe operators
- Operator precedence and associativity

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from lark import Token, Tree

from dana.core.lang.ast import (
    BinaryExpression,
    BinaryOperator,
    UnaryExpression,
)
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer


class OperatorTransformer(BaseTransformer):
    """Transformer for operator expressions."""

    def _extract_operator_string(self, op_token):
        """Extract operator string from a token or tree."""
        if isinstance(op_token, Token):
            return op_token.value
        elif isinstance(op_token, Tree):
            return self._op_tree_to_str(op_token)
        elif hasattr(op_token, "value"):  # BinaryOperator enum
            return op_token.value
        else:
            return str(op_token)

    def _op_tree_to_str(self, tree):
        """Convert an operator tree to its string representation."""
        if hasattr(tree, "data") and tree.data in ["not_in_op", "is_not_op"]:
            return " ".join(self._extract_operator_string(child) for child in tree.children)
        else:
            return str(tree)

    def _left_associative_binop(self, items, operator_getter):
        """
        Handle left-associative binary operations.

        Args:
            items: List of alternating expressions and operators
            operator_getter: Function to convert operator token/string to BinaryOperator enum
        """
        if len(items) == 1:
            return items[0]

        # Build left-associative tree: ((a + b) + c) + d
        result = items[0]
        for i in range(1, len(items), 2):
            op_token = items[i]
            right_expr = items[i + 1]

            op_str = self._extract_operator_string(op_token)
            operator = operator_getter(op_str)

            result = BinaryExpression(left=result, operator=operator, right=right_expr)

        return result

    def _get_binary_operator(self, op_str):
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

    def or_expr(self, items):
        """Handle OR expressions with left associativity."""
        return self._left_associative_binop(items, lambda op: BinaryOperator.OR)

    def and_expr(self, items):
        """Handle AND expressions with left associativity."""
        return self._left_associative_binop(items, lambda op: BinaryOperator.AND)

    def pipe_expr(self, items):
        """Handle pipe expressions with left associativity."""
        return self._left_associative_binop(items, lambda op: BinaryOperator.PIPE)

    def not_expr(self, items):
        """
        Handle NOT expressions and comparisons.

        Grammar: not_expr: NOT_OP not_expr | comparison
        """
        if len(items) == 1:
            # Single item - pass through
            return items[0]
        elif len(items) == 2:
            # NOT operation
            op_token = items[0]
            operand = items[1]

            # Extract operator (should be "not")
            if isinstance(op_token, Token):
                op_str = op_token.value
            else:
                op_str = str(op_token)

            return UnaryExpression(operator=op_str, operand=operand)
        else:
            self.error(f"Unexpected not_expr structure: {len(items)} items")
            return items[0] if items else None

    def comparison(self, items):
        """Handle comparison expressions with left associativity."""
        return self._left_associative_binop(items, self._get_binary_operator)

    def sum_expr(self, items):
        """Handle addition/subtraction expressions with left associativity."""
        return self._left_associative_binop(items, self._get_binary_operator)

    def term(self, items):
        """Handle multiplication/division/modulo expressions with left associativity."""
        return self._left_associative_binop(items, self._get_binary_operator)

    def factor(self, items):
        """
        Handle unary operators and atoms.

        Grammar: factor: (ADD | SUB) factor | atom trailer*
        """
        if len(items) == 1:
            # Single atom - pass through
            return items[0]
        elif len(items) == 2:
            # Unary operation
            op_token = items[0]
            operand = items[1]

            # Extract operator
            if isinstance(op_token, Token):
                op_str = op_token.value
            else:
                op_str = str(op_token)

            return UnaryExpression(operator=op_str, operand=operand)
        else:
            self.error(f"Unexpected factor structure: {len(items)} items")
            return items[0] if items else None

    def power(self, items):
        """
        Handle power expressions with right associativity.

        Grammar: power: factor (POW power)?
        """
        if len(items) == 1:
            return items[0]
        elif len(items) == 3:
            # Right-associative: a ** b ** c = a ** (b ** c)
            left = items[0]
            items[1]  # Should be "**"
            right = items[2]

            return BinaryExpression(left=left, operator=BinaryOperator.POWER, right=right)
        else:
            self.error(f"Unexpected power structure: {len(items)} items")
            return items[0] if items else None

    # Token handlers for operators
    def ADD(self, token):
        """Handle the addition operator token."""
        return BinaryOperator.ADD

    def SUB(self, token):
        """Handle the subtraction operator token."""
        return BinaryOperator.SUBTRACT

    def MUL(self, token):
        """Handle the multiplication operator token."""
        return BinaryOperator.MULTIPLY

    def DIV(self, token):
        """Handle the division operator token."""
        return BinaryOperator.DIVIDE

    def FDIV(self, token):
        """Handle the floor division operator token."""
        return BinaryOperator.FLOOR_DIVIDE

    def MOD(self, token):
        """Handle the modulo operator token."""
        return BinaryOperator.MODULO

    def POW(self, token):
        """Handle the power operator token."""
        return BinaryOperator.POWER

    def PIPE(self, token):
        """Handle the pipe operator token."""
        return BinaryOperator.PIPE

    def EQ_OP(self, token):
        """Handle the equality operator token."""
        return BinaryOperator.EQUALS

    def NE_OP(self, token):
        """Handle the not-equals operator token."""
        return BinaryOperator.NOT_EQUALS

    def LT_OP(self, token):
        """Handle the less-than operator token."""
        return BinaryOperator.LESS_THAN

    def GT_OP(self, token):
        """Handle the greater-than operator token."""
        return BinaryOperator.GREATER_THAN

    def LE_OP(self, token):
        """Handle the less-equals operator token."""
        return BinaryOperator.LESS_EQUALS

    def GE_OP(self, token):
        """Handle the greater-equals operator token."""
        return BinaryOperator.GREATER_EQUALS

    def IN_OP(self, token):
        """Handle the 'in' operator token."""
        return BinaryOperator.IN

    def NOT_IN_OP(self, token):
        """Handle the 'not in' operator token."""
        return BinaryOperator.NOT_IN

    def IS_OP(self, token):
        """Handle the 'is' operator token."""
        return BinaryOperator.IS

    def IS_NOT_OP(self, token):
        """Handle the 'is not' operator token."""
        return BinaryOperator.IS_NOT

    def NOT_OP(self, token):
        """Handle the 'not' operator token."""
        return "not"
