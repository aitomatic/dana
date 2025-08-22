"""Base I/O resource implementation for Dana.

This module provides the abstract base class for all I/O resources in Dana.
It defines the core interface that all I/O classes must implement to handle
input/output operations while extending BaseResource functionality.
"""

from abc import abstractmethod
from typing import Any

from dana.common.mixins import ToolCallable
from dana.common.sys_resource import BaseSysResource
from dana.common.types import BaseRequest, BaseResponse


class BaseIO(BaseSysResource):
    """Base class for I/O resources.

    This abstract class defines the interface for handling input/output operations
    in Dana while providing resource capabilities.
    """

    def __init__(self, name: str, description: str | None = None):
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
    async def query(self, request: BaseRequest) -> BaseResponse:
        """Handle resource queries by mapping to send/receive.

        Args:
            request: Query request with either send or receive in arguments

        Returns:
            Dict with query results

        Raises:
            ValueError: If neither send nor receive specified
        """
        if "send" in request.arguments:
            await self.send(request.arguments["send"])
            return BaseResponse(success=True)
        if "receive" in request.arguments:
            response = await self.receive()
            return BaseResponse(success=True, content={"response": response})

        return BaseResponse(success=False, error="Invalid query - must specify send or receive")

    def can_handle(self, request: BaseRequest) -> bool:
        """Check if request contains valid IO operations."""
        return "send" in request.arguments or "receive" in request.arguments
