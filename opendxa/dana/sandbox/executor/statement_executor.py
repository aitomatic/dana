"""Statement executor for the DANA interpreter.

This module provides the StatementExecutor class, which is responsible for
executing DANA program statements.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from opendxa.dana.common.error_utils import ErrorUtils
from opendxa.dana.common.exceptions import SandboxError, StateError
from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    Conditional,
    Expression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    LogLevel,
    LogLevelSetStatement,
    LogStatement,
    PrintStatement,
    Program,
    ReasonStatement,
    Statement,
    WhileLoop,
)
from opendxa.dana.sandbox.core_functions.reason_function import ReasonFunction
from opendxa.dana.sandbox.executor.base_executor import BaseExecutor
from opendxa.dana.sandbox.executor.context_manager import ContextManager
from opendxa.dana.sandbox.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.sandbox.executor.llm_integration import LLMIntegration
from opendxa.dana.sandbox.hooks import HookRegistry, HookType
from opendxa.dana.sandbox.log_manager import LogManager

# Map DANA LogLevel to Python logging levels
LEVEL_MAP = {LogLevel.DEBUG: logging.DEBUG, LogLevel.INFO: logging.INFO, LogLevel.WARN: logging.WARNING, LogLevel.ERROR: logging.ERROR}

# Define the types of nodes we can execute
ExecutableNode = Union[
    Assignment, LogStatement, Conditional, WhileLoop, LogLevelSetStatement, ReasonStatement, FunctionCall, Identifier, Program
]


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

    LAST_VALUE = "system.__last_value"

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

    def _execute_hook(self, hook_type: HookType, node: Any, additional_context: Optional[Dict[str, Any]] = None) -> None:
        """Execute hooks for the given hook type.

        Args:
            hook_type: The type of hook to execute
            node: The AST node being executed
            additional_context: Additional context data to include in the hook context
        """
        if HookRegistry.has_hooks(hook_type):
            hook_context = {
                "node": node,
                "environment": self.environment,
                "interpreter": self.interpreter,
            }
            if additional_context:
                hook_context.update(additional_context)
            HookRegistry.execute(hook_type, hook_context)

    def execute(self, statement: Statement) -> Any:
        """Execute a statement.

        Args:
            statement: The statement to execute

        Returns:
            The result of executing the statement

        Raises:
            RuntimeError: If the statement type is not supported
        """
        if isinstance(statement, Assignment):
            return self.execute_assignment(statement)
        elif isinstance(statement, LogStatement):
            return self.execute_log_statement(statement)
        elif isinstance(statement, Conditional):
            return self.execute_conditional(statement)
        elif isinstance(statement, WhileLoop):
            return self.execute_while_loop(statement)
        elif isinstance(statement, LogLevelSetStatement):
            return self.execute_log_level_set(statement)
        elif isinstance(statement, ReasonStatement):
            return self.execute_reason_statement(statement)
        elif isinstance(statement, FunctionCall):
            return self.execute_function_call(statement)
        elif isinstance(statement, PrintStatement):
            return self.execute_print_statement(statement)
        elif isinstance(statement, (Identifier, BinaryExpression, FunctionCall, LiteralExpression)):
            return self.expression_evaluator.evaluate(statement)
        else:
            raise SandboxError(f"Unsupported statement type: {type(statement)}")

    def execute_assignment(self, node: Assignment) -> Any:
        """Execute an assignment statement.

        Args:
            node: The assignment node to execute

        Returns:
            The result of the assignment
        """
        try:
            # Execute before assignment hook
            self._execute_hook(HookType.BEFORE_ASSIGNMENT, node)

            # Evaluate the right-hand side
            value = self.expression_evaluator.evaluate(node.value)

            # Handle scoped variables
            if "." in node.target.name:
                parts = node.target.name.split(".", 1)
                scope, var_name = parts

                # Validate scope
                if scope not in RuntimeScopes.ALL:
                    raise ErrorUtils.create_state_error(f"Invalid scope: {scope}", node)

                # Set the value in the appropriate scope
                self.context_manager.set_in_context(var_name, value, scope=scope)
            else:
                # Set the value in the current context
                self.context_manager.set(node.target.name, value)

            result = value  # Store the value as the result
            self.context_manager.set_in_context(StatementExecutor.LAST_VALUE, result)

            # Execute after assignment hook
            self._execute_hook(HookType.AFTER_ASSIGNMENT, node, {"value": value})

            return result
        except Exception as e:
            self.debug(f"Error in assignment: {e}")
            if isinstance(e, StateError):
                raise e
            else:
                raise ErrorUtils.create_runtime_error(f"Error in assignment: {e}", node)

    def execute_log_statement(self, node: LogStatement) -> Any:
        """Execute a log statement.

        Args:
            node: The log statement node to execute

        Returns:
            The result of the log statement
        """
        try:
            # Execute before log hook
            self._execute_hook(HookType.BEFORE_LOG, node)

            # Evaluate the message expression
            value = self.expression_evaluator.evaluate(node.message)

            # Log the message with the appropriate level
            self.context_manager.context.logger.log(node.level, str(value))

            # Execute after log hook
            self._execute_hook(HookType.AFTER_LOG, node, {"message": value})

            return value
        except Exception as e:
            self.debug(f"Error in log statement: {e}")
            raise ErrorUtils.create_runtime_error(f"Error in log statement: {e}", node)

    def execute_log_level_set(self, node: LogLevelSetStatement) -> None:
        """Execute a log level set statement.

        Args:
            node: The log level set statement node to execute

        Raises:
            RuntimeError: If the log level set statement fails
        """
        # Set the log level via the central LogManager
        LogManager.set_dana_log_level(node.level, self.context_manager.context)

    def execute_print_statement(self, node: PrintStatement) -> None:
        """Execute a print statement.

        Args:
            node: The print statement to execute

        Raises:
            RuntimeError: If the print statement fails
        """
        try:
            # Use a custom context that includes direct references to unprefixed variables
            custom_context = self._enhance_local_context()

            # Evaluate the message
            value = self.expression_evaluator.evaluate(node.message, custom_context)
            print(value)  # Use Python's print function
        except Exception as e:
            error, passthrough = ErrorUtils.handle_execution_error(e, node, "executing print statement")
            if passthrough:
                raise error
            else:
                raise SandboxError(f"Failed to execute print statement: {e}")

    def execute_conditional(self, node: Conditional) -> Any:
        """Execute a conditional statement.

        Args:
            node: The conditional node to execute

        Returns:
            The result of the executed branch
        """
        try:
            # Execute before conditional hook
            self._execute_hook(HookType.BEFORE_CONDITIONAL, node)

            # Evaluate the condition
            condition = self.expression_evaluator.evaluate(node.condition)

            if condition:
                # Execute the if body
                return self.execute(node.then_branch)
            elif node.else_branch:
                # Execute the else body if condition is false and else body exists
                return self.execute(node.else_branch)

            # Execute after conditional hook
            self._execute_hook(HookType.AFTER_CONDITIONAL, node, {"condition": condition})

            return None
        except Exception as e:
            error, passthrough = ErrorUtils.handle_execution_error(e, node, "executing conditional")
            if passthrough:
                raise error
            else:
                raise SandboxError(f"Failed to execute conditional: {e}")

    def execute_while_loop(self, node: WhileLoop) -> Any:
        """Execute a while loop.

        Args:
            node: The while loop node to execute

        Returns:
            The result of the last executed statement in the loop
        """
        try:
            max_iterations = 1000  # Prevent infinite loops
            iteration_count = 0
            result = None

            while True:
                # Evaluate the condition
                condition = self.expression_evaluator.evaluate(node.condition)

                # If condition is false, break out of the loop
                if not condition:
                    break

                # Check for maximum iterations
                iteration_count += 1
                if iteration_count > max_iterations:
                    raise SandboxError("Maximum iteration count exceeded")

                # Execute all statements in the body
                for stmt in node.body:
                    result = self.execute(stmt)

            # Execute after loop hook
            self._execute_hook(HookType.AFTER_LOOP, node, {"iterations": iteration_count})

            return result
        except Exception as e:
            error, passthrough = ErrorUtils.handle_execution_error(e, node, "executing while loop")
            if passthrough:
                raise error
                raise SandboxError(f"Failed to execute while loop: {e}")

    def execute_reason_statement(self, node: ReasonStatement) -> Any:
        """Execute a reason statement.

        Args:
            node: The reason statement to execute

        Returns:
            The result of the reasoning operation

        Raises:
            RuntimeError: If the statement cannot be executed
        """
        try:
            # Execute before reason hooks
            self._execute_hook(HookType.BEFORE_REASON, {"statement": node})

            # Evaluate the prompt expression
            if node.prompt is None:
                raise SandboxError("Reason statement must have a prompt")
            prompt = str(self.expression_evaluator.evaluate(node.prompt))

            # Evaluate any options expressions
            options = {}
            if node.options:
                for key, value in node.options.items():
                    if isinstance(value, Expression):
                        options[key] = self.expression_evaluator.evaluate(value)
                    else:
                        options[key] = value

            # Execute the reason function
            result = ReasonFunction.call(
                prompt=prompt,
                context=self.context_manager.context,
                llm_integration=self.llm_integration,
                options=options,
            )

            # Execute after reason hooks
            self._execute_hook(HookType.AFTER_REASON, {"statement": node, "result": result})

            return result

        except Exception as e:
            self.error(f"Error executing reason statement: {e}")
            raise SandboxError(f"Error executing reason statement: {e}") from e

    def execute_function_call(self, node: FunctionCall) -> Any:
        """Execute a function call.

        Args:
            node: The function call node to execute

        Returns:
            The result of the function call

        Raises:
            RuntimeError: If the function call fails
        """
        # Execute the function call
        result = self._execute_method_or_variable_function(node)

        # Store the result in the context
        self.context_manager.set_in_context(StatementExecutor.LAST_VALUE, result)

        return result

    def _execute_method_or_variable_function(self, node: FunctionCall) -> Any:
        """Execute a method call or variable function.

        Args:
            node: The function call node

        Returns:
            The result of the function call

        Raises:
            RuntimeError: If the function call fails
        """
        # Convert all argument values first
        processed_args = {}
        for key, value in node.args.items():
            processed_args[key] = self.expression_evaluator.evaluate(value)

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
            func = self.context_manager.get_from_context(node.name)

            if callable(func):
                return func(*args_list, **kwargs)
            else:
                raise SandboxError(f"Variable '{node.name}' is not callable")

    def _execute_method_call(self, name: str, args: List[Any], kwargs: Dict[str, Any]) -> Any:
        """Execute a method call on an object.

        Args:
            name: The name of the method to call
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            The result of the method call

        Raises:
            RuntimeError: If the method call fails
        """
        # Split the name into object and method parts
        parts = name.split(".")
        obj_name = ".".join(parts[:-1])
        method_name = parts[-1]

        # Get the object
        obj = self.context_manager.get_from_context(obj_name)

        # Get the method
        method = getattr(obj, method_name, None)
        if method is None:
            raise SandboxError(f"Object '{obj_name}' has no method '{method_name}'")

        # Call the method
        return method(*args, **kwargs)

    def _enhance_local_context(self) -> Dict[str, Any]:
        """Enhance the local context with unprefixed variables from the local scope.

        Returns:
            The enhanced context
        """
        custom_context = {}

        # Add unprefixed variables from the local scope
        try:
            local_scope = self.context_manager.context._state.get("local", {})
            for key, value in local_scope.items():
                # Only add top-level local variables to context
                if "." not in key and key not in custom_context:
                    custom_context[key] = value
        except (AttributeError, KeyError):
            # If we can't access private scope, just use the original context
            pass

        return custom_context
