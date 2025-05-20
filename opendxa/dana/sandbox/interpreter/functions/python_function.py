"""Python function."""

from typing import Any, Callable, Optional

from opendxa.dana.sandbox.sandbox_context import SandboxContext

from .base_function import BaseFunction


class PythonFunction(BaseFunction):
    def __init__(self, func: Callable, context: Optional[SandboxContext] = None):
        super().__init__(context)
        self.func = func

    def __do_call__(self, the_context: SandboxContext, *the_args: Any, **the_kwargs: Any) -> Any:
        """Execute the function body with the provided context and local context.

        Args:
            the_context: The context to use for execution, not used because the function is a Python function
            *the_args: Positional arguments
            **the_kwargs: Keyword arguments
        """
        return self.func(*the_args, **the_kwargs)
