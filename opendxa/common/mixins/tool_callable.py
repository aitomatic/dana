"""Tool-callable functionality for DXA.

This module provides the ToolCallable mixin class that enables any class to expose
methods as tools to the LLM. It handles the generation of OpenAI-compatible function
specifications and manages tool-callable function registration.

MCP Tool Format:
    Each tool is represented as a Tool object with:
    {
        "name": str,                    # Tool name (function name)
        "description": str,             # Tool description (function docstring)
        "inputSchema": {                # JSON Schema for parameters
            "type": "object",
            "properties": {
                "param1": {             # Parameter name
                    "type": str | List[str],  # Parameter type
                    "description": str,       # Parameter description
                    "title": str,             # Optional parameter title
                    "items": {                # For array types
                        "type": str
                    }
                },
                ...
            },
            "required": List[str],      # Required parameter names
            "additionalProperties": False
        }
    }

Example:
    class MyClass(ToolCallable):
        @ToolCallable.tool
        async def my_function(self, param1: str) -> Dict[str, Any]:
            '''A function that does something.
            
            @param1: A multi-line description of param1
                that continues on multiple lines
                and can include more details.
            '''
            pass
"""

from collections.abc import Sequence
from typing import Dict, Any, Set, Optional, List, Callable, TypeVar, get_type_hints, get_origin, get_args, Union, Tuple, Type
from mcp.types import Tool as McpTool
from opendxa.common.mixins.registerable import Registerable

# Type variable for the decorated function
F = TypeVar('F', bound=Callable[..., Any])
OpenAIFunctionCall = TypeVar('OpenAIFunctionCall', bound=Dict[str, Any])

def _type_to_schema(type_hint: Any) -> Dict[str, Any]:
    """Convert Python type hint to JSON Schema.
    
    Args:
        type_hint: Python type hint to convert
        
    Returns:
        Dict[str, Any]: JSON Schema representation of the type
    """
    origin = get_origin(type_hint)
    args = get_args(type_hint)
    
    if origin is Union:
        # Handle Optional[T] which is Union[T, None]
        if len(args) == 2 and type(None) in args:
            non_none_type = next(t for t in args if t is not type(None))
            return _type_to_schema(non_none_type)
        # Handle other unions
        return {"type": [_type_to_schema(t)["type"] for t in args]}
    
    if origin is list or origin is List:
        return {
            "type": "array",
            "items": _type_to_schema(args[0])
        }
    
    if origin is dict or origin is Dict:
        return {
            "type": "object",
            "additionalProperties": _type_to_schema(args[1])
        }
    
    # Handle basic types
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        Any: "any"
    }
    return {"type": type_map.get(type_hint, "string")}

class ToolCallable(Registerable):
    """A mixin class that provides tool-callable functionality to classes.
    
    This class can be used as a mixin to add tool-callable functionality to any class.
    It provides a decorator to mark methods as callable by the LLM as tools.
    
    Example:
        class MyClass(ToolCallable):
            @ToolCallable.tool
            async def my_function(self, param1: str) -> Dict[str, Any]:
                pass
    """
    
    # Class-level cache for tool function names
    _tool_callable_function_caches: Dict[Type['ToolCallable'], Set[str]] = {}
    
    def __init__(self):
        """Initialize the ToolCallable mixin.
        
        This constructor initializes the MCP tool list cache,
        and OpenAI function list cache.
        """
        self.__mcp_tool_list_cache: Optional[List[McpTool]] = None
        self.__openai_function_list_cache: Optional[List[OpenAIFunctionCall]] = None
        super().__init__()
 
    @classmethod
    def tool_callable_decorator(cls, func: F) -> F:
        """Decorator to mark a function as callable by the LLM as a tool.
        
        Args:
            func: The function to be marked as tool-callable
            
        Returns:
            The decorated function
        """
        func_name = func.__name__
        if cls not in cls._tool_callable_function_caches:
            cls._tool_callable_function_caches[cls] = set()
        cls._tool_callable_function_caches[cls].add(func_name)
        return func
    
    # Alias for shorter decorator usage
    tool = tool_callable_decorator

    def list_mcp_tools(self) -> List[McpTool]:
        """List all tools available to the agent.
        
        This method converts Python functions marked with @tool into MCP Tool objects.
        It extracts type information from function annotations and docstrings to build
        the tool's input schema.
        
        Tool Function Docstring Format:
            The docstring of a tool function should follow this format:
            
            '''@param1: A description of the first parameter.
                This description can span multiple lines.
                Indentation is preserved in the output.
            
            @description: A description of what the tool does.
                This description can span multiple lines.
                Indentation is preserved in the output.
            
            @param2: A description of the second parameter.
                Multi-line descriptions are supported.
                Each line after the first should be indented.
            
            @param3: A single line description.
            '''
            
            The docstring should:
            1. Include an @description: field for the tool's general description
            2. List each parameter with @param_name: format
            3. Support multi-line descriptions with proper indentation
            4. Preserve newlines in the output schema
            5. Fields can appear in any order
        
        Returns:
            List[Tool]: List of MCP Tool objects representing the available tools
        """
        if self.__mcp_tool_list_cache is not None:
            return self.__mcp_tool_list_cache

        mcp_tools = []
        my_class = self.__class__
        # pylint: disable=protected-access
        for func_name in my_class._tool_callable_function_caches[my_class]: 
            if not hasattr(self, func_name):
                continue
            func = getattr(self, func_name)
            type_hints = get_type_hints(func)
            
            # Get parameter descriptions from docstring
            doc = func.__doc__ or ""
            param_docs = {}
            tool_description = ""
            if doc:
                # Parse docstring for parameter descriptions using @ field format
                current_param = None
                current_desc = []
                
                for line in doc.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith('@'):
                        # Save previous param if exists
                        if current_param:
                            if current_param == "description":
                                tool_description = '\n'.join(current_desc).strip()
                            else:
                                param_docs[current_param] = '\n'.join(current_desc).strip()
                            current_desc = []
                            
                        # Start new param
                        parts = line[1:].split(':', 1)
                        if len(parts) == 2:
                            current_param = parts[0].strip()
                            current_desc = [parts[1].strip()]
                        else:
                            current_param = None
                    elif current_param and line:
                        # Continue description for current param
                        current_desc.append(line)
                        
                # Save last param if exists
                if current_param:
                    if current_param == "description":
                        tool_description = '\n'.join(current_desc).strip()
                    else:
                        param_docs[current_param] = '\n'.join(current_desc).strip()
            
            # Build schema
            properties = {}
            required = []
            for param_name, param_type in type_hints.items():
                if param_name == "return":
                    continue
                    
                # Get type schema
                type_schema = _type_to_schema(param_type)
                
                # Add description if available
                if param_name in param_docs:
                    type_schema["description"] = param_docs[param_name]
                
                # Check if parameter is optional
                if get_origin(param_type) is Union and type(None) in get_args(param_type):
                    type_schema["type"] = [type_schema["type"], "null"]
                else:
                    required.append(param_name)
                
                properties[param_name] = type_schema
            
            mcp_tools.append(McpTool(
                name=func_name,
                description=tool_description or func.__doc__ or "",
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False
                }
            ))
        self.__mcp_tool_list_cache = mcp_tools
        return mcp_tools

    def list_openai_functions(self) -> List[OpenAIFunctionCall]:
        """List all tools available to the agent."""
        if self.__openai_function_list_cache is not None:
            return self.__openai_function_list_cache

        mcp_tools = self.list_mcp_tools()
        self.__openai_function_list_cache = self._convert_mcp_tools_to_openai_functions(mcp_tools)
        return self.__openai_function_list_cache

    def _convert_mcp_tools_to_openai_functions(
        self,
        mcp_tools: List[McpTool]
    ) -> List[OpenAIFunctionCall]:
        """Convert a list of tools to OpenAI's function calling format.
        
        Input Format (tools):
            List of tool dictionaries, each with:
            {
                "name": str,                    # Tool name
                "description": str,             # Tool description
                "inputSchema": {                # JSON Schema for parameters
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": str | List[str],  # Parameter type
                            "description": str,       # Parameter description
                            "title": str,             # Optional parameter title
                            "items": {                # For array types
                                "type": str
                            }
                        },
                        ...
                    },
                    "required": List[str],      # Required parameter names
                    "$schema": str              # Optional JSON Schema reference
                }
            }
        
        Output Format:
            List of OpenAI function specifications:
            [
                {
                    "type": "function",
                    "function": {
                        "name": str,            # Namespaced as "{self.name}__{self.id}__{tool_name}"
                        "description": str,     # Tool description
                        "parameters": {         # Cleaned JSON Schema
                            "type": "object",
                            "properties": {
                                "param1": {
                                    "type": str | List[str],  # Type or union with "null"
                                    "description": str,
                                    "title": str,
                                    "items": {
                                        "type": str
                                    }
                                },
                                ...
                            },
                            "required": List[str],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                },
                ...
            ]
        
        Transformations Applied:
        1. Schema Cleanup:
           - Removes 'self' references from properties
           - Updates required fields list
        2. Property Processing:
           - Makes non-required fields nullable
           - Cleans up property definitions to essential keys
        3. Schema Validation:
           - Removes $schema field
           - Enforces strict parameter validation
        
        Args:
            mcp_tools: List of tools to convert
            
        Returns:
            List of OpenAI function specifications
        """
        openai_functions: List[OpenAIFunctionCall] = []
        
        for mcp_tool in mcp_tools:
            # Get the input schema
            parameters = getattr(mcp_tool, "inputSchema", {}).copy()
            
            # Remove 'self' references if present
            if "properties" in parameters:
                properties = parameters["properties"]
                if properties.pop("self", None) is not None and "required" in parameters:
                    parameters["required"] = [
                        field for field in parameters["required"] 
                        if field != "self"
                    ]
            
            # Process properties if they exist
            if "properties" in parameters and "required" in parameters:
                properties = parameters["properties"]
                required_fields = parameters["required"]
                
                # Make non-required fields nullable
                for field_name, field_props in properties.items():
                    if field_name not in required_fields and "type" in field_props:
                        field_type = field_props["type"]
                        if isinstance(field_type, str):
                            field_props["type"] = [field_type, "null"]
                        # Only add null if field_type doesn't contain "null"
                        elif isinstance(field_type, Sequence) and not any([item == "null" for item in field_type]): 
                            field_props["type"] = [*field_type, "null"]
                
                # Clean up property definitions
                allowed_keys = {"description", "title", "type", "items"}
                properties.update({
                    prop_name: {
                        k: v for k, v in prop.items() 
                        if k in allowed_keys
                    }
                    for prop_name, prop in properties.items()
                })
            
            # Remove JSON Schema specific fields
            parameters.pop("$schema", None)
            
            # Enforce strict parameter validation
            parameters["additionalProperties"] = False
            
            # Create OpenAI function specification
            openai_functions.append({
                "type": "function",
                "function": {
                    "name": self.build_name_id_function_string(self.name, self.id, mcp_tool.name),
                    "description": mcp_tool.description,
                    "parameters": parameters,
                    "strict": True  # TODO: NOTE: strict=True doesn't work with type ['string', 'null']
                }
            })
        
        return openai_functions

    @classmethod
    def parse_name_id_function_string(cls, function_name: str) -> Tuple[str, str, str]:
        """Parse a function name string into its components.
        
        The function name string is expected to be in the format:
        "{resource_name}__{resource_id}__{tool_name}"
        
        Args:
            function_name: The function name string to parse
            
        Returns:
            Tuple of (resource_name, resource_id, tool_name)
            
        Raises:
            ValueError: If the function name is not in the expected format
        """
        parts = function_name.split("__")
        if len(parts) != 3:
            raise ValueError(
                f"Function name must be in format 'resource_name__resource_id__tool_name', got: {function_name}"
            )
        return tuple(parts)

    @classmethod
    def build_name_id_function_string(cls, resource_name: str, resource_id: str, tool_name: str) -> str:
        """Build a function name string from its components.
        
        The function name string will be in the format:
        "{resource_name}__{resource_id}__{tool_name}"
        
        Args:
            resource_name: Name of the resource
            resource_id: ID of the resource
            tool_name: Name of the tool
            
        Returns:
            Function name string in the format "resource_name__resource_id__tool_name"
            
        Raises:
            ValueError: If any component contains "__" which would break the format
        """
        if any("__" in component for component in (resource_name, resource_id, tool_name)):
            raise ValueError("Resource name, ID, and tool name cannot contain '__'")
        return f"{resource_name}__{resource_id}__{tool_name}"
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool with the given name and arguments.
        
        Args:
            tool_name: The name of the tool to call
            arguments: The arguments to pass to the tool
        """
        if not hasattr(self, tool_name):
            raise ValueError(f"Tool {tool_name} not found in {self.__class__.__name__}")
        func = getattr(self, tool_name)
        return func(**arguments)
