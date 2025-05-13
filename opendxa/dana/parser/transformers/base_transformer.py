"""Base transformer class for DANA language parsing."""

from typing import Any, Union

from lark import Token, Tree

from opendxa.dana.common.exceptions import ParseError
from opendxa.dana.parser.ast import ASTNode, LiteralExpression


class BaseTransformer:
    """Base class for DANA AST transformers.

    Provides common utility methods for transforming Lark parse trees into DANA AST nodes.
    """

    def _parse_literal(self, text):
        """Parse a simple literal value from text."""
        text = text.strip()

        # Try numbers first
        try:
            if "." in text:
                return LiteralExpression(value=float(text))
            else:
                return LiteralExpression(value=int(text))
        except ValueError:
            pass

        # Try boolean
        if text.lower() == "true":
            return LiteralExpression(value=True)
        elif text.lower() == "false":
            return LiteralExpression(value=False)

        # Try string (with quotes)
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            return LiteralExpression(value=text[1:-1])

        # Default to string
        return LiteralExpression(value=text)

    def _create_literal(self, token):
        """Create a LiteralExpression node from a token."""
        token_type = token.type
        value = token.value

        if token_type == "STRING":
            # Remove quotes (either single or double)
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            return LiteralExpression(value=value)
        elif token_type == "NUMBER":
            # Check if it's an integer or float
            if "." in value:
                return LiteralExpression(value=float(value))
            else:
                return LiteralExpression(value=int(value))
        elif token_type == "BOOL":
            return LiteralExpression(value=value.lower() == "true")
        elif value == "null":
            return LiteralExpression(value=None)

        # Fallback
        return LiteralExpression(value=value)

    def _insert_local_scope(self, parts: Union[list[str], str]) -> Any:
        """Insert local scope prefix to parts if not already present."""
        if isinstance(parts, str):
            if "." in parts:
                raise ParseError(f"Local variable must be a simple name: {parts}")
            return f"local.{parts}"
        elif isinstance(parts, list):
            if len(parts) == 0:
                raise ParseError("No local variable name provided")
            elif len(parts) > 1:
                # For nested identifiers, keep as is
                return parts
            else:
                parts.insert(0, "local")
                return parts
        else:
            raise ParseError(f"Invalid type for local variable: {type(parts)}")

    def _unwrap_tree(self, item: Union[Tree, Token, ASTNode]) -> Union[Token, ASTNode]:
        """Recursively unwrap a Tree until an AST node or token is reached."""
        while hasattr(item, "children") and len(item.children) == 1:
            item = item.children[0]
        return item  # type: ignore
