"""MCP Resource Example

This example demonstrates how to use MCP (Model Control Protocol) resources in the DXA framework.
MCP resources allow you to integrate external services and tools into your agents.

Key concepts demonstrated:
1. Creating and using local custom MCP servers
2. Accessing community-created MCP servers
3. Using Server-Sent Events (SSE) for remote MCP servers

What you'll learn:
1. How to create and run a local MCP service
2. How to discover and use available tools from MCP services
3. How to handle responses and errors from MCP services
4. How to integrate community MCP services
5. How to work with remote MCP services using SSE

The example includes three main demonstrations:
1. Local Echo Service: A simple echo service that demonstrates basic MCP functionality
2. Community Weather Service: Shows how to use a community-created MCP service
3. Remote Service with SSE: Demonstrates working with remote MCP services

Each demonstration includes:
- Service initialization
- Tool discovery
- Example queries
- Error handling
- Response processing

Prerequisites:
- Python 3.8+
- DXA framework installed
- Required dependencies (specified in requirements.txt)
"""

import asyncio

from dxa.agent.resource import McpLocalResource, McpRemoteResource
from dxa.agent.resource.base_resource import ResourceResponse
from dxa.common import DXA_LOGGER

# Configure logging
DXA_LOGGER.basicConfig(level=DXA_LOGGER.DEBUG)
logger = DXA_LOGGER.getLogger(__file__.rsplit("/", maxsplit=1)[-1])

# Path to the local echo service script
MCP_SERVICE_SCRIPT = "examples/learning_paths/02_core_concepts/mcp_servers/mcp_echo.py"


async def run_local_server_example():
    """Run the local echo MCP server example

    This example demonstrates:
    1. Creating a local MCP resource
    2. Discovering available tools
    3. Making queries to the service
    4. Handling responses

    The echo service provides two simple tools:
    - ping: Returns "pong" (useful for testing connectivity)
    - echo: Returns the message sent to it
    """
    print("\n========= Starting Local Echo MCP Server Example =========")
    print("Initializing local echo MCP server...")

    # Create a local MCP resource using our custom echo service
    echo = McpLocalResource(
        name="echo",
        connection_params={"command": "python", "args": [MCP_SERVICE_SCRIPT]},
    )

    # Example: Using local echo service
    print("\n=== STEP 1: Discovering Available Tools ===")
    print("Querying available echo service tools...")
    tools = await echo.list_tools()
    print(f"Found {len(tools)} available tools")

    for tool in tools:
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        print("Parameters:")
        for param_name, param_details in tool.inputSchema["properties"].items():
            print(f"  - {param_name}: {param_details.get('type')}")
            if param_details.get("optional"):
                print("    (Optional)")
        print(f"Required parameters: {', '.join(tool.inputSchema['required'])}")

    print("\n=== STEP 2: Testing Echo Server ===")
    print("Testing ping tool...")
    ping_response: ResourceResponse = await echo.query({"tool": "ping"})
    print(f"Ping response: {ping_response.content}")

    print("\nTesting echo tool...")
    echo_response = await echo.query({"tool": "echo", "arguments": {"message": "Hello from local MCP service!"}})
    print(f"Echo response: {echo_response.content}")


async def run_community_server_example():
    """Run the Weather MCP server from community MCP server example

    This example demonstrates:
    1. Using a community-created MCP service
    2. Discovering weather-related tools
    3. Making weather forecast queries
    4. Handling responses and errors

    Note: This example uses a hypothetical weather service.
    In a real implementation, you would use an actual weather service.
    """
    print("\n========= Starting Weather MCP Community Server Example =========")
    print("Initializing weather MCP server...")

    # Create a local MCP resource using a community server
    # This example uses a hypothetical community server
    weather = McpLocalResource(
        name="weather",
        connection_params={
            "command": "npx",
            "args": ["-y", "@h1deya/mcp-server-weather"],
        },
    )

    # Example: Using community server
    print("\n=== STEP 1: Discovering Weather Tools ===")
    print("Querying available weather server tools...")
    tools = await weather.list_tools()
    print(f"Found {len(tools)} available weather tools")

    for tool in tools:
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        print("Parameters:")
        for param_name, param_details in tool.inputSchema["properties"].items():
            print(f"  - {param_name}: {param_details.get('type')}")

    # Example: Using the weather forecast tool
    print("\n=== STEP 2: Testing Weather Server ===")
    try:
        response = await weather.query(
            {
                "tool": "get-forecast",
                "arguments": {"latitude": 37.7749, "longitude": -122.4194},
            }
        )
        print("\nWeather forecast response:")
        print(f"Success: {response.success}")
        if response.success:
            print(f"Forecast data: {response.content}")
        else:
            print(f"Error: {response.error}")
    except Exception as e:
        print(f"Error accessing weather server: {e}")
        print("Note: This example requires the weather MCP service to be installed")


async def run_remote_server_example():
    """Run the remote MCP service example with SSE

    This example demonstrates:
    1. Connecting to a remote MCP server using SSE
    2. Discovering available tools
    3. Executing long-running tasks
    4. Handling SSE events and responses
    5. Error handling for remote connections

    Server-Sent Events (SSE) allow for real-time updates from the server,
    making it ideal for long-running tasks or streaming data.
    """
    print("\n========= Starting Remote MCP Server Example =========")
    print("Initializing remote MCP server with SSE...")

    # Create a remote MCP resource with SSE support
    remote = McpRemoteResource(
        name="remote",
        url="https://mcp.aitomatic.com/weather",
    )

    print("\n=== STEP 1: Discovering Available Tools ===")
    try:
        # First list available tools
        tools = await remote.list_tools()
        print(f"Found {len(tools)} available tools")

        for tool in tools:
            print(f"\nTool: {tool.name}")
            print(f"Description: {tool.description}")
            print("Parameters:")
            for param_name, param_details in tool.inputSchema["properties"].items():
                print(f"  - {param_name}: {param_details.get('type')}")

        print("\n=== STEP 2: Testing Long-Running Task ===")
        # Execute a long-running task with SSE updates
        remote_response = await remote.query(
            {
                "tool": "get_forecast",
                "arguments": {"latitude": 37.7749, "longitude": -122.4194},
            }
        )

        # Handle the response
        print("\nWeather forecast response:")
        print(f"Success: {remote_response.success}")
        if remote_response.success:
            print(f"Forecast data: {remote_response.content}")
        else:
            print(f"Error: {remote_response.error}")

    except ConnectionError as e:
        print(f"\nFailed to connect to remote server: {e}")
        print("Hint: Make sure the MCP server is running and accessible")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Note: This example requires a compatible remote MCP service with SSE support")


async def main():
    """Main function demonstrating MCP resource usage

    This function runs all three examples in sequence:
    1. Local Echo Service
    2. Community Weather Service
    3. Remote Service with SSE

    Each example demonstrates different aspects of working with MCP resources.
    """
    print("========= MCP Resource Examples =========")
    print("This example demonstrates how to use MCP (Model Control Protocol) resources")
    print("Three different types of MCP services will be demonstrated:")
    print("1. Local custom service (Echo)")
    print("2. Community service (Weather)")
    print("3. Remote service with SSE (Weather)")
    print("\nLet's begin...\n")

    # Run local echo service example
    await run_local_server_example()

    # Run community service example
    await run_community_server_example()

    # Run remote service example with SSE
    await run_remote_server_example()


if __name__ == "__main__":
    asyncio.run(main())
