"""DANA Runtime: Executes parsed AST nodes."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Union

from opendxa.dana.exceptions import InterpretError, ParseError, RuntimeError, StateError
from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    FStringExpression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    LogLevel,
    LogStatement,
    Program,
)
from opendxa.dana.language.parser import ParseResult
from opendxa.dana.runtime.context import RuntimeContext

# Conditional import for type hinting only
if TYPE_CHECKING:
    # No RuntimeContext import needed here anymore
    pass

# ANSI color codes
COLORS = {
    LogLevel.DEBUG: "\033[36m",  # Cyan
    LogLevel.INFO: "\033[32m",  # Green
    LogLevel.WARN: "\033[33m",  # Yellow
    LogLevel.ERROR: "\033[31m",  # Red
}
RESET = "\033[0m"  # Reset color


@dataclass
class LogMessage:
    """Represents a log message with runtime information."""

    timestamp: str
    execution_id: str
    level: str
    scope: str
    message: str

    def __str__(self) -> str:
        color = COLORS.get(LogLevel(self.level), "")
        return f"[opendxa.dana {self.timestamp}] {color}{self.message} | {self.execution_id} | {self.level} | {self.scope}{RESET}"


def format_error_location(node: Any) -> str:
    """Format location information for error messages."""
    if not hasattr(node, "location") or not node.location:
        return ""
    line, column, source_text = node.location
    # Add padding to align the column indicator
    padding = " " * (column - 1)
    return f"\nAt line {line}, column {column}:\n{source_text}\n{padding}^"


def format_log_message(timestamp: str, execution_id: str, level: str, scope: str, message: str) -> str:
    """Format a log message with runtime information."""
    return f"[DANA Runtime] {timestamp} | {execution_id} | {level} | {scope} | {message}"


class Interpreter:
    """Interpreter for executing DANA programs."""

    def __init__(self, context: RuntimeContext):
        self.context = context
        self._execution_id = str(uuid.uuid4())[:8]  # Short unique ID for this execution
        self._log_level = LogLevel.INFO  # Default log level

        # Initialize execution state
        self.context.set("execution.id", self._execution_id)
        self.context.set("execution.log_level", self._log_level.value)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if a message with the given level should be logged."""
        # Define log level priorities (higher number = higher priority)
        level_priorities = {LogLevel.DEBUG: 0, LogLevel.INFO: 1, LogLevel.WARN: 2, LogLevel.ERROR: 3}

        # Only log if the message level is at or above the current threshold
        return level_priorities[level] >= level_priorities[self._log_level]

    def _log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """Log a message with runtime information."""
        # Check if message should be logged based on current level
        if self._should_log(level):
            # Create log message
            log_msg = LogMessage(
                timestamp=datetime.now().astimezone().strftime("%Y%m%d %H:%M:%S%z").replace("00", ""),
                execution_id=self._execution_id,
                level=level.value,
                scope="execution",  # Use execution scope for logging
                message=message,
            )

            # Print formatted message
            print(str(log_msg))

    def set_log_level(self, level: LogLevel) -> None:
        """Set the global log level threshold."""
        self._log_level = level
        self.context.set("execution.log_level", level.value)

    def execute_program(self, parse_result: ParseResult) -> None:
        """Executes a DANA program, node by node.

        Args:
            parse_result: Result of parsing the program, containing:
                - program: The Program to execute
                - errors: List of ParseErrors encountered during parsing
        """
        if not isinstance(parse_result.program, Program):
            raise InterpretError(f"Expected a Program node, got {type(parse_result.program).__name__}")

        try:
            # Execute all statements that come before the first error
            for statement in parse_result.program.statements:
                self._execute_statement(statement)

            # If there are any parse errors, stop at the first one
            if parse_result.errors:
                raise parse_result.errors[0]

        except (InterpretError, StateError, RuntimeError, ParseError) as e:
            self._log_level = LogLevel.ERROR
            self.context.set("execution.log_level", LogLevel.ERROR.value)
            raise e from None
        except Exception as e:
            # Wrap unexpected Python errors in RuntimeError
            self._log_level = LogLevel.ERROR
            self.context.set("execution.log_level", LogLevel.ERROR.value)
            raise RuntimeError(str(e)) from e

    def _get_variable(self, name: str) -> Any:
        """Get a variable value from the context."""
        # If the name already contains a dot, use it as is
        if "." in name:
            return self.context.get(name)
        # Otherwise, use the private scope
        return self.context.get(f"private.{name}")

    def _set_variable(self, name: str, value: Any) -> None:
        """Set a variable value in the context."""
        # If the name already contains a dot, use it as is
        if "." in name:
            self.context.set(name, value)
        else:
            # Otherwise, use the private scope
            self.context.set(f"private.{name}", value)

    def _execute_statement(self, statement: Union[Assignment, LogStatement, Conditional]) -> None:
        """Execute a single DANA statement."""
        try:
            if isinstance(statement, Assignment):
                value = self._evaluate_expression(statement.value)
                self._set_variable(statement.target.name, value)
                self._log(f"Set {statement.target.name} = {value}", LogLevel.DEBUG)

            elif isinstance(statement, LogStatement):
                message = self._evaluate_expression(statement.message)
                self._log(str(message), statement.level)

            elif isinstance(statement, Conditional):
                condition = self._evaluate_expression(statement.condition)
                if condition:
                    for body_stmt in statement.body:
                        self._execute_statement(body_stmt)

        except (RuntimeError, StateError):
            raise
        except Exception as e:
            error_msg = f"Error executing statement: {type(e).__name__}: {e}"
            error_msg += format_error_location(statement)
            raise RuntimeError(error_msg) from e

    def _evaluate_expression(self, expr: Union[LiteralExpression, Identifier, BinaryExpression, FunctionCall]) -> Any:
        """Evaluate a DANA expression node."""
        try:
            if isinstance(expr, LiteralExpression):
                if isinstance(expr.literal.value, FStringExpression):
                    # Evaluate f-string
                    result = ""
                    for part in expr.literal.value.parts:
                        if isinstance(part, str):
                            result += part
                        else:
                            # Evaluate the expression and convert to string
                            value = self._evaluate_expression(part)
                            result += str(value)
                    return result
                return expr.literal.value
            elif isinstance(expr, Identifier):
                try:
                    return self._get_variable(expr.name)
                except StateError:
                    error_msg = f"Variable not found: {expr.name}"
                    error_msg += format_error_location(expr)
                    raise StateError(error_msg) from None
            elif isinstance(expr, BinaryExpression):
                left = self._evaluate_expression(expr.left)
                right = self._evaluate_expression(expr.right)

                try:
                    if expr.operator == BinaryOperator.ADD:
                        # Handle string concatenation by converting non-string values to strings
                        if isinstance(left, str) or isinstance(right, str):
                            return str(left) + str(right)
                        return left + right
                    elif expr.operator == BinaryOperator.SUBTRACT:
                        return left - right
                    elif expr.operator == BinaryOperator.MULTIPLY:
                        return left * right
                    elif expr.operator == BinaryOperator.DIVIDE:
                        if right == 0:
                            error_msg = "Division by zero"
                            error_msg += format_error_location(expr)
                            raise StateError(error_msg)
                        return left / right
                    else:
                        error_msg = f"Unsupported binary operator: {expr.operator}"
                        error_msg += format_error_location(expr)
                        raise RuntimeError(error_msg)
                except (TypeError, ValueError) as e:
                    error_msg = f"Error in binary operation: {str(e)}"
                    error_msg += format_error_location(expr)
                    raise RuntimeError(error_msg) from e
            elif isinstance(expr, FunctionCall):
                error_msg = "Function calls are not yet implemented"
                error_msg += format_error_location(expr)
                raise RuntimeError(error_msg)
            else:
                error_msg = f"Unsupported expression type: {type(expr).__name__}"
                error_msg += format_error_location(expr)
                raise RuntimeError(error_msg)
        except (RuntimeError, StateError):
            raise
        except Exception as e:
            error_msg = f"Error evaluating expression: {type(e).__name__}: {e}"
            error_msg += format_error_location(expr)
            raise RuntimeError(error_msg) from e
