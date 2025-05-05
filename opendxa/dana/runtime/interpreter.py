"""DANA Runtime: Executes parsed AST nodes."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

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
    LogLevelSetStatement,
    LogStatement,
    Program,
    WhileLoop,
)
from opendxa.dana.language.parser import ParseResult
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.function_registry import call_function, has_function
from opendxa.dana.runtime.hooks import HookType, execute_hook, has_hooks

# Conditional import for type hinting only
if TYPE_CHECKING:
    # No RuntimeContext import needed here anymore
    pass

# Feature flag to control whether to use the visitor pattern by default
USE_VISITOR_PATTERN = False

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
    """Interpreter for executing DANA programs.
    
    This class can use either the traditional approach or the visitor pattern
    for executing DANA programs, depending on the use_visitor flag.
    """

    def __init__(self, context: RuntimeContext, use_visitor: bool = USE_VISITOR_PATTERN):
        """Initialize the interpreter with a runtime context.
        
        Args:
            context: The runtime context for state management
            use_visitor: Whether to use the visitor pattern (default based on global flag)
        """
        self.context = context
        self._execution_id = str(uuid.uuid4())[:8]  # Short unique ID for this execution
        self._log_level = LogLevel.WARN  # Default log level to WARN
        self._use_visitor = use_visitor
        self._visitor = None

        # Initialize execution state
        self.context.set("execution.id", self._execution_id)
        self.context.set("execution.log_level", self._log_level.value)
        
        # Lazily load the visitor if needed to avoid circular imports
        if self._use_visitor:
            from opendxa.dana.runtime.interpreter_visitor import InterpreterVisitor
            self._visitor = InterpreterVisitor(context)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if a message with the given level should be logged."""
        # Define log level priorities (higher number = higher priority)
        level_priorities = {LogLevel.DEBUG: 0, LogLevel.INFO: 1, LogLevel.WARN: 2, LogLevel.ERROR: 3}

        # Only log if the message level is at or above the current threshold
        return level_priorities[level] >= level_priorities[self._log_level]

    def _log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """Log a message with runtime information."""
        # If using visitor, delegate to it
        if self._use_visitor and self._visitor:
            self._visitor._log(message, level)
            return
            
        # Check if message should be logged based on current level
        if self._should_log(level):
            # Evaluate any f-strings in the message
            try:
                # Replace {variable} with actual values
                while "{" in message and "}" in message:
                    start = message.find("{")
                    end = message.find("}", start)
                    if start == -1 or end == -1:
                        break
                    var_name = message[start + 1 : end]
                    try:
                        value = self._get_variable(var_name)
                        message = message[:start] + str(value) + message[end + 1 :]
                    except StateError:
                        # If variable not found, leave it as is
                        break
            except Exception:
                # If evaluation fails, use the original message
                pass

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
        
        # If using visitor, also set its log level
        if self._use_visitor and self._visitor:
            self._visitor.set_log_level(level)

    def execute_program(self, parse_result: ParseResult) -> None:
        """Executes a DANA program, node by node.

        Args:
            parse_result: Result of parsing the program, containing:
                - program: The Program to execute
                - errors: List of ParseErrors encountered during parsing
                
        Raises:
            InterpretError: If a program is not provided
            Various exceptions: For errors during execution
        """
        # Create hook context
        hook_context = {
            "interpreter": self,
            "context": self.context,
            "program": parse_result.program,
            "errors": parse_result.errors
        }
        
        # Execute before program hooks
        if has_hooks(HookType.BEFORE_PROGRAM):
            execute_hook(HookType.BEFORE_PROGRAM, hook_context)
            
        if self._use_visitor and self._visitor:
            # Delegate to visitor implementation
            try:
                self._visitor.execute_program(parse_result)
            except Exception as e:
                # Ensure error handling is consistent with traditional approach
                self._log_level = LogLevel.ERROR
                self.context.set("execution.log_level", LogLevel.ERROR.value)
                
                # Execute error hooks
                if has_hooks(HookType.ON_ERROR):
                    error_context = {**hook_context, "error": e}
                    execute_hook(HookType.ON_ERROR, error_context)
                    
                raise e
                
            # Execute after program hooks
            if has_hooks(HookType.AFTER_PROGRAM):
                execute_hook(HookType.AFTER_PROGRAM, hook_context)
                
            return
            
        if not isinstance(parse_result.program, Program):
            raise InterpretError(f"Expected a Program node, got {type(parse_result.program).__name__}")

        try:
            # Execute all statements that come before the first error
            for statement in parse_result.program.statements:
                self._execute_statement(statement)

            # If there are any parse errors, stop at the first one
            if parse_result.errors:
                raise parse_result.errors[0]
                
            # Execute after program hooks
            if has_hooks(HookType.AFTER_PROGRAM):
                execute_hook(HookType.AFTER_PROGRAM, hook_context)

        except (InterpretError, StateError, RuntimeError, ParseError) as e:
            self._log_level = LogLevel.ERROR
            self.context.set("execution.log_level", LogLevel.ERROR.value)
            
            # Execute error hooks
            if has_hooks(HookType.ON_ERROR):
                error_context = {**hook_context, "error": e}
                execute_hook(HookType.ON_ERROR, error_context)
                
            raise e from None
        except Exception as e:
            # Wrap unexpected Python errors in RuntimeError
            self._log_level = LogLevel.ERROR
            self.context.set("execution.log_level", LogLevel.ERROR.value)
            
            # Execute error hooks
            if has_hooks(HookType.ON_ERROR):
                error_context = {**hook_context, "error": e}
                execute_hook(HookType.ON_ERROR, error_context)
                
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

    def _execute_statement(self, statement: Union[Assignment, LogStatement, Conditional, WhileLoop, LogLevelSetStatement]) -> None:
        """Execute a single DANA statement."""
        # Create hook context
        hook_context = {
            "interpreter": self,
            "context": self.context,
            "statement": statement
        }
        
        # Execute before statement hooks
        if has_hooks(HookType.BEFORE_STATEMENT):
            execute_hook(HookType.BEFORE_STATEMENT, hook_context)
            
        try:
            if isinstance(statement, Assignment):
                # Execute before assignment hooks
                if has_hooks(HookType.BEFORE_ASSIGNMENT):
                    execute_hook(HookType.BEFORE_ASSIGNMENT, hook_context)
                    
                value = self._evaluate_expression(statement.value)
                self._set_variable(statement.target.name, value)
                self._log(f"Set {statement.target.name} = {value}", LogLevel.DEBUG)
                
                # Execute after assignment hooks
                if has_hooks(HookType.AFTER_ASSIGNMENT):
                    assign_context = {**hook_context, "value": value}
                    execute_hook(HookType.AFTER_ASSIGNMENT, assign_context)

            elif isinstance(statement, LogStatement):
                # Execute before log hooks
                if has_hooks(HookType.BEFORE_LOG):
                    execute_hook(HookType.BEFORE_LOG, hook_context)
                    
                message = self._evaluate_expression(statement.message)
                self._log(str(message), statement.level)
                
                # Execute after log hooks
                if has_hooks(HookType.AFTER_LOG):
                    log_context = {**hook_context, "message": message, "level": statement.level}
                    execute_hook(HookType.AFTER_LOG, log_context)

            elif isinstance(statement, LogLevelSetStatement):
                self._log_level = statement.level
                self.context.set("execution.log_level", statement.level.value)
                self._log(f"Set log level to {statement.level.value}", LogLevel.DEBUG)

            elif isinstance(statement, Conditional):
                # Execute before conditional hooks
                if has_hooks(HookType.BEFORE_CONDITIONAL):
                    execute_hook(HookType.BEFORE_CONDITIONAL, hook_context)
                    
                condition = self._evaluate_expression(statement.condition)
                
                # Add condition result to context for hooks
                cond_context = {**hook_context, "condition_result": condition}
                
                # Only execute the conditional body if the condition evaluates to a truthy value
                if bool(condition):
                    # Simply execute each statement in the body
                    # Since our parser properly handles nested conditionals now, this is cleaner
                    for body_stmt in statement.body:
                        self._execute_statement(body_stmt)
                
                # Execute after conditional hooks
                if has_hooks(HookType.AFTER_CONDITIONAL):
                    execute_hook(HookType.AFTER_CONDITIONAL, cond_context)
                    
            elif isinstance(statement, WhileLoop):
                # Create hook context for the while loop
                hook_context_while = {**hook_context, "loop_type": "while"}
                
                # Execute before while loop hooks
                if has_hooks(HookType.BEFORE_LOOP):
                    execute_hook(HookType.BEFORE_LOOP, hook_context_while)
                
                # Execute the loop
                max_iterations = 1000  # Prevent infinite loops
                iteration_count = 0
                
                # Loop as long as the condition is true
                while True:
                    # Evaluate the condition
                    condition = self._evaluate_expression(statement.condition)
                    
                    # If condition is false, break out of the loop
                    if not bool(condition):
                        break
                        
                    # Check for max iterations to prevent infinite loops
                    iteration_count += 1
                    if iteration_count > max_iterations:
                        self._log(f"Max iterations ({max_iterations}) reached in while loop, breaking", LogLevel.WARN)
                        break
                    
                    # Execute all statements in the body
                    for body_stmt in statement.body:
                        self._execute_statement(body_stmt)
                if has_hooks(HookType.AFTER_LOOP):
                    hook_context_while["iterations"] = iteration_count
                    execute_hook(HookType.AFTER_LOOP, hook_context_while)
            
            # Execute after statement hooks
            if has_hooks(HookType.AFTER_STATEMENT):
                execute_hook(HookType.AFTER_STATEMENT, hook_context)

        except (RuntimeError, StateError) as e:
            # Execute error hooks
            if has_hooks(HookType.ON_ERROR):
                error_context = {**hook_context, "error": e}
                execute_hook(HookType.ON_ERROR, error_context)
            raise
        except Exception as e:
            # Execute error hooks
            if has_hooks(HookType.ON_ERROR):
                error_context = {**hook_context, "error": e}
                execute_hook(HookType.ON_ERROR, error_context)
                
            error_msg = f"Error executing statement: {type(e).__name__}: {e}"
            error_msg += format_error_location(statement)
            raise RuntimeError(error_msg) from e

    def _evaluate_expression(self, expr: Union[LiteralExpression, Identifier, BinaryExpression, FunctionCall]) -> Any:
        """Evaluate a DANA expression node."""
        # Create hook context
        hook_context = {
            "interpreter": self,
            "context": self.context,
            "expression": expr
        }
        
        # Execute before expression hooks
        if has_hooks(HookType.BEFORE_EXPRESSION):
            execute_hook(HookType.BEFORE_EXPRESSION, hook_context)
            
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
                    elif expr.operator == BinaryOperator.MODULO:
                        if right == 0:
                            error_msg = "Modulo by zero"
                            error_msg += format_error_location(expr)
                            raise StateError(error_msg)
                        return left % right
                    elif expr.operator == BinaryOperator.EQUALS:
                        return left == right
                    elif expr.operator == BinaryOperator.NOT_EQUALS:
                        return left != right
                    elif expr.operator == BinaryOperator.LESS_THAN:
                        return left < right
                    elif expr.operator == BinaryOperator.GREATER_THAN:
                        return left > right
                    elif expr.operator == BinaryOperator.LESS_EQUALS:
                        return left <= right
                    elif expr.operator == BinaryOperator.GREATER_EQUALS:
                        return left >= right
                    elif expr.operator == BinaryOperator.AND:
                        if not isinstance(left, bool) or not isinstance(right, bool):
                            error_msg = "AND operator requires boolean operands"
                            error_msg += format_error_location(expr)
                            raise StateError(error_msg)
                        return left and right
                    elif expr.operator == BinaryOperator.OR:
                        if not isinstance(left, bool) or not isinstance(right, bool):
                            error_msg = "OR operator requires boolean operands"
                            error_msg += format_error_location(expr)
                            raise StateError(error_msg)
                        return left or right
                    elif expr.operator == BinaryOperator.IN:
                        if not isinstance(right, (list, dict, str)):
                            error_msg = "IN operator requires a list, dict, or string as right operand"
                            error_msg += format_error_location(expr)
                            raise StateError(error_msg)
                        return left in right
                    else:
                        error_msg = f"Unsupported binary operator: {expr.operator}"
                        error_msg += format_error_location(expr)
                        raise RuntimeError(error_msg)
                except (TypeError, ValueError) as e:
                    error_msg = f"Error in binary operation: {str(e)}"
                    error_msg += format_error_location(expr)
                    raise RuntimeError(error_msg) from e
            elif isinstance(expr, FunctionCall):
                # Process function call using the function registry
                try:
                    # First check if this is a function call to a variable
                    if "." not in expr.name and has_function(expr.name):
                        # Convert arguments - in future this would handle proper parameter matching
                        args = {}
                        for key, value in expr.args.items():
                            # Evaluate argument expressions if needed
                            if isinstance(value, (LiteralExpression, Identifier, BinaryExpression, FunctionCall)):
                                args[key] = self._evaluate_expression(value)
                            else:
                                args[key] = value
                                
                        # Call the function from the registry
                        return call_function(expr.name, self.context, args)
                    else:
                        error_msg = f"Function '{expr.name}' is not registered"
                        error_msg += format_error_location(expr)
                        raise RuntimeError(error_msg)
                except Exception as e:
                    error_msg = f"Error calling function '{expr.name}': {str(e)}"
                    error_msg += format_error_location(expr)
                    raise RuntimeError(error_msg) from e
            else:
                error_msg = f"Unsupported expression type: {type(expr).__name__}"
                error_msg += format_error_location(expr)
                raise RuntimeError(error_msg)
        except (RuntimeError, StateError) as e:
            # Execute error hooks
            if has_hooks(HookType.ON_ERROR):
                error_context = {**hook_context, "error": e}
                execute_hook(HookType.ON_ERROR, error_context)
            raise
        except Exception as e:
            # Execute error hooks
            if has_hooks(HookType.ON_ERROR):
                error_context = {**hook_context, "error": e}
                execute_hook(HookType.ON_ERROR, error_context)
                
            error_msg = f"Error evaluating expression: {type(e).__name__}: {e}"
            error_msg += format_error_location(expr)
            raise RuntimeError(error_msg) from e
            
        # Get the result
        result = None
        
        if isinstance(expr, LiteralExpression):
            if isinstance(expr.literal.value, FStringExpression):
                # Result was already computed
                pass
            else:
                result = expr.literal.value
        elif isinstance(expr, Identifier):
            try:
                result = self._get_variable(expr.name)
            except StateError:
                raise  # Already handled above
        elif isinstance(expr, BinaryExpression):
            # Result was computed above in try block
            pass
        elif isinstance(expr, FunctionCall):
            # Result was computed above in try block
            pass
        
        # Execute after expression hooks
        if has_hooks(HookType.AFTER_EXPRESSION):
            expr_context = {**hook_context, "result": result}
            execute_hook(HookType.AFTER_EXPRESSION, expr_context)
            
        return result


# Factory function to create an interpreter with an option to use the visitor pattern
def create_interpreter(context: RuntimeContext, use_visitor: bool = USE_VISITOR_PATTERN) -> Interpreter:
    """Create a new interpreter with the given context and visitor option.
    
    Args:
        context: The runtime context to use
        use_visitor: Whether to use the visitor pattern implementation
        
    Returns:
        A new Interpreter instance
    """
    return Interpreter(context, use_visitor)
