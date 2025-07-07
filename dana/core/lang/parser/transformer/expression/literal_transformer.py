"""
Literal transformer for Dana language parsing.

This module handles all literal expressions including:
- String literals (regular, f-strings, raw strings, multiline)
- Number literals (integers, floats)
- Boolean literals (true, false)
- None literals
- Basic identifier handling

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from lark import Token

from dana.core.lang.ast import Identifier, LiteralExpression
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer


class LiteralTransformer(BaseTransformer):
    """Transformer for literal expressions and basic values."""

    def literal(self, items):
        """Transform a literal rule into a LiteralExpression."""
        # Unwrap and convert all literal tokens/trees to primitives
        return self.atom(items)

    def atom(self, items):
        """Transform an atom rule into appropriate literal or identifier."""
        if not items:
            return None

        item = items[0]

        # Use TreeTraverser to unwrap single-child trees
        item = self.tree_traverser.unwrap_single_child_tree(item)

        # Handle tokens directly
        if isinstance(item, Token):
            return self._atom_from_token(item)

        # Handle other cases
        return item

    def _atom_from_token(self, token):
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

    def string_literal(self, items):
        """
        Handle string_literal rule from the grammar.

        Supports REGULAR_STRING, F_STRING_TOKEN, RAW_STRING, SINGLE_QUOTED_STRING, MULTILINE_STRING.
        """
        if not items:
            return LiteralExpression("")

        item = items[0]

        if isinstance(item, Token):
            # F-string handling
            if item.type == "F_STRING_TOKEN":
                # Pass to the FStringTransformer
                from dana.core.lang.parser.transformer.fstring_transformer import FStringTransformer

                fstring_transformer = FStringTransformer()
                return fstring_transformer.fstring([item])

            # Regular string
            elif item.type == "REGULAR_STRING":
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

        # If we reach here, it's an unexpected string type
        self.error(f"Unexpected string literal type: {type(item)}")
        return LiteralExpression("")

    def identifier(self, items):
        """Handle identifier transformation (fallback from VariableTransformer)."""
        if len(items) == 1 and isinstance(items[0], Token):
            return Identifier(name=items[0].value)
        raise TypeError(f"Cannot transform identifier: {items}")

    # Token handlers for boolean and none literals
    def TRUE(self, token):
        """Handle TRUE token."""
        return LiteralExpression(value=True)

    def FALSE(self, token):
        """Handle FALSE token."""
        return LiteralExpression(value=False)

    def NONE(self, token):
        """Handle NONE token."""
        return LiteralExpression(value=None)

    def NUMBER(self, token):
        """Handle NUMBER token."""
        value = token.value
        if "." in value:
            return LiteralExpression(value=float(value))
        else:
            return LiteralExpression(value=int(value))

    def REGULAR_STRING(self, token):
        """Handle REGULAR_STRING token."""
        value = token.value[1:-1]  # Strip quotes
        return LiteralExpression(value)

    def SINGLE_QUOTED_STRING(self, token):
        """Handle SINGLE_QUOTED_STRING token."""
        value = token.value[1:-1]  # Strip quotes
        return LiteralExpression(value)

    def RAW_STRING(self, token):
        """Handle RAW_STRING token."""
        value = token.value
        if value.startswith('r"') and value.endswith('"'):
            value = value[2:-1]
        elif value.startswith("r'") and value.endswith("'"):
            value = value[2:-1]
        return LiteralExpression(value)

    def MULTILINE_STRING(self, token):
        """Handle MULTILINE_STRING token."""
        value = token.value
        if value.startswith('"""') and value.endswith('"""'):
            value = value[3:-3]
        elif value.startswith("'''") and value.endswith("'''"):
            value = value[3:-3]
        return LiteralExpression(value)
