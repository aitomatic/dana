"""Parser factory for DANA language.

This module provides a factory for creating DANA parsers, allowing users to
perform optional type checking.
"""

import os
from enum import Enum
from typing import Callable, Optional

from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.language.parser import ParseResult, parse
from opendxa.dana.language.type_checker import check_types

# Type alias for parser functions
ParserFunc = Callable[[str], ParseResult]


class ParserType(Enum):
    """Types of parsers available for DANA language."""

    GRAMMAR = "grammar"  # Grammar-based parser using Lark


class ParserFactory:
    """Factory for creating DANA parsers."""

    def __init__(self):
        """Initialize the parser factory."""
        self._parsers = {}
        self._default_parser = ParserType.GRAMMAR
        self._type_check_enabled = True

        # Register the grammar parser
        self.register_parser(ParserType.GRAMMAR, parse)

    def set_default_parser(self, parser_type: ParserType) -> None:
        """Set the default parser type.

        Args:
            parser_type: The parser type to use as default
        """
        if parser_type not in self._parsers:
            raise ValueError(f"Unknown parser type: {parser_type}")
        self._default_parser = parser_type

    def set_type_checking(self, enabled: bool) -> None:
        """Enable or disable type checking.

        Args:
            enabled: Whether to enable type checking
        """
        self._type_check_enabled = enabled

    def register_parser(self, parser_type: ParserType, parse_func: ParserFunc) -> None:
        """Register a new parser implementation.

        Args:
            parser_type: The parser type to register
            parse_func: The parsing function to use
        """
        self._parsers[parser_type] = parse_func

    def parse(self, code: str, parser_type: Optional[ParserType] = None, type_check: Optional[bool] = None) -> ParseResult:
        """Parse DANA code using the specified or default parser.

        Args:
            code: The DANA code to parse
            parser_type: The parser type to use, or None for default
            type_check: Whether to perform type checking, or None to use default setting

        Returns:
            A ParseResult containing the parsed program and any errors

        Raises:
            ValueError: If the specified parser type is not registered
        """
        # Use default parser if not specified
        parser_type = parser_type or self._default_parser

        if parser_type not in self._parsers:
            raise ValueError(f"Unknown parser type: {parser_type}")

        # Use factory default for type checking if not specified
        if type_check is None:
            type_check = self._type_check_enabled

        # Get the parser function
        parse_func = self._parsers[parser_type]

        # Parse the code
        result = parse_func(code)

        # Perform type checking if enabled and parsing was successful
        if type_check and result.is_valid:
            type_errors = check_types(result.program)
            if type_errors:
                # Add type errors to the result
                result = ParseResult(program=result.program, errors=list(result.errors) + type_errors)

        return result


# Check for environment variable to control type checking

# Create a logger for dana
logger = DXA_LOGGER.getLogger("opendxa.dana.language.ParserFactory")

# Environment variable keys
ENV_TYPE_CHECK = "DANA_TYPE_CHECK"

# Parse environment variables
ENABLE_TYPE_CHECK = os.environ.get(ENV_TYPE_CHECK, "1").lower() in ["1", "true", "yes", "y"]

# Create a singleton instance of the parser factory
_parser_factory = ParserFactory()

# Set type checking based on environment variable
_parser_factory.set_type_checking(ENABLE_TYPE_CHECK)
if not ENABLE_TYPE_CHECK:
    logger.info("Type checking disabled for DANA (controlled by DANA_TYPE_CHECK environment variable)")


def get_parser_factory() -> ParserFactory:
    """Get the singleton parser factory instance.

    Returns:
        The parser factory instance
    """
    return _parser_factory
