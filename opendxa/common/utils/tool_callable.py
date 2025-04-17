"""Tool-callable functionality for DXA.

This module provides the ToolCallable mixin class that enables any class to expose
methods as tools to the LLM. It handles the generation of OpenAI-compatible function
specifications and manages tool-callable function registration.

Example:
    class MyClass(ToolCallable):
        @ToolCallable.tool
        async def my_function(self, param1: str) -> Dict[str, Any]:
            pass
"""

from typing import Dict, Any, Set, ClassVar, Optional, List, Callable, TypeVar
from dataclasses import dataclass

# Type variable for the decorated function
F = TypeVar('F', bound=Callable[..., Any])

@dataclass
class ToolCallable():
    """A mixin class that provides tool-callable functionality to classes.
    
    This class can be used as a mixin to add tool-callable functionality to any class.
    It provides a decorator to mark methods as callable by the LLM as tools.
    
    Example:
        class MyClass(ToolCallable):
            @ToolCallable.tool
            async def my_function(self, param1: str) -> Dict[str, Any]:
                pass
    """
    
    # Class variable to store tool-callable function names
    _tool_callable_functions: ClassVar[Set[str]] = set()
    
    # Cache for tool call specifications
    _tool_call_specs: Optional[List[Dict[str, Any]]] = None
    
    @classmethod
    def tool_callable(cls, func: F) -> F:
        """Decorator to mark a function as callable by the LLM as a tool.
        
        Args:
            func: The function to be marked as tool-callable
            
        Returns:
            The decorated function
        """
        func_name = func.__name__
        if not hasattr(cls, '_tool_callable_functions'):
            cls._tool_callable_functions = set()
        cls._tool_callable_functions.add(func_name)
        return func
    
    # Alias for shorter decorator usage
    tool = tool_callable  # type: ignore
    
    def as_tool_call_specs(self, my_id: str) -> List[Dict[str, Any]]:
        """Generate OpenAI-compatible function specifications for all tool-callable functions.
        
        Returns:
            A list of function specifications in OpenAI format
        """
        if self._tool_call_specs is not None:
            return self._tool_call_specs
        
        specs = []
        for func_name in self._tool_callable_functions:
            func = getattr(self, func_name)
            docstring = func.__doc__ or ""
            
            # Parse docstring for description
            description = ""
            for line in docstring.split("\n"):
                if line.strip().startswith("@description:"):
                    description = line.split("@description:")[1].strip()
                    break
            
            # If no @description found, use the first line of docstring
            if not description:
                description = docstring.split("\n")[0].strip()
            
            # Get function annotations
            annotations = func.__annotations__
            parameters = {}
            required = []
            
            # Parse docstring for parameter descriptions
            param_docs = {}
            in_args = False
            for line in docstring.split("\n"):
                line = line.strip()
                if line.startswith("Args:"):
                    in_args = True
                    continue
                if in_args and ":" in line:
                    param_name = line.split(":")[0].strip()
                    param_desc = line.split(":")[1].strip()
                    param_docs[param_name] = param_desc
            
            # Build parameter specifications
            for param_name, param_type in annotations.items():
                if param_name == "return":
                    continue
                    
                param_spec = {
                    "type": self._get_type_string(param_type),
                    "description": param_docs.get(param_name, "")
                }
                
                # Check if parameter has a default value
                if hasattr(func, "__defaults__") and func.__defaults__:
                    default_index = list(func.__code__.co_varnames).index(param_name) - 1
                    if default_index < len(func.__defaults__):
                        param_spec["default"] = func.__defaults__[default_index]
                else:
                    required.append(param_name)
                
                parameters[param_name] = param_spec
            
            # Build the final function specification
            spec = {
                "type": "function",
                "function": {
                    "name": self._get_name_id_function_string(
                        self.__class__.__name__,
                        my_id,
                        func_name
                    ),
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": parameters,
                        "required": required
                    }
                }
            }
            
            specs.append(spec)
        
        self._tool_call_specs = specs
        return specs
    
    def _get_name_id_function_string(self, my_name: str, my_id: str, function_name: str) -> str:
        """Generate a unique identifier for a function.
        
        Args:
            name: The name of the object
            id: The unique identifier of the object
            function_name: The name of the function
            
        Returns:
            A string in the format "name__id__function_name"
        """
        return f"{my_name}__{my_id}__{function_name}"
    
    def _parse_name_id_function_string(self, name_id_function: str) -> tuple[str, str, str]:
        """Parse a function identifier into name, id, and function names.
        
        Args:
            name_id: The function identifier string
            
        Returns:
            A tuple of (name, id, function_name)
            
        Raises:
            ValueError: If the name_id does not have exactly three components
        """
        parts = name_id_function.split("__")
        if len(parts) != 3:
            raise ValueError(f"Invalid function identifier: {name_id_function}. Expected format: name__resource_id__function_name")
        return parts[0], parts[1], parts[2]
    
    def _get_type_string(self, type_obj: Any) -> str:
        """Convert a Python type to a JSON schema type string.
        
        Args:
            type_obj: The Python type object
            
        Returns:
            A string representing the JSON schema type
        """
        if type_obj == str:
            return "string"
        elif type_obj == int:
            return "integer"
        elif type_obj == float:
            return "number"
        elif type_obj == bool:
            return "boolean"
        elif type_obj == list:
            return "array"
        elif type_obj == dict:
            return "object"
        else:
            return "string"  # Default to string for unknown types 