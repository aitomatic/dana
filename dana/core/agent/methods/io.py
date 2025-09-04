from typing import Any

from dana.core.lang.sandbox_context import SandboxContext


class InputMixin:
    def input_sync(
        self,
        request: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: Any = None,
    ) -> Any:
        """Synchronous agent input method."""
        return self._input_impl(request, sandbox_context or SandboxContext(), problem_context)

    def _input_impl(
        self,
        request: str,
        sandbox_context: SandboxContext,
        problem_context: Any = None,
    ) -> str:
        """Implementation of input functionality."""
        # Prompt the user for input from the console
        response = input(request)

        # Return the response
        return response
