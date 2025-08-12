#!/usr/bin/env python3
"""
Simple HTTP Streamable MCP Server for DANA Testing

This server provides 3 basic tools for testing DANA's MCP integration
over HTTP Streamable transport.

Usage:
    python examples/dana/05_mcp_integration/start_http_streamable_server.py

The server will start on http://localhost:8081/mcp and provide:
- echo: Echo messages back
- ping: Test connectivity
- get_current_time: Get current timestamp
"""

import sys
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server for HTTP Streamable transport
mcp = FastMCP("DANA Test Server")


@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back to test basic connectivity.

    Args:
        message: The message to echo back

    Returns:
        The same message that was sent
    """
    return f"Echo: {message}"


@mcp.tool()
def ping() -> str:
    """Simple ping tool to test server connectivity.

    Returns:
        A pong response with timestamp
    """
    return f"pong at {datetime.now().isoformat()}"


@mcp.tool()
def get_current_time() -> str:
    """Get the current system time.

    Returns:
        Current timestamp in ISO format
    """
    return datetime.now().isoformat()


def main():
    """Main function to start the HTTP Streamable MCP server."""
    print("🚀 Starting DANA Test HTTP Streamable MCP Server...")
    print("📡 Server will be available at default MCP port (typically 8000)")
    print("🔧 Available tools:")
    print("   - echo: Echo messages back")
    print("   - ping: Test connectivity")
    print("   - get_current_time: Get current timestamp")
    print()
    print("🔄 To test with DANA, use an MCP resource with HTTP Streamable transport:")
    print("   HttpTransportParams(url='http://localhost:8000/mcp') (default port)")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    try:
        # Run the server with Streamable HTTP transport using official MCP SDK API
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
