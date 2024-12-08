"""Human resource implementation."""

import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

from dxa.core.resource.base_resource import BaseResource, ResourceConfig, ResourceResponse, ResourceError

@dataclass
class HumanConfig(ResourceConfig):
    """Human resource configuration."""
    role: str = "user"

@dataclass 
class HumanResponse(ResourceResponse):
    """Human resource response."""
    response: str
    success: bool = True
    error: Optional[str] = None

class HumanResource(BaseResource):
    """Resource representing human interaction."""
    
    def __init__(self, name: str, role: str = "user"):
        config = HumanConfig(name=name, role=role)
        super().__init__(name=name, config=config)
        self.role = role

    async def initialize(self) -> None:
        """Initialize the human resource."""
        self._is_available = True

    async def cleanup(self) -> None:
        """Clean up the human resource."""
        self._is_available = False

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request can be handled by human."""
        return self._is_available and isinstance(request, dict)

    async def query(self, request: Dict[str, Any]) -> HumanResponse:
        """Query the human resource."""
        if not self.can_handle(request):
            raise ResourceError("Resource unavailable or invalid request format")

        try:
            response = await self._get_human_input(request)
            # pylint: disable=unexpected-keyword-arg
            return HumanResponse(response=response)
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