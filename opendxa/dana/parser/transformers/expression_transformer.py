"""Expression transformers for DANA language parsing."""

from lark import Token

from opendxa.dana.parser.ast import (
    BinaryExpression,
    BinaryOperator,
    FunctionCall,
    Identifier,
    LiteralExpression,
)
from opendxa.dana.parser.transformers.base_transformer import BaseTransformer


class ExpressionTransformer(BaseTransformer):
    """Transformer for expression-related AST nodes."""

    def expression(self, items):
        """Transform an expression into an AST node or pass through."""
        return self._unwrap_tree(items[0])

    def or_expr(self, items):
        """Transform an or expression into a BinaryExpression or pass through."""
        item = self._unwrap_tree(items[0])
        if len(items) == 1:
            return self._ensure_expr(item)
        result = self._ensure_expr(self._unwrap_tree(items[0]))
        for i in range(1, len(items), 2):
            operator_item = items[i]
            operator_value = operator_item.children[0].value if hasattr(operator_item, "children") else operator_item.value
            operator = self._get_binary_operator(operator_value)
            right = self._ensure_expr(self._unwrap_tree(items[i + 1]))
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def and_expr(self, items):
        """Transform an and expression into a BinaryExpression or pass through."""
        item = self._unwrap_tree(items[0])
        if len(items) == 1:
            return self._ensure_expr(item)
        result = self._ensure_expr(self._unwrap_tree(items[0]))
        for i in range(1, len(items), 2):
            operator_item = items[i]
            operator_value = operator_item.children[0].value if hasattr(operator_item, "children") else operator_item.value
            operator = self._get_binary_operator(operator_value)
            right = self._ensure_expr(self._unwrap_tree(items[i + 1]))
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def comparison(self, items):
        """Transform a comparison into a BinaryExpression or pass through."""
        item = self._unwrap_tree(items[0])
        if len(items) == 1:
            return self._ensure_expr(item)
        result = self._ensure_expr(self._unwrap_tree(items[0]))
        for i in range(1, len(items), 2):
            operator_item = items[i]
            operator_value = operator_item.children[0].value if hasattr(operator_item, "children") else operator_item.value
            operator = self._get_binary_operator(operator_value)
            right = self._ensure_expr(self._unwrap_tree(items[i + 1]))
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def comp_op(self, items):
        """Transform a comparison operator token into a string."""
        return items[0]

    def EQ(self, _):  # noqa: N802
        return Token("COMP_OP", "==")  # type: ignore

    def NEQ(self, _):  # noqa: N802
        return Token("COMP_OP", "!=")  # type: ignore

    def LT(self, _):  # noqa: N802
        return Token("COMP_OP", "<")  # type: ignore

    def GT(self, _):  # noqa: N802
        return Token("COMP_OP", ">")  # type: ignore

    def LTE(self, _):  # noqa: N802
        return Token("COMP_OP", "<=")  # type: ignore

    def GTE(self, _):  # noqa: N802
        return Token("COMP_OP", ">=")  # type: ignore

    def sum_expr(self, items):
        """Transform a sum expression into a BinaryExpression or pass through."""
        item = self._unwrap_tree(items[0])
        if len(items) == 1:
            return self._ensure_expr(item)
        result = self._ensure_expr(self._unwrap_tree(items[0]))
        for i in range(1, len(items), 2):
            operator_item = items[i]
            operator_value = operator_item.children[0].value if hasattr(operator_item, "children") else operator_item.value
            operator = self._get_binary_operator(operator_value)
            right = self._ensure_expr(self._unwrap_tree(items[i + 1]))
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def add_op(self, items):
        """Transform an addition operator token into a string."""
        return items[0]

    def PLUS(self, _):  # noqa: N802
        return Token("ADD_OP", "+")  # type: ignore

    def MINUS(self, _):  # noqa: N802
        return Token("ADD_OP", "-")  # type: ignore

    def product(self, items):
        """Transform a product into a BinaryExpression or pass through."""
        item = self._unwrap_tree(items[0])
        if len(items) == 1:
            return self._ensure_expr(item)
        result = self._ensure_expr(self._unwrap_tree(items[0]))
        for i in range(1, len(items), 2):
            operator_item = items[i]
            operator_value = operator_item.children[0].value if hasattr(operator_item, "children") else operator_item.value
            operator = self._get_binary_operator(operator_value)
            right = self._ensure_expr(self._unwrap_tree(items[i + 1]))
            result = BinaryExpression(left=result, operator=operator, right=right)
        return result

    def mul_op(self, items):
        """Transform a multiplication operator token into a string."""
        return items[0]

    def MULT(self, _):  # noqa: N802
        return Token("MUL_OP", "*")  # type: ignore

    def DIV(self, _):  # noqa: N802
        return Token("MUL_OP", "/")  # type: ignore

    def MOD(self, _):  # noqa: N802
        return Token("MUL_OP", "%")  # type: ignore

    def atom(self, items):
        """Transform an atom into an AST node or pass through."""
        return self._unwrap_tree(items[0])

    def TRUE(self, _):  # noqa: N802
        """Transform a TRUE token into a LiteralExpression with value True."""
        return LiteralExpression(value=True)

    def FALSE(self, _):  # noqa: N802
        """Transform a FALSE token into a LiteralExpression with value False."""
        return LiteralExpression(value=False)

    def array_literal(self, items):
        """Transform an array literal into a LiteralExpression node."""
        # If empty array, return empty list
        if len(items) == 0:
            return LiteralExpression(value=[])

        # If we have array items, extract them
        array_items = items[0] if len(items) > 0 else []

        # Convert to a Literal node with a list value
        return LiteralExpression(value=array_items)

    def array_items(self, items):
        """Transform array items into a list."""
        return items

    def literal(self, items):
        """Transform a literal into a LiteralExpression or pass through."""
        return self._unwrap_tree(items[0])

    def identifier(self, items):
        # This method is now handled by VariableTransformer
        raise NotImplementedError("identifier is handled by VariableTransformer")

    def not_expr(self, items):
        """Transform a not expression into a BinaryExpression or pass through."""
        return self._unwrap_tree(items[0])

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

    def _ensure_expr(self, node):
        # Helper to ensure node is a valid Expression type
        if isinstance(node, (LiteralExpression, BinaryExpression, FunctionCall)):
            return node
        if isinstance(node, Identifier):
            return node
        # If it's a Token, treat as a literal value
        if isinstance(node, Token):
            return LiteralExpression(value=node.value)
        return node
