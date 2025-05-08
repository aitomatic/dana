"""Base transformer class for DANA language parsing."""

from opendxa.dana.language.ast import Literal


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
                return Literal(value=float(text))
            else:
                return Literal(value=int(text))
        except ValueError:
            pass

        # Try boolean
        if text.lower() == "true":
            return Literal(value=True)
        elif text.lower() == "false":
            return Literal(value=False)

        # Try string (with quotes)
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            return Literal(value=text[1:-1])

        # Default to string
        return Literal(value=text)

    def _create_literal(self, token):
        """Create a Literal node from a token."""
        token_type = token.type
        value = token.value

        if token_type == "STRING":
            # Remove quotes (either single or double)
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            return Literal(value=value)
        elif token_type == "NUMBER":
            # Check if it's an integer or float
            if "." in value:
                return Literal(value=float(value))
            else:
                return Literal(value=int(value))
        elif token_type == "BOOL":
            return Literal(value=value.lower() == "true")
        elif value == "null":
            return Literal(value=None)

        # Fallback
        return Literal(value=value)
