"""
DANA function implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, Dict, List, Optional

from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class DanaFunction:
    """A DANA function that can be called with arguments."""

    def __init__(self, body: List[Any], parameters: List[str], context: SandboxContext):
        """Initialize a DANA function.

        Args:
            body: The function body statements
            parameters: The parameter names
            context: The sandbox context
        """
        self.body = body
        self.parameters = parameters
        self.context = context

    def __call__(
        self,
        context: Optional[SandboxContext] = None,
        local_context: Optional[Dict[str, Any]] = None,
        *the_args: Any,
        **the_kwargs: Any,
    ) -> Any:
        """Call the function with arguments.

        Args:
            context: Optional context to use for execution
            local_context: Optional local context to use for execution
            *the_args: Positional arguments
            **the_kwargs: Keyword arguments

        Returns:
            The function result

        Raises:
            SandboxError: If argument binding fails
        """
        # Use provided context or default to self.context
        exec_context = context or self.context

        # Create a new local scope for the function
        local_scope: Dict[str, Any] = {}

        # Bind positional arguments
        if len(the_args) > len(self.parameters):
            raise SandboxError(f"Too many arguments: expected {len(self.parameters)}, got {len(the_args)}")
        for param, arg in zip(self.parameters, the_args):
            local_scope[param] = arg

        # Bind keyword arguments
        for name, value in the_kwargs.items():
            if name not in self.parameters:
                raise SandboxError(f"Unknown parameter: {name}")
            if name in local_scope:
                raise SandboxError(f"Parameter already bound: {name}")
            local_scope[name] = value

        # Check that all parameters are bound
        unbound = set(self.parameters) - set(local_scope.keys())
        if unbound:
            raise SandboxError(f"Missing arguments for parameters: {', '.join(unbound)}")

        for k, v in local_scope.copy().items():
            if k.startswith("local.") or k.startswith("local:"):
                local_scope[k[6:]] = v
                del local_scope[k]

        # Set the local context
        saved_local_context = exec_context.get_scope("local")
        local_context = local_context or {}
        local_context = {**local_context, **local_scope}
        exec_context.set_scope("local", local_context)

        # Execute the function body with the local scope
        result = None
        from opendxa.dana.sandbox.interpreter.executor.statement_executor import ReturnStatementExit

        try:
            for statement in self.body:
                result = exec_context.interpreter.execute_statement(statement)
        except ReturnStatementExit as e:
            return e.value

        # Restore the original local context
        exec_context.set_scope("local", saved_local_context)

        return result
