"""
Streamable HTTP transport implementation for MCP client communication.
Provides HTTP-based streaming communication with MCP servers using the Model Context Protocol.
This implementation uses the official MCP Python SDK streamable HTTP client for protocol compliance.
"""

from fastmcp.client.transports import StreamableHttpTransport

from dana.integrations.mcp.resource.mcp.client.transport.base_transport import BaseTransport


class MCPHTTPTransport(StreamableHttpTransport, BaseTransport):
    pass
