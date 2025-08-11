"""Base resource implementation for Dana.

This module provides the foundational resource class that defines the interface
and common functionality for all Dana resources. Resources are managed entities
that provide specific capabilities to the system.

Classes:
    ResourceError: Base exception class for resource-related errors
    ResourceUnavailableError: Error raised when a resource cannot be accessed
    ResourceAccessError: Error raised when resource access is denied
    BaseResource: Abstract base class for all resources

Example:
    class CustomResource(BaseResource):
        async def initialize(self):
            # Resource-specific initialization
            pass

        async def cleanup(self):
            # Resource-specific cleanup
            pass
"""

from typing import Any, TypeVar

from dana.common.mixins import ToolCallable
from dana.common.mixins.configurable import Configurable
from dana.common.mixins.loggable import Loggable
from dana.common.mixins.queryable import Queryable
from dana.common.types import BaseRequest, BaseResponse

from ..utils.misc import Misc

T = TypeVar("T", bound="BaseSysResource")


class ResourceError(Exception):
    """Base class for resource errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error
        # Use class logger for error logging
        logger = Loggable.get_class_logger()
        logger.error("Resource error occurred", extra={"error": message, "exception": original_error})


class ResourceUnavailableError(ResourceError):
    """Error raised when resource is unavailable."""

    pass


class ResourceAccessError(ResourceError):
    """Error raised when resource access fails."""

    pass


class BaseSysResource(Configurable, Queryable, ToolCallable, Loggable):
    """Abstract base resource."""

    def __init__(self, name: str, description: str | None = None, config: dict[str, Any] | None = None):
        """Initialize base resource.

        Args:
            name: Resource name
            description: Optional resource description
            config: Optional additional configuration
        """
        Configurable.__init__(self)
        Queryable.__init__(self)
        ToolCallable.__init__(self)
        Loggable.__init__(self)

        self.name = name
        self.description = description or "No description provided"
        self.config = config or {}
        self._is_available = False
        # self.initialize()   # prefer lazy initialization

    @property
    def is_available(self) -> bool:
        """Check if resource is available."""
        return self._is_available

    async def initialize(self) -> None:
        """Initialize resource."""
        self._is_available = True
        self.info(f"Resource [{self.name}] initialized")

    async def cleanup(self) -> None:
        """Clean up resource."""
        self._is_available = False
        self.info(f"Resource [{self.name}] cleaned up")

    @ToolCallable.tool
    async def query(self, request: BaseRequest) -> BaseResponse:
        """Query resource.

        Args:
            request: The request to query the resource with.
        """
        if not self._is_available:
            return BaseResponse(success=False, error=f"Resource {self.name} not available")
        self.debug(f"Resource [{self.name}] received query: {self._sanitize_log_data(request.arguments)}")
        return BaseResponse(success=True, content=request.arguments, error=None)

    def can_handle(self, request: BaseRequest) -> bool:
        """Check if resource can handle request."""
        self.debug(f"Checking if [{self.name}] can handle {self._sanitize_log_data(request.arguments)}")
        return False

    def _sanitize_log_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize sensitive data before logging"""
        sanitized = data.copy()
        # Example sanitization - extend based on your needs
        for key in ["password", "api_key", "token"]:
            if key in sanitized:
                sanitized[key] = "***REDACTED***"
        return sanitized

    async def __aenter__(self) -> "BaseSysResource":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.cleanup()

    def __enter__(self) -> "BaseSysResource":
        Misc.safe_asyncio_run(self.__aenter__)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        Misc.safe_asyncio_run(self.__aexit__, exc_type, exc_val, exc_tb)
