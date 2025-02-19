"""Minimal MCP Echo Service matching mcp_server.py pattern"""

from mcp.server.fastmcp import FastMCP
from dxa.common import DXA_LOGGER

# Create MCP server instance
mcp = FastMCP("EchoServer")

logger = DXA_LOGGER.getLogger(__file__.rsplit('/', maxsplit=1)[-1])

@mcp.tool(name="echo", description="Echo service")
def echo(message: str) -> str:
    """Echo implementation matching simple server pattern"""
    logger.debug("Processing echo request: %s", message)
    return message

if __name__ == "__main__":
    logger.debug("Starting MCP echo service")
    mcp.run(transport='stdio') 
