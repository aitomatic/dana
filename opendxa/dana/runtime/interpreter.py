"""DANA Runtime Interpreter.

This module provides the main Interpreter implementation for executing DANA programs.
It traverses the AST and executes each node according to DANA language semantics.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from opendxa.common.types import BaseRequest
from opendxa.common.utils.misc import Misc
from opendxa.dana.exceptions import InterpretError, RuntimeError, StateError
from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    FStringExpression,
    FunctionCall,
    Identifier,
    Literal,
    LiteralExpression,
    LogLevel,
    LogLevelSetStatement,
    LogStatement,
    Program,
    ReasonStatement,
    WhileLoop,
)
from opendxa.dana.language.parser import ParseResult
from opendxa.dana.language.visitor import ASTVisitor
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.function_registry import call_function, has_function
from opendxa.dana.runtime.hooks import HookType, execute_hook, has_hooks

# ANSI color codes
COLORS = {
    LogLevel.DEBUG: "\033[36m",  # Cyan
    LogLevel.INFO: "\033[32m",  # Green
    LogLevel.WARN: "\033[33m",  # Yellow
    LogLevel.ERROR: "\033[31m",  # Red
}
RESET = "\033[0m"  # Reset color


def format_error_location(node: Any) -> str:
    """Format location information for error messages."""
    if not hasattr(node, "location") or not node.location:
        return ""
    line, column, source_text = node.location
    # Add padding to align the column indicator
    padding = " " * (column - 1)
    return f"\nAt line {line}, column {column}:\n{source_text}\n{padding}^"


class Interpreter(ASTVisitor):
    """Interpreter for executing DANA programs.

    This class traverses the AST and executes each node according to the DANA
    language semantics, managing state through the runtime context.
    """

    def __init__(self, context: RuntimeContext):
        """Initialize the interpreter with a runtime context.

        Args:
            context: The runtime context for state management
        """
        self.context = context
        self._execution_id = str(uuid.uuid4())[:8]  # Short unique ID for this execution
        self._log_level = LogLevel.WARN  # Default log level to WARN

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

            # Format and print the log message
            timestamp = datetime.now().astimezone().strftime("%Y%m%d %H:%M:%S%z").replace("00", "")
            color = COLORS.get(level, "")
            print(f"[opendxa.dana {timestamp}] {color}{message} | {self._execution_id} | {level.value} | execution{RESET}")

    def set_log_level(self, level: LogLevel) -> None:
        """Set the global log level threshold."""
        self._log_level = level
        self.context.set("execution.log_level", level.value)

    def execute_program(self, parse_result: ParseResult) -> None:
        """Execute a DANA program.

        Args:
            parse_result: Result of parsing the program

        Raises:
            InterpretError: If a program is not provided
            Various exceptions: For errors during execution
        """
        if not isinstance(parse_result.program, Program):
            raise InterpretError(f"Expected a Program node, got {type(parse_result.program).__name__}")

        # Create hook context for program hooks
        hook_context = {"interpreter": self, "context": self.context, "program": parse_result.program, "errors": parse_result.errors}

        # Execute before program hooks
        if has_hooks(HookType.BEFORE_PROGRAM):
            execute_hook(HookType.BEFORE_PROGRAM, hook_context)

        try:
            # Execute all statements that come before the first error
            self.visit_program(parse_result.program)

            # If there are any parse errors, stop at the first one
            if parse_result.errors:
                raise parse_result.errors[0]

            # Execute after program hooks
            if has_hooks(HookType.AFTER_PROGRAM):
                execute_hook(HookType.AFTER_PROGRAM, hook_context)

        except Exception as e:
            # Set log level to ERROR for any exceptions
            self._log_level = LogLevel.ERROR
            self.context.set("execution.log_level", LogLevel.ERROR.value)

            # Execute error hooks
            if has_hooks(HookType.ON_ERROR):
                error_context = {**hook_context, "error": e}
                execute_hook(HookType.ON_ERROR, error_context)

            raise e

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

    # Visitor methods implementation

    def visit_program(self, node: Program, context: Optional[Dict[str, Any]] = None) -> None:
        """Visit a Program node, executing all statements."""
        for statement in node.statements:
            # Create hook context for statement hooks
            hook_context = {"visitor": self, "context": self.context, "statement": statement}

            # Execute before statement hooks
            if has_hooks(HookType.BEFORE_STATEMENT):
                execute_hook(HookType.BEFORE_STATEMENT, hook_context)

            # Execute the statement
            self.visit_node(statement, context)

            # Execute after statement hooks
            if has_hooks(HookType.AFTER_STATEMENT):
                execute_hook(HookType.AFTER_STATEMENT, hook_context)

    def visit_assignment(self, node: Assignment, context: Optional[Dict[str, Any]] = None) -> None:
        """Visit an Assignment node, evaluating and storing the value."""
        # Create hook context
        hook_context = {"visitor": self, "context": self.context, "statement": node}

        # Execute before assignment hooks
        if has_hooks(HookType.BEFORE_ASSIGNMENT):
            execute_hook(HookType.BEFORE_ASSIGNMENT, hook_context)

        try:
            # Evaluate the expression and store the value
            value = self.visit_node(node.value, context)
            self._set_variable(node.target.name, value)
            self._log(f"Set {node.target.name} = {value}", LogLevel.DEBUG)

            # Execute after assignment hooks with the value
            if has_hooks(HookType.AFTER_ASSIGNMENT):
                assign_context = {**hook_context, "value": value}
                execute_hook(HookType.AFTER_ASSIGNMENT, assign_context)

        except Exception as e:
            if isinstance(e, (RuntimeError, StateError)):
                raise
            error_msg = f"Error executing assignment: {type(e).__name__}: {e}"
            error_msg += format_error_location(node)
            raise RuntimeError(error_msg) from e

    def visit_log_statement(self, node: LogStatement, context: Optional[Dict[str, Any]] = None) -> None:
        """Visit a LogStatement node, evaluating and logging the message."""
        try:
            message = self.visit_node(node.message, context)
            self._log(str(message), node.level)
        except Exception as e:
            if isinstance(e, (RuntimeError, StateError)):
                raise
            error_msg = f"Error executing log statement: {type(e).__name__}: {e}"
            error_msg += format_error_location(node)
            raise RuntimeError(error_msg) from e

    def visit_log_level_set_statement(self, node: LogLevelSetStatement, context: Optional[Dict[str, Any]] = None) -> None:
        """Visit a LogLevelSetStatement node, setting the log level."""
        try:
            self._log_level = node.level
            self.context.set("execution.log_level", node.level.value)
            self._log(f"Set log level to {node.level.value}", LogLevel.DEBUG)
        except Exception as e:
            if isinstance(e, (RuntimeError, StateError)):
                raise
            error_msg = f"Error setting log level: {type(e).__name__}: {e}"
            error_msg += format_error_location(node)
            raise RuntimeError(error_msg) from e

    def visit_conditional(self, node: Conditional, context: Optional[Dict[str, Any]] = None) -> None:
        """Visit a Conditional node, evaluating the condition and executing the body if true."""
        try:
            condition = self.visit_node(node.condition, context)
            if condition:
                for body_stmt in node.body:
                    # Support nested conditionals by visiting them too
                    self.visit_node(body_stmt, context)
        except Exception as e:
            if isinstance(e, (RuntimeError, StateError)):
                raise
            error_msg = f"Error executing conditional: {type(e).__name__}: {e}"
            error_msg += format_error_location(node)
            raise RuntimeError(error_msg) from e

    def visit_while_loop(self, node: WhileLoop, context: Optional[Dict[str, Any]] = None) -> None:
        """Visit a WhileLoop node, repeatedly executing the body while the condition is true."""
        try:
            # Execute the loop
            max_iterations = 1000  # Prevent infinite loops
            iteration_count = 0

            # Loop as long as the condition is true
            while True:
                # Evaluate the condition
                condition = self.visit_node(node.condition, context)

                # If condition is false, break out of the loop
                if not bool(condition):
                    break

                # Check for max iterations to prevent infinite loops
                iteration_count += 1
                if iteration_count > max_iterations:
                    self._log(f"Max iterations ({max_iterations}) reached in while loop, breaking", LogLevel.WARN)
                    break

                # Execute all statements in the body
                for body_stmt in node.body:
                    self.visit_node(body_stmt, context)
        except Exception as e:
            if isinstance(e, (RuntimeError, StateError)):
                raise
            error_msg = f"Error executing while loop: {type(e).__name__}: {e}"
            error_msg += format_error_location(node)
            raise RuntimeError(error_msg) from e

    async def _perform_reasoning(
        self, prompt: str, context_vars: Optional[List[str]] = None, options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a reasoning operation by calling the LLM.

        Args:
            prompt: The reasoning prompt to send to the LLM
            context_vars: Optional list of variable names to include as context
            options: Optional parameters for the LLM call (temperature, format, etc.)

        Returns:
            The reasoning result from the LLM.

        Raises:
            RuntimeError: If the LLM resource is not available or if the query fails.
        """
        # Get the LLM resource, or create a default one if not available
        try:
            llm = self.context.get_resource("reason_llm")
        except StateError:
            try:
                llm = self.context.get_resource("llm")
            except StateError:
                from opendxa.common.resource.llm_resource import LLMResource

                # Create a default LLM resource
                self._log("No LLM resource found, creating a default one", LogLevel.WARN)
                llm = LLMResource(name="reason_llm")

                # Register it with the context
                self.context.register_resource("reason_llm", llm)
                self._log("reason_llm resource registered", LogLevel.INFO)

        if llm:
            await llm.initialize()  # Ensure resource is initialized
        else:
            error_msg = (
                "Failed to create default LLM resource.\n"
                "To use reason() statements, you need to configure an LLM resource:\n"
                "1. Set environment variables (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY)\n"
                "2. Or register an LLM resource with the context using: context.register_resource('llm', llm_resource)"
            )
            self._log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)

        # Prepare the context data to include with the prompt
        context_data = {}
        if context_vars:
            for var_name in context_vars:
                try:
                    # Get the variable value from context
                    value = self._get_variable(var_name)
                    # Add it to the context data
                    context_data[var_name] = value
                except StateError:
                    self._log(f"Warning: Context variable '{var_name}' not found", LogLevel.WARN)

        # Build the combined prompt with context
        enriched_prompt = prompt
        if context_data:
            # Format the context as JSON for inclusion in the prompt
            context_str = json.dumps(context_data, indent=2, default=str)
            enriched_prompt = f"{prompt}\n\nContext:\n{context_str}"

        # Prepare the LLM request
        system_message = "You are a reasoning engine. Analyze the query and provide a thoughtful, accurate response."

        # Add any format-specific instructions
        format_type = options.get("format", "text") if options else "text"
        if format_type == "json":
            system_message += " Return your answer in valid JSON format."

        # Set up the messages
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": enriched_prompt}]

        # Prepare other LLM parameters
        params = {
            "messages": messages,
            "temperature": options.get("temperature", 0.7) if options else 0.7,
        }

        # Add max_tokens if specified
        if options and "max_tokens" in options:
            params["max_tokens"] = options["max_tokens"]

        # Make the LLM call
        try:
            # Log the reasoning request
            self._log(f"Reasoning: {prompt[:100]}{'...' if len(prompt) > 100 else ''}", LogLevel.DEBUG)

            # Make the asynchronous LLM query
            response = await llm.query(BaseRequest(arguments=params))

            if not response.success:
                raise RuntimeError(f"LLM reasoning failed: {response.error}")

            # Extract the content from the response
            content = response.content

            # If it's a completion-style response with choices
            if isinstance(content, dict) and "choices" in content:
                result = content["choices"][0]
                result = Misc.get_field(result, "message")
                result = Misc.get_field(result, "content")
            # If it's a direct content response
            elif isinstance(content, dict) and "content" in content:
                result = Misc.get_field(content, "content", content)

            # Format conversion if needed
            if format_type == "json" and isinstance(result, str):
                try:
                    # Try to parse the result as JSON
                    result = json.loads(result)
                except json.JSONDecodeError:
                    self._log(f"Warning: Could not parse LLM response as JSON: {result[:100]}", LogLevel.WARN)

            return result

        except Exception as e:
            raise RuntimeError("Error during LLM reasoning") from e

    def _visit_reason_statement_sync(self, node: ReasonStatement, context: Optional[Dict[str, Any]] = None) -> None:
        """Synchronous version of visit_reason_statement for tests and REPL."""
        # Create hook context
        hook_context = {"visitor": self, "context": self.context, "statement": node}

        try:
            # Execute before reason hooks if they exist
            if has_hooks(HookType.BEFORE_REASON):
                execute_hook(HookType.BEFORE_REASON, hook_context)

            # Evaluate the prompt
            prompt_value = self.visit_node(node.prompt, context)
            prompt_str = str(prompt_value)  # Convert to string if it's not already

            # Extract context variable names
            context_vars = []
            if node.context:
                context_vars = [ident.name for ident in node.context]

            # Execute the reasoning
            try:
                # Create a new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Run the reasoning
                    result = loop.run_until_complete(self._perform_reasoning(prompt_str, context_vars, node.options))
                finally:
                    loop.close()

                # If we have a target variable, store the result
                if node.target:
                    self._set_variable(node.target.name, result)
                else:
                    # Otherwise, log the result
                    if isinstance(result, (dict, list)):
                        result_str = json.dumps(result, indent=2)
                    else:
                        result_str = str(result)

                    # Log at most the first 500 characters to avoid huge log entries
                    preview = result_str[:500] + "..." if len(result_str) > 500 else result_str
                    self._log(f"Reasoning result: {preview}", LogLevel.INFO)

                # Create result context for the hook
                result_context = {**hook_context, "result": result}

                # Execute after reason hooks if they exist
                if has_hooks(HookType.AFTER_REASON):
                    execute_hook(HookType.AFTER_REASON, result_context)

            except Exception as e:
                self._log(f"Error in reason statement: {str(e)}", LogLevel.ERROR)
                raise RuntimeError("Reasoning error") from e

        except Exception as e:
            if isinstance(e, (RuntimeError, StateError)):
                raise
            error_msg = f"Error executing reason statement: {type(e).__name__}: {e}"
            error_msg += format_error_location(node)
            raise RuntimeError(error_msg) from e

    async def visit_reason_statement(self, node: ReasonStatement, context: Optional[Dict[str, Any]] = None) -> None:
        """Visit a ReasonStatement node, executing the reasoning operation using an LLM."""
        # Create hook context
        hook_context = {"visitor": self, "context": self.context, "statement": node}

        try:
            # Execute before reason hooks if they exist
            if has_hooks(HookType.BEFORE_REASON):
                execute_hook(HookType.BEFORE_REASON, hook_context)

            # Evaluate the prompt
            prompt_value = self.visit_node(node.prompt, context)
            prompt_str = str(prompt_value)  # Convert to string if it's not already

            # Extract context variable names
            context_vars = []
            if node.context:
                context_vars = [ident.name for ident in node.context]

            # Execute the reasoning
            try:
                # Use the existing event loop or create a new one
                try:
                    loop = asyncio.get_running_loop()
                    # If we're already in an async context, await directly
                    result = await self._perform_reasoning(prompt_str, context_vars, node.options)
                except RuntimeError:
                    # No running event loop - create one and run until complete
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(self._perform_reasoning(prompt_str, context_vars, node.options))
                    loop.close()

                # If we have a target variable, store the result
                if node.target:
                    self._set_variable(node.target.name, result)
                else:
                    # Otherwise, log the result
                    if isinstance(result, (dict, list)):
                        result_str = json.dumps(result, indent=2)
                    else:
                        result_str = str(result)

                    # Log at most the first 500 characters to avoid huge log entries
                    preview = result_str[:500] + "..." if len(result_str) > 500 else result_str
                    self._log(f"Reasoning result: {preview}", LogLevel.INFO)

                # Create result context for the hook
                result_context = {**hook_context, "result": result}

                # Execute after reason hooks if they exist
                if has_hooks(HookType.AFTER_REASON):
                    execute_hook(HookType.AFTER_REASON, result_context)

            except Exception as e:
                self._log(f"Error in reason statement: {str(e)}", LogLevel.ERROR)
                raise RuntimeError("Reasoning error") from e

        except Exception as e:
            if isinstance(e, (RuntimeError, StateError)):
                raise
            error_msg = f"Error executing reason statement: {type(e).__name__}: {e}"
            error_msg += format_error_location(node)
            raise RuntimeError(error_msg) from e

    def visit_binary_expression(self, node: BinaryExpression, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a BinaryExpression node, evaluating the expression."""
        try:
            left = self.visit_node(node.left, context)
            right = self.visit_node(node.right, context)

            if node.operator == BinaryOperator.ADD:
                # Handle string concatenation by converting non-string values to strings
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            elif node.operator == BinaryOperator.SUBTRACT:
                return left - right
            elif node.operator == BinaryOperator.MULTIPLY:
                return left * right
            elif node.operator == BinaryOperator.DIVIDE:
                if right == 0:
                    error_msg = "Division by zero"
                    error_msg += format_error_location(node)
                    raise StateError(error_msg)
                return left / right
            elif node.operator == BinaryOperator.MODULO:
                if right == 0:
                    error_msg = "Modulo by zero"
                    error_msg += format_error_location(node)
                    raise StateError(error_msg)
                return left % right
            elif node.operator == BinaryOperator.EQUALS:
                return left == right
            elif node.operator == BinaryOperator.NOT_EQUALS:
                return left != right
            elif node.operator == BinaryOperator.LESS_THAN:
                return left < right
            elif node.operator == BinaryOperator.GREATER_THAN:
                return left > right
            elif node.operator == BinaryOperator.LESS_EQUALS:
                return left <= right
            elif node.operator == BinaryOperator.GREATER_EQUALS:
                return left >= right
            elif node.operator == BinaryOperator.AND:
                if not isinstance(left, bool) or not isinstance(right, bool):
                    error_msg = "AND operator requires boolean operands"
                    error_msg += format_error_location(node)
                    raise StateError(error_msg)
                return left and right
            elif node.operator == BinaryOperator.OR:
                if not isinstance(left, bool) or not isinstance(right, bool):
                    error_msg = "OR operator requires boolean operands"
                    error_msg += format_error_location(node)
                    raise StateError(error_msg)
                return left or right
            elif node.operator == BinaryOperator.IN:
                if not isinstance(right, (list, dict, str)):
                    error_msg = "IN operator requires a list, dict, or string as right operand"
                    error_msg += format_error_location(node)
                    raise StateError(error_msg)
                return left in right
            else:
                error_msg = f"Unsupported binary operator: {node.operator}"
                error_msg += format_error_location(node)
                raise RuntimeError(error_msg)
        except Exception as e:
            if isinstance(e, (RuntimeError, StateError)):
                raise
            error_msg = f"Error evaluating binary expression: {type(e).__name__}: {e}"
            error_msg += format_error_location(node)
            raise RuntimeError(error_msg) from e

    def visit_literal_expression(self, node: LiteralExpression, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a LiteralExpression node, returning the literal value."""
        if isinstance(node.literal.value, FStringExpression):
            return self.visit_fstring_expression(node.literal.value, context)
        return node.literal.value

    def visit_identifier(self, node: Identifier, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit an Identifier node, retrieving the variable value."""
        try:
            return self._get_variable(node.name)
        except StateError:
            error_msg = f"Variable not found: {node.name}"
            error_msg += format_error_location(node)
            raise StateError(error_msg) from None

    def visit_function_call(self, node: FunctionCall, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a FunctionCall node, executing the function."""
        try:
            # First check if this is a function call to a registered function
            if "." not in node.name and has_function(node.name):
                # Convert arguments - in future this would handle proper parameter matching
                args = {}
                for key, value in node.args.items():
                    # Evaluate argument expressions if needed
                    if isinstance(value, (LiteralExpression, Identifier, BinaryExpression, FunctionCall)):
                        args[key] = self.visit_node(value, context)
                    else:
                        args[key] = value

                # Call the function from the registry
                return call_function(node.name, self.context, args)
            
            # If the function name contains dots, it might be a Python object method call
            elif "." in node.name:
                # Try to resolve the object path
                obj = None
                parts = node.name.split(".")
                
                # Start by getting the base object
                try:
                    obj = self._get_variable(parts[0])
                    
                    # Navigate through the object attributes/methods
                    for i, part in enumerate(parts[1:], start=1):
                        if i == len(parts) - 1:
                            # Last part is the method to call
                            method = getattr(obj, part)
                            
                            # Convert arguments
                            args_list = []
                            kwargs = {}
                            
                            for key, value in node.args.items():
                                # Evaluate argument expressions if needed
                                if isinstance(value, (LiteralExpression, Identifier, BinaryExpression, FunctionCall)):
                                    evaluated_value = self.visit_node(value, context)
                                else:
                                    evaluated_value = value
                                
                                # If the key is a position number, add to args_list
                                if key.isdigit():
                                    position = int(key)
                                    # Expand args_list if needed
                                    while len(args_list) <= position:
                                        args_list.append(None)
                                    args_list[position] = evaluated_value
                                else:
                                    # Otherwise it's a keyword argument
                                    kwargs[key] = evaluated_value
                            
                            # Check if we have a callable
                            if callable(method):
                                return method(*args_list, **kwargs)
                            else:
                                error_msg = f"Object attribute '{part}' in '{node.name}' is not callable"
                                error_msg += format_error_location(node)
                                raise RuntimeError(error_msg)
                        else:
                            # Navigate to the next attribute
                            obj = getattr(obj, part)
                    
                    # We should never reach this point due to the return in the last part
                    return obj
                
                except (AttributeError, TypeError) as e:
                    error_msg = f"Error accessing object or method in '{node.name}': {str(e)}"
                    error_msg += format_error_location(node)
                    raise RuntimeError(error_msg) from e
                except StateError:
                    error_msg = f"Variable not found in '{node.name}'"
                    error_msg += format_error_location(node)
                    raise RuntimeError(error_msg)
            
            else:
                error_msg = f"Function '{node.name}' is not registered"
                error_msg += format_error_location(node)
                raise RuntimeError(error_msg)
        except Exception as e:
            if isinstance(e, (RuntimeError, StateError)):
                raise
            error_msg = f"Error calling function '{node.name}': {str(e)}"
            error_msg += format_error_location(node)
            raise RuntimeError(error_msg) from e

    def visit_literal(self, node: Literal, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a Literal node, returning its value."""
        if isinstance(node.value, FStringExpression):
            return self.visit_fstring_expression(node.value, context)
        return node.value

    def visit_fstring_expression(self, node: FStringExpression, context: Optional[Dict[str, Any]] = None) -> str:
        """Visit an FStringExpression node, evaluating all parts."""
        result = ""
        for part in node.parts:
            if isinstance(part, str):
                result += part
            else:
                value = self.visit_node(part, context)
                result += str(value)
        return result

    def visit_node(self, node: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Generic visit method that dispatches to specific methods based on node type."""
        if isinstance(node, Program):
            return self.visit_program(node, context)
        elif isinstance(node, Assignment):
            return self.visit_assignment(node, context)
        elif isinstance(node, LogStatement):
            return self.visit_log_statement(node, context)
        elif isinstance(node, LogLevelSetStatement):
            return self.visit_log_level_set_statement(node, context)
        elif isinstance(node, Conditional):
            return self.visit_conditional(node, context)
        elif isinstance(node, WhileLoop):
            return self.visit_while_loop(node, context)
        elif isinstance(node, ReasonStatement):
            # For tests and synchronous environments
            # First make it synchronous again by removing async from visit_reason_statement
            return self._visit_reason_statement_sync(node, context)
        elif isinstance(node, BinaryExpression):
            return self.visit_binary_expression(node, context)
        elif isinstance(node, LiteralExpression):
            return self.visit_literal_expression(node, context)
        elif isinstance(node, Identifier):
            return self.visit_identifier(node, context)
        elif isinstance(node, FunctionCall):
            # Handle Function Call both as expression and statement
            return self.visit_function_call(node, context)
        elif isinstance(node, Literal):
            return self.visit_literal(node, context)
        elif isinstance(node, FStringExpression):
            return self.visit_fstring_expression(node, context)
        else:
            error_msg = f"Unsupported node type: {type(node).__name__}"
            raise RuntimeError(error_msg)


# Factory function for creating interpreters
def create_interpreter(context: RuntimeContext) -> Interpreter:
    """Create a new interpreter with the given context."""
    return Interpreter(context)
