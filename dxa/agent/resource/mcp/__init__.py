"""MCP resource implementation. """

from .mcp_config import MCPConfig
from .mcp_local_resource import McpLocalResource
from .mcp_remote_resource import McpRemoteResource
from .mcp_services import (
    BaseMcpService,
    McpEchoService,
)

__all__ = [
    "McpLocalResource",
    "McpRemoteResource",
    "BaseMcpService",
    "McpEchoService",
    "MCPConfig",
]
