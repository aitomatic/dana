"""
Parsing utility functions for Dana language parsing.

This module provides utilities for literal parsing, expression parsing,
and parser caching to avoid circular dependencies.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from lark import Token

from dana.core.lang.ast import LiteralExpression


class ParserCache:
    """Thread-safe cache for parser instances to avoid creating multiple parsers."""

    _instances: dict[str, Any] = {}

    @classmethod
    def get_parser(cls, parser_type: str = "dana") -> Any:
        """Get a cached parser instance or create a new one.

        Args:
            parser_type: Type of parser to get (default: "dana")

        Returns:
            Parser instance
        """
        if parser_type not in cls._instances:
            # Import here to avoid circular dependencies
            from dana.core.lang.parser.dana_parser import DanaParser

            cls._instances[parser_type] = DanaParser()

        return cls._instances[parser_type]

    @classmethod
    def clear_cache(cls):
        """Clear the parser cache."""
        cls._instances.clear()


def parse_literal(text: Any) -> LiteralExpression:
    """Parse a simple literal value from text or Token.

    Args:
        text: Text or Token to parse

    Returns:
        LiteralExpression containing the parsed value
    """
    # Unwrap Token to its value
    if isinstance(text, Token):
        text = text.value
    if isinstance(text, str):
        text = text.strip()

    # Try numbers first
    try:
        if isinstance(text, str) and "." in text:
            return LiteralExpression(value=float(text))
        elif isinstance(text, str):
            return LiteralExpression(value=int(text))
        elif isinstance(text, int | float):
            return LiteralExpression(value=text)
    except ValueError:
        pass

    # Try boolean
    if isinstance(text, str):
        if text.lower() == "true":
            return LiteralExpression(value=True)
        elif text.lower() == "false":
            return LiteralExpression(value=False)

    # Try string (with quotes)
    if isinstance(text, str) and ((text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'"))):
        return LiteralExpression(value=text[1:-1])

    # Default to string
    return LiteralExpression(value=text)


def create_literal(token: Token) -> LiteralExpression:
    """Create a LiteralExpression node from a token.

    Args:
        token: Token to convert to literal

    Returns:
        LiteralExpression containing the token value
    """
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


def parse_expression_in_fstring(expr_text: str) -> Any | None:
    """Parse an expression within an f-string using a cached parser.

    This function is extracted to avoid circular dependencies between
    FStringTransformer and DanaParser.

    Args:
        expr_text: Expression text to parse

    Returns:
        Parsed AST node or None if parsing fails
    """
    try:
        from lark import UnexpectedInput, UnexpectedToken

        # Get cached parser instance
        parser = ParserCache.get_parser("dana")

        # Create a temporary expression wrapper for the parser
        # We need to make this a valid complete expression and add a newline
        wrapped_expr = f"{expr_text}\n"

        # Parse the expression directly
        try:
            # Try to parse as a complete expression
            parse_tree = parser.parse(wrapped_expr, do_transform=True)

            # Extract the resulting expression from the parsed program
            if hasattr(parse_tree, "statements") and parse_tree.statements:
                # If the parser returns a Program, extract the expression
                if len(parse_tree.statements) == 1:
                    stmt = parse_tree.statements[0]
                    # If it's a FunctionCall or an Identifier, return it directly
                    if hasattr(stmt, "value"):
                        return stmt.value
                    return stmt

            # Fallback to None if extraction fails
            return None

        except (UnexpectedInput, UnexpectedToken):
            # Return None for parsing errors
            return None

    except Exception:
        # Return None for any other errors
        return None
