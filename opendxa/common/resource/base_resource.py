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
from typing import Any, Dict, List, Optional, Union

from opendxa.common.utils.logging.loggable import Loggable

@dataclass
class ResourceConfig:
    """Configuration for a resource."""
    name: str
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceConfig':
        """Create a ResourceConfig from a dictionary."""
        return cls(**data)

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
    """Base response for all resources."""
    success: bool = True
    content: Optional[Any] = None  # Added MCP-compatible field
    error: Optional[str] = None

class BaseResource(Loggable):
    """Abstract base resource."""

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        resource_config: Optional[Union[Dict[str, Any], ResourceConfig]] = None
    ):
        """Initialize resource.

        Args:
            name: Resource name
            description: Optional resource description
            config: Either a ResourceConfig object or a dict that can be converted to one
        """
        # Initialize Loggable first to ensure logger is available
        super().__init__()
        
        if isinstance(resource_config, dict):
            self.config = ResourceConfig.from_dict(resource_config)
        elif isinstance(resource_config, ResourceConfig):
            self.config = resource_config
        else:
            self.config = ResourceConfig(name=name, description=description)

        self.name = name or self.config.name
        self.description = self.config.description or "No description provided"
        self._is_available = False  # will only be True after initialization

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

    # pylint: disable=unused-argument
    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Query resource."""
        if not self._is_available:
            raise ResourceUnavailableError(f"Resource {self.name} not initialized")
        self.debug(f"Resource [{self.name}] received query: {self._sanitize_log_data(request)}")
        return ResourceResponse(success=True)

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if resource can handle request."""
        self.debug(f"Checking if [{self.name}] can handle request")
        return False

    async def __aenter__(self) -> 'BaseResource':
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.cleanup()

    def _sanitize_log_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data before logging"""
        sanitized = data.copy()
        # Example sanitization - extend based on your needs
        for key in ["password", "api_key", "token"]:
            if key in sanitized:
                sanitized[key] = "***REDACTED***"
        return sanitized
    
    async def get_tool_strings(
        self, 
        resource_id: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Format a resource into OpenAI function specification.
        
        Args:
            resource: Resource instance to format
            **kwargs: Additional keyword arguments
            
        Returns:
            OpenAI function specification list
        """
        query_params = self.query.__annotations__
        properties = {}
        required = []

        type_map = {
            Dict: "object",
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean"
        }

        for param_name, param_type in query_params.items():
            if param_name == "return":
                continue

            required.append(param_name)

            # Check if parameter is Optional[T] by examining Union type with None
            is_optional = (hasattr(param_type, "__origin__") and 
                           hasattr(param_type, "__args__") and
                           getattr(param_type, "__origin__") is Union and
                           type(None) in getattr(param_type, "__args__", ()))

            # Extract the actual type from Optional if present
            actual_type = getattr(param_type, "__args__", (param_type,))[0] if is_optional else param_type

            # Get schema type, defaulting to string if type not in map
            param_schema_type = type_map.get(actual_type, "string")

            # Make optional params accept null for flexibility
            if is_optional:
                param_schema_type = [param_schema_type, "null"]

            properties[param_name] = {
                "type": param_schema_type,
                "description": f"{param_name} parameter"
            }

        # Build function name based on whether this is an agent resource
        function_name = f"{resource_id}__query"
        description = self.description or self.query.__doc__

        return [{
            "type": "function",
            "function": {
                "name": function_name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False
                },
                "strict": True
            }
        }]
