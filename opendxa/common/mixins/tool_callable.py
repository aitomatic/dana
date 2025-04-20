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
from abc import abstractmethod
from mcp.types import Tool
from opendxa.common.mixins.registerable import Registerable

# Type variable for the decorated function
F = TypeVar('F', bound=Callable[..., Any])

@dataclass
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
    
    # Class variable to store tool-callable function names
    _tool_callable_functions: ClassVar[Set[str]] = set()
    
    # Cache for tool call specifications
    _tool_call_specs: Optional[List[Dict[str, Any]]] = None
    
    @classmethod
    def tool_callable_function(cls, func: F) -> F:
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
    tool = tool_callable_function 

    @abstractmethod
    async def list_tools(self) -> List[Tool]:
        """List all tools available to the agent."""
        pass

    @abstractmethod
    def as_tool_call_specs(self, my_id: str) -> List[Dict[str, Any]]:
        """Convert the tool-callable functions to a list of tool call specifications."""
        pass
