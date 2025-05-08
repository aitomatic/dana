"""Error handling utilities for DANA language parsing."""

from typing import List, Optional, Tuple

from opendxa.dana.exceptions import ParseError
from opendxa.dana.language.ast import Program


def create_error_message(error_text: str, line: int, column: int, source_line: str, adjustment: Optional[str] = None) -> str:
    """Create a formatted error message with location information.

    Args:
        error_text: The main error description
        line: The line number where the error occurred
        column: The column number where the error occurred
        source_line: The source code line containing the error
        adjustment: Optional adjustment to the error position

    Returns:
        A formatted error message string
    """
    location_info = f"Syntax error at line {line}, column {column}"
    indicator = " " * column + "^"

    if adjustment:
        return f"{location_info}: {error_text}\n{source_line}\n{indicator} {adjustment}"
    else:
        return f"{location_info}: {error_text}\n{source_line}\n{indicator}"


def handle_parse_error(e: Exception, program_text: str) -> Tuple[Program, List[ParseError]]:
    """Handle parse errors and create appropriate error objects.

    Args:
        e: The exception that occurred during parsing
        program_text: The source code being parsed

    Returns:
        A tuple of (empty program, list of parse errors)
    """
    errors = []
    lines = program_text.split("\n")

    # Create an empty program as a fallback
    empty_program = Program(statements=[], source_text=program_text)

    if hasattr(e, "line") and hasattr(e, "column"):
        # This is likely an UnexpectedInput error
        error_line = lines[e.line - 1] if e.line > 0 and e.line <= len(lines) else ""
        column = e.column

        # Adjust error message for assignment errors
        if "=" in error_line:
            equals_pos = error_line.find("=")
            if column > equals_pos and "#" in error_line[equals_pos:]:
                # It's likely a missing expression after equals sign
                comment_pos = error_line.find("#", equals_pos)
                if comment_pos > equals_pos and (comment_pos - equals_pos <= 3):
                    column = equals_pos + 1
                    error_msg = create_error_message(
                        "Missing expression after equals sign", e.line, column, error_line, "Missing expression after equals sign"
                    )
                    errors.append(ParseError(error_msg, e.line, error_line))
                    return empty_program, errors

        # Clean up the error message
        error_text = str(e)
        if "Expected one of:" in error_text:
            # Split into main error and expected tokens
            parts = error_text.split("Expected one of:")
            main_error = parts[0].strip()
            expected = parts[1].strip()
            # Format expected tokens more cleanly
            expected = expected.replace("\n", ", ").replace("\t", "").replace("* ", "")
            error_text = f"{main_error}\nExpected: {expected}"

        # Generic error message
        error_msg = create_error_message(error_text, e.line, column, error_line)
        errors.append(ParseError(error_msg, e.line, error_line))
    else:
        # Generic error without position information
        error_msg = f"Parsing error: {str(e)}"
        errors.append(ParseError(error_msg, 0, lines[0] if lines else ""))

    return empty_program, errors
