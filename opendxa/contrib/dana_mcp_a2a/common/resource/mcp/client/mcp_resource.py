"""
MCP Resource implementation for OpenDXA integration.
"""

from typing import Any, Dict, List, Optional, Union

from mcp.types import Tool as McpTool

from opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.mcp_client import MCPClient
from opendxa.common.resource.base_resource import BaseResource
from opendxa.common.types import BaseRequest, BaseResponse
from opendxa.common.mixins.tool_formats import ToolFormat, OpenAIToolFormat
from opendxa.common import Misc
import inspect

class MCPResource(BaseResource):
    """MCP Resource for OpenDXA integration.
    
    Example:
        mcp_resource = MCPResource("filesystem", "http://localhost:3000/sse")    
        response = await mcp_resource.query(BaseRequest(
            arguments={"tool": "read_file", "path": "/tmp/test.txt"}
        ))
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        *client_args,
        **client_kwargs
    ):
        """Initialize MCP resource.
        
        Args:
            name: Resource name
            description: Optional resource description
            config: Optional additional configuration
            *client_args: Additional MCP client parameters
            **client_kwargs: Additional MCP client parameters
        """
        super().__init__(name, description, config)
        
        self.client = MCPClient(*client_args, **client_kwargs)
        self._mcp_tools_cache: Optional[List[McpTool]] = None
        self.list_tools() # Pre-fetch the MCP tools first

    def mcp_tool_decorator(self, func_name:str) -> Any:
        """Decorator to wrap a function as an MCP tool."""
        def wrapper(**kwargs) -> Any:
            if inspect.iscoroutinefunction(self.call_tool):
                return Misc.safe_asyncio_run(self.call_tool, func_name, kwargs)
            else:
                return self.call_tool(func_name, kwargs)
        return wrapper

    def __getattr__(self, name: str) -> Any:
        try:
            return BaseResource.__getattribute__(self, name)
        except AttributeError:
            tools = BaseResource.__getattribute__(self, "_mcp_tools_cache")
            for tool in tools:
                if tool.name == name:
                    return self.mcp_tool_decorator(tool.name)
            raise
        
    async def initialize(self) -> None:
        """Initialize the MCP resource."""
        await super().initialize()
        await self._discover_tools()
            
    async def _discover_tools(self) -> None:
        """Discover and cache tools from MCP server."""
        try:
            async with self.client as _client:
                self._mcp_tools_cache = await _client.list_tools()
        except Exception as e:
            self._is_available = False
            raise
            
    def _list_tools(self, format_converter: OpenAIToolFormat) -> List[Any]:
        """Return cached tools in OpenAI format."""
        if not self._mcp_tools_cache:
            Misc.safe_asyncio_run(self._discover_tools)
        if not self._mcp_tools_cache:
            return []
        tools = []
        for tool in self._mcp_tools_cache:
            tools.append(format_converter.from_mcp_tool_format(tool))
        return tools
    
        
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute MCP tool."""
        self.debug(f"Calling tool {tool_name} with arguments {arguments}")
        print(f"Calling tool {tool_name} with arguments {arguments}")
        async with self.client as _client:
            results = await _client.call_tool(tool_name, arguments) # This will raise ToolError if the tool call fails.

        assert len(results) == 1, f"Tool {tool_name} with arguments {arguments} returned {len(results)} results, expected 1. \nresults: {results}"
        
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
    import asyncio
    async def main():
        mcp_resource = MCPResource("sensors", "http://localhost:8880/sensors")
        response = mcp_resource._list_tools(OpenAIToolFormat(mcp_resource.name, mcp_resource.id))
        print(response)
        response = await mcp_resource.call_tool("list_all_sensors", {})
        print(response)
        
    asyncio.run(main())