"""LLM Result Resource implementation.

This module provides a resource for handling structured LLM results, ensuring consistent
output formatting and easy parsing of LLM interactions.

Classes:
    LLMResultResource: Resource for handling structured LLM results
"""

from typing import Dict, Any, Optional
from .base_resource import BaseResource, ResourceUnavailableError

class LLMResultResource(BaseResource):
    """Resource for processing and storing final LLM results."""

    def __init__(self):
        """Initialize the LLM result resource."""
        super().__init__("llm_result")
        self._exposed_functions = {"final_result"}  # Only expose final_result

    @BaseResource.tool_callable
    async def final_result(
        self,
        content: str,
        status: str,
        metadata: Optional[Dict] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log the final result of an LLM interaction.
        
        @description: Must be called to log the final result of an LLM interaction.
        
        Args:
            content: The content of the result
            status: The status of the result
                    @enum: success, error, partial
            metadata: Optional metadata about the result
            error: Optional error message if status is error
        """
        if not self._is_available:
            raise ResourceUnavailableError(f"Resource {self.name} not initialized")

        if status not in ["success", "error", "partial"]:
            raise ValueError(f"Invalid status: {status}. Must be one of: success, error, partial")

        try:
            self.info("Final Result Parameters:")
            self.info(f"Content: {content}")
            self.info(f"Status: {status}")
            self.info(f"Metadata: {metadata}")
            self.info(f"Error: {error}")

        except Exception as e:
            self.error(f"Failed to log result parameters: {e}", exc_info=True)
            raise

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request can be handled by this resource.
        
        Args:
            request: Request to check
            
        Returns:
            True if request contains LLM result data
        """
        return "content" in request 