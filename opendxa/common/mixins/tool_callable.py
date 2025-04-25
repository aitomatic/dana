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

import inspect
from typing import Dict, Any, Set, Optional, List, Callable, TypeVar
from pydantic import create_model
from mcp import Tool as McpTool
from opendxa.common.mixins.registerable import Registerable
from opendxa.common.mixins.loggable import Loggable
from opendxa.common.mixins.tool_formats import ToolFormat, McpToolFormat, OpenAIToolFormat

# Type variable for the decorated function
F = TypeVar('F', bound=Callable[..., Any])
OpenAIFunctionCall = TypeVar('OpenAIFunctionCall', bound=Dict[str, Any])

def create_model_from_signature(func: Callable) -> Any:
    """Create a Pydantic model from a function's signature.
    
    Args:
        func: The function to create a model for
        
    Returns:
        A Pydantic model class for the function's parameters
    """
    sig = inspect.signature(func)
    fields = {}
    
    for name, param in sig.parameters.items():
        if name == 'self':
            continue
            
        # Get the type annotation
        annotation = param.annotation
        if annotation == inspect.Parameter.empty:
            annotation = Any
            
        # Get the default value
        default = param.default
        if default == inspect.Parameter.empty:
            default = ...
            
        fields[name] = (annotation, default)
    
    return create_model(f"{func.__name__}Params", **fields)

class ToolCallable(Registerable, Loggable):
    """A mixin class that provides tool-callable functionality to classes.
    
    This class can be used as a mixin to add tool-callable functionality to any class.
    It provides a decorator to mark methods as callable by the LLM as tools.
    
    Example:
        class MyClass(ToolCallable):
            @ToolCallable.tool
            async def my_function(self, param1: str) -> Dict[str, Any]:
                pass
    """
    
    # Class-level set of all tool function names
    _all_tool_callable_function_names: Set[str] = set()
    
    def __init__(self):
        """Initialize the ToolCallable mixin.
        
        This constructor initializes the MCP tool list cache,
        and OpenAI function list cache.
        """
        self._tool_callable_function_cache: Set[str] = set()  # computed in __post_init__
        self._params_model_cache: Dict[str, Any] = {}  # cache for parameter models
        self.__mcp_tool_list_cache: Optional[List[McpTool]] = None  # computed lazily in list_mcp_tools
        self.__openai_function_list_cache: Optional[List[OpenAIFunctionCall]] = None  # computed lazily in list_openai_functions
        super().__init__()
        self.__post_init__()
        
    def __post_init__(self):
        """Scan the instance's methods for tool decorators and register them."""
        for name, method in inspect.getmembers(self.__class__, predicate=inspect.isfunction):
            if name.startswith('_'):
                continue  # Skip private methods (those starting with _)
            
            # Quick check if this function name is in our tool set
            if name in self._all_tool_callable_function_names:
                # Verify it has our decorator by checking for the marker attribute
                if hasattr(method, '_is_tool_callable'):
                    self._tool_callable_function_cache.add(name)

    @classmethod
    def tool_callable_decorator(cls, func: F) -> F:
        """Decorator to mark a function as callable by the LLM as a tool."""
        # Add the function name to our class-level set
        cls._all_tool_callable_function_names.add(func.__name__)
        # Mark the function with our decorator
        func._is_tool_callable = True  # pylint: disable=protected-access
        return func
    
    # Alias for shorter decorator usage
    tool = tool_callable_decorator

    def _parse_docstring(self, docstring: Optional[str]) -> str:
        """Parse a docstring to extract the description.
        
        The description is taken from the @description: tag if present, otherwise
        from the first part of the docstring before any parameter descriptions.
        
        Args:
            docstring: The docstring to parse
            
        Returns:
            The extracted description
        """
        if not docstring:
            return ""
            
        # Split into lines and remove leading/trailing whitespace
        lines = [line.strip() for line in docstring.split('\n')]
        
        # First look for @description: tag
        for line in lines:
            if line.startswith('@description:'):
                return line[len('@description:'):].strip()
        
        # If no @description: tag found, use the first part of the docstring
        description_lines = []
        for line in lines:
            if line.startswith('@') or line.startswith('Args:'):
                break
            if line:  # Only add non-empty lines
                description_lines.append(line)
                
        # Join the description lines and clean up
        description = ' '.join(description_lines).strip()
        return description

    def _list_tools(self, format_converter: ToolFormat) -> List[Any]:
        """Common base method for listing tools in any format.
        
        Args:
            format_converter: A converter that transforms tool information into the desired format
            
        Returns:
            List of tools in the requested format
        """
        tools = []
        for func_name in self._tool_callable_function_cache:
            func = getattr(self, func_name)
            
            # Get the Pydantic model for parameters from cache or create it
            params_model = self._params_model_cache.get(func_name)
            if params_model is None:
                params_model = create_model_from_signature(func)
                self._params_model_cache[func_name] = params_model
            
            # Get the schema from the Pydantic model
            schema = params_model.model_json_schema()
            
            # Parse the docstring to get the description
            description = self._parse_docstring(func.__doc__)
            
            # Convert to desired format
            tool = format_converter.convert(
                name=func_name,
                description=description,
                schema=schema
            )
            tools.append(tool)
        
        return tools

    def list_mcp_tools(self) -> List[McpTool]:
        """List all tools available to the agent in MCP format."""
        if self.__mcp_tool_list_cache is not None:
            return self.__mcp_tool_list_cache

        self.__mcp_tool_list_cache = self._list_tools(McpToolFormat())
        return self.__mcp_tool_list_cache

    def list_openai_functions(self) -> List[Dict[str, Any]]:
        """List all tools available to the agent in OpenAI format."""
        if self.__openai_function_list_cache is not None:
            return self.__openai_function_list_cache

        self.__openai_function_list_cache = self._list_tools(
            OpenAIToolFormat(self.name, self.id)
        )
        return self.__openai_function_list_cache
    
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
