"""
MCP Resource implementation for Dana integration.
"""

import inspect
from typing import Any

from mcp.types import Tool as McpTool

from dana.common.mixins.tool_formats import OpenAIToolFormat
from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.common.types import BaseRequest, BaseResponse
from dana.common.utils.misc import Misc
from dana.integrations.mcp.client.mcp_client import MCPClient


class MCPResource(BaseSysResource):
    """MCP Resource for Dana integration.

    Example:
        mcp_resource = MCPResource("filesystem", "http://localhost:3000/sse")
        response = await mcp_resource.query(BaseRequest(
            arguments={"tool": "read_file", "path": "/tmp/test.txt"}
        ))
    """

    def __init__(self, name: str, description: str | None = None, config: dict[str, Any] | None = None, *client_args, **client_kwargs):
        """Initialize MCP resource.

        Args:
            name: Resource name
            description: Optional resource description
            config: Optional additional configuration
            *client_args: Additional MCP client parameters
            **client_kwargs: Additional MCP client parameters
        """
        # Initialize the cache attribute FIRST to prevent recursion
        self._mcp_tools_cache: list[McpTool] | None = None

        # Now call parent __init__
        super().__init__(name, description, config)

        self.client = MCPClient(*client_args, **client_kwargs)
        # Don't pre-fetch tools immediately - defer until needed

    def mcp_tool_decorator(self, func_name: str) -> Any:
        """Decorator to wrap a function as an MCP tool."""

        def wrapper(**kwargs) -> Any:
            if inspect.iscoroutinefunction(self.call_tool):
                return Misc.safe_asyncio_run(self.call_tool, func_name, kwargs)
            else:
                return self.call_tool(func_name, kwargs)

        return wrapper

    def __getattr__(self, name: str) -> Any:
        # Check if it's a private attribute - don't try to find it as a tool
        if name.startswith("_"):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        try:
            return super().__getattribute__(name)
        except AttributeError:
            # Ensure tools are discovered first - use object.__getattribute__ to avoid recursion
            tools_cache = object.__getattribute__(self, "_mcp_tools_cache")
            if tools_cache is None:
                Misc.safe_asyncio_run(self._discover_tools)
                tools_cache = object.__getattribute__(self, "_mcp_tools_cache")

            if tools_cache:
                for tool in tools_cache:
                    if tool.name == name:
                        return self.mcp_tool_decorator(tool.name)

            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    async def initialize(self) -> None:
        """Initialize the MCP resource."""
        await super().initialize()
        await self._discover_tools()

    async def _discover_tools(self) -> None:
        """Discover and cache tools from MCP server."""
        try:
            async with self.client as _client:
                response = await _client.list_tools()
                self._mcp_tools_cache = response.tools
        except Exception as e:
            self.log_error(f"Failed to discover tools: {e}")
            self._is_available = False
            self._mcp_tools_cache = []

    def _list_tools(self, format_converter: OpenAIToolFormat) -> list[Any]:
        """Return cached tools in OpenAI format."""
        if self._mcp_tools_cache is None:
            Misc.safe_asyncio_run(self._discover_tools)
        if not self._mcp_tools_cache:
            return []
        tools = []
        for tool in self._mcp_tools_cache:
            tools.append(format_converter.from_mcp_tool_format(tool))
        return tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute MCP tool."""
        self.log_debug(f"Calling tool {tool_name} with arguments {arguments}")
        print(f"Calling tool {tool_name} with arguments {arguments}")
        async with self.client as _client:
            response = await _client.call_tool(tool_name, arguments)  # This will raise ToolError if the tool call fails.

        results = response.content

        assert (
            len(results) == 1
        ), f"Tool {tool_name} with arguments {arguments} returned {len(results)} results, expected 1. \nresults: {results}"

        if Misc.get_field(results[0], "type") == "text":
            return Misc.get_field(results[0], "text")
        else:
            return results[0]

    async def query(self, request: BaseRequest) -> BaseResponse:
        """Handle resource queries by calling MCP tools."""
        if not self._is_available:
            return BaseResponse(success=False, error=f"Resource {self.name} not available")

        arguments = request.arguments
        tool_name = arguments.get("tool") or arguments.get("tool_name")

        if not tool_name:
            return BaseResponse(success=False, error="No tool specified")

        tool_args = arguments.get("arguments", {})
        if not tool_args:
            # Use all arguments except tool identifier
            tool_args = {k: v for k, v in arguments.items() if k not in ["tool", "tool_name"]}

        try:
            result = await self.call_tool(tool_name, tool_args)
            return BaseResponse(success=True, content=result)
        except Exception as e:
            return BaseResponse(success=False, error=str(e))

    def can_handle(self, request: BaseRequest) -> bool:
        """Check if this resource can handle the request."""
        if not isinstance(request, BaseRequest) or not request.arguments:
            return False

        arguments = request.arguments
        has_tool = "tool" in arguments or "tool_name" in arguments

        return has_tool and self._is_available


if __name__ == "__main__":
    from dana.common.utils.misc import Misc

    async def main():
        mcp_resource = MCPResource("sensors", url="http://localhost:8880/sensors")
        response = mcp_resource._list_tools(OpenAIToolFormat(mcp_resource.name, mcp_resource.id))
        print(response)
        response = Misc.safe_asyncio_run(mcp_resource.call_tool, "list_all_sensors", {})
        print(response)

    Misc.safe_asyncio_run(main)
    Misc.safe_asyncio_run(main)

    import time

    time.sleep(20)
