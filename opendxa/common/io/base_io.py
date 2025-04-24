"""Base I/O resource implementation for DXA.

This module provides the abstract base class for all I/O resources in DXA.
It defines the core interface that all I/O classes must implement to handle
input/output operations while extending BaseResource functionality.
"""

from abc import abstractmethod
from typing import Any, Optional
from opendxa.base.resource import BaseResource, ResourceResponse
from opendxa.common.mixins import ToolCallable
from opendxa.common.mixins.queryable import QueryParams

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

    @ToolCallable.tool
    async def query(self, params: QueryParams = None) -> ResourceResponse:
        """Handle resource queries by mapping to send/receive.

        Args:
            request: Dict with either "send" or "receive" key

        Returns:
            Dict with query results

        Raises:
            ValueError: If neither send nor receive specified
        """
        if "send" in params:
            await self.send(params["send"])
            return ResourceResponse(success=True)
        if "receive" in params:
            response = await self.receive()
            return ResourceResponse(success=True, content={"response": response})
        
        return ResourceResponse.error_response("Invalid query - must specify send or receive")

    def can_handle(self, params: QueryParams) -> bool:
        """Check if request contains valid IO operations."""
        return "send" in params or "receive" in params
