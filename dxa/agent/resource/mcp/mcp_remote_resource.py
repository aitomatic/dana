"""MCP remote resource using HTTP transport"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from mcp import ClientSession, Tool
from mcp.client.sse import sse_client

from ....common import DXA_LOGGER
from ..base_resource import BaseResource, ResourceResponse


@dataclass
class McpRemoteConnectionParams:
    """Parameters for connecting to a remote MCP resource via HTTP"""

    url: str
    timeout: Optional[float] = 5.0
    headers: dict[str, Any] | None = None
    sse_read_timeout: float = 60 * 5


class McpRemoteResource(BaseResource):
    """MCP resource for remote HTTP tool execution"""

    def __init__(
        self,
        name: str,
        connection_params: Optional[Union[McpRemoteConnectionParams, Dict[str, Any]]] = None,
        **params,
    ):
        super().__init__(name)
        self.logger = DXA_LOGGER.getLogger(__class__.__name__)

        if isinstance(connection_params, McpRemoteConnectionParams):
            url = connection_params.url
            headers = connection_params.headers
            timeout = connection_params.timeout
            sse_read_timeout = connection_params.sse_read_timeout
        elif isinstance(connection_params, dict):
            url = connection_params.get("url")
            headers = connection_params.get("headers")
            timeout = connection_params.get("timeout", 5.0)
            sse_read_timeout = connection_params.get("sse_read_timeout", 60 * 5)
        else:
            url = params.get("url")
            headers = params.get("headers")
            timeout = params.get("timeout", 5.0)
            sse_read_timeout = params.get("sse_read_timeout", 60 * 5)

        self.server_params = {
            "url": url,
            "headers": headers,
            "timeout": timeout,
            "sse_read_timeout": sse_read_timeout,
            **params.get("sse_config", {}),
        }

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Handle HTTP tool execution request"""
        self.logger.debug("Starting MCP remote query: %s", request)
        try:
            async with sse_client(**self.server_params) as streams:
                self.logger.debug("SSE client created")
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    self.logger.debug("Session initialized")

                    arguments = request.get("arguments", {})
                    # Prepend arguments with 'self', because the MCP framework
                    # will not pass 'self' as the first argument to the tool,
                    # which we implement as an instance method
                    arguments = {"self": None, **arguments}
                    response = await session.call_tool(request["tool"], arguments)
                    return ResourceResponse(success=True, content=response)
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error("HTTP tool execution failed", exc_info=True)
            return ResourceResponse(success=False, error=str(e))

    async def list_tools(self) -> List[Tool]:
        """List all available tools from the MCP server.

        Returns:
            List[Tool]: List of available tools with their schemas
        """
        try:
            async with sse_client(**self.server_params) as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    return result.tools

        except Exception as e:  # pylint: disable=broad-except
            self.logger.error(f"Tool listing failed: {e}", exc_info=True)
            return []

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check for HTTP tool execution pattern"""
        return "tool" in request and "base_url" in request
