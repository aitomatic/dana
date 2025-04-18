"""Base resource implementation for DXA.

This module provides the foundational resource class that defines the interface
and common functionality for all DXA resources. Resources are managed entities
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

import uuid
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any, Optional, ClassVar, TypeVar
from opendxa.common.mixins.loggable import Loggable
from opendxa.common.mixins.configurable import Configurable
from opendxa.common.mixins.tool_callable import ToolCallable

T = TypeVar('T', bound='BaseResource')

class QueryStrategy(Enum):
    """Resource querying strategies."""
    ONCE = auto()       # Single query without iteration, default for most resources
    ITERATIVE = auto()  # Iterative querying - default, e.g., for LLMResource

class ResourceError(Exception):
    """Base class for resource errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
        # Use class logger for error logging
        logger = Loggable.get_class_logger()
        logger.error(
            "Resource error occurred",
            extra={"error": message, "exception": original_error}
        )

class ResourceUnavailableError(ResourceError):
    """Error raised when resource is unavailable."""
    pass

class ResourceAccessError(ResourceError):
    """Error raised when resource access fails."""
    pass

@dataclass
class ResourceResponse:
    """Resource response."""
    success: bool
    content: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BaseResource(Configurable, Loggable, ToolCallable):
    """Abstract base resource."""

    # Class-level default configuration
    default_config: ClassVar[Dict[str, Any]] = {
        "name": "",
        "description": None,
        "query_strategy": QueryStrategy.ONCE,
        "query_max_iterations": 3
    }

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize resource.

        Args:
            name: Resource name
            description: Optional resource description
            config: Optional additional configuration
        """
        # Initialize Loggable first to ensure logger is available
        Loggable.__init__(self)
        ToolCallable.__init__(self)
        # Initialize Configurable with the provided config
        config_dict = config or {}
        if name:
            config_dict["name"] = name
        if description:
            config_dict["description"] = description
        Configurable.__init__(self, **config_dict)

        self.name = self.config["name"]
        self.description = self.config["description"] or "No description provided"
        self._is_available = False  # will only be True after initialization
        self._resource_id = str(uuid.uuid4())[:8]

        self._query_strategy = self.config.get("query_strategy", QueryStrategy.ONCE)
        self._query_max_iterations = self.config.get("query_max_iterations", 3)

    def _validate_config(self) -> None:
        """Validate the configuration.

        This method extends the base Configurable validation with resource-specific checks.
        """
        # Call base class validation first
        super()._validate_config()

        # Validate resource-specific fields
        if "name" not in self.config:
            raise ValueError("Resource configuration must have a 'name' field")

        if "description" not in self.config:
            raise ValueError("Resource configuration must have a 'description' field")

        # Validate resource name
        if not self.config["name"]:
            raise ValueError("Resource name cannot be empty")

        # Validate query strategy if present
        if "query_strategy" in self.config:
            if not isinstance(self.config["query_strategy"], QueryStrategy):
                raise ValueError("query_strategy must be a QueryStrategy enum")

        # Validate max iterations if present
        if "query_max_iterations" in self.config:
            if not isinstance(self.config["query_max_iterations"], int):
                raise ValueError("query_max_iterations must be an integer")

    @property
    def is_available(self) -> bool:
        """Check if resource is currently available."""
        return self._is_available

    @property
    def resource_id(self) -> str:
        """Get the resource ID."""
        if self._resource_id is None:
            self._resource_id = str(uuid.uuid4())[:8]
        return self._resource_id

    async def initialize(self) -> None:
        """Initialize resource."""
        self._is_available = True
        self.info(f"Initializing resource [{self.name}]")
        # Resource-specific initialization logic
        self.debug(f"Resource [{self.name}] initialized successfully")

    async def cleanup(self) -> None:
        """Cleanup resource."""
        self._is_available = False
        self.info(f"Cleaning up resource [{self.name}]")
        # Resource-specific cleanup logic
        self.debug(f"Resource [{self.name}] cleanup completed")

    # pylint: disable=unused-argument
    @ToolCallable.tool
    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Query resource."""
        if not self._is_available:
            return ResourceResponse(success=False, error=f"Resource {self.name} not initialized")
        self.debug(f"Resource [{self.name}] received query: {self._sanitize_log_data(request)}")
        return ResourceResponse(success=True)

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if resource can handle request."""
        self.debug(f"Checking if [{self.name}] can handle request")
        return False

    def get_query_strategy(self) -> QueryStrategy:
        """Get the query strategy for the resource."""
        return self._query_strategy

    def get_query_max_iterations(self) -> int:
        """Get the maximum number of iterations for the resource. Default is 3."""
        return self._query_max_iterations

    def _sanitize_log_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data before logging"""
        sanitized = data.copy()
        # Example sanitization - extend based on your needs
        for key in ["password", "api_key", "token"]:
            if key in sanitized:
                sanitized[key] = "***REDACTED***"
        return sanitized

    async def __aenter__(self) -> 'BaseResource':
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.cleanup()
