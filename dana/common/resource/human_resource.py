"""Human resource implementation for DXA.

This module provides a resource that allows interaction with human users through
the console. It's useful for getting human input during execution.

Classes:
    HumanResource: Resource for getting human input
    HumanResponse: Response type for human resource
"""

from dana.common.resource.base_resource import BaseResource
from dana.common.types import BaseRequest, BaseResponse


class HumanResource(BaseResource):
    """Resource for getting human input."""

    def __init__(self, name: str, description: str | None = None):
        """Initialize human resource.

        Args:
            name: Resource name
            description: Optional resource description
        """
        super().__init__(name, description)
        self._is_available = True

    def can_handle(self, request: BaseRequest) -> bool:
        """Check if resource can handle request.

        Args:
            request: The request to check

        Returns:
            bool: True if resource can handle request
        """
        return isinstance(request, BaseRequest) and isinstance(request.arguments, dict) and "prompt" in request.arguments

    async def query(self, request: BaseRequest) -> BaseResponse:
        """Get human input.

        Args:
            request: The request containing the prompt

        Returns:
            BaseResponse: The response from the human resource.
        """
        if not self._is_available or not self.can_handle(request):
            return BaseResponse(success=False, error="Resource unavailable or invalid request format")

        try:
            response = await self._get_human_input(request.arguments["prompt"])
            return BaseResponse(success=True, content={"response": response})
        except Exception as e:
            return BaseResponse(success=False, error=f"Failed to get human input: {e}")

    async def _get_human_input(self, prompt: str) -> str:
        """Get input from human user.

        Args:
            prompt: The prompt to show to the user

        Returns:
            str: The user's input
        """
        print(f"\n{prompt}")
        return input("> ")
