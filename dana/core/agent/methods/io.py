from typing import Any

from dana.core.lang.sandbox_context import SandboxContext


class InputMixin:
    def input_sync(
        self,
        request: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: Any = None,
    ) -> str:
        """Synchronous agent input method."""
        # Prompt the user for input from the console
        response = input(request)

        # Return the response
        return response
