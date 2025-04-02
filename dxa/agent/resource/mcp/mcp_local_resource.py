"""MCP local resource using stdio transport (matches mcp_client.py pattern)"""

from typing import Dict, Any, List, Optional, Union, Literal, cast
from dataclasses import dataclass
import uuid
from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.stdio import stdio_client, get_default_environment
from ..base_resource import BaseResource, ResourceResponse
from ....common import DXA_LOGGER

@dataclass
class McpLocalConnectionParams:
    """Parameters for connecting to a local MCP resource via stdio"""
    connection_type: Literal['stdio'] = 'stdio'
    server_id: str = ""
    command: Optional[str] = None
    args: Optional[list] = None
    env: Optional[Dict[str, str]] = None

class McpLocalResource(BaseResource):
    """MCP resource for local stdio tool execution with optional exposure"""
    
    def __init__(self,
                 name: str,
                 connection_params: Optional[Union[McpLocalConnectionParams, Dict[str, Any]]] = None,
                 expose: bool = False,
                 **params):
        super().__init__(name)
        self.logger = DXA_LOGGER.getLogger(__class__.__name__)
        self.server_id = str(uuid.uuid4())[:8]  # Generate unique ID for this server
        
        env = get_default_environment()
        env["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
        
        user_env = params.get("env", {})
        if user_env is not None:
            env.update(user_env)
            
        self.env = env

        if isinstance(connection_params, McpLocalConnectionParams):
            self.command = connection_params.command or "python3"
            self.args = connection_params.args if connection_params.args else [params.get("server_script")]
            if connection_params.env:
                self.env.update(connection_params.env)
        elif isinstance(connection_params, dict):
            self.command = connection_params.get("command", "python3")
            self.args = connection_params.get("args", [params.get("server_script")])
            if connection_params.get("env"):
                self.env.update(connection_params["env"])
        else:
            self.command = params.get("command", "python3")
            self.args = [params.get("server_script")]

        if self.args is None:
            self.args = []
        
        self.args = cast(List[str], self.args)

        self.server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
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
                    return ResourceResponse(success=True, content=result)
                    
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error("Tool execution failed", exc_info=True)
            return ResourceResponse(success=False, error=str(e))

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check for local tool execution pattern"""
        return "tool" in request

    async def list_tools(self) -> List[Tool]:
        """List all available tools from the MCP server.
        
        Returns:
            List[Tool]: List of available tools with their schemas
        """
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    return result.tools
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error(f"Tool listing failed: {e}", exc_info=True)
            return []
        
    async def get_tool_strings(
        self, 
        resource_id: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Format a resource into OpenAI function specification.
        
        Args:
            resource: Resource instance to format
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

            tool_strings.append({
                "type": "function",
                "function": {
                    "name": f"{resource_id}__query__{tool.name}",
                    "description": tool.description,
                    "parameters": parameters,
                    "strict": True
                }
            })

        return tool_strings