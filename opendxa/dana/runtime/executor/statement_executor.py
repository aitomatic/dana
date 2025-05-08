"""Statement executor for the DANA interpreter.

This module provides the StatementExecutor class, which is responsible for
executing statements in DANA programs.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from opendxa.common.utils.logging.dxa_logger import DXA_LOGGER
from opendxa.dana.exceptions import RuntimeError, StateError
from opendxa.dana.language.ast import (
    Assignment,
    Conditional,
    FunctionCall,
    LogLevel,
    LogLevelSetStatement,
    LogStatement,
    PrintStatement,
    ReasonStatement,
    WhileLoop,
)
from opendxa.dana.runtime.executor.base_executor import BaseExecutor
from opendxa.dana.runtime.executor.context_manager import ContextManager
from opendxa.dana.runtime.executor.error_utils import (
    handle_execution_error,
)
from opendxa.dana.runtime.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.runtime.executor.llm_integration import LLMIntegration
from opendxa.dana.runtime.function_registry import call_function, has_function
from opendxa.dana.runtime.hooks import HookType, has_hooks

# Map DANA LogLevel to Python logging levels
LEVEL_MAP = {LogLevel.DEBUG: logging.DEBUG, LogLevel.INFO: logging.INFO, LogLevel.WARN: logging.WARNING, LogLevel.ERROR: logging.ERROR}


class StatementExecutor(BaseExecutor):
    """Executes statements in DANA programs.

    Responsibilities:
    - Execute assignments
    - Execute conditionals
    - Execute loops
    - Execute log statements
    - Execute function calls
    - Execute reason statements
    """

    def __init__(self, context_manager: ContextManager, expression_evaluator: ExpressionEvaluator, llm_integration: LLMIntegration):
        """Initialize the statement executor.

        Args:
            context_manager: The context manager for variable resolution
            expression_evaluator: The evaluator for expressions
            llm_integration: The integration for LLM reasoning
        """
        super().__init__()
        self.context_manager = context_manager
        self.expression_evaluator = expression_evaluator
        self.llm_integration = llm_integration

    def execute(self, node: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a statement node.

        Args:
            node: The statement node to execute
            context: Optional local context for variable resolution

        Returns:
            The result of executing the statement (or None for statements that don't produce values)

        Raises:
            RuntimeError: If the statement cannot be executed
        """
        # Prepare the hook context
        hook_context = {
            "statement": node,
            "visitor": self,  # For backward compatibility
            "interpreter": self,
            "context": self.context_manager.context,
        }

        try:
            # Execute before statement hooks
            if has_hooks(HookType.BEFORE_STATEMENT):
                from opendxa.dana.runtime.hooks import execute_hook

                execute_hook(HookType.BEFORE_STATEMENT, hook_context)

            # Execute the statement based on its type and store the result
            result = None
            if isinstance(node, Assignment):
                # Execute assignment with appropriate hooks
                # Before assignment hook
                if has_hooks(HookType.BEFORE_ASSIGNMENT):
                    from opendxa.dana.runtime.hooks import execute_hook

                    assignment_hook_context = {"statement": node, "interpreter": self, "context": self.context_manager.context}
                    execute_hook(HookType.BEFORE_ASSIGNMENT, assignment_hook_context)

                # For assignments, evaluate the value first
                value = self.expression_evaluator.evaluate(node.value, context)
                self.context_manager.set_variable(node.target.name, value)
                result = value  # Store the value as the result
                self.context_manager.set_variable("private.__last_value", value)  # Store for REPL output
                self.debug(f"Set {node.target.name} = {value}")

                # After assignment hook
                if has_hooks(HookType.AFTER_ASSIGNMENT):
                    from opendxa.dana.runtime.hooks import execute_hook

                    # Include the evaluated value in the hook context
                    assignment_hook_context = {
                        "statement": node,
                        "interpreter": self,
                        "context": self.context_manager.context,
                        "value": value,
                    }
                    execute_hook(HookType.AFTER_ASSIGNMENT, assignment_hook_context)
            elif isinstance(node, LogStatement):
                self.execute_log_statement(node)
                # Log statements don't have a return value
                self.context_manager.set_variable("private.__last_value", None)
            elif isinstance(node, LogLevelSetStatement):
                self.execute_log_level_set_statement(node)
                # Log level statements don't have a return value
                self.context_manager.set_variable("private.__last_value", None)
            elif isinstance(node, PrintStatement):
                self.execute_print_statement(node, context)
                # Print statements don't return a value (handled in execute_print_statement)
            elif isinstance(node, Conditional):
                self.execute_conditional(node, context)
                # Conditionals don't have a return value
                self.context_manager.set_variable("private.__last_value", None)
            elif isinstance(node, WhileLoop):
                self.execute_while_loop(node, context)
                # Loops don't have a return value
                self.context_manager.set_variable("private.__last_value", None)
            elif isinstance(node, ReasonStatement):
                result = self.execute_reason_statement(node, context)
                # The result is already stored in __last_value inside execute_reason_statement
            elif isinstance(node, FunctionCall):
                result = self.execute_function_call(node, context)
                # Store function call results for REPL output
                self.context_manager.set_variable("private.__last_value", result)
            else:
                error_msg = f"Unsupported statement type: {type(node).__name__}"
                raise RuntimeError(error_msg)

            # Execute after statement hooks
            if has_hooks(HookType.AFTER_STATEMENT):
                from opendxa.dana.runtime.hooks import execute_hook

                execute_hook(HookType.AFTER_STATEMENT, hook_context)

            return result

        except Exception as e:
            error, passthrough = handle_execution_error(e, node, "executing statement")
            if passthrough:
                raise error
            else:
                raise RuntimeError(f"Failed to execute statement: {e}")

    def execute_assignment(self, node: Assignment, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute an assignment statement.

        Args:
            node: The assignment statement to execute
            context: Optional local context for variable resolution

        Returns:
            The evaluated value of the assignment

        Raises:
            RuntimeError: If the assignment fails
        """
        # Prepare the hook context
        hook_context = {"statement": node, "interpreter": self, "context": self.context_manager.context}

        try:
            # Execute before assignment hooks
            if has_hooks(HookType.BEFORE_ASSIGNMENT):
                from opendxa.dana.runtime.hooks import execute_hook

                execute_hook(HookType.BEFORE_ASSIGNMENT, hook_context)

            # Evaluate the expression and store the value
            value = self.expression_evaluator.evaluate(node.value, context)

            # Get the target name for assignment
            target_name = node.target.name

            # Handle explicit scoping requirement
            if "." not in target_name:
                # Log a warning about missing scope
                self.warning(f"Variable '{target_name}' assigned without scope prefix. Use 'private.{target_name}' for clarity.")

            # Store the value in the variable
            self.context_manager.set_variable(target_name, value)

            # Store the value in __last_value for REPL output
            self.context_manager.set_variable("private.__last_value", value)
            self.debug(f"Set {node.target.name} = {value}")

            # Update hook context with assignment result
            hook_context["value"] = value

            # Execute after assignment hooks
            if has_hooks(HookType.AFTER_ASSIGNMENT):
                from opendxa.dana.runtime.hooks import execute_hook

                execute_hook(HookType.AFTER_ASSIGNMENT, hook_context)

            # Return the value for consistent behavior in the REPL
            return value

        except Exception as e:
            error, passthrough = handle_execution_error(e, node, "executing assignment")
            if passthrough:
                raise error
            else:
                raise RuntimeError(f"Failed to execute assignment: {e}")

    def execute_log_statement(self, node: LogStatement) -> None:
        """Execute a log statement."""
        # Get the current log level
        current_level = self.context_manager.get_variable("system.log_level")
        if current_level is None:
            current_level = LogLevel.INFO.value

        # Check if the message should be logged based on level
        level_priorities = {LogLevel.DEBUG: 0, LogLevel.INFO: 1, LogLevel.WARN: 2, LogLevel.ERROR: 3}
        if level_priorities[node.level] >= level_priorities[LogLevel(current_level)]:
            message = self.expression_evaluator.evaluate(node.message)
            # Use Loggable methods directly based on the level
            # Note: These log levels correspond to user-requested log levels in DANA code
            # (e.g., log.error(), log.info(), etc.) and are not system errors
            if node.level == LogLevel.DEBUG:
                self.debug(str(message))
            elif node.level == LogLevel.INFO:
                self.info(str(message))
            elif node.level == LogLevel.WARN:
                self.warning(str(message))
            elif node.level == LogLevel.ERROR:
                self.error(str(message))

    def execute_log_level_set_statement(self, node: LogLevelSetStatement) -> None:
        """Execute a log level set statement."""
        DXA_LOGGER.setLevel(LEVEL_MAP[node.level], scope="opendxa.dana")
        self.context_manager.set_variable("system.log_level", node.level.value)
        self.debug(f"Set log level to {node.level.value}")

    def execute_print_statement(self, node: PrintStatement, context: Optional[Dict[str, Any]] = None) -> None:
        """Execute a print statement.

        Args:
            node: The print statement to execute
            context: Optional local context for variable resolution

        Raises:
            RuntimeError: If the print statement fails
        """
        try:
            # Use a custom context that includes direct references to unprefixed variables
            custom_context = self._enhance_local_context(context)

            # Evaluate the message
            message = self.expression_evaluator.evaluate(node.message, custom_context)

            # Convert the message to a string
            if message is None:
                message_str = "None"
            else:
                message_str = str(message)

            # Print to stdout
            print(message_str)

            # Also log at debug level
            self.debug(f"Printed: {message_str}")

            # Clear the __last_value so it doesn't return anything in the REPL
            # Print statements should not produce a return value
            self.context_manager.set_variable("private.__last_value", None)
        except Exception as e:
            error, passthrough = handle_execution_error(e, node, "executing print statement")
            if passthrough:
                raise error
            else:
                raise RuntimeError(f"Failed to execute print statement: {e}")

    def execute_conditional(self, node: Conditional, context: Optional[Dict[str, Any]] = None) -> None:
        """Execute a conditional statement.

        Args:
            node: The conditional statement to execute
            context: Optional local context for variable resolution

        Raises:
            RuntimeError: If the conditional fails
        """
        try:
            # Evaluate the condition
            condition = self.expression_evaluator.evaluate(node.condition, context)

            if condition:
                # Execute the if body
                for body_stmt in node.body:
                    self.execute(body_stmt, context)
            elif node.else_body:
                # Execute the else body if condition is false and else body exists
                for else_stmt in node.else_body:
                    self.execute(else_stmt, context)
        except Exception as e:
            error, passthrough = handle_execution_error(e, node, "executing conditional")
            if passthrough:
                raise error
            else:
                raise RuntimeError(f"Failed to execute conditional: {e}")

    def execute_while_loop(self, node: WhileLoop, context: Optional[Dict[str, Any]] = None) -> None:
        """Execute a while loop.

        Args:
            node: The while loop to execute
            context: Optional local context for variable resolution

        Raises:
            RuntimeError: If the while loop fails
        """
        try:
            # Execute the loop with safety limits
            max_iterations = 1000  # Prevent infinite loops
            iteration_count = 0

            while True:
                # Evaluate the condition
                condition = self.expression_evaluator.evaluate(node.condition, context)

                # If condition is false, break out of the loop
                if not bool(condition):
                    break

                # Check for max iterations to prevent infinite loops
                iteration_count += 1
                if iteration_count > max_iterations:
                    self.warning(f"Max iterations ({max_iterations}) reached in while loop, breaking")
                    break

                # Execute all statements in the body
                for body_stmt in node.body:
                    self.execute(body_stmt, context)
        except Exception as e:
            error, passthrough = handle_execution_error(e, node, "executing while loop")
            if passthrough:
                raise error
            else:
                raise RuntimeError(f"Failed to execute while loop: {e}")

    def execute_reason_statement(self, node: ReasonStatement, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a reason statement.

        Args:
            node: The reason statement to execute
            context: Optional local context for variable resolution

        Returns:
            The result of the reasoning, if requested

        Raises:
            RuntimeError: If the reason statement fails
        """
        try:
            return self._execute_reason_statement_sync(node, context)
        except Exception as e:
            error, passthrough = handle_execution_error(e, node, "executing reason statement")
            if passthrough:
                raise error
            else:
                raise RuntimeError(f"Failed to execute reason statement: {e}")

    def _execute_reason_statement_sync(self, node: ReasonStatement, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a reason statement synchronously.

        Args:
            node: The reason statement to execute
            context: Optional local context for variable resolution

        Returns:
            The result of the reasoning

        Raises:
            RuntimeError: If the reason statement fails
        """
        # The ReasonStatement structure has a prompt instead of query
        if node.prompt is None:
            raise RuntimeError("Reason statement must have a prompt")

        try:
            # Evaluate the prompt
            prompt_value = self.expression_evaluator.evaluate(node.prompt, context)
            prompt_str = str(prompt_value)

            # Log the prompt for debugging
            self.debug(f"Reasoning prompt: {prompt_str[:100]}{'...' if len(prompt_str) > 100 else ''}")

            # Extract context variable names
            context_vars = None
            if node.context:
                context_vars = [ident.name for ident in node.context]

            # Create local context for enhanced variable access
            custom_context = self._enhance_local_context(context)

            # Execute direct synchronous reasoning with the LLM
            result = self.llm_integration.execute_direct_synchronous_reasoning(prompt_str, context_vars, node.options)

            # Store the result in __last_value for REPL output
            self.context_manager.set_variable("private.__last_value", result)

            # If we have a target variable, store the result there too
            if node.target:
                self.context_manager.set_variable(node.target.name, result)
            else:
                # Otherwise, log the result
                if isinstance(result, (dict, list)):
                    result_str = json.dumps(result, indent=2)
                else:
                    result_str = str(result)

                # Log at most the first 500 characters to avoid huge log entries
                preview = result_str[:500] + "..." if len(result_str) > 500 else result_str
                self.info(f"Reasoning result: {preview}")

            # Return the result for REPL display
            return result

        except Exception as e:
            # Provide a more helpful error message
            self.error(f"Failed to execute reason statement: {e}")
            raise RuntimeError(f"Failed to execute reason statement: {e}")

    def execute_function_call(self, node: FunctionCall, context: Optional[Dict[str, Any]] = None) -> None:
        """Execute a function call.

        Args:
            node: The function call to execute
            context: Optional local context for variable resolution

        Raises:
            RuntimeError: If the function call fails
        """
        try:
            # Check if this is a call to a registered function
            if "." not in node.name and has_function(node.name):
                self._execute_registered_function(node, context)
            else:
                # Try to handle it as a method call or variable function
                result = self._execute_method_or_variable_function(node, context)

                # Log the result (only for standalone function calls)
                if result is not None:
                    self.debug(f"Function {node.name} returned: {result}")
        except Exception as e:
            error, passthrough = handle_execution_error(e, node, f"calling function '{node.name}'")
            if passthrough:
                raise error
            else:
                raise RuntimeError(f"Failed to call function '{node.name}': {e}")

    def _execute_registered_function(self, node: FunctionCall, context: Optional[Dict[str, Any]]) -> Any:
        """Execute a registered function from the function registry.

        Args:
            node: The function call node
            context: Optional local context for variable resolution

        Returns:
            The result of the function call

        Raises:
            RuntimeError: If the function call fails
        """
        # Evaluate argument expressions
        args = {}
        for key, value in node.args.items():
            # Evaluate argument expressions if needed
            args[key] = self.expression_evaluator.evaluate(value, context)

        # Call the function from the registry
        result = call_function(node.name, self.context_manager.context, args)
        return result

    def _execute_method_or_variable_function(self, node: FunctionCall, context: Optional[Dict[str, Any]]) -> Any:
        """Execute a method call or variable function.

        Args:
            node: The function call node
            context: Optional local context for variable resolution

        Returns:
            The result of the function call

        Raises:
            RuntimeError: If the function call fails
        """
        # Convert all argument values first
        processed_args = {}
        for key, value in node.args.items():
            processed_args[key] = self.expression_evaluator.evaluate(value, context)

        # Prepare positional and keyword arguments
        args_list = []
        kwargs = {}
        for key, value in processed_args.items():
            # If the key is a position number, add to args_list
            if key.isdigit():
                position = int(key)
                # Expand args_list if needed
                while len(args_list) <= position:
                    args_list.append(None)
                args_list[position] = value
            else:
                # Otherwise it's a keyword argument
                kwargs[key] = value

        # If the function name contains dots, it might be a Python object method call
        if "." in node.name:
            return self._execute_method_call(node.name, args_list, kwargs)
        else:
            # Try to get function as variable
            func = self.context_manager.get_variable(node.name, context)

            if callable(func):
                return func(*args_list, **kwargs)
            else:
                raise RuntimeError(f"Variable '{node.name}' is not callable")

    def _execute_method_call(self, method_path: str, args_list: List[Any], kwargs: Dict[str, Any]) -> Any:
        """Execute a method call on an object.

        Args:
            method_path: The dot-path to the method (e.g., "obj.method")
            args_list: Positional arguments
            kwargs: Keyword arguments

        Returns:
            The result of the method call

        Raises:
            RuntimeError: If the method call fails
        """
        # Split the path into object and method parts
        parts = method_path.split(".")

        # Start by getting the base object
        base_name = parts[0]
        if "." not in base_name:
            base_name = f"private.{base_name}"

        try:
            obj = self.context_manager.get_variable(base_name)

            # Navigate through the object attributes to get the method
            for i, part in enumerate(parts[1:], start=1):
                if i == len(parts) - 1:
                    # Last part is the method to call
                    method = getattr(obj, part)

                    # Check if we have a callable
                    if callable(method):
                        return method(*args_list, **kwargs)
                    else:
                        raise RuntimeError(f"Object attribute '{part}' in '{method_path}' is not callable")
                else:
                    # Navigate to the next attribute
                    obj = getattr(obj, part)
        except (AttributeError, TypeError) as e:
            raise RuntimeError(f"Error accessing object or method in '{method_path}': {str(e)}")
        except StateError:
            raise RuntimeError(f"Variable not found in '{method_path}'")

    def _enhance_local_context(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enhance the local context with unprefixed variables from the private scope.

        Args:
            context: The original context to enhance

        Returns:
            The enhanced context
        """
        custom_context = context or {}

        # Add unprefixed variables from the private scope
        try:
            private_scope = self.context_manager.context._state.get("private", {})
            for key, value in private_scope.items():
                # Only add top-level private variables to context
                if "." not in key and key not in custom_context:
                    custom_context[key] = value
        except (AttributeError, KeyError):
            # If we can't access private scope, just use the original context
            pass

        return custom_context
