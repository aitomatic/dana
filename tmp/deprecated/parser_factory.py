"""Parser factory for DANA language.

This module provides a factory for creating DANA parsers, allowing users to
choose between different parser implementations and perform optional type checking.
"""

from enum import Enum
from typing import Callable, Optional

from opendxa.dana.language.parser import ParseResult
from opendxa.dana.language.parser import parse as regex_parse
from opendxa.dana.language.type_checker import check_types

# Try to import Lark parser
try:
    from opendxa.dana.language.lark_parser import _grammar_parser
    from opendxa.dana.language.lark_parser import parse as grammar_parse

    GRAMMAR_PARSER_AVAILABLE = _grammar_parser.is_available()
except ImportError:
    GRAMMAR_PARSER_AVAILABLE = False

    # Define a stub function if grammar parser is not available
    def grammar_parse(code: str) -> ParseResult:
        from opendxa.dana.exceptions import ParseError
        from opendxa.dana.language.ast import Program

        return ParseResult(program=Program(statements=[]), errors=[ParseError("Grammar parser not available")])


# Type alias for parser functions
ParserFunc = Callable[[str], ParseResult]


class ParserType(Enum):
    """Types of parsers available for DANA language."""

    REGEX = "regex"  # Original regex-based parser
    GRAMMAR = "grammar"  # Grammar-based parser using Lark


class ParserFactory:
    """Factory for creating DANA parsers.

    This factory manages different parser implementations and allows switching
    between them based on configuration or feature flags.
    """

    def __init__(self):
        """Initialize the parser factory."""
        self._parsers = {
            ParserType.REGEX: regex_parse,
            ParserType.GRAMMAR: grammar_parse,
        }
        # Default to regex parser since it's always available
        self._default_parser = ParserType.REGEX
        # Default to enabling type checking
        self._type_check_enabled = True

    def set_default_parser(self, parser_type: ParserType) -> None:
        """Set the default parser type.

        Args:
            parser_type: The parser type to use as default

        Raises:
            ValueError: If the specified parser type is not available
        """
        if parser_type not in self._parsers:
            raise ValueError(f"Unknown parser type: {parser_type}")

        if parser_type == ParserType.GRAMMAR and not GRAMMAR_PARSER_AVAILABLE:
            raise ValueError("Grammar parser is not available. Install lark-parser package.")

        self._default_parser = parser_type

    def get_default_parser_type(self) -> ParserType:
        """Get the current default parser type.

        Returns:
            The current default parser type
        """
        return self._default_parser

    def set_type_checking(self, enabled: bool) -> None:
        """Enable or disable type checking.

        Args:
            enabled: Whether to enable type checking
        """
        self._type_check_enabled = enabled

    def is_type_checking_enabled(self) -> bool:
        """Check if type checking is enabled.

        Returns:
            True if type checking is enabled, False otherwise
        """
        return self._type_check_enabled

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

        # Fall back to regex parser if grammar parser is requested but not available
        if parser_type == ParserType.GRAMMAR and not GRAMMAR_PARSER_AVAILABLE:
            parser_type = ParserType.REGEX

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

    def is_parser_available(self, parser_type: ParserType) -> bool:
        """Check if a parser type is available.

        Args:
            parser_type: The parser type to check

        Returns:
            True if the parser is available, False otherwise
        """
        if parser_type not in self._parsers:
            return False

        if parser_type == ParserType.GRAMMAR:
            return GRAMMAR_PARSER_AVAILABLE

        return True


# Check for environment variable to control parser type
import logging
import os

# Create a logger for dana
logger = logging.getLogger("dana")

# Environment variable keys
ENV_USE_GRAMMAR_PARSER = "DANA_USE_GRAMMAR_PARSER"
ENV_TYPE_CHECK = "DANA_TYPE_CHECK"

# Parse environment variables
USE_GRAMMAR_PARSER = os.environ.get(ENV_USE_GRAMMAR_PARSER, "").lower() in ["1", "true", "yes", "y"]
ENABLE_TYPE_CHECK = os.environ.get(ENV_TYPE_CHECK, "1").lower() in ["1", "true", "yes", "y"]

# Create a singleton instance of the parser factory
_parser_factory = ParserFactory()

# Set type checking based on environment variable
_parser_factory.set_type_checking(ENABLE_TYPE_CHECK)
if not ENABLE_TYPE_CHECK:
    logger.info("Type checking disabled for DANA (controlled by DANA_TYPE_CHECK environment variable)")

# Set default parser based on environment variable
if USE_GRAMMAR_PARSER:
    if GRAMMAR_PARSER_AVAILABLE:
        try:
            _parser_factory.set_default_parser(ParserType.GRAMMAR)
            logger.info("Using grammar-based parser for DANA (controlled by DANA_USE_GRAMMAR_PARSER environment variable)")
        except ValueError:
            # Fall back to regex parser if grammar parser is not available
            logger.warning("Grammar-based parser is not available, falling back to regex parser")
            _parser_factory.set_default_parser(ParserType.REGEX)
    else:
        logger.warning("Grammar-based parser requested but not available. Install lark-parser package.")
        logger.warning("Falling back to regex parser")
        _parser_factory.set_default_parser(ParserType.REGEX)


def get_parser_factory() -> ParserFactory:
    """Get the singleton parser factory instance.

    Returns:
        The parser factory instance
    """
    return _parser_factory


def get_parser(parser_type: Optional[ParserType] = None) -> ParserFunc:
    """Get a parser function for the specified parser type.

    Args:
        parser_type: The parser type to use, or None for default

    Returns:
        A parser function that takes a code string and returns a ParseResult
    """
    factory = get_parser_factory()
    parser_type = parser_type or factory.get_default_parser_type()

    if parser_type == ParserType.GRAMMAR and not factory.is_parser_available(ParserType.GRAMMAR):
        # Fall back to regex parser if grammar parser is not available
        parser_type = ParserType.REGEX

    if parser_type == ParserType.REGEX:
        return regex_parse
    elif parser_type == ParserType.GRAMMAR:
        return grammar_parse
    else:
        raise ValueError(f"Unknown parser type: {parser_type}")


def parse(code: str, parser_type: Optional[ParserType] = None, type_check: Optional[bool] = None) -> ParseResult:
    """Parse DANA code using the specified or default parser with optional type checking.

    This is a convenience function that uses the singleton parser factory.

    Args:
        code: The DANA code to parse
        parser_type: The parser type to use, or None for default
        type_check: Whether to perform type checking, or None to use default setting

    Returns:
        A ParseResult containing the parsed program and any errors
    """
    return get_parser_factory().parse(code, parser_type, type_check)


# Compatibility with older API
def parse_with_type_checking(code: str, use_lark: bool = False) -> ParseResult:
    """Parse DANA code with type checking.

    This function is provided for compatibility with older code.

    Args:
        code: The DANA code to parse
        use_lark: Whether to use the Lark-based parser

    Returns:
        A ParseResult containing the parsed program and any errors
    """
    parser_type = ParserType.GRAMMAR if use_lark else ParserType.REGEX
    return parse(code, parser_type, True)
