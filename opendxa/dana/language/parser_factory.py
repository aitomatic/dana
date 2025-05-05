"""Parser factory for DANA language.

This module provides a factory for creating DANA parsers, allowing users to
choose between the regex-based parser and the Lark-based parser, and also
provides optional type checking.
"""

from typing import Callable, List

from opendxa.dana.exceptions import TypeError
from opendxa.dana.language.parser import ParseResult, parse as regex_parse
from opendxa.dana.language.type_checker import check_types

# Feature flags to control parser behavior
USE_LARK_PARSER_DEFAULT = False
TYPE_CHECK_DEFAULT = True

# Type alias for parser functions
ParserFunc = Callable[[str], ParseResult]


def get_parser(use_lark: bool = USE_LARK_PARSER_DEFAULT) -> ParserFunc:
    """Get a parser implementation based on the specified parser type.
    
    Args:
        use_lark: Whether to use the Lark-based parser (default: False)
        
    Returns:
        A parser function that takes a code string and returns a ParseResult
    """
    if use_lark:
        try:
            from opendxa.dana.language.lark_parser import parse as lark_parse
            return lark_parse
        except ImportError:
            # Fallback to regex parser if Lark is not available
            return regex_parse
    else:
        return regex_parse


def parse(
    code: str,
    use_lark: bool = USE_LARK_PARSER_DEFAULT,
    type_check: bool = TYPE_CHECK_DEFAULT
) -> ParseResult:
    """Parse DANA code using the specified parser implementation.
    
    Args:
        code: The DANA code to parse
        use_lark: Whether to use the Lark-based parser (default: False)
        type_check: Whether to perform type checking (default: False)
        
    Returns:
        A ParseResult containing the parsed program and any errors
    """
    parser = get_parser(use_lark)
    result = parser(code)
    
    if type_check and result.is_valid:
        # Only do type checking if parsing was successful
        type_errors = check_types(result.program)
        if type_errors:
            # Add type errors to the result
            result = ParseResult(
                program=result.program,
                errors=list(result.errors) + type_errors
            )
    
    return result