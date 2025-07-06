"""MCP resource implementation using either stdio or HTTP transport."""

import asyncio
import functools
from collections.abc import Callable
from typing import Any, Literal, TypeVar, cast

from mcp import ClientSession, StdioServerParameters
from mcp import Tool as McpTool
from mcp.client.sse import sse_client
from mcp.client.stdio import get_default_environment, stdio_client

from dana.common.mixins.loggable import Loggable
from dana.common.resource.base_resource import BaseResource, ResourceError
from dana.common.types import BaseRequest, BaseResponse
from dana.common.utils.misc import Misc
from dana.integrations.mcp.mcp_config import HttpTransportParams, McpConfig, McpConfigError, StdioTransportParams

T = TypeVar("T")


def with_retries(retries: int = 3, delay: float = 1.0):
    """Decorator for adding retry logic to async functions.

    Args:
        retries: Number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            attempt = 0
            last_error = None

            while attempt < retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    last_error = e
                    if attempt < retries:
                        await asyncio.sleep(delay)

            raise last_error

        return wrapper  # type: ignore

    return decorator


class McpResource(BaseResource):
    """MCP resource that can use either stdio or HTTP transport.

    The Model Context Protocol (MCP) allows applications to provide context for LLMs
    in a standardized way, separating the concerns of providing context from the
    actual LLM interaction.

    MCP servers can expose:
    - Resources: Data that can be loaded into the LLM's context (similar to GET endpoints)
    - Tools: Functions that the LLM can call to take actions (similar to POST endpoints)
    - Prompts: Reusable templates for LLM interactions

    This resource implementation supports connecting to MCP servers using either:
    - STDIO transport: For local MCP servers running in the same process or machine
    - HTTP transport with SSE: For remote MCP servers that need long-lived connections

    The resource handles all MCP protocol messages and lifecycle events, making it
    easy to integrate MCP servers into your application.
    """

    @classmethod
    def from_config(cls, name: str, config: str | dict[str, Any]) -> "McpResource":
        """Create McpResource instance from configuration.

        This is a convenience method to create an MCP resource from a JSON configuration file
        or a configuration dictionary.

        Args:
            name: Name to give the resource
            config: Either:
                - Path to a configuration file containing mcpServers
                - Configuration dictionary for a single server (will be wrapped in mcpServers)

        Returns:
            Configured McpResource instance

        Example:
            ```python
            # From file with multiple servers
            resource = McpResource.from_config("weather", "config.json")

            # From dictionary - STDIO transport
            config = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/ctn/"]
            }
            resource = McpResource.from_config("filesystem", config)

            # From dictionary - HTTP transport
            config = {
                "url": "https://api.weather.com/mcp",
                "headers": {"Authorization": "Bearer token"}
            }
            resource = McpResource.from_config("weather", config)
            ```
        """
        try:
            if isinstance(config, str):
                # If it's a file path, use it directly
                config_manager = McpConfig(config)
            else:
                # If it's a dict, wrap it in mcpServers structure
                config_manager = McpConfig({"mcpServers": {name: config}})
            transport_params = config_manager.get_transport_params(name)
            return cls(name=name, transport_params=transport_params)
        except McpConfigError as e:
            raise ValueError(f"Failed to create MCP resource from config: {e}") from e

    def __init__(
        self,
        name: str,
        transport_params: StdioTransportParams | HttpTransportParams | None = None,
    ):
        """Initialize MCP resource.

        Args:
            name: Resource name
            transport_params: Transport-specific parameters. Must be either:
                - StdioTransportParams: For STDIO transport with fields:
                    - server_script: Path to the Python script to execute
                    - command: Command to execute (default: "python3")
                    - args: Optional list of arguments for the command
                    - env: Optional dictionary of environment variables
                    - stdio_config: Optional additional configuration for STDIO transport
                - HttpTransportParams: For HTTP transport with fields:
                    - url: URL for the HTTP endpoint
                    - headers: Optional dictionary of HTTP headers
                    - timeout: Connection timeout in seconds for initial HTTP connection establishment.
                        This is a relatively short timeout (default: 5.0s) used for the basic HTTP
                        request/response cycle.
                    - sse_read_timeout: Server-Sent Events (SSE) read timeout in seconds.
                        This is a longer timeout (default: 300s/5min) used for maintaining the SSE
                        connection and receiving data over time. SSE connections are long-lived
                        and may receive data for extended periods.
                    - sse_config: Optional additional configuration for SSE transport
        """
        super().__init__(name)
        Loggable.__init__(self)
        self.server_id = Misc.generate_base64_uuid(8)

        # Parse transport params
        if isinstance(transport_params, StdioTransportParams | HttpTransportParams):
            self.transport_params = transport_params
        else:
            # Default to stdio transport with required server_script
            raise ValueError("transport_params is required")

        # Create server params
        # Note: There's a distinction between transport_params (user-facing configuration)
        # and server_params (internal parameters used by the MCP library):
        # - For STDIO: We use StdioServerParameters from the MCP library
        # - For HTTP: We use a dictionary that's passed directly to sse_client
        if isinstance(self.transport_params, StdioTransportParams):
            env = get_default_environment()
            env["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"

            stdio_params = cast(StdioTransportParams, self.transport_params)
            if stdio_params.env:
                env.update(stdio_params.env)

            args = stdio_params.args or [stdio_params.server_script]
            if not all(isinstance(arg, str) for arg in args):
                raise ValueError("All args must be strings")

            self.server_params: StdioServerParameters | dict[str, Any] = StdioServerParameters(
                command=stdio_params.command, args=list(args), env=env, **(stdio_params.stdio_config or {})
            )
        else:  # HTTP
            http_params = cast(HttpTransportParams, self.transport_params)
            self.server_params: StdioServerParameters | dict[str, Any] = {
                "url": http_params.url,
                "headers": http_params.headers,
                "timeout": http_params.timeout,
                "sse_read_timeout": http_params.sse_read_timeout,
                **(http_params.sse_config or {}),
            }

    @property
    def transport_type(self) -> Literal["stdio", "http"]:
        """Get the transport type used by this resource.

        Returns:
            "stdio" for STDIO transport or "http" for HTTP transport
        """
        return "stdio" if isinstance(self.transport_params, StdioTransportParams) else "http"

    @with_retries(retries=3, delay=1.0)
    async def query(self, request: BaseRequest | None = None) -> BaseResponse:
        """Execute a tool on the MCP server.

        This method sends a request to the MCP server to execute a specific tool with the provided arguments.
        The method handles the connection to the server based on the transport type (stdio or http) and
        returns the result of the tool execution.

        Args:
            request: Tool execution request with the following structure:
                {
                    "tool": "tool_name",  # Name of the MCP tool to call
                    "arguments": {        # Dictionary of arguments for the tool
                        "param1": value1,
                        "param2": value2,
                        ...
                    }
                }

                The "tool" field is required and must match the name of a tool exposed by the MCP server.
                The "arguments" field is optional and contains the parameters for the tool.
                If "arguments" is not provided, an empty dictionary will be used.

        Returns:
            BaseResponse with execution results. The response includes:
            - success: Boolean indicating if the tool execution was successful
            - content: The result of the tool execution if successful
            - error: Error message if the execution failed

        Raises:
            Exception: If there is an error connecting to the MCP server or executing the tool.
                     The exception is caught and returned as part of the BaseResponse.

        Examples:
            Basic usage with a simple tool:
            ```python
            response = await mcp_resource.query({
                "tool": "calculate_bmi",
                "arguments": {"weight_kg": 70, "height_m": 1.75}
            })

            if response.success:
                print(f"BMI: {response.content}")
            else:
                print(f"Error: {response.error}")
            ```

            Calling a tool without arguments:
            ```python
            response = await mcp_resource.query({
                "tool": "get_current_time"
            })

            if response.success:
                print(f"Current time: {response.content}")
            ```

            Error handling with try-except:
            ```python
            try:
                response = await mcp_resource.query({
                    "tool": "process_data",
                    "arguments": {"data": large_dataset}
                })

                if response.success:
                    process_result(response.content)
                else:
                    handle_error(response.error)
            except Exception as e:
                print(f"Unexpected error: {e}")
            ```

            Discovering available tools first:
            ```python
            # First, discover available tools
            tools = await mcp_resource.list_tools()

            # Find a specific tool
            target_tool = next((tool for tool in tools if tool.name == "analyze_text"), None)

            if target_tool:
                # Check required parameters
                required_params = target_tool.inputSchema.get("required", [])

                # Prepare arguments
                arguments = {param: value for param, value in request.items()
                            if param in required_params or param in target_tool.inputSchema.get("properties", {})}

                # Execute the tool
                response = await mcp_resource.query({
                    "tool": target_tool.name,
                    "arguments": arguments
                })
            else:
                print("Tool not found")
            ```
        """
        self.debug("Starting MCP query: %s", request)

        # Convert BaseRequest to dict if needed, or handle None
        if request is None:
            request_dict = {}
        elif isinstance(request, BaseRequest):
            request_dict = request.arguments
        else:
            request_dict = request

        try:
            if self.transport_type == "stdio":
                assert isinstance(self.server_params, StdioServerParameters)
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        return await self._execute_query(session, request_dict)
            else:  # http
                assert isinstance(self.server_params, dict)
                async with sse_client(**self.server_params) as streams:
                    async with ClientSession(*streams) as session:
                        return await self._execute_query(session, request_dict)
        except Exception as e:
            self.error("Tool execution failed", exc_info=True)
            return BaseResponse.error_response(str(e))

    @with_retries(retries=3, delay=1.0)
    async def _execute_query(self, session: ClientSession, request: dict[str, Any]) -> BaseResponse:
        """Execute query through MCP session with automatic retries.

        Args:
            session: Active MCP client session
            request: Tool execution request

        Returns:
            BaseResponse with execution results
        """
        await session.initialize()

        arguments = request.get("arguments", {})
        if isinstance(arguments, str):
            import json

            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                raise ValueError("Arguments must be a dictionary") from e

        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary")

        # Prepend arguments with 'self' for instance methods
        arguments = {"self": None, **arguments}

        try:
            result = await session.call_tool(request["tool"], arguments)

            # Handle progress reporting if available
            if isinstance(result, dict) and "progress" in result:
                progress = result["progress"]
                total = result.get("total", 100)
                percentage = (progress / total) * 100
                self.info(f"Progress: {progress}/{total} ({percentage:.1f}%)")

            # Handle streaming responses
            if isinstance(result, list | tuple) and len(result) > 0:
                if isinstance(result[0], tuple) and result[0][0] == "stream":
                    # Process streaming response
                    stream_data = []
                    for item in result:
                        if isinstance(item, tuple) and item[0] == "stream":
                            stream_data.append(item[1])
                    result = "".join(stream_data)

            return BaseResponse(success=True, content=result)

        except Exception as e:
            raise ResourceError("Tool execution failed") from e

    def can_handle(self, request: dict[str, Any]) -> bool:
        """Check if request can be handled by this resource.

        Args:
            request: Request to check

        Returns:
            True if request contains tool execution pattern
        """
        return "tool" in request

    def list_mcp_tools(self) -> list[McpTool]:
        """Override to get all tools from the MCP server instead of my functions."""
        return asyncio.run(self.list_tools())

    __mcp_tool_list_cache: list[McpTool] | None = None

    async def list_tools(self) -> list[McpTool]:
        """List all available tools from the MCP server.

        This method discovers all tools exposed by the MCP server. Each tool has:
        - name: The name of the tool
        - description: A description of what the tool does
        - inputSchema: JSON Schema describing the tool's parameters

        Tools are the primary way for LLMs to take actions through an MCP server.
        They are similar to POST endpoints in a REST API - they perform computation
        and can have side effects.

        Returns:
            List of available tools with their schemas
        """
        if self.__mcp_tool_list_cache is not None:
            return self.__mcp_tool_list_cache

        try:
            if self.transport_type == "stdio":
                assert isinstance(self.server_params, StdioServerParameters)
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.list_tools()

                        # Process tools response
                        tools = []
                        if hasattr(result, "tools"):
                            # Direct tools attribute
                            tools.extend(result.tools)
                        elif isinstance(result, list | tuple):
                            # Tuple format response
                            for item in result:
                                if isinstance(item, tuple) and item[0] == "tools":
                                    for tool in item[1]:
                                        if isinstance(tool, McpTool):
                                            tools.append(tool)
                                        else:
                                            # Create Tool instance if needed
                                            tools.append(
                                                McpTool(
                                                    name=tool.get("name", ""),
                                                    description=tool.get("description", ""),
                                                    inputSchema=tool.get("inputSchema", {}),
                                                )
                                            )

                        self.__mcp_tool_list_cache = tools
                        return self.__mcp_tool_list_cache
            else:  # http
                assert isinstance(self.server_params, dict)
                async with sse_client(**self.server_params) as streams:
                    async with ClientSession(*streams) as session:
                        await session.initialize()
                        result = await session.list_tools()
                        self.__mcp_tool_list_cache = result.tools if hasattr(result, "tools") else []
                        return self.__mcp_tool_list_cache
        except Exception as e:
            self.error(f"Tool listing failed: {e}", exc_info=True)
            return []

    def get_transport_params(self) -> StdioTransportParams | HttpTransportParams:
        """Get transport parameters for this resource.

        This method is used to expose the transport parameters to other resources,
        allowing them to connect to this resource's MCP server.

        Returns:
            A copy of the original transport parameters object (StdioTransportParams or HttpTransportParams)
            that can be used to create a new McpResource instance without affecting the original.
        """
        if isinstance(self.transport_params, StdioTransportParams):
            # Create a copy of StdioTransportParams
            stdio_params = self.transport_params
            return StdioTransportParams(
                server_script=stdio_params.server_script,
                command=stdio_params.command,
                args=list(stdio_params.args) if stdio_params.args else None,
                env=stdio_params.env.copy() if stdio_params.env else None,
                stdio_config=stdio_params.stdio_config.copy() if stdio_params.stdio_config else None,
            )
        else:
            # Create a copy of HttpTransportParams
            http_params = self.transport_params
            return HttpTransportParams(
                url=http_params.url,
                headers=http_params.headers.copy() if http_params.headers else None,
                timeout=http_params.timeout,
                sse_read_timeout=http_params.sse_read_timeout,
                sse_config=http_params.sse_config.copy() if http_params.sse_config else None,
            )

    def _call_tool_after_validation(self, tool_name: str, arguments: Any) -> Any:
        """Call a tool with the given name and validated arguments.

        Args:
            tool_name: The name of the tool to call
            arguments: The validated arguments to pass to the tool
        """
        return self.query({"tool": tool_name, "arguments": arguments})
