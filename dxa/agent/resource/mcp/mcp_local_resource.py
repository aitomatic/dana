"""MCP local resource using stdio transport (matches mcp_client.py pattern)"""

from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client, get_default_environment
from ..base_resource import BaseResource, ResourceResponse
from ....common import DXA_LOGGER

class McpLocalResource(BaseResource):
    """MCP resource for local stdio tool execution"""
    
    def __init__(self, name: str, server_script: str, **params):
        super().__init__(name)
        self.logger = DXA_LOGGER.getLogger(__class__.__name__)
        
        env = get_default_environment()
        env["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
        user_env = params.get("env", {})
        if user_env is not None:
            env.update(user_env)

        self.server_params = StdioServerParameters(
            command=params.get("command", "python3"),
            args=[server_script],
            env=env,
            **params.get("stdio_config", {})
        )

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
                    # which we implemnt as an instance method
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
        return "tool" in request and "server_script" in request 