"""Human resource implementation.

This module defines the HumanResource class, which handles human-in-the-loop interactions
within the DXA framework. It includes configuration and response handling for human resources.
"""

import asyncio
from typing import Dict, Any, Optional, ClassVar
from dataclasses import dataclass

from opendxa.base.resource.base_resource import BaseResource, ResourceResponse, ResourceError
from opendxa.common.mixins import ToolCallable
from opendxa.common.mixins.queryable import QueryParams

@dataclass 
class HumanResponse(ResourceResponse):
    """Human resource response.

    Attributes:
        response (str): The response provided by the human.
        success (bool): Indicates whether the operation was successful.
        error (Optional[str]): An optional error message if the operation failed.
    """
    response: str = ""
    success: bool = True
    error: Optional[str] = None

class HumanResource(BaseResource):
    """Resource representing human interaction.

    This class manages the interaction with human users, allowing for input collection
    and response handling.

    Attributes:
        role (str): The role of the human resource.
        _is_available (bool): Indicates whether the resource is available for interaction.
    """

    # Class-level default configuration
    default_config: ClassVar[Dict[str, Any]] = {
        "role": "user",
        "description": "A human resource that can provide information"
    }
    
    def __init__(
        self,
        name: str,
        role: str = "user",
        description: str = "A human resource that can provide information",
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the HumanResource instance.

        Args:
            name (str): The name identifier for this human resource.
            role (str): The role of the human resource, defaulting to "user".
            description (str): The description of the human resource.
            config: Optional additional configuration
        """
        # Build config dict from parameters
        config_dict = config or {}
        if role != "user":
            config_dict["role"] = role
        if description != "A human resource that can provide information":
            config_dict["description"] = description

        super().__init__(name=name, config=config_dict)
        self._is_available = True

    @property
    def role(self) -> str:
        """Get the role of the human resource."""
        return self.config.get("role", "user")

    async def initialize(self) -> None:
        """Initialize the human resource.

        This method sets the resource as available for interaction.
        """
        self._is_available = True

    async def cleanup(self) -> None:
        """Clean up the human resource.

        This method sets the resource as unavailable for interaction.
        """
        self._is_available = False

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if the request can be handled by the human resource.

        Args:
            request (Dict[str, Any]): The request to check.

        Returns:
            bool: True if the request can be handled, False otherwise.
        """
        return self._is_available and isinstance(request, dict)

    @ToolCallable.tool
    async def query(self, params: QueryParams = None) -> ResourceResponse:
        """Query the human resource for input.

        Args:
            request (Dict[str, Any]): The request containing query parameters.

        Returns:
            ResourceResponse: The response from the human resource.
        """
        if not self.can_handle(params):
            return ResourceResponse.error_response("Resource unavailable or invalid request format")

        try:
            response = await self._get_human_input(params)
            return ResourceResponse(success=True, content={"response": response})
        except Exception as e:
            return ResourceResponse.error_response(f"Failed to get human input: {e}")

    async def _get_human_input(self, params: QueryParams = None) -> str:
        """Get input from the human user.

        Args:
            params (QueryParams): The query parameters.

        Returns:
            str: The response provided by the human.

        Raises:
            ResourceError: If input cannot be obtained.
        """
        try:
            prompt = params.get("prompt", "Please provide input")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, input, f"{prompt}\n> ")
            return response
        except Exception as e:
            raise ResourceError("Failed to get human input") from e