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
from typing import Dict, Any, Optional, List, Tuple, ClassVar, Callable
from ...common.utils.logging.loggable import Loggable
from ...common.utils.configurable import Configurable

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

class BaseResource(Configurable, Loggable):
    """Abstract base resource."""

    # Class-level default configuration
    default_config: ClassVar[Dict[str, Any]] = {
        "name": "",
        "description": None,
        "query_strategy": QueryStrategy.ONCE,
        "query_max_iterations": 3
    }

    # Set to store function names marked for inclusion
    _tool_call_function_names: ClassVar[set[str]] = set()

    @staticmethod
    def tool_callable(func: Callable) -> Callable:
        """Decorator to mark a function as callable by the LLM as a tool.
        
        Usage:
            @BaseResource.tool_callable
            async def my_function(self, param1: str) -> Dict[str, Any]:
                pass
        """
        cls_name = func.__qualname__.split('.')[0]
        cls_obj = globals().get(cls_name)

        # pylint: disable=protected-access
        if isinstance(cls_obj, type) and issubclass(cls_obj, BaseResource):
            if not hasattr(cls_obj, "_tool_callable_functions"):
                cls_obj._tool_call_function_names = set()
            cls_obj._tool_call_function_names.add(func.__name__)

        return func

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

        self.name = self.config["name"]
        self.description = self.config["description"] or "No description provided"
        self._is_available = False  # will only be True after initialization
        self._resource_id = str(uuid.uuid4())[:8]

        self._query_strategy = self.config.get("query_strategy", QueryStrategy.ONCE)
        self._query_max_iterations = self.config.get("query_max_iterations", 3)

        self._tool_call_specs: Optional[List[Dict[str, Any]]] = None

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
    @tool_callable
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
    
    def _as_tool_call_specs(self) -> List[Dict[str, Any]]:
        """Format a resource into OpenAI function specifications.
        
        This method generates function specifications for all methods that should
        be exposed to the LLM. By default, only the query method is included.
        
        Returns:
            List of OpenAI function specifications
        """
        if self._tool_call_specs is None:
            self._tool_call_specs = []
            for function_name in self._tool_call_function_names:
                self._tool_call_specs.append(self._generate_tool_call_spec(function_name))
        return self._tool_call_specs

    def _generate_tool_call_spec(self, function_name: str) -> Dict[str, Any]:
        """Generate tool-calling specification for a given method.
        
        This method creates an OpenAI-compatible tool-calling specification by:
        1. Using type hints to determine parameter types and requirements
        2. Using only the @description field from docstring for function description
        3. Building the final schema structure
        4. Using @schema annotations in docstrings to override parameter schemas

        Limitation: we do not support Optional[T] or Union[T, None] in the method signature.
        
        Args:
            function_name: Name of the method to generate spec for
            
        Returns:
            OpenAI function specification
        """
        # Get the method object and its type annotations
        function = getattr(self, function_name)
        params = function.__annotations__
        
        # Extract only the @description field from docstring
        docstring = function.__doc__ or ""
        description_lines = []
        in_description = False
        
        # Parse docstring for description and parameter schemas
        param_schemas = {}
        current_param = None
        in_args = False
        current_indent = 0
        collecting_schema = False
        schema_lines = []
        
        for line in docstring.split('\n'):
            line = line.rstrip()  # Keep leading whitespace
            stripped_line = line.strip()
            
            # Handle @description field
            if stripped_line.startswith('@description:'):
                in_description = True
                description_lines.append(stripped_line.replace('@description:', '').strip())
            elif in_description:
                if not stripped_line or stripped_line.startswith('Args:') or stripped_line.startswith('Raises:'):
                    in_description = False
                else:
                    description_lines.append(stripped_line.strip())
            
            # Handle Args section
            if stripped_line.startswith('Args:'):
                in_args = True
                current_indent = len(line) - len(line.lstrip())
            elif in_args and stripped_line and len(line) - len(line.lstrip()) <= current_indent:
                in_args = False
                if collecting_schema:
                    # Process collected schema
                    try:
                        import json
                        schema = json.loads(''.join(schema_lines))
                        param_schemas[current_param] = schema
                    except json.JSONDecodeError as e:
                        self.warning(f"Invalid JSON schema for parameter {current_param}: {e}")
                    collecting_schema = False
                    schema_lines = []
            elif in_args and stripped_line:
                # Parse parameter line
                if ':' in stripped_line and not stripped_line.startswith('@schema:'):
                    if collecting_schema:
                        # Process collected schema
                        try:
                            import json
                            schema = json.loads(''.join(schema_lines))
                            param_schemas[current_param] = schema
                        except json.JSONDecodeError as e:
                            self.warning(f"Invalid JSON schema for parameter {current_param}: {e}")
                        collecting_schema = False
                        schema_lines = []
                    
                    param_name = stripped_line.split(':')[0].strip()
                    current_param = param_name
                elif current_param and stripped_line.startswith('@schema:'):
                    collecting_schema = True
                    schema_lines = [stripped_line.replace('@schema:', '').strip()]
                elif collecting_schema:
                    schema_lines.append(stripped_line)
        
        # Process any remaining schema
        if collecting_schema:
            try:
                import json
                schema = json.loads(''.join(schema_lines))
                param_schemas[current_param] = schema
            except json.JSONDecodeError as e:
                self.warning(f"Invalid JSON schema for parameter {current_param}: {e}")
        
        # Join all description lines into a single string with a single space between words
        description = ' '.join(' '.join(description_lines).split()) if description_lines else None
        
        # Initialize schema components
        parameters = {}  # Will hold parameter definitions
        required = []    # Will track required parameters
        
        # Map Python types to JSON Schema types
        type_map = {
            Dict: "object",
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            List: "array",
            Any: "object"  # Handle Any type as object
        }

        # Process each parameter's type annotation
        for param_name, param_type in params.items():
            # Skip return type annotation
            if param_name == "return":
                continue

            # Extract the actual type from Optional[T] or Union[T, None]
            actual_type = getattr(param_type, "__args__", (param_type,))[0]
            
            # Start with an empty schema object that we'll build up
            param_schema = {}
            
            # Check if this is a complex type (Dict, List, etc.) or a simple type
            if hasattr(actual_type, "__origin__"):
                if actual_type.__origin__ in [Dict, dict] or type_map.get(actual_type, "string") == "object":
                    # For object types, we need to specify that no additional properties are allowed
                    # This ensures strict validation of the object structure
                    param_schema.update({
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                        "required": []
                    })
                else:
                    # For List types, use "array", otherwise fall back to the type map
                    param_schema["type"] = "array" if actual_type.__origin__ is List else type_map.get(actual_type, "string")
            else:
                # For simple types, just use the type map
                param_schema["type"] = type_map.get(actual_type, "string")

            # If this parameter has a custom schema from @schema annotation, use it
            if param_name in param_schemas:
                param_schema = param_schemas[param_name]

            # Add the completed schema to the parameters
            parameters[param_name] = param_schema

            required.append(param_name)

        # Build the final function specification
        tool_call_spec = {
            "type": "function",
            "function": {
                # Create unique function name combining resource name, ID, and function name
                "name": self._get_name_id_function_string(self.name, self.resource_id, function_name),
                # Use only the @description field from docstring, or fall back to resource description
                "description": description or self.description or "No description provided",
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required,
                    # Prevent LLM from sending unexpected parameters
                    "additionalProperties": False
                },
                # Enforce strict parameter validation
                "strict": True
            }
        }

        self.warning(f"Tool-call spec: {tool_call_spec}")
        return tool_call_spec

    def _get_name_id_function_string(self, name: str, the_id: str, function_name: str) -> str:
        """Get the name-id-function string."""
        result = f"{name}__{the_id}__{function_name}"
        # self.info(f"Name-id-function string: {result}")
        return result

    def _parse_name_id_function_string(self, name_id_function_string: str) -> Tuple[str, str, str]:
        """Parse the name-id-function string."""
        return name_id_function_string.split("__")
    