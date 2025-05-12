"""F-string expression transformer for DANA language parsing."""

from typing import Any, List

from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.language.ast import (
    BinaryExpression,
    BinaryOperator,
    FStringExpression,
    Identifier,
    LiteralExpression,
)
from opendxa.dana.language.transformers.base_transformer import BaseTransformer


class FStringTransformer(BaseTransformer):
    """Transformer for f-string expressions."""

    def f_string(self, items):
        """Transform an f-string rule into a LiteralExpression node with FStringExpression."""
        # Remove the 'f' and quotes
        s = items[0].value
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]  # Remove quotes
        elif s.startswith("'") and s.endswith("'"):
            s = s[1:-1]  # Remove quotes

        parts = self._parse_fstring_parts(s)

        # Create the f-string expression
        fstring_expr = FStringExpression(parts=parts)

        # Set special flags for runtime evaluation
        setattr(fstring_expr, "_is_fstring", True)
        setattr(fstring_expr, "_original_text", s)

        return LiteralExpression(literal=Literal(value=fstring_expr))

    def _parse_fstring_parts(self, s: str) -> List:
        """Parse an f-string into its component parts."""
        # Parse f-string for {expression} placeholders
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
                start_idx = i + 1
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

                if expr_text:
                    expr_text = expr_text.strip()
                    part = self._parse_expression_in_fstring(expr_text)
                    parts.append(part)
            else:
                current_text += s[i]
                i += 1

        if current_text:
            parts.append(current_text)

        # Add special marker for simple strings that need variable substitution
        if not parts:
            parts = [f"F-STRING-PLACEHOLDER:{s}"]
        elif len(parts) == 1 and isinstance(parts[0], str):
            parts = [f"F-STRING-PLACEHOLDER:{s}"]

        return parts

    def _parse_expression_in_fstring(self, expr_text: str) -> Any:
        """Parse expressions found in f-string placeholders."""
        # Handle simple binary operations
        binary_ops = [
            ("+", BinaryOperator.ADD),
            ("-", BinaryOperator.SUBTRACT, lambda x: not x.startswith("-")),  # Not negative number
            ("*", BinaryOperator.MULTIPLY),
            ("/", BinaryOperator.DIVIDE),
        ]

        for op_spec in binary_ops:
            op_str = op_spec[0]
            op_enum = op_spec[1]

            # Check if we need to apply a condition to this operator
            condition_func = op_spec[2] if len(op_spec) > 2 else None

            if op_str in expr_text and (condition_func is None or condition_func(expr_text)):
                left, right = expr_text.split(op_str, 1)
                left = left.strip()
                right = right.strip()

                # Convert to appropriate expression nodes
                left_expr = self._parse_expression_term(left)
                right_expr = self._parse_expression_term(right)

                return BinaryExpression(left=left_expr, operator=op_enum, right=right_expr)

        # If no binary operation, parse as a single term
        return self._parse_expression_term(expr_text)

    def _parse_expression_term(self, term: str) -> Any:
        """Parse a single term in an f-string expression."""
        if "." in term or term.isalnum():
            # Add local scope if no scope prefix
            parts = term.split(".")
            if parts[0] not in RuntimeScopes.ALL:
                parts = self._insert_local_scope(parts)
            return Identifier(name=".".join(parts))
        else:
            return LiteralExpression(literal=self._parse_literal(term))
