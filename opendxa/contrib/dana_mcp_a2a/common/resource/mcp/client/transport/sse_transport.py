"""
Server-Sent Events (SSE) transport implementation for MCP client communication.
Provides real-time streaming communication with MCP servers using the Model Context Protocol.
This implementation uses the official MCP Python SDK for protocol compliance.
"""

from fastmcp.client.transports import SSETransport
from opendxa.contrib.dana_mcp_a2a.common.resource.mcp.client.transport.base_transport import BaseTransport

class MCPSSETransport(SSETransport, BaseTransport):
    pass