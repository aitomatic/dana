"""
Server-Sent Events (SSE) transport implementation for MCP client communication.
Provides real-time streaming communication with MCP servers using the Model Context Protocol.
This implementation uses the official MCP Python SDK for protocol compliance.
"""

# SSE transport temporarily disabled due to API changes
# from fastmcp.client.transports import SSETransport

from .base_transport import BaseTransport


class MCPSSETransport(BaseTransport):
    """Placeholder SSE transport - needs implementation with new MCP API"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise NotImplementedError("SSE transport needs to be updated for new MCP API")
