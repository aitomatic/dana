"""DANA program validation utilities."""

from typing import List, Optional

from opendxa.dana.common.exceptions import ValidationError
from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    Conditional,
    Expression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    LogStatement,
    Program,
    Statement,
)
from opendxa.dana.language.types import validate_identifier


class ValidationResult:
    """Result of validating a DANA program."""

    def __init__(self, is_valid: bool, errors: Optional[List[ValidationError]] = None):
        self.is_valid = is_valid
        self.errors = errors or []


def validate_program(program: Program) -> ValidationResult:
    """Validate a DANA program for syntax and semantic correctness."""
    errors: List[ValidationError] = []

    # Validate each statement
    for i, statement in enumerate(program.statements):
        try:
            validate_statement(statement)
        except ValidationError as e:
            errors.append(ValidationError(f"Statement {i + 1}: {str(e)}"))

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def validate_expression(expr: Expression) -> None:
    """Validate an expression."""
    if isinstance(expr, Identifier):
        if not validate_identifier(expr.name):
            raise ValidationError(f"Invalid identifier format: {expr.name}")

    elif isinstance(expr, LiteralExpression):
        # Literal expressions are always valid
        pass

    elif isinstance(expr, BinaryExpression):
        validate_expression(expr.left)
        validate_expression(expr.right)
        # TODO: Add type checking for binary expressions

    elif isinstance(expr, FunctionCall):
        if expr.name == "reason":
            if "context" not in expr.args:
                raise ValidationError("reason() requires context parameter")
            if not isinstance(expr.args["context"], str):
                raise ValidationError("reason() context must be a string")
        else:
            raise ValidationError(f"Unsupported function: {expr.name}")

    else:
        raise ValidationError(f"Unknown expression type: {type(expr)}")


def validate_statement(statement: Statement) -> None:
    """Validate a single DANA statement."""
    if isinstance(statement, Assignment):
        # Validate target identifier
        if not validate_identifier(statement.target.name):
            raise ValidationError(f"Invalid target identifier format: {statement.target.name}")

        # Validate value expression
        validate_expression(statement.value)

    elif isinstance(statement, LogStatement):
        # Validate message is a string literal
        if not isinstance(statement.message, LiteralExpression):
            raise ValidationError("Log message must be a literal")
        if not isinstance(statement.message.literal.value, str):
            raise ValidationError("Log message must be a string")

    elif isinstance(statement, Conditional):
        # Validate condition expression
        validate_expression(statement.condition)

        # Validate body statements
        for body_stmt in statement.body:
            validate_statement(body_stmt)

    else:
        raise ValidationError(f"Unknown statement type: {type(statement)}")
