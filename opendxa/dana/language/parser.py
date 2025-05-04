"""Parser for DANA language."""

import re
from typing import List, NamedTuple, Optional, Tuple

from opendxa.dana.exceptions import ParseError
from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    Expression,
    FunctionCall,
    Identifier,
    Literal,
    LiteralExpression,
    LogStatement,
    Program,
    Statement,
)
from opendxa.dana.language.types import validate_identifier


class ParseResult(NamedTuple):
    """Result of parsing a DANA program."""

    program: Program
    error: Optional[ParseError] = None


# Regex patterns for different statement types
ASSIGNMENT_REGEX = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$")
LOG_REGEX = re.compile(r"^\s*log\(\s*\"(.*)\"\s*\)\s*$")
IF_REGEX = re.compile(r"^\s*if\s+(.*):\s*$")
FUNCTION_CALL_REGEX = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)\s*$")


def parse_literal(value_str: str) -> Literal:
    """Parse a string into a Literal value."""
    value_str = value_str.strip()

    # Check for boolean values
    if value_str.lower() == "true":
        return Literal(value=True)
    if value_str.lower() == "false":
        return Literal(value=False)

    # Check for integers
    if value_str.isdigit() or (value_str.startswith("-") and value_str[1:].isdigit()):
        return Literal(value=int(value_str))

    # Check for quoted strings
    if value_str.startswith('"') and value_str.endswith('"'):
        return Literal(value=value_str[1:-1])

    raise ParseError(f"Invalid literal value: '{value_str}'")


def parse_expression(expr_str: str) -> Expression:
    """Parse an expression string into an Expression node."""
    expr_str = expr_str.strip()

    # Check for function calls
    func_match = FUNCTION_CALL_REGEX.match(expr_str)
    if func_match:
        func_name, args_str = func_match.groups()
        # For now, only support reason() with context
        if func_name == "reason":
            context_match = re.match(r"context\s*=\s*([a-zA-Z_][a-zA-Z0-9_\.]*)", args_str)
            if not context_match:
                raise ParseError("reason() requires context parameter")
            context = context_match.group(1)
            return FunctionCall(name="reason", args={"context": context})
        raise ParseError(f"Unsupported function: {func_name}")

    # Check for binary expressions
    for op in BinaryOperator:
        if f" {op.value} " in expr_str:
            left, right = expr_str.split(f" {op.value} ", 1)
            return BinaryExpression(left=parse_expression(left), operator=op, right=parse_expression(right))

    # Check for identifiers
    if "." in expr_str and validate_identifier(expr_str):
        return Identifier(name=expr_str)

    # Try parsing as a literal
    try:
        return LiteralExpression(literal=parse_literal(expr_str))
    except ParseError:
        raise ParseError(f"Invalid expression: {expr_str}")


def parse_statement(line: str, line_num: int) -> Tuple[Optional[Statement], Optional[ParseError]]:
    """Parse a single line into a Statement or error."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None, None

    # Try matching log statement
    log_match = LOG_REGEX.match(line)
    if log_match:
        message_str = log_match.group(1)
        message_literal = Literal(value=message_str)
        message_expr = LiteralExpression(literal=message_literal)
        return LogStatement(message=message_expr), None

    # Try matching if statement
    if_match = IF_REGEX.match(line)
    if if_match:
        condition_str = if_match.group(1)
        try:
            condition = parse_expression(condition_str)
            return Conditional(condition=condition, body=[]), None
        except ParseError as e:
            return None, ParseError(f"Line {line_num}: Invalid condition: {str(e)}")

    # Try matching assignment
    assign_match = ASSIGNMENT_REGEX.match(line)
    if assign_match:
        target_str, value_str = assign_match.groups()

        if not validate_identifier(target_str):
            return None, ParseError(f"Line {line_num}: Invalid target identifier format '{target_str}'")

        try:
            value = parse_expression(value_str)
            return Assignment(target=Identifier(name=target_str), value=value), None
        except ParseError as e:
            return None, ParseError(f"Line {line_num}: {str(e)}")

    return None, ParseError(f"Line {line_num}: Invalid syntax")


def parse(code: str) -> ParseResult:
    """Parse a DANA program string into an AST."""
    statements: List[Statement] = []
    lines = code.splitlines()
    current_conditional: Optional[Conditional] = None

    for line_num, line in enumerate(lines, 1):
        statement, error = parse_statement(line, line_num)
        if error:
            return ParseResult(program=Program(statements=statements), error=error)

        if statement:
            if current_conditional:
                if isinstance(statement, Conditional):
                    # Nested if - not supported yet
                    return ParseResult(
                        program=Program(statements=statements), error=ParseError(f"Line {line_num}: Nested conditionals not supported")
                    )
                current_conditional.body.append(statement)
            else:
                if isinstance(statement, Conditional):
                    current_conditional = statement
                else:
                    statements.append(statement)

    # Add any pending conditional to the statements
    if current_conditional:
        statements.append(current_conditional)

    return ParseResult(program=Program(statements=statements))
