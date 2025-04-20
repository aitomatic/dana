"""Base I/O resource implementation for DXA.

This module provides the abstract base class for all I/O resources in DXA.
It defines the core interface that all I/O classes must implement to handle
input/output operations while extending BaseResource functionality.
"""

from abc import abstractmethod
from typing import Any, Dict, Optional
from opendxa.base.resource import BaseResource, ResourceResponse

class BaseIO(BaseResource):
    """Base class for I/O resources.

    This abstract class defines the interface for handling input/output operations
    in DXA while providing resource capabilities.
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """Initialize base I/O with logging and resource capabilities."""
        super().__init__(name, description)

    @abstractmethod
    async def send(self, message: Any) -> None:
        """Send message through IO channel."""
        pass

    @abstractmethod
    async def receive(self) -> Any:
        """Receive message from IO channel."""
        pass

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Handle resource queries by mapping to send/receive.

        Args:
            request: Dict with either "send" or "receive" key

        Returns:
            Dict with query results

        Raises:
            ValueError: If neither send nor receive specified
        """
        if "send" in request:
            await self.send(request["send"])
            return ResourceResponse(success=True)
        if "receive" in request:
            response = await self.receive()
            return ResourceResponse(success=True, content={"response": response})
        
        return ResourceResponse.error_response("Invalid query - must specify send or receive")

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request contains valid IO operations."""
        return "send" in request or "receive" in request
