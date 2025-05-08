"""Expression transformers for DANA language parsing."""

from lark import Token

from opendxa.dana.language.ast import (
    BinaryExpression,
    BinaryOperator,
    Identifier,
    Literal,
    LiteralExpression,
)
from opendxa.dana.language.transformers.base_transformer import BaseTransformer


class ExpressionTransformer(BaseTransformer):
    """Transformer for expression-related AST nodes."""

    def expression(self, items):
        """Transform an expression rule into an Expression node."""
        # Pass through to the or_expr rule
        return items[0]

    def or_expr(self, items):
        """Transform an or expression into a BinaryExpression or pass through."""
        if len(items) == 1:
            return items[0]

        # Build a left-associative tree of binary expressions
        result = items[0]
        for i in range(1, len(items)):
            result = BinaryExpression(left=result, operator=BinaryOperator.OR, right=items[i])
        return result

    def and_expr(self, items):
        """Transform an and expression into a BinaryExpression or pass through."""
        if len(items) == 1:
            return items[0]

        # Build a left-associative tree of binary expressions
        result = items[0]
        for i in range(1, len(items)):
            result = BinaryExpression(left=result, operator=BinaryOperator.AND, right=items[i])
        return result

    def comparison(self, items):
        """Transform a comparison into a BinaryExpression or pass through."""
        if len(items) == 1:
            return items[0]

        # Items alternate between expressions and operators
        result = items[0]
        for i in range(1, len(items), 2):
            operator = self._get_binary_operator(items[i].value)
            right = items[i + 1]
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def comp_op(self, items):
        """Transform a comparison operator token into a string."""
        return items[0]

    def EQ(self, _):
        return Token("COMP_OP", "==")

    def NEQ(self, _):
        return Token("COMP_OP", "!=")

    def LT(self, _):
        return Token("COMP_OP", "<")

    def GT(self, _):
        return Token("COMP_OP", ">")

    def LTE(self, _):
        return Token("COMP_OP", "<=")

    def GTE(self, _):
        return Token("COMP_OP", ">=")

    def sum_expr(self, items):
        """Transform a sum expression into a BinaryExpression or pass through."""
        if len(items) == 1:
            return items[0]

        # Items alternate between expressions and operators
        result = items[0]
        for i in range(1, len(items), 2):
            operator = self._get_binary_operator(items[i].value)
            right = items[i + 1]
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def add_op(self, items):
        """Transform an addition operator token into a string."""
        return items[0]

    def PLUS(self, _):
        return Token("ADD_OP", "+")

    def MINUS(self, _):
        return Token("ADD_OP", "-")

    def product(self, items):
        """Transform a product expression into a BinaryExpression or pass through."""
        if len(items) == 1:
            return items[0]

        # Items alternate between expressions and operators
        result = items[0]
        for i in range(1, len(items), 2):
            operator = self._get_binary_operator(items[i].value)
            right = items[i + 1]
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def mul_op(self, items):
        """Transform a multiplication operator token into a string."""
        return items[0]

    def MULT(self, _):
        return Token("MUL_OP", "*")

    def DIV(self, _):
        return Token("MUL_OP", "/")

    def MOD(self, _):
        return Token("MUL_OP", "%")

    def atom(self, items):
        """Transform an atom rule into an Expression node."""
        return items[0]

    def TRUE(self, _):
        """Transform a TRUE token into a LiteralExpression with value True."""
        return LiteralExpression(literal=Literal(value=True))

    def FALSE(self, _):
        """Transform a FALSE token into a LiteralExpression with value False."""
        return LiteralExpression(literal=Literal(value=False))

    def array_literal(self, items):
        """Transform an array literal into a LiteralExpression node."""
        # If empty array, return empty list
        if len(items) == 0:
            return LiteralExpression(literal=Literal(value=[]))

        # If we have array items, extract them
        array_items = items[0] if len(items) > 0 else []

        # Convert to a Literal node with a list value
        return LiteralExpression(literal=Literal(value=array_items))

    def array_items(self, items):
        """Transform array items into a list."""
        return items

    def literal(self, items):
        """Transform a literal rule into a LiteralExpression node."""
        return LiteralExpression(literal=self._create_literal(items[0]))

    def identifier(self, items):
        """Transform an identifier rule into an Identifier node."""
        # Join parts with dots for nested identifiers (e.g., "a.b.c")
        if len(items) == 1:
            name = items[0].value
        else:
            name = ".".join(item.value for item in items)
        return Identifier(name=name)

    def _get_binary_operator(self, op_str):
        """Convert an operator string to a BinaryOperator enum value."""
        op_map = {
            "+": BinaryOperator.ADD,
            "-": BinaryOperator.SUBTRACT,
            "*": BinaryOperator.MULTIPLY,
            "/": BinaryOperator.DIVIDE,
            "%": BinaryOperator.MODULO,
            "<": BinaryOperator.LESS_THAN,
            ">": BinaryOperator.GREATER_THAN,
            "<=": BinaryOperator.LESS_EQUALS,
            ">=": BinaryOperator.GREATER_EQUALS,
            "==": BinaryOperator.EQUALS,
            "!=": BinaryOperator.NOT_EQUALS,
            "and": BinaryOperator.AND,
            "or": BinaryOperator.OR,
        }

        return op_map.get(op_str, BinaryOperator.EQUALS)  # Default to equals if unknown
