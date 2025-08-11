"""
LLM Tool Call Manager for Dana.

This module handles tool/function calling logic for LLM resources.
Extracted from LLMResource for better separation of concerns.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import json
import uuid
from typing import Any, cast

from dana.common.mixins.loggable import Loggable
from dana.common.mixins.registerable import Registerable
from dana.common.mixins.tool_callable import OpenAIFunctionCall, ToolCallable
from dana.common.mixins.tool_formats import ToolFormat
from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.common.types import BaseRequest, BaseResponse
from dana.common.utils.misc import Misc

# To avoid accidentally sending too much data to the LLM,
# we limit the total length of tool-call responses.
MAX_TOOL_CALL_RESPONSE_LENGTH = 40000


class LLMToolCallManager(Loggable):
    """Manages LLM tool/function calling operations."""

    def __init__(self, max_response_length: int | None = MAX_TOOL_CALL_RESPONSE_LENGTH):
        """Initialize tool call manager.

        Args:
            max_response_length: Maximum length for tool call responses
        """
        super().__init__()
        self.max_response_length = max_response_length

    def build_request_params(
        self, request: dict[str, Any], model: str | None = None, available_resources: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Build request parameters for LLM API call including tool definitions.

        Args:
            request: Dictionary containing request parameters
            model: The LLM model name
            available_resources: Optional dictionary of available resources

        Returns:
            Dict[str, Any]: Dictionary of request parameters with tools
        """
        from dana.common.utils.misc import Misc

        # Get original messages
        original_messages = Misc.get_field(request, "messages", [])

        # Let AISuite handle system message transformation completely
        # Just pass messages as-is - AISuite will transform them correctly for each provider
        params = {
            "messages": original_messages,
            "temperature": Misc.get_field(request, "temperature", 0.7),
        }

        if Misc.has_field(request, "max_tokens"):
            params["max_tokens"] = Misc.get_field(request, "max_tokens")

        if model:
            params["model"] = model

        if available_resources:
            params["tools"] = self.get_openai_functions(available_resources)

        return params

    def get_openai_functions(self, resources: dict[str, BaseSysResource]) -> list[OpenAIFunctionCall]:
        """Get OpenAI functions from available resources.

        Args:
            resources: Dictionary of available resources

        Returns:
            List[OpenAIFunctionCall]: List of tool definitions
        """
        functions = []
        for _, resource in resources.items():
            functions.extend(resource.list_openai_functions())
        return functions

    async def call_requested_tools(self, tool_calls: list[OpenAIFunctionCall]) -> list[dict[str, Any]]:
        """Call requested resources and get responses.

        This method handles tool calls from the LLM, executing each requested tool
        and collecting their responses.

        Expected Tool Call Format:
            The format of tool calls is defined by the ToolCallable mixin, which
            converts tool definitions into OpenAI's function calling format.

            Each tool call should be a dictionary with:
            {
                "type": "function",
                "function": {
                    "name": str,  # Format: "{resource_name}__{resource_id}__{tool_name}"
                    "arguments": str  # JSON string of parameter values
                }
            }

            Example:
            {
                "type": "function",
                "function": {
                    "name": "search__123__query",
                    "arguments": '{"query": "find documents", "limit": 5}'
                }
            }

            The method will:
            1. Parse the function name to identify resource and tool
            2. Parse the arguments from JSON string to Python dict
            3. Call the appropriate tool with the arguments
            4. Collect and return all responses

            Each response will be in OpenAI's tool response format:
            {
                "role": "tool",
                "name": str,  # The original function name
                "content": str  # The tool's response or error message
            }

        Args:
            tool_calls: List of tool calls from the LLM

        Returns:
            List[dict[str, Any]]: List of tool responses in OpenAI format
        """

        responses: list[dict[str, Any]] = []
        for tool_call in tool_calls:
            try:
                # Get the function object (can be object or dict)
                function_obj = Misc.get_field(tool_call, "function")
                tool_call_id = Misc.get_field(tool_call, "id")

                # Ensure tool_call_id is never None
                if tool_call_id is None:
                    tool_call_id = "fallback_" + str(uuid.uuid4())[:8]
                    self.warning(f"Tool call missing ID, generated fallback ID: {tool_call_id}")

                if not function_obj:
                    self.error("Invalid tool call structure: missing function object")
                    continue
                function_name = Misc.get_field(function_obj, "name")
                arguments_str = Misc.get_field(function_obj, "arguments")
                if not function_name or not arguments_str:
                    self.error("Invalid tool call structure: missing function name or arguments")
                    continue
                if isinstance(arguments_str, str):
                    arguments = json.loads(arguments_str)
                elif isinstance(arguments_str, dict):
                    arguments = arguments_str
                else:
                    self.error(f"Invalid tool call structure: invalid arguments type {type(arguments_str)} : {arguments_str}")
                    continue

                # Parse the function name to get the resource name, id, and tool name
                resource_name, resource_id, tool_name = ToolFormat.parse_tool_name(function_name)

                # Get the resource
                resource: ToolCallable | None = cast(ToolCallable | None, Registerable.get_from_registry(resource_id))
                if resource is None:
                    self.warning(f"Resource {resource_name} with id {resource_id} not found")
                    continue

                # Call the tool
                response = await resource.call_tool(tool_name, arguments)

                # Convert response to JSON string to ensure JSON-serializability
                if hasattr(response, "to_json") and callable(response.to_json):
                    response = response.to_json()

                # Truncate response if needed
                if self.max_response_length and isinstance(response, str):
                    response = response[
                        : self.max_response_length
                    ]  # NOTE : This may reduce our LLM performance because we are truncating the tool response naively

            except Exception as e:
                response = f"Tool call failed: {str(e)}"
                self.error(response)
                function_name = "unknown"
                # Ensure tool_call_id is never None for tool messages
                if tool_call_id is None:
                    tool_call_id = "error_" + str(uuid.uuid4())[:8]

            responses.append({"role": "tool", "name": function_name, "content": response, "tool_call_id": tool_call_id})

        return responses

    async def call_tools_legacy(self, tool_calls: list[dict[str, Any]], available_resources: list[BaseSysResource]) -> list[BaseResponse]:
        """Call tools based on LLM's tool calls (legacy format).

        NOTE: This method is marked for deprecation. Use call_requested_tools instead.

        Args:
            tool_calls: List of tool calls from LLM
            available_resources: List of available resources

        Returns:
            List[BaseResponse]: List of tool responses
        """
        responses: list[BaseResponse] = []
        for tool_call in tool_calls:
            # Find matching resource
            resource = next((r for r in available_resources if r.name == tool_call["name"]), None)
            if not resource:
                responses.append(BaseResponse(success=False, error=f"Resource {tool_call['name']} not found"))
                continue

            # Call resource
            try:
                response = await resource.query(BaseRequest(arguments=tool_call["arguments"]))
                responses.append(response)
            except Exception as e:
                responses.append(BaseResponse(success=False, error=str(e)))

        return responses

    def format_tool_call_message(self, response_message: dict[str, Any], tool_calls: list[OpenAIFunctionCall]) -> dict[str, Any]:
        """Format a tool call message for the conversation history.

        Args:
            response_message: The LLM response message containing tool calls
            tool_calls: List of tool calls to format

        Returns:
            Dict[str, Any]: Formatted message for conversation history
        """
        from dana.common.utils.misc import Misc

        return {
            "role": Misc.get_field(response_message, "role"),
            "content": Misc.get_field(response_message, "content"),
            "tool_calls": [i.model_dump() if hasattr(i, "model_dump") else i for i in tool_calls],
        }

    def has_tool_calls(self, response_message: dict[str, Any]) -> bool:
        """Check if a response message contains tool calls.

        Args:
            response_message: The LLM response message to check

        Returns:
            bool: True if the message contains valid tool calls
        """
        from dana.common.utils.misc import Misc

        tool_calls: list[OpenAIFunctionCall] = Misc.get_field(response_message, "tool_calls")
        return bool(tool_calls and isinstance(tool_calls, list))

    def register_resources(self, available_resources: dict[str, Any]) -> None:
        """Register all resources in the registry for tool calling.

        Args:
            available_resources: Dictionary of available resources
        """
        for resource in available_resources.values():
            resource.add_to_registry()

    def unregister_resources(self, available_resources: dict[str, Any]) -> None:
        """Unregister all resources from the registry to avoid memory leaks.

        Args:
            available_resources: Dictionary of available resources
        """
        for resource in available_resources.values():
            resource.remove_from_registry()
