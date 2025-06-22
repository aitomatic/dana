"""Tool format converters for different API formats.

This module provides converters for different tool formats (MCP, OpenAI, etc.)
that can be used with the ToolCallable mixin.
"""

from typing import Any, Protocol

from mcp import Tool as McpTool


def _strip_fields(schema: dict[str, Any], fields_to_strip: set[str]) -> dict[str, Any]:
    """Recursively remove specified fields from a schema dictionary."""
    if not isinstance(schema, dict):
        return schema

    # Create a new dict without the specified fields
    result = {k: v for k, v in schema.items() if k not in fields_to_strip}

    # Recursively process nested dictionaries
    for key, value in result.items():
        if isinstance(value, dict):
            result[key] = _strip_fields(value, fields_to_strip)
        elif isinstance(value, list):
            result[key] = [_strip_fields(item, fields_to_strip) if isinstance(item, dict) else item for item in value]

    return result


class ToolFormat(Protocol):
    """Protocol for tool format converters."""

    @classmethod
    def parse_tool_name(cls, name: str) -> tuple[str, str, str]:
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
            raise ValueError(f"Function name must be in format 'resource_name__resource_id__tool_name', got: {name}")
        return (parts[0], parts[1], parts[2])

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

    def convert(self, name: str, description: str, schema: dict[str, Any]) -> Any:
        """Convert tool information to the desired format.

        Args:
            name: Name of the tool/function
            description: Description of the tool/function
            schema: JSON Schema for the tool's parameters

        Returns:
            Tool in the desired format
        """
        ...


class McpToolFormat(ToolFormat):
    """Converter for MCP tool format."""

    def __init__(self, fields_to_strip: set[str] | None = None):
        """Initialize the MCP format converter.

        Args:
            fields_to_strip: Set of field names to remove from the schema
        """
        self.fields_to_strip = fields_to_strip or {"title", "default", "additionalProperties"}

    def convert(self, name: str, description: str, schema: dict[str, Any]) -> McpTool:
        """Convert to MCP tool format.

        Returns:
            McpTool: Tool in MCP format

            Example (after stripping defaults like title, default, additionalProperties):
            {
                "name": "get_weather",
                "description": "Get the current weather for a given city.",
                "inputSchema": {  # Note: This is the 'parameters' part of the input schema dict
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city to get the weather for."
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit."
                        }
                    },
                    "required": ["city"]
                }
            }
        """
        # Extract the parameters part of the schema provided by _list_tools
        parameters_schema = schema.get("parameters", {})
        # Strip unwanted fields
        stripped_parameters_schema = _strip_fields(parameters_schema, self.fields_to_strip or set())

        return McpTool(
            name=name,
            description=description,
            inputSchema=stripped_parameters_schema,  # Use the stripped parameters schema
        )


class OpenAIToolFormat(ToolFormat):
    """Converter for OpenAI function format."""

    def __init__(self, resource_name: str, resource_id: str, fields_to_strip: set[str] | None = None):
        """Initialize the OpenAI format converter.

        Args:
            resource_name: Name of the resource
            resource_id: ID of the resource
            fields_to_strip: Set of field names to remove from the schema
        """
        self.resource_name = resource_name
        self.resource_id = resource_id
        self.fields_to_strip = fields_to_strip or {"title", "default", "additionalProperties"}

    def convert(self, name: str, description: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Convert to OpenAI function format.

        Args:
            name: Name of the tool/function
            description: Description of the tool/function
            schema: JSON Schema for the tool's parameters

        Returns:
            Dict[str, Any]: Function in OpenAI format

            Example:
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather for a given city.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The city to get the weather for."
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "Temperature unit."
                            }
                        },
                        "required": ["city"]
                    },
                    "strict": True
                }
            }
        """
        parameters_schema = schema.get("parameters", {})
        stripped_parameters_schema = _strip_fields(parameters_schema, self.fields_to_strip or set())
        return {
            "type": "function",
            "function": {
                "name": self.build_tool_name(self.resource_name, self.resource_id, name),
                "description": description,
                "parameters": stripped_parameters_schema,
                "strict": False,  # Make it more lenient and less error-prone
            },
        }

    def from_mcp_tool_format(self, mcp_tool: McpTool) -> dict[str, Any]:
        """Convert an MCP tool to OpenAI function format."""
        return {
            "type": "function",
            "function": {
                "name": self.build_tool_name(self.resource_name, self.resource_id, mcp_tool.name),
                "description": mcp_tool.description,
                "parameters": mcp_tool.inputSchema,
                "strict": False,
            },
        }


class RawToolFormat(OpenAIToolFormat):
    @classmethod
    def build_tool_name(cls, resource_name: str, resource_id: str, tool_name: str) -> str:
        return tool_name
