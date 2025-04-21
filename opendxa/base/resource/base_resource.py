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

from dataclasses import dataclass
from typing import Dict, Any, Optional, ClassVar, TypeVar
from opendxa.common.mixins.loggable import Loggable
from opendxa.common.mixins.configurable import Configurable
from opendxa.common.mixins.queryable import Queryable, QueryStrategy, QueryResponse
T = TypeVar('T', bound='BaseResource')

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
class ResourceResponse(QueryResponse):
    """Resource response."""

    @classmethod
    def error_response(cls, message: str) -> 'ResourceResponse':
        """Create an error response with a ResourceError.
        
        Args:
            message: Error message
            
        Returns:
            ResourceResponse with error set to a ResourceError
        """
        return cls(success=False, error=ResourceError(message))

class BaseResource(Configurable, Loggable, Queryable):
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

        # Initialize Configurable with the provided config
        config_dict = config or {}
        if name:
            config_dict["name"] = name
        if description:
            config_dict["description"] = description
        Configurable.__init__(self, **config_dict)

        self._is_available = False  # will only be True after initialization

        self.name = self.config["name"]
        self.description = self.config["description"] or "No description provided"

        self._query_strategy = self.config.get("query_strategy", QueryStrategy.ONCE)
        self._query_max_iterations = self.config.get("query_max_iterations", 3)
        Queryable.__init__(self)

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

    async def query(self, params: Optional[Dict[str, Any]] = None) -> ResourceResponse:
        """Query resource.

        Args:
            params: The parameters to query the resource with.
        """
        if not self._is_available:
            return ResourceResponse(success=False, error=f"Resource {self.name} not available")
        self.debug(f"Resource [{self.name}] received query: {self._sanitize_log_data(params)}")
        return ResourceResponse(success=True, content=params, error=None)

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if resource can handle request."""
        self.debug(f"Checking if [{self.name}] can handle {self._sanitize_log_data(request)}")
        return False

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
