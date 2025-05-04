"""Extremely simple parser for DANA Iteration 1: Assignments only."""

import re
from typing import List

from opendxa.dana.language.ast import (
    Program, Statement, Assignment, Identifier, Literal, LiteralExpression,
    LogStatement
)
from opendxa.dana.exceptions import ParseError

# Very basic regex for Iteration 1: scope.variable = value
# Allows spaces around =, captures scope.variable and the rest
# Value parsing is rudimentary
ASSIGNMENT_REGEX = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$")

# Regex for log statement (Iteration 1 - simple string literal only)
# Captures the content inside the quotes
LOG_REGEX = re.compile(r"^\s*log\(\s*\"(.*)\"\s*\)\s*$")

def parse_literal(value_str: str) -> Literal:
    """Attempts to parse a string into an Integer or String Literal."""
    value_str = value_str.strip()
    # Check if it's an integer
    if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
        return Literal(value=int(value_str))
    # Check if it's a quoted string (simple check)
    if (value_str.startswith('"') and value_str.endswith('"')):
        # No need to strip quotes here if the regex/caller handles it
        return Literal(value=value_str[1:-1])
    # Removed single quote option for simplicity with log regex

    # Basic fallback for Iteration 1: treat as unquoted string if not number/quoted?
    # Or raise error? Let's raise error for stricter parsing.
    # raise ParseError(f"Cannot parse literal value: '{value_str}'")
    # KISS: For Iteration 1, maybe allow unquoted strings if they don't look like numbers?
    # Let's be strict for now.
    raise ParseError(f"Invalid literal value: '{value_str}'. Only integers and double-quoted strings supported currently.")


def parse(code: str) -> Program:
    """Parses a DANA program string (Iteration 1: assignments and log)."""
    statements: List[Statement] = []
    lines = code.splitlines()

    for line_num, line in enumerate(lines, 1):
        # original_line = line # Keep original for error messages if needed (Removed for now)
        line = line.strip()
        if not line or line.startswith('#'):  # Skip empty lines and comments
            continue

        # Try matching log statement first
        log_match = LOG_REGEX.match(line)
        if log_match:
            message_str = log_match.group(1)
            # Note: The regex ensures the message is a simple string literal content
            message_literal = Literal(value=message_str)
            message_expr = LiteralExpression(literal=message_literal)
            log_node = LogStatement(message=message_expr)
            statements.append(log_node)
            continue  # Move to next line

        # If not log, try matching assignment
        assign_match = ASSIGNMENT_REGEX.match(line)
        if assign_match:
            target_str, value_str = assign_match.groups()

            # Validate identifier format simply (scope.variable)
            # Note: parser already checks this somewhat with regex, but good practice
            if '.' not in target_str or target_str.count('.') != 1:
                # This check might be redundant given the regex, but kept for clarity
                raise ParseError(f"Line {line_num}: Invalid target identifier format '{target_str}'. Expected 'scope.variable'.")

            # Validate value is not empty
            if not value_str:
                raise ParseError(f"Line {line_num}: Missing value for assignment to '{target_str}'")

            try:
                literal_node = parse_literal(value_str)
            except ParseError as e:
                raise ParseError(f"Line {line_num}: {e}") from e

            target_node = Identifier(name=target_str)
            value_node = LiteralExpression(literal=literal_node)
            assignment_node = Assignment(target=target_node, value=value_node)
            statements.append(assignment_node)
        else:
            # If it's not log or assignment, it's an error in Iteration 1
            raise ParseError(f"Line {line_num}: Invalid syntax. Expected assignment, log statement, or comment.")

    return Program(statements=statements) 