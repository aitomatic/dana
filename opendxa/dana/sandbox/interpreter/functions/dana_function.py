"""
Dana function implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.sandbox.interpreter.executor.control_flow_executor import ReturnException
from opendxa.dana.sandbox.interpreter.functions.sandbox_function import SandboxFunction
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class DanaFunction(SandboxFunction, Loggable):
    """A Dana function that can be called with arguments."""

    def __init__(self, body: list[Any], parameters: list[str], context: SandboxContext | None = None):
        """Initialize a Dana function.

        Args:
            body: The function body statements
            parameters: The parameter names
            context: The sandbox context
        """
        super().__init__(context)
        self.body = body
        self.parameters = parameters  # Properly set the parameters property

    def prepare_context(self, context: SandboxContext | Any, args: list[Any], kwargs: dict[str, Any]) -> SandboxContext:
        """
        Prepare context for a Dana function.

        For Dana functions:
        - Creates a clean local scope
        - Sets up interpreter if needed
        - Maps arguments to the local scope

        Args:
            context: The original context or a positional argument
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Prepared context
        """
        # If context is not a SandboxContext, assume it's a positional argument
        if not isinstance(context, SandboxContext):
            args = [context] + args
            context = self.context.copy() if self.context else SandboxContext()

        # Create a copy of the context to work with
        prepared_context = context.copy()

        # If the context doesn't have an interpreter, try to get it from the original
        if not hasattr(prepared_context, "_interpreter") or prepared_context._interpreter is None:
            if hasattr(context, "_interpreter") and context._interpreter is not None:
                prepared_context._interpreter = context._interpreter

        # Store original local scope so we can restore it later
        original_locals = prepared_context.get_scope("local").copy()
        prepared_context._original_locals = original_locals

        # Map positional arguments to parameters in the local scope
        for i, param_name in enumerate(self.parameters):
            if i < len(args):
                prepared_context.set(param_name, args[i])

        # Map keyword arguments to the local scope
        for kwarg_name, kwarg_value in kwargs.items():
            if kwarg_name in self.parameters:
                prepared_context.set(kwarg_name, kwarg_value)

        return prepared_context

    def restore_context(self, context: SandboxContext, original_context: SandboxContext) -> None:
        """
        Restore the context after Dana function execution.

        Args:
            context: The current context
            original_context: The original context before execution
        """
        # Restore the original local scope
        if hasattr(context, "_original_locals"):
            context.set_scope("local", context._original_locals)
            delattr(context, "_original_locals")

    def execute(self, context: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute the function with the given arguments.

        Args:
            context: The execution context
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the function execution
        """
        try:
            # Create a new context for function execution
            if not isinstance(context, SandboxContext):
                context = SandboxContext(parent=self.context)
            else:
                # Create a new context that inherits from the provided context
                context = SandboxContext(parent=context)

            # If the context doesn't have an interpreter, assign the one from self.context
            if not hasattr(context, "_interpreter") or context._interpreter is None:
                if self.context is not None and hasattr(self.context, "_interpreter") and self.context._interpreter is not None:
                    context._interpreter = self.context._interpreter

            # Create a new scope for the function
            for i, param_name in enumerate(self.parameters):
                if i < len(args):
                    # Parameter names are already scoped (e.g., "local.x"), so use set() directly
                    context.set(param_name, args[i])

            # Set any keyword args
            for kwarg_name, kwarg_value in kwargs.items():
                if kwarg_name in self.parameters:
                    # Parameter names are already scoped, so use set() directly
                    context.set(kwarg_name, kwarg_value)

            # Execute each statement in the function body
            result = None
            for statement in self.body:
                try:
                    # Use _interpreter attribute (with underscore)
                    if hasattr(context, "_interpreter") and context._interpreter is not None:
                        # Execute the statement and capture its result
                        stmt_result = context._interpreter.execute_statement(statement, context)
                        # Update result with the statement's value if it's not None
                        if stmt_result is not None:
                            result = stmt_result
                        self.debug(f"statement: {statement}, result: {stmt_result}")
                    else:
                        raise RuntimeError("No interpreter available in context")
                except ReturnException as e:
                    # Return statement was encountered - return its value
                    return e.value
                except Exception as e:
                    self.error(f"Error executing statement: {e}")
                    raise

            # Return the last non-None result
            return result

        except ReturnException as e:
            # Return statement was encountered in outer scope
            return e.value
        except Exception as e:
            self.error(f"Error in function execution: {e}")
            raise
