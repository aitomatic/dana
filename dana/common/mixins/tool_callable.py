"""Tool-callable functionality for Dana.

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

            Args:
                param1: A multi-line description of param1
                    that continues on multiple lines
                    and can include more details.
            '''
            pass
"""

import inspect
from collections.abc import Callable
from typing import Any, TypeVar

try:
    from mcp import Tool as McpTool
except ImportError:
    # MCP is optional - create a placeholder class
    class McpTool:
        """Placeholder for MCP Tool when mcp module is not available."""

        pass


from pydantic import BaseModel, ValidationError, create_model

from dana.common.mixins.loggable import Loggable
from dana.common.mixins.registerable import Registerable
from dana.common.mixins.tool_formats import McpToolFormat, OpenAIToolFormat, RawToolFormat, ToolFormat

# Type variable for the decorated function
F = TypeVar("F", bound=Callable[..., Any])


# OpenAIFunctionCall = TypeVar("OpenAIFunctionCall", bound=Dict[str, Any])
class OpenAIFunctionCall(dict[str, Any]):
    """A class that represents an OpenAI function call."""

    pass


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
    _all_tool_callable_function_names: set[str] = set()

    def __init__(self):
        """Initialize the ToolCallable mixin.

        This constructor initializes the MCP tool list cache,
        and OpenAI function list cache.
        """
        self._tool_callable_function_cache: set[str] = set()  # computed in __post_init__
        self._func_model_cache: dict[str, type[BaseModel]] = {}  # cache for function models
        self.__mcp_tool_list_cache: list[McpTool] | None = None  # computed lazily in list_mcp_tools
        self.__openai_function_list_cache: list[OpenAIFunctionCall] | None = None  # computed lazily in list_openai_functions
        self.__raw_function_list_cache: list[OpenAIFunctionCall] | None = None  # computed lazily in list_openai_functions
        super().__init__()
        self.__post_init__()

    def __post_init__(self):
        """Scan the instance's methods for tool decorators and register them."""
        for name, method in inspect.getmembers(self.__class__, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue  # Skip private methods (those starting with _)

            # Quick check if this function name is in our tool set
            if name in self._all_tool_callable_function_names:
                # Verify it has our decorator by checking for the marker attribute
                if hasattr(method, "_is_tool_callable"):
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

    @classmethod
    def _create_func_model(cls, func: Callable) -> type[BaseModel]:
        """Create a Pydantic model from a function's signature.

        The fields dictionary maps parameter names to tuples of (type, default):
        {
            "param_name": (
                type_annotation,  # The parameter's type annotation, or Any if not specified
                default_value     # The parameter's default value, or ... if required
            ),
            ...
        }

        For example, given a function:
            def search(query: str, limit: int = 10) -> Dict[str, Any]:
                pass

        The fields dictionary would be:
        {
            "query": (str, ...),     # Required parameter with type str
            "limit": (int, 10)       # Optional parameter with type int and default 10
        }

        Args:
            func: The function to create a model for

        Returns:
            A Pydantic model class for the function's parameters
        """
        sig = inspect.signature(func)
        fields = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            field_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
            field_default = param.default if param.default != inspect.Parameter.empty else ...
            fields[name] = (field_type, field_default)

        model = create_model(f"{func.__name__}Params", **fields)

        # Store metadata on the model
        setattr(model, "__return_type__", sig.return_annotation if sig.return_annotation != inspect.Signature.empty else Any)
        setattr(model, "__input_schema__", model.model_json_schema())

        return model

    def _resolve_schema_refs(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Recursively resolve $ref references in a JSON schema dictionary."""
        # Find definitions, preferring '$defs' over 'definitions'
        defs_key = "$defs" if "$defs" in schema else "definitions"
        definitions = schema.get(defs_key, {})

        if not definitions:
            return schema  # No definitions to resolve

        resolved_definitions = {}  # Cache for already resolved definitions

        def _resolve(item: Any) -> Any:
            if isinstance(item, dict):
                if "$ref" in item:
                    ref_path = item["$ref"]
                    # Simple check for local refs like '#/$defs/ModelName'
                    if ref_path.startswith(f"#/{defs_key}/"):
                        def_name = ref_path.split("/")[-1]
                        if def_name in resolved_definitions:
                            return resolved_definitions[def_name]  # Return from cache
                        if def_name in definitions:
                            # Resolve the definition itself first
                            resolved_def = _resolve(definitions[def_name])
                            resolved_definitions[def_name] = resolved_def  # Cache it
                            return resolved_def
                        else:
                            # Ref not found, return original ref dict or handle error
                            self.warning(f"Schema reference {ref_path} not found in definitions.")
                            return item
                    else:
                        # Non-local or unknown ref format, ignore
                        return item
                else:
                    # Recursively resolve values in the dict
                    return {k: _resolve(v) for k, v in item.items()}
            elif isinstance(item, list):
                # Recursively resolve items in the list
                return [_resolve(elem) for elem in item]
            else:
                # Primitive type, return as is
                return item

        # Resolve the main schema structure
        resolved_schema = _resolve(schema)
        # Remove the definitions section after resolving
        resolved_schema.pop(defs_key, None)
        return resolved_schema

    def _list_tools(self, format_converter: ToolFormat) -> list[Any]:
        """Common base method for listing tools in any format.

        Args:
            format_converter: A converter that transforms tool information into the desired format

        Returns:
            List of tools in the requested format
        """
        formatted_tools = []
        for func_name in self._tool_callable_function_cache:
            func = getattr(self, func_name)

            # Extract description from docstring using @description tag
            docstring = inspect.getdoc(func) or ""
            description_lines = []
            in_description = False
            if docstring:
                lines = docstring.strip().split("\n")
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith("@description:"):
                        description_lines.append(stripped_line[len("@description:") :].strip())
                        in_description = True
                    elif in_description and stripped_line and not stripped_line.startswith("@"):
                        description_lines.append(stripped_line)
                    elif in_description and not stripped_line:
                        # Allow empty lines within the description block
                        description_lines.append(stripped_line)
                    elif in_description:
                        # Stop when another @tag is encountered
                        in_description = False

                # If @description tag not found, use the first line of the docstring
                if not description_lines and lines:
                    description = lines[0].strip()
                else:
                    description = " ".join(description_lines).strip()
            else:
                description = "No description available."

            # Get the Pydantic model for parameters from cache or create it
            func_model = self._func_model_cache.get(func_name)
            if func_model is None:
                func_model = self._create_func_model(func)
                self._func_model_cache[func_name] = func_model

            # Get the raw schema, potentially with $refs
            raw_parameters_schema = func_model.model_json_schema()

            # Resolve $refs to get a flattened schema
            flattened_parameters_schema = self._resolve_schema_refs(raw_parameters_schema)

            # Create a generic function schema that can be converted to any format
            function_schema = {
                "name": func_name,
                "description": description,  # Use parsed description
                "parameters": flattened_parameters_schema,  # Use the flattened schema
            }

            # Convert to desired format
            formatted_tool = format_converter.convert(
                name=func_name,
                description=function_schema["description"],
                schema=function_schema,  # Use parsed description
            )
            formatted_tools.append(formatted_tool)

        return formatted_tools

    def list_tools(self) -> list[Any]:
        """List all tools available to the agent in raw format."""
        if self.__raw_function_list_cache is not None:
            return self.__raw_function_list_cache

        self.__raw_function_list_cache = self._list_tools(RawToolFormat(self.name, self.id))
        return self.__raw_function_list_cache

    def list_mcp_tools(self) -> list[McpTool]:
        """List all tools available to the agent in MCP format."""
        if self.__mcp_tool_list_cache is not None:
            return self.__mcp_tool_list_cache

        self.__mcp_tool_list_cache = self._list_tools(McpToolFormat())
        return self.__mcp_tool_list_cache

    def list_openai_functions(self) -> list[OpenAIFunctionCall]:
        """List all tools available to the agent in OpenAI format."""
        if self.__openai_function_list_cache is not None:
            return self.__openai_function_list_cache

        self.__openai_function_list_cache = self._list_tools(OpenAIToolFormat(self.name, self.id))
        return self.__openai_function_list_cache

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool with the given name and arguments, validating arguments first."""
        if not hasattr(self, tool_name):
            raise ValueError(f"Tool {tool_name} not found in {self.__class__.__name__}")
        func = getattr(self, tool_name)

        # Get the Pydantic model for validation
        func_model = self._func_model_cache.get(tool_name)
        if func_model is None:
            # Should ideally be cached by list_tools, but generate if needed
            self.warning(f"Function model for {tool_name} not found in cache, generating.")
            func_model = self._create_func_model(func)
            self._func_model_cache[tool_name] = func_model

        try:
            # Validate the incoming arguments against the model
            validated_args_model = func_model(**arguments)
            # Dump the validated model back to a dict for the function call
            validated_args_dict = validated_args_model.model_dump()
            # Call the actual tool function
            return self._call_tool_after_validation(tool_name, validated_args_dict)

        except ValidationError as e:
            self.error(f"Tool call validation failed for {tool_name} with args {arguments}: {e}")
            # Re-raise the validation error to indicate invalid arguments were provided
            raise e

    def _call_tool_after_validation(self, tool_name: str, arguments: Any) -> Any:
        """Call a tool with the given name and validated arguments.

        Args:
            tool_name: The name of the tool to call
            arguments: The validated arguments to pass to the tool
        """
        if not hasattr(self, tool_name):
            raise ValueError(f"Tool {tool_name} not found in {self.__class__.__name__}")
        func = getattr(self, tool_name)
        return func(**arguments)
