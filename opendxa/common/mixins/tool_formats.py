"""Tool format converters for different API formats.

This module provides converters for different tool formats (MCP, OpenAI, etc.)
that can be used with the ToolCallable mixin.
"""

from typing import Dict, Any, Tuple
from abc import ABC, abstractmethod
from mcp import Tool as McpTool

class ToolFormat(ABC):
    """Base class for tool format converters."""
    
    @classmethod
    def parse_tool_name(cls, name: str) -> Tuple[str, str, str]:
        """Parse a function name string into its components.
        
        The function name string is expected to be in the format:
        "{resource_name}__{resource_id}__{tool_name}"
        
        Args:
            name: The function name string to parse
            
        Returns:
            Tuple of (resource_name, resource_id, tool_name)
            
        Raises:
            ValueError: If the function name is not in the expected format
        """
        parts = name.split("__")
        if len(parts) != 3:
            raise ValueError(
                f"Function name must be in format 'resource_name__resource_id__tool_name', got: {name}"
            )
        return tuple(parts)

    @classmethod
    def build_tool_name(cls, resource_name: str, resource_id: str, tool_name: str) -> str:
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

    @abstractmethod
    def convert(self, name: str, description: str, schema: Dict[str, Any]) -> Any:
        """Convert tool information to the desired format.
        
        Args:
            name: Name of the tool/function
            description: Description of the tool/function
            schema: JSON Schema for the tool's parameters
            
        Returns:
            Tool in the desired format
        """
        pass

class McpToolFormat(ToolFormat):
    """Converter for MCP tool format."""
    def convert(self, name: str, description: str, schema: Dict[str, Any]) -> McpTool:
        """Convert to MCP tool format.
        
        Returns:
            McpTool: Tool in MCP format
        """
        return McpTool(
            name=name,
            description=description,
            inputSchema=schema
        )

class OpenAIToolFormat(ToolFormat):
    """Converter for OpenAI function format."""
    def __init__(self, resource_name: str, resource_id: str):
        """Initialize the OpenAI format converter.
        
        Args:
            resource_name: Name of the resource
            resource_id: ID of the resource
        """
        self.resource_name = resource_name
        self.resource_id = resource_id

    def convert(self, name: str, description: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to OpenAI function format.
        
        Returns:
            Dict[str, Any]: Function in OpenAI format
        """
        return {
            "type": "function",
            "function": {
                "name": self.build_tool_name(self.resource_name, self.resource_id, name),
                "description": description,
                "parameters": schema,
                "strict": True
            }
        } 