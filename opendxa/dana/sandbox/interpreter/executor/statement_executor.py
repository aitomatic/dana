"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Statement executor for the DANA interpreter.

This module provides the StatementExecutor class, which is responsible for
executing DANA program statements.
"""

from typing import Any, Dict, List, Optional, Union

from opendxa.dana.common.error_utils import ErrorUtils
from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.sandbox.interpreter.executor.base_executor import BaseExecutor
from opendxa.dana.sandbox.interpreter.executor.context_manager import ContextManager
from opendxa.dana.sandbox.interpreter.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.sandbox.interpreter.executor.llm_integration import LLMIntegration
from opendxa.dana.sandbox.interpreter.hooks import HookRegistry, HookType
from opendxa.dana.sandbox.parser.ast import (
    AssertStatement,
    Assignment,
    BinaryExpression,
    BreakStatement,
    Conditional,
    ContinueStatement,
    ForLoop,
    FunctionCall,
    Identifier,
    LiteralExpression,
    PassStatement,
    PrintStatement,
    Program,
    RaiseStatement,
    ReturnStatement,
    Statement,
    WhileLoop,
)

# Define the types of nodes we can execute
ExecutableNode = Union[Assignment, Conditional, WhileLoop, FunctionCall, Identifier, Program]


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


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
        self._output_buffer = []  # Buffer for capturing print output

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
        elif isinstance(statement, Conditional):
            return self.execute_conditional(statement)
        elif isinstance(statement, WhileLoop):
            return self.execute_while_loop(statement)
        elif isinstance(statement, ForLoop):
            return self.execute_for_loop(statement)
        elif isinstance(statement, FunctionCall):
            return self.execute_function_call(statement)
        elif isinstance(statement, PrintStatement):
            return self.execute_print_statement(statement)
        elif isinstance(statement, PassStatement):
            return self.execute_pass_statement(statement)
        elif isinstance(statement, ReturnStatement):
            return self.execute_return_statement(statement)
        elif isinstance(statement, BreakStatement):
            return self.execute_break_statement(statement)
        elif isinstance(statement, ContinueStatement):
            return self.execute_continue_statement(statement)
        elif isinstance(statement, RaiseStatement):
            return self.execute_raise_statement(statement)
        elif isinstance(statement, AssertStatement):
            return self.execute_assert_statement(statement)
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
            value = None
            self._execute_hook(HookType.BEFORE_ASSIGNMENT, node)
            try:
                value = self.expression_evaluator.evaluate(node.value)

                # Special handling for FStringExpression to ensure it's properly evaluated
                if hasattr(value, "__class__") and value.__class__.__name__ == "FStringExpression":
                    value = self.expression_evaluator.evaluate(value)
            except Exception:
                raise

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
        except Exception:
            raise

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
            print(str(value))  # Write to stdout for test capture
            self._output_buffer.append(str(value))  # Also capture for REPL/UX
        except Exception as e:
            error, passthrough = ErrorUtils.handle_execution_error(e, node, "executing print statement")
            if passthrough:
                raise error
            else:
                raise SandboxError(f"Failed to execute print statement: {e}")

    def execute_conditional(self, node: "Conditional") -> Any:
        """Execute a conditional (if/else) statement."""
        condition = self.expression_evaluator.evaluate(node.condition)
        if condition:
            result = None
            for stmt in node.body:
                result = self.execute(stmt)
            return result
        elif node.else_body:
            result = None
            for stmt in node.else_body:
                result = self.execute(stmt)
            return result
        return None

    def execute_while_loop(self, node: "WhileLoop") -> Any:
        """Execute a while loop statement."""
        max_iterations = 1000  # Prevent infinite loops
        iteration_count = 0
        result = None
        while True:
            condition = self.expression_evaluator.evaluate(node.condition)
            if not condition:
                break
            iteration_count += 1
            if iteration_count > max_iterations:
                raise SandboxError("Maximum iteration count exceeded")
            try:
                for stmt in node.body:
                    result = self.execute(stmt)
            except BreakException:
                break
            except ContinueException:
                continue
        return result

    def execute_for_loop(self, node: "ForLoop") -> Any:
        """Execute a for loop statement."""
        # Evaluate the iterable expression
        iterable = self.expression_evaluator.evaluate(node.iterable)

        # Special handling for lists with LiteralExpression items
        if isinstance(iterable, list):
            # Extract values from LiteralExpression objects
            processed_iterable = []
            for item in iterable:
                if hasattr(item, "__class__") and item.__class__.__name__ == "LiteralExpression":
                    if hasattr(item, "value"):
                        processed_iterable.append(item.value)
                    else:
                        processed_iterable.append(item)
                else:
                    processed_iterable.append(item)
            iterable = processed_iterable

        # Ensure the iterable is actually iterable
        if not hasattr(iterable, "__iter__"):
            raise SandboxError(f"For loop iterable must be iterable, got {type(iterable)}")

        # Iterate over the iterable
        result = None
        max_iterations = 1000  # Prevent infinite loops
        iteration_count = 0

        for item in iterable:
            iteration_count += 1
            if iteration_count > max_iterations:
                raise SandboxError("Maximum iteration count exceeded")

            # Set the loop variable in the context
            var_name = node.target.name
            if "." in var_name:
                # If the target has a scope prefix, use it
                parts = var_name.split(".", 1)
                scope, name = parts
                self.context_manager.set_in_context(name, item, scope=scope)
            else:
                # Otherwise, use local scope
                self.context_manager.set_in_context(var_name, item, scope="local")

            # Execute the loop body
            try:
                for stmt in node.body:
                    result = self.execute(stmt)
            except BreakException:
                break
            except ContinueException:
                continue

        return result

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

        # Explicit scope: local:foo, private:bar, etc.
        if ":" in node.name:
            scope, var_name = node.name.split(":", 1)
            try:
                func = self.context_manager.get_from_context(var_name, scope=scope)
                if callable(func):
                    return func(*args_list, **kwargs)
                else:
                    raise SandboxError(f"Variable '{scope}:{var_name}' is not callable")
            except Exception:
                raise SandboxError(f"Function or variable '{scope}:{var_name}' not found in context")

        # If the function name contains dots, it might be a Python object method call
        if "." in node.name:
            return self._execute_method_call(node.name, args_list, kwargs)
        else:
            # Try DanaRegistry and PythonRegistry first
            from opendxa.dana.sandbox.interpreter.functions.dana_function import DanaRegistry
            from opendxa.dana.sandbox.interpreter.functions.python_function import PythonRegistry

            if DanaRegistry().has(node.name):
                func = DanaRegistry().get(node.name)
                return func.call(self.context_manager.context, *args_list, **kwargs)
            elif PythonRegistry().has(node.name):
                func = PythonRegistry().get(node.name)
                return func.call(self.context_manager.context, *args_list, **kwargs)
            # Fallback: Try to get local.foo as a variable from context
            try:
                func = self.context_manager.get_from_context(node.name, scope="local")
                if callable(func):
                    return func(*args_list, **kwargs)
                else:
                    raise SandboxError(f"Variable 'local:{node.name}' is not callable")
            except Exception:
                raise SandboxError(f"Function or variable '{node.name}' not found in registries or local context")

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

    def execute_pass_statement(self, node: "PassStatement") -> None:
        """Execute a pass statement (does nothing)."""
        return None

    def execute_return_statement(self, node: "ReturnStatement") -> None:
        """Execute a return statement by raising ReturnException with the value."""
        value = self.expression_evaluator.evaluate(node.value) if node.value is not None else None
        raise ReturnException(value)

    def execute_break_statement(self, node: "BreakStatement") -> None:
        """Execute a break statement by raising BreakException."""
        raise BreakException()

    def execute_continue_statement(self, node: "ContinueStatement") -> None:
        """Execute a continue statement by raising ContinueException."""
        raise ContinueException()

    def execute_raise_statement(self, node: "RaiseStatement") -> None:
        """Execute a raise statement by raising a Python exception with the evaluated value."""
        # Evaluate the value to raise (if provided)
        value = None
        if node.value is not None:
            value = self.expression_evaluator.evaluate(node.value)

        # If the value is a string, use it as the error message
        if isinstance(value, str):
            raise SandboxError(value)
        # If it's an exception instance, raise it directly
        elif isinstance(value, Exception):
            raise value
        # Otherwise, raise a generic exception with the value
        else:
            raise SandboxError(f"Raised: {str(value)}")

    def execute_assert_statement(self, node: "AssertStatement") -> None:
        """Execute an assert statement by raising AssertionError if the condition is false."""
        condition = self.expression_evaluator.evaluate(node.condition)
        if not condition:
            message = self.expression_evaluator.evaluate(node.message) if node.message is not None else None
            raise AssertionError(message)

    def get_and_clear_output(self) -> str:
        """Retrieve and clear the output buffer as a single string (joined by newlines)."""
        output = "\n".join(self._output_buffer)
        self._output_buffer.clear()
        return output
