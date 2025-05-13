"""F-string expression transformer for DANA language parsing.

Handles the f_string rule in the grammar:
    f_string: "f" REGULAR_STRING

Parses f-strings with embedded expressions, returning a LiteralExpression(FStringExpression(...)).
Follows the style and best practices of StatementTransformer and ExpressionTransformer.
"""

from typing import Any, List

from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.parser.ast import (
    BinaryExpression,
    BinaryOperator,
    FStringExpression,
    Identifier,
    LiteralExpression,
)
from opendxa.dana.parser.transformers.base_transformer import BaseTransformer


class FStringTransformer(BaseTransformer):
    """
    Transforms f-string parse tree nodes into AST FStringExpression nodes.

    Handles the f_string rule in the DANA grammar, parsing embedded expressions and returning
    a LiteralExpression(FStringExpression(...)).
    """

    # === Entry Point ===
    def f_string(self, items):
        """
        Transform an f-string rule into a LiteralExpression node with FStringExpression.
        Grammar: f_string: "f" REGULAR_STRING
        Example: f"Hello {name}!" -> LiteralExpression(value=FStringExpression(parts=["Hello ", Identifier(name="local.name"), "!"]))
        """
        s = items[0].value
        # Remove quotes (single or double)
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        elif s.startswith("'") and s.endswith("'"):
            s = s[1:-1]

        parts = self._parse_fstring_parts(s)
        fstring_expr = FStringExpression(parts=parts)
        setattr(fstring_expr, "_is_fstring", True)
        setattr(fstring_expr, "_original_text", s)
        return LiteralExpression(value=fstring_expr)

    # === Parsing Helpers ===
    def _parse_fstring_parts(self, s: str) -> List:
        """
        Parse an f-string into its component parts (literals and expressions).
        Returns a list of strings and AST nodes.
        Example: 'Hello {name}!' -> ["Hello ", Identifier(name="local.name"), "!"]
        """
        parts = []
        current_text = ""
        i = 0
        while i < len(s):
            if s[i] == "{" and (i == 0 or s[i - 1] != "\\"):
                # Found start of expression
                if current_text:
                    parts.append(current_text)
                    current_text = ""
                # Find the matching closing brace
                brace_level = 1
                expr_text = ""
                i += 1
                while i < len(s) and brace_level > 0:
                    if s[i] == "{" and s[i - 1] != "\\":
                        brace_level += 1
                    elif s[i] == "}" and s[i - 1] != "\\":
                        brace_level -= 1
                    if brace_level > 0:
                        expr_text += s[i]
                    i += 1
                if brace_level != 0:
                    raise ValueError("Unbalanced braces in f-string expression.")
                if expr_text:
                    expr_text = expr_text.strip()
                    part = self._parse_expression_in_fstring(expr_text)
                    parts.append(part)
            else:
                current_text += s[i]
                i += 1
        if current_text:
            parts.append(current_text)
        return parts

    def _parse_expression_in_fstring(self, expr_text: str) -> Any:
        """
        Parse an expression found in an f-string placeholder.
        Supports simple binary operations and identifiers.
        TODO: Support full DANA expressions using the main ExpressionTransformer.
        """
        binary_ops = [
            ("+", BinaryOperator.ADD),
            ("-", BinaryOperator.SUBTRACT, lambda x: not x.startswith("-")),  # Not negative number
            ("*", BinaryOperator.MULTIPLY),
            ("/", BinaryOperator.DIVIDE),
        ]
        for op_spec in binary_ops:
            op_str = op_spec[0]
            op_enum = op_spec[1]
            condition_func = op_spec[2] if len(op_spec) > 2 else None
            if op_str in expr_text and (condition_func is None or condition_func(expr_text)):
                left, right = expr_text.split(op_str, 1)
                left = left.strip()
                right = right.strip()
                left_expr = self._parse_expression_term(left)
                right_expr = self._parse_expression_term(right)
                return BinaryExpression(left=left_expr, operator=op_enum, right=right_expr)
        # If no binary operation, parse as a single term
        return self._parse_expression_term(expr_text)

    def _parse_expression_term(self, term: str) -> Any:
        """
        Parse a single term in an f-string expression.
        Returns an Identifier if the term is a valid variable, else a LiteralExpression.
        Example: 'foo' -> Identifier(name='local.foo')
                 '42' -> LiteralExpression(value=42)
        """
        term = term.strip()
        if term.replace(".", "").isalnum():
            parts = term.split(".")
            if parts[0] not in RuntimeScopes.ALL:
                parts = self._insert_local_scope(parts)
            return Identifier(name=".".join(parts))
        else:
            return self._parse_literal(term)
