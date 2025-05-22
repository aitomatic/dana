"""
DANA function implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, Dict, List, Optional

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.sandbox.interpreter.executor.dana_executor import ReturnException
from opendxa.dana.sandbox.interpreter.functions.sandbox_function import SandboxFunction
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class DanaFunction(SandboxFunction, Loggable):
    """A DANA function that can be called with arguments."""

    def __init__(self, body: List[Any], parameters: List[str], context: Optional[SandboxContext] = None):
        """Initialize a DANA function.

        Args:
            body: The function body statements
            parameters: The parameter names
            context: The sandbox context
        """
        super().__init__(context)
        self.body = body
        self.parameters = parameters  # Properly set the parameters property

    def prepare_context(self, context: SandboxContext, args: List[Any], kwargs: Dict[str, Any]) -> SandboxContext:
        """
        Prepare context for a DANA function.

        For DANA functions:
        - Creates a clean local scope
        - Sets up interpreter if needed
        - Maps arguments to the local scope

        Args:
            context: The original context
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Prepared context
        """
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
        Restore the context after DANA function execution.

        Args:
            context: The current context
            original_context: The original context before execution
        """
        # Restore the original local scope
        if hasattr(context, "_original_locals"):
            context.set_scope("local", context._original_locals)
            delattr(context, "_original_locals")

    def execute(self, context: SandboxContext, *args: Any, **kwargs: Any) -> Any:
        """Execute the function body with the provided context and arguments.

        Args:
            context: The context to use for execution
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        try:
            # If the context doesn't have an interpreter, assign the one from self.context
            if not hasattr(context, "_interpreter") or context._interpreter is None:
                if self.context is not None and hasattr(self.context, "_interpreter") and self.context._interpreter is not None:
                    context._interpreter = self.context._interpreter

            # Copy args and kwargs into the local scope by parameter names, but only if they don't exist
            for i, param_name in enumerate(self.parameters):
                if i < len(args):
                    # Only set the parameter if it doesn't already exist in local scope
                    if not context.has(f"local.{param_name}"):
                        context.set_in_scope(param_name, args[i], scope="local")

            # Set any keyword args if they don't already exist
            for kwarg_name, kwarg_value in kwargs.items():
                if kwarg_name in self.parameters and not context.has(f"local.{kwarg_name}"):
                    context.set_in_scope(kwarg_name, kwarg_value, scope="local")

            for statement in self.body:
                result = context.interpreter.execute_statement(statement, context)
                self.debug(f"statement: {statement}, result: {result}")
        except ReturnException as e:
            return e.value
