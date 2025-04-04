"""MCP Resource Example

This example demonstrates how to use MCP (Model Control Protocol) resources in the DXA framework.
MCP resources allow you to integrate external services and tools into your agents.

Key concepts demonstrated:
1. Creating and using local custom MCP servers
2. Accessing community-created MCP servers
3. Using Server-Sent Events (SSE) for remote MCP servers

What you'll learn:
1. How to create and run a local MCP server
2. How to discover and use available tools from MCP services
3. How to handle responses and errors from MCP services
4. How to integrate community MCP services
5. How to work with remote MCP services using SSE

The example includes three main demonstrations:
1. Local Echo Server: A simple echo server that demonstrates basic MCP functionality
2. Community Weather Server: Shows how to use a community-created MCP server
3. Remote Server with SSE: Demonstrates working with remote MCP services

Each demonstration includes:
- Server initialization
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
from pathlib import Path

from dxa.agent.resource import McpLocalResource, McpRemoteResource
from dxa.agent.resource.base_resource import ResourceResponse
from dxa.common import DXA_LOGGER

# Configure logging
DXA_LOGGER.basicConfig(level=DXA_LOGGER.DEBUG)
logger = DXA_LOGGER.getLogger(__file__.rsplit("/", maxsplit=1)[-1])

# Path to the local echo server script
MCP_ECHO_SERVER_SCRIPT = "examples/learning_paths/02_core_concepts/mcp_servers/mcp_echo.py"
MCP_SQLITE_SERVER_SCRIPT = "examples/learning_paths/02_core_concepts/mcp_servers/mcp_sqlite.py"


async def run_local_server_example():
    """Run the local echo MCP server example

    This example demonstrates:
    1. Creating a local MCP resource
    2. Discovering available tools
    3. Making queries to the server
    4. Handling responses

    The echo server provides two simple tools:
    - ping: Returns "pong" (useful for testing connectivity)
    - echo: Returns the message sent to it
    """
    print("\n========= Starting Local Echo MCP Server Example =========")
    print("Initializing local echo MCP server...")

    # Create a local MCP resource using our custom echo server
    echo = McpLocalResource(
        name="echo",
        connection_params={"command": "python", "args": [MCP_ECHO_SERVER_SCRIPT]},
    )

    # Example: Using local echo server
    print("\n=== STEP 1: Discovering Available Tools ===")
    print("Querying available echo server tools...")
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
    echo_response = await echo.query({"tool": "echo", "arguments": {"message": "Hello from local MCP server!"}})
    print(f"Echo response: {echo_response.content}")


async def run_local_sqlite_server_example():
    """Run the local sqlite MCP server example

    This example demonstrates:
    1. Creating a local MCP resource
    2. Discovering available tools
    3. Making queries to the server
    4. Handling responses

    The sqlite server provides the following tools:
    - read_query: Execute a SELECT query on the SQLite database
    - write_query: Execute an INSERT, UPDATE, or DELETE query on the SQLite database
    - create_table: Create a new table in the SQLite database
    - list_tables: List all tables in the SQLite database
    - describe_table: Get the schema information for a specific table
    - append_insight: Add a business insight to the memo
    """
    print("\n========= Starting Local SQLite MCP Server Example =========")
    print("Initializing local sqlite MCP server...")

    # Create a local MCP resource using our custom sqlite server
    sqlite_resource = McpLocalResource(
        name="sqlite",
        connection_params={"command": "python", "args": [MCP_SQLITE_SERVER_SCRIPT]},
        env={"SQLITE_DB_PATH": str(Path(MCP_SQLITE_SERVER_SCRIPT).parent / "mcp_sqlite.db")},
    )

    # Example: Using local sqlite server
    print("\n=== STEP 1: Discovering Available Tools ===")
    print("Querying available sqlite server tools...")
    tools = await sqlite_resource.list_tools()
    print(f"Found {len(tools)} available sqlite server tools")

    for tool in tools:
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        print("Parameters:")
        for param_name, param_details in tool.inputSchema["properties"].items():
            print(f"  - {param_name}: {param_details.get('type')}")

    print("\n=== STEP 2: Testing SQLite Server ===")
    print("Creating a test table...")
    create_table_response = await sqlite_resource.query(
        {
            "tool": "create_table",
            "arguments": {
                "query": """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            },
        }
    )
    print(f"Create table response: {create_table_response.content}")

    print("\nListing available tables...")
    list_tables_response = await sqlite_resource.query({"tool": "list_tables"})
    print(f"Tables in database: {list_tables_response.content}")

    print("\nDescribing users table schema...")
    describe_table_response = await sqlite_resource.query(
        {"tool": "describe_table", "arguments": {"table_name": "users"}}
    )
    print(f"Users table schema: {describe_table_response.content}")

    print("\n=== STEP 3: Testing Write & Read Query ===")
    print("Inserting test data into users table...")
    insert_data_response = await sqlite_resource.query(
        {
            "tool": "write_query",
            "arguments": {
                "query": """
                INSERT INTO users (name, email) VALUES 
                ('Alice', 'alice@example.com'),
                ('Bob', 'bob@example.com'),
                ('Charlie', 'charlie@example.com')
                """
            },
        }
    )
    print(f"Insert data response: {insert_data_response.content}")

    print("\nListing all users...")
    list_users_response = await sqlite_resource.query(
        {"tool": "read_query", "arguments": {"query": "SELECT * FROM users"}}
    )
    print(f"Users in database: {list_users_response.content}")

    print("\n=== STEP 4: Testing Delete Query ===")
    print("Deleting user 'Bob' from users table...")
    delete_response = await sqlite_resource.query(
        {
            "tool": "write_query",
            "arguments": {"query": "DELETE FROM users"},
        }
    )
    print(f"Delete response: {delete_response.content}")

    print("\nVerifying deletion by listing remaining users...")
    remaining_users_response = await sqlite_resource.query(
        {"tool": "read_query", "arguments": {"query": "SELECT * FROM users"}}
    )
    print(f"Remaining users in database: {remaining_users_response.content}")


async def run_community_server_example():
    """Run the Weather MCP server from community MCP server example

    This example demonstrates:
    1. Using a community-created MCP server
    2. Discovering weather-related tools
    3. Making weather forecast queries
    4. Handling responses and errors

    Note: This example uses a hypothetical weather server.
    In a real implementation, you would use an actual weather server.
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
        print("Note: This example requires the weather MCP server to be installed")


async def run_remote_server_example():
    """Run the remote MCP server example with SSE

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
        print("Note: This example requires a compatible remote MCP server with SSE support")


async def main():
    """Main function demonstrating MCP resource usage

    This function runs all three examples in sequence:
    1. Local Echo Server
    2. Community Weather Server
    3. Remote Server with SSE

    Each example demonstrates different aspects of working with MCP resources.
    """
    print("========= MCP Resource Examples =========")
    print("This example demonstrates how to use MCP (Model Control Protocol) resources")
    print("Three different types of MCP services will be demonstrated:")
    print("1. Local custom server (Echo)")
    print("2. Community server (Weather)")
    print("3. Remote server with SSE (Weather)")
    print("\nLet's begin...\n")

    # Run local echo server example
    await run_local_server_example()

    # Run local sqlite server example
    await run_local_sqlite_server_example()

    # Run community server example
    await run_community_server_example()

    # Run remote server example with SSE
    await run_remote_server_example()


if __name__ == "__main__":
    asyncio.run(main())
