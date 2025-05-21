"""Python function."""

import inspect
from typing import Any, Callable, List, Optional, Set

from opendxa.dana.sandbox.sandbox_context import SandboxContext

from .sandbox_function import SandboxFunction


class PythonFunction(SandboxFunction):
    """Wrapper for Python functions that makes them compatible with BaseFunction interface."""

    def __init__(self, func: Callable, context: Optional[SandboxContext] = None):
        """Initialize a Python function wrapper.

        Args:
            func: The Python function to wrap
            context: Optional sandbox context
        """
        super().__init__(context)
        self.func = func

        # Extract parameters from function signature
        self.parameters: List[str] = []  # All parameters
        self.required_parameters: Set[str] = set()  # Required parameters (no default)

        try:
            sig = inspect.signature(func)
            param_names = []
            required_params = set()

            # Get all parameters and identify which are required
            for name, param in sig.parameters.items():
                # Skip context-related params that will be injected
                if name in ("ctx", "context", "the_context", "sandbox_context"):
                    continue
                if name in ("local_ctx", "local_context"):
                    continue

                # Add to parameter list
                param_names.append(name)

                # If parameter has no default and isn't VAR_POSITIONAL or VAR_KEYWORD,
                # it's required
                if param.default is param.empty and param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                    required_params.add(name)

            self.parameters = param_names
            self.required_parameters = required_params

        except (ValueError, TypeError):
            # If we can't get parameters, use empty collections
            self.parameters = []
            self.required_parameters = set()

    def __do_call__(self, the_context: SandboxContext, *the_args: Any, **the_kwargs: Any) -> Any:
        """Execute the function body with the provided context and local context.

        Args:
            the_context: The context to use for execution, intelligently injected into the arguments
            *the_args: Positional arguments
            **the_kwargs: Keyword arguments

        Returns:
            The result of calling the Python function
        """
        # Call the wrapped function with the context, local context, and the arguments
        # We need to pass {} as local_context because we're directly calling the func
        return self.func(*the_args, **the_kwargs)
