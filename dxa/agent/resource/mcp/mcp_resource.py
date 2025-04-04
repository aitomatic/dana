"""MCP resource implementation using either stdio or HTTP transport."""

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union

from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.stdio import get_default_environment, stdio_client
from mcp.client.sse import sse_client

from ....common import Loggable
from ..base_resource import BaseResource, ResourceResponse


class McpTransportType(Enum):
    """Type of transport to use for MCP communication."""
    STDIO = "stdio"  # Local communication using standard input/output
    HTTP = "http"    # Remote communication using HTTP/SSE


@dataclass
class McpConnectionParams:
    """Parameters for connecting to an MCP resource."""
    transport_type: McpTransportType
    # Process-specific params
    command: Optional[str] = None
    args: Optional[Sequence[str]] = None
    env: Optional[Dict[str, str]] = None
    # HTTP-specific params
    url: Optional[str] = None
    timeout: Optional[float] = 5.0
    headers: Optional[Dict[str, Any]] = None
    sse_read_timeout: float = 60 * 5


class McpResource(BaseResource, Loggable):
    """MCP resource that can use either stdio or HTTP transport."""

    def __init__(
        self,
        name: str,
        connection_params: Optional[Union[McpConnectionParams, Dict[str, Any]]] = None,
        **params,
    ):
        """Initialize MCP resource.
        
        Args:
            name: Resource name
            connection_params: Connection parameters for either stdio or HTTP transport
            **params: Additional parameters passed to transport
        """
        super().__init__(name)
        Loggable.__init__(self)
        self.server_id = str(uuid.uuid4())[:8]

        # Parse connection params
        if isinstance(connection_params, McpConnectionParams):
            self.transport_type = connection_params.transport_type
            if self.transport_type == McpTransportType.STDIO:
                env = get_default_environment()
                env["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
                if connection_params.env:
                    env.update(connection_params.env)
                if "env" in params:
                    env.update(params["env"])

                server_script = params.get("server_script")
                if not server_script:
                    raise ValueError("server_script is required for stdio transport")

                self.server_params = StdioServerParameters(
                    command=connection_params.command or "python3",
                    args=list(connection_params.args or [server_script]),
                    env=env,
                    **params.get("stdio_config", {})
                )
            else:  # HTTP
                if not connection_params.url:
                    raise ValueError("URL is required for HTTP transport")
                self.server_params = {
                    "url": connection_params.url,
                    "headers": connection_params.headers,
                    "timeout": connection_params.timeout,
                    "sse_read_timeout": connection_params.sse_read_timeout,
                    **params.get("sse_config", {})
                }
        elif isinstance(connection_params, dict):
            # Handle dict params similarly
            self.transport_type = McpTransportType(connection_params.get("transport_type", "stdio"))
            if self.transport_type == McpTransportType.STDIO:
                env = get_default_environment()
                env["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
                if "env" in connection_params:
                    env.update(connection_params["env"])
                if "env" in params:
                    env.update(params["env"])

                server_script = params.get("server_script")
                if not server_script:
                    raise ValueError("server_script is required for stdio transport")

                args = connection_params.get("args", [server_script])
                if not all(isinstance(arg, str) for arg in args):
                    raise ValueError("All args must be strings")

                self.server_params = StdioServerParameters(
                    command=connection_params.get("command", "python3"),
                    args=list(args),
                    env=env,
                    **params.get("stdio_config", {})
                )
            else:  # HTTP
                url = connection_params.get("url")
                if not url:
                    raise ValueError("URL is required for HTTP transport")
                self.server_params = {
                    "url": url,
                    "headers": connection_params.get("headers"),
                    "timeout": connection_params.get("timeout", 5.0),
                    "sse_read_timeout": connection_params.get("sse_read_timeout", 60 * 5),
                    **params.get("sse_config", {})
                }
        else:
            # Default to stdio transport
            self.transport_type = McpTransportType.STDIO
            env = get_default_environment()
            env["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
            if "env" in params:
                env.update(params["env"])

            server_script = params.get("server_script")
            if not server_script:
                raise ValueError("server_script is required for stdio transport")

            self.server_params = StdioServerParameters(
                command=params.get("command", "python3"),
                args=[server_script],
                env=env,
                **params.get("stdio_config", {})
            )

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Handle tool execution request.
        
        Args:
            request: Tool execution request with tool name and arguments
            
        Returns:
            ResourceResponse with execution results
        """
        self.debug("Starting MCP query: %s", request)
        try:
            if self.transport_type == McpTransportType.STDIO:
                assert isinstance(self.server_params, StdioServerParameters)
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        return await self._execute_query(session, request)
            else:
                assert isinstance(self.server_params, dict)
                async with sse_client(**self.server_params) as streams:
                    async with ClientSession(*streams) as session:
                        return await self._execute_query(session, request)
        except Exception as e:
            self.error("Tool execution failed", exc_info=True)
            return ResourceResponse(success=False, error=str(e))

    async def _execute_query(self, session: ClientSession, request: Dict[str, Any]) -> ResourceResponse:
        """Execute query through MCP session.
        
        Args:
            session: Active MCP client session
            request: Tool execution request
            
        Returns:
            ResourceResponse with execution results
        """
        await session.initialize()
        arguments = request.get("arguments", {})
        # Prepend arguments with 'self' for instance methods
        arguments = {"self": None, **arguments}
        result = await session.call_tool(request["tool"], arguments)
        return ResourceResponse(success=True, content=result)

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request can be handled by this resource.
        
        Args:
            request: Request to check
            
        Returns:
            True if request contains tool execution pattern
        """
        return "tool" in request

    async def list_tools(self) -> List[Tool]:
        """List all available tools from the MCP server.
        
        Returns:
            List of available tools with their schemas
        """
        try:
            if self.transport_type == McpTransportType.STDIO:
                assert isinstance(self.server_params, StdioServerParameters)
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.list_tools()
                        return result.tools
            else:
                assert isinstance(self.server_params, dict)
                async with sse_client(**self.server_params) as streams:
                    async with ClientSession(*streams) as session:
                        await session.initialize()
                        result = await session.list_tools()
                        return result.tools
        except Exception as e:
            self.error(f"Tool listing failed: {e}", exc_info=True)
            return []

    async def get_tool_strings(self, resource_id: str, **kwargs) -> List[Dict[str, Any]]:
        """Format resource into OpenAI function specification.
        
        Args:
            resource_id: Resource identifier
            **kwargs: Additional keyword arguments
            
        Returns:
            OpenAI function specification list
        """
        tool_strings = []
        mcp_tools = await self.list_tools()

        for tool in mcp_tools:
            # Copy and clean up base schema
            parameters = tool.inputSchema.copy()

            # Remove 'self' references if present
            if "properties" in parameters:
                properties = parameters["properties"]
                if "self" in properties:
                    del properties["self"]
                    if "required" in parameters:
                        parameters["required"].remove("self")

            # Process properties if they exist
            if "properties" in parameters and "required" in parameters:
                properties = parameters["properties"]
                required_fields = parameters["required"]

                # Make non-required fields nullable and add to required list
                for field_name, field_props in properties.items():
                    if field_name not in required_fields and "type" in field_props:
                        field_type = field_props["type"]
                        field_props["type"] = ([field_type] if isinstance(field_type, str) else field_type) + ["null"]
                        parameters["required"].append(field_name)

                # Clean up property definitions to only include essential keys
                allowed_keys = {"description", "title", "type"}
                for prop in properties.values():
                    prop_keys = set(prop.keys())
                    for key in prop_keys - allowed_keys:
                        del prop[key]

            parameters["additionalProperties"] = False

            tool_strings.append(
                {
                    "type": "function",
                    "function": {
                        "name": f"{resource_id}__query__{tool.name}",
                        "description": tool.description,
                        "parameters": parameters,
                        "strict": True,
                    },
                }
            )

        return tool_strings

    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters for this resource.
        
        This method is used to expose the connection parameters to other resources,
        allowing them to connect to this resource's MCP server.
        
        Returns:
            Dict containing connection parameters
        """
        if self.transport_type == McpTransportType.STDIO:
            assert isinstance(self.server_params, StdioServerParameters)
            return {
                "transport_type": "stdio",
                "command": self.server_params.command,
                "args": self.server_params.args,
                "env": self.server_params.env,
            }
        else:
            assert isinstance(self.server_params, dict)
            return {
                "transport_type": "http",
                "url": self.server_params["url"],
                "headers": self.server_params.get("headers"),
                "timeout": self.server_params.get("timeout", 5.0),
                "sse_read_timeout": self.server_params.get("sse_read_timeout", 60 * 5),
            } 