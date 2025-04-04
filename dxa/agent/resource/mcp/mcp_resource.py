"""MCP resource implementation using either stdio or HTTP transport."""

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Union, cast, Literal

from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.stdio import get_default_environment, stdio_client
from mcp.client.sse import sse_client

from ....common import Loggable
from ..base_resource import BaseResource, ResourceResponse


@dataclass
class StdioTransportParams:
    """Parameters for STDIO transport.
    
    Args:
        server_script: Path to the Python script that will be executed as the MCP server.
            This script should implement the MCP server protocol over standard input/output.
        command: Command to execute the server script (default: "python3").
            This is the interpreter or executable that will run the server_script.
        args: Optional list of additional arguments to pass to the command.
            If not provided, only the server_script will be passed as an argument.
        env: Optional dictionary of environment variables to set for the server process.
            These will be merged with the default environment variables.
        stdio_config: Optional additional configuration for STDIO transport.
            This can include settings specific to the STDIO communication protocol.
            Common parameters include:
            - buffer_size: Size of the read/write buffers (default: 8192)
            - encoding: Text encoding for communication (default: "utf-8")
            - line_buffering: Whether to use line buffering (default: True)
            - timeout: Timeout for read/write operations in seconds
            
            The STDIO transport is ideal for local MCP servers that run in the same process
            or on the same machine. It uses standard input/output streams for communication,
            making it simple to set up and debug.
    """
    server_script: str
    command: str = "python3"
    args: Optional[Sequence[str]] = None
    env: Optional[Dict[str, str]] = None
    stdio_config: Optional[Dict[str, Any]] = None


@dataclass
class HttpTransportParams:
    """Parameters for HTTP transport.
    
    Args:
        url: URL for the HTTP endpoint
        headers: Optional dictionary of HTTP headers
        timeout: Connection timeout in seconds for initial HTTP connection establishment.
            This is a relatively short timeout (default: 5.0s) used for the basic HTTP
            request/response cycle.
        sse_read_timeout: Server-Sent Events (SSE) read timeout in seconds.
            This is a longer timeout (default: 300s/5min) used for maintaining the SSE
            connection and receiving data over time. SSE connections are long-lived
            and may receive data for extended periods.
        sse_config: Optional additional configuration for SSE transport.
            Common parameters include:
            - retry_interval: Time to wait between reconnection attempts (default: 1.0s)
            - max_retries: Maximum number of reconnection attempts (default: 3)
            - backoff_factor: Multiplier for retry interval after each attempt
            - event_types: List of SSE event types to listen for
            - keep_alive: Whether to send keep-alive messages (default: True)
            - keep_alive_interval: Interval for keep-alive messages in seconds
            
            The HTTP transport with SSE is ideal for remote MCP servers that need to
            maintain long-lived connections for real-time updates. SSE allows the server
            to push data to the client asynchronously, making it suitable for streaming
            responses and long-running operations.
    """
    url: str
    headers: Optional[Dict[str, Any]] = None
    timeout: float = 5.0
    sse_read_timeout: float = 60 * 5
    sse_config: Optional[Dict[str, Any]] = None


class McpResource(BaseResource, Loggable):
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

    def __init__(
        self,
        name: str,
        transport_params: Optional[Union[StdioTransportParams, HttpTransportParams]] = None,
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
        self.server_id = str(uuid.uuid4())[:8]

        # Parse transport params
        if isinstance(transport_params, (StdioTransportParams, HttpTransportParams)):
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

            self.server_params: Union[StdioServerParameters, Dict[str, Any]] = StdioServerParameters(
                command=stdio_params.command,
                args=list(args),
                env=env,
                **(stdio_params.stdio_config or {})
            )
        else:  # HTTP
            http_params = cast(HttpTransportParams, self.transport_params)
            self.server_params: Union[StdioServerParameters, Dict[str, Any]] = {
                "url": http_params.url,
                "headers": http_params.headers,
                "timeout": http_params.timeout,
                "sse_read_timeout": http_params.sse_read_timeout,
                **(http_params.sse_config or {})
            }
    
    @property
    def transport_type(self) -> Literal["stdio", "http"]:
        """Get the transport type used by this resource.
        
        Returns:
            "stdio" for STDIO transport or "http" for HTTP transport
        """
        return "stdio" if isinstance(self.transport_params, StdioTransportParams) else "http"

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
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
            ResourceResponse with execution results. The response includes:
            - success: Boolean indicating if the tool execution was successful
            - content: The result of the tool execution if successful
            - error: Error message if the execution failed
            
        Raises:
            Exception: If there is an error connecting to the MCP server or executing the tool.
                     The exception is caught and returned as part of the ResourceResponse.
            
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
                arguments = {param: value for param, value in params.items() 
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
        try:
            if self.transport_type == "stdio":
                assert isinstance(self.server_params, StdioServerParameters)
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        return await self._execute_query(session, request)
            else:  # http
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
        
        This method discovers all tools exposed by the MCP server. Each tool has:
        - name: The name of the tool
        - description: A description of what the tool does
        - inputSchema: JSON Schema describing the tool's parameters
        
        Tools are the primary way for LLMs to take actions through an MCP server.
        They are similar to POST endpoints in a REST API - they perform computation
        and can have side effects.
        
        Returns:
            List of available tools with their schemas
            
        Example:
            ```python
            tools = await mcp_resource.list_tools()
            for tool in tools:
                print(f"Tool: {tool.name}")
                print(f"Description: {tool.description}")
                print("Parameters:")
                for param_name, param_details in tool.inputSchema["properties"].items():
                    print(f"  - {param_name}: {param_details.get('type')}")
            ```
        """
        try:
            if self.transport_type == "stdio":
                assert isinstance(self.server_params, StdioServerParameters)
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.list_tools()
                        return result.tools
            else:  # http
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

    def get_transport_params(self) -> Union[StdioTransportParams, HttpTransportParams]:
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
                stdio_config=stdio_params.stdio_config.copy() if stdio_params.stdio_config else None
            )
        else:
            # Create a copy of HttpTransportParams
            http_params = self.transport_params
            return HttpTransportParams(
                url=http_params.url,
                headers=http_params.headers.copy() if http_params.headers else None,
                timeout=http_params.timeout,
                sse_read_timeout=http_params.sse_read_timeout,
                sse_config=http_params.sse_config.copy() if http_params.sse_config else None
            ) 