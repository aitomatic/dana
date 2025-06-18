"""
Dana function implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.sandbox.interpreter.executor.control_flow_executor import ReturnException
from opendxa.dana.sandbox.interpreter.functions.sandbox_function import SandboxFunction
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class DanaFunction(SandboxFunction, Loggable):
    """A Dana function that can be called with arguments."""

    def __init__(self, body: list[Any], parameters: list[str], context: SandboxContext | None = None, return_type: str | None = None):
        """Initialize a Dana function.

        Args:
            body: The function body statements
            parameters: The parameter names
            context: The sandbox context
            return_type: The function's return type annotation
        """
        super().__init__(context)
        self.body = body
        self.parameters = parameters
        self.return_type = return_type
        DXA_LOGGER.debug(f"Created DanaFunction with parameters={parameters}, return_type={return_type}")

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
        DXA_LOGGER.debug("DanaFunction.execute called with:")
        DXA_LOGGER.debug(f"  context: {type(context)}")
        DXA_LOGGER.debug(f"  args: {args}")
        DXA_LOGGER.debug(f"  kwargs: {kwargs}")
        DXA_LOGGER.debug(f"  parameters: {self.parameters}")
        DXA_LOGGER.debug(f"  body: {self.body}")
        DXA_LOGGER.debug(f"  return_type: {self.return_type}")

        try:
            # Prepare the execution context using the existing method
            prepared_context = self.prepare_context(context, list(args), kwargs)

            # Execute each statement in the function body
            result = None
            for statement in self.body:
                try:
                    # Use _interpreter attribute (with underscore)
                    if hasattr(prepared_context, "_interpreter") and prepared_context._interpreter is not None:
                        # Execute the statement and capture its result
                        stmt_result = prepared_context._interpreter.execute_statement(statement, prepared_context)
                        # Update result with the statement's value if it's not None
                        if stmt_result is not None:
                            result = stmt_result
                        DXA_LOGGER.debug(f"statement: {statement}, result: {stmt_result}")
                    else:
                        raise RuntimeError("No interpreter available in context")
                except ReturnException as e:
                    # Return statement was encountered - return its value
                    return e.value
                except Exception as e:
                    DXA_LOGGER.error(f"Error executing statement: {e}")
                    raise

            # Restore the original context if needed
            if isinstance(context, SandboxContext):
                self.restore_context(prepared_context, context)

            # Return the last non-None result
            return result

        except Exception as e:
            DXA_LOGGER.error(f"Error executing Dana function: {e}")
            raise
