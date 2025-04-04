"""Minimal MCP Echo Server Example

This example demonstrates how to create a simple MCP (Model Control Protocol) server
that can be used as a resource by DXA agents. The echo server provides two basic
tools that demonstrate fundamental MCP server patterns.

Key concepts demonstrated:
1. Creating a custom MCP server by extending BaseMcpService
2. Defining tools using the @tool decorator
3. Implementing simple server methods
4. Running the server as a standalone process

What you'll learn:
1. How to create a basic MCP server
2. How to define and implement MCP tools
3. How to handle server requests
4. How to run the server as a separate process

The echo server provides two simple tools:
1. ping: A basic connectivity test that returns "pong"
   - No parameters required
   - Returns a simple string response
   - Useful for testing server availability

2. echo: Returns the message sent to it
   - Takes a message parameter
   - Returns the same message
   - Demonstrates parameter handling

Usage:
1. Run this script directly to start the echo server:
   $ python mcp_echo.py

2. The server can then be used by MCP resources in other parts of the system,
   such as in the 06_mcp_resource.py example.

Note: This server runs as a separate process, so it uses absolute module references
to ensure proper imports regardless of how it's started.
"""

# Note that this will be executed as a separate process, so
# we need to use absolute module references.
from dxa.agent.resource import BaseMcpService


class McpEchoServer(BaseMcpService):
    """MCP Echo Server Implementation

    This class implements a simple echo server that demonstrates basic MCP patterns.
    It extends BaseMcpService to provide the core MCP functionality and adds two
    simple tools: ping and echo.

    The server is designed to be:
    - Simple to understand
    - Easy to extend
    - Demonstrative of MCP patterns

    Example usage in an MCP resource:
    ```python
    echo = McpResource(
        name="echo",
        transport_params=StdioTransportParams(
            server_script="mcp_echo.py",
            command="python",
            args=["mcp_echo.py"]
        ),
    )
    response = await echo.query({"tool": "echo", "arguments": {"message": "Hello!"}})
    ```
    """

    @BaseMcpService.tool(name="echo", description="Echo server that returns the input message")
    def echo(self, message: str) -> str:
        """Echo implementation matching simple server pattern

        Args:
            message: The message to echo back

        Returns:
            The same message that was received

        Example:
            Input: {"message": "Hello World"}
            Output: "Hello World"
        """
        return message

    @BaseMcpService.tool(name="ping", description="Ping server that returns 'pong'")
    def ping(self) -> str:
        """Ping implementation matching simple server pattern

        Returns:
            Always returns "pong"

        Example:
            Input: {}
            Output: "pong"
        """
        return "pong"


if __name__ == "__main__":
    # Start the echo server
    print("Starting MCP Echo Server...")
    print("Available tools:")
    print("  - ping: Returns 'pong' (connectivity test)")
    print("  - echo: Returns the message sent to it")
    print("\nService is running. Press Ctrl+C to stop.")
    McpEchoServer().run()
