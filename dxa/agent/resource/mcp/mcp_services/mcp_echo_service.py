"""Minimal MCP Echo Service matching mcp_server.py pattern"""

# Note that this will be excuted as a separate process, so
# we need to use absolute module references.
from dxa.agent.resource.mcp.mcp_services import BaseMcpService

class McpEchoService(BaseMcpService):
    """MCP Echo Service"""
    
    @BaseMcpService.tool(name="echo", description="Echo service")
    def echo(self, message: str) -> str:
        """Echo implementation matching simple server pattern"""
        return message

    @BaseMcpService.tool(name="ping", description="Ping service")
    def ping(self) -> str:
        """Ping implementation matching simple server pattern"""
        return "pong"


if __name__ == "__main__":
    McpEchoService().run()