"""MCP local resource using stdio transport (matches mcp_client.py pattern)"""

from typing import Dict, Any, Optional, Union, Literal
from dataclasses import dataclass
import uuid
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client, get_default_environment
from ..base_resource import BaseResource, ResourceResponse
from ....common import DXA_LOGGER

@dataclass
class McpLocalConnectionParams:
    """Parameters for connecting to a local MCP resource via stdio"""
    connection_type: Literal['stdio'] = 'stdio'
    server_id: str = None
    command: Optional[str] = None
    args: Optional[list] = None
    env: Optional[Dict[str, str]] = None

class McpLocalResource(BaseResource):
    """MCP resource for local stdio tool execution with optional exposure"""
    
    def __init__(self, name: str, connection_params: Optional[Union[McpLocalConnectionParams, Dict[str, Any]]] = None, expose: bool = False, **params):
        super().__init__(name)
        self.logger = DXA_LOGGER.getLogger(__class__.__name__)
        self.expose = expose
        self.server_id = str(uuid.uuid4())[:8]  # Generate unique ID for this server
        
        env = get_default_environment()
        env["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
        
        # Add environment variables for exposure if needed
        if self.expose:
            env["MCP_EXPOSE"] = "1"
                
        user_env = params.get("env", {})
        if user_env is not None:
            env.update(user_env)
            
        self.env = env

        if isinstance(connection_params, McpLocalConnectionParams):
            self.command = connection_params.command or "python3"
            self.server_script = connection_params.args[0] if connection_params.args else params.get("server_script")
            if connection_params.env:
                self.env.update(connection_params.env)
        elif isinstance(connection_params, dict):
            self.command = connection_params.get("command", "python3")
            self.server_script = connection_params.get("args", [params.get("server_script")])[0]
            if connection_params.get("env"):
                self.env.update(connection_params["env"])
        else:
            self.command = params.get("command", "python3")
            self.server_script = params.get("server_script")

        self.server_params = StdioServerParameters(
            command=self.command,
            args=[self.server_script],
            env=self.env,
            **params.get("stdio_config", {})
        )

    async def initialize(self) -> None:
        """Initialize the resource and start server"""
        await super().initialize()
        

    async def query(self, request: Dict[str, Any]) -> ResourceResponse:
        """Handle tool execution request matching mcp_client.py flow"""
        self.logger.debug("Starting MCP local query: %s", request)
        try:
            async with stdio_client(self.server_params) as (read, write):
                self.logger.debug("Stdio transport established")
                async with ClientSession(read, write) as session:
                    self.logger.debug("Client session created")
                    await session.initialize()
                    self.logger.debug("Session initialization complete")
                    
                    arguments = request.get("arguments", {})
                    # Prepend arguments with 'self', because the MCP framework
                    # will not pass 'self' as the first argument to the tool,
                    # which we implement as an instance method
                    arguments = {"self": None, **arguments}
                    result = await session.call_tool(
                        request["tool"],
                        arguments
                    )
                    self.logger.debug("Tool call returned: %s", result)
                    return ResourceResponse(success=True, content=result)
                    
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error("Tool execution failed", exc_info=True)
            return ResourceResponse(success=False, error=str(e))

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check for local tool execution pattern"""
        return "tool" in request

    def get_connection_params(self) -> McpLocalConnectionParams:
        """Get parameters for other agents to connect to this resource"""
        if not self.expose:
            raise ValueError(f"MCP resource '{self.name}' is not configured for exposure")
            
        return McpLocalConnectionParams(
            connection_type='stdio',
            command=self.command,
            args=[self.server_script],
            env=self.env,
            server_id=self.server_id
        )