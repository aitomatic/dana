"""Human resource implementation."""

import asyncio
from typing import Dict, Any

from dxa.core.resource.base_resource import BaseResource
from dxa.common.errors import ResourceError

class HumanResource(BaseResource):
    """Resource representing human interaction."""
    
    def __init__(self, name: str, role: str = "user"):
        """Initialize human resource.
        
        Args:
            name: Resource identifier
            role: Human's role (e.g., "user", "expert", "supervisor")
        """
        super().__init__(name)
        self.role = role

    async def initialize(self) -> None:
        """Initialize the human resource."""
        self._is_available = True

    async def cleanup(self) -> None:
        """Clean up the human resource."""
        self._is_available = False

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request can be handled by human.
        
        Args:
            request: Query parameters
            
        Returns:
            True if request can be handled, False otherwise
        """
        return self._is_available and isinstance(request, dict)

    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Query the human resource.
        
        Args:
            request: Query parameters
            
        Returns:
            Response from human
            
        Raises:
            ResourceError: If interaction fails
        """
        if not self.can_handle(request):
            raise ResourceError("Resource unavailable or invalid request format")

        try:
            # Implementation of human interaction
            response = await self._get_human_input(request)
            return {"response": response, "success": True}
        except Exception as e:
            raise ResourceError(f"Failed to get human input: {str(e)}") from e

    async def _get_human_input(self, request: Dict[str, Any]) -> str:
        """Get input from human.
        
        Args:
            request: Query parameters
            
        Returns:
            Human's response
            
        Raises:
            ResourceError: If input cannot be obtained
        """
        try:
            prompt = request.get("prompt", "Please provide input")
            print(f"\n[{self.role}] {prompt}")
            # Use asyncio.get_event_loop().run_in_executor() for input
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, input, "> ")
            return response
        except Exception as e:
            raise ResourceError("Failed to get human input") from e