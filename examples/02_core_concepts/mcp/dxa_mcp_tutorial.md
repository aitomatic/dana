# DXA Framework: Model Control Protocol (MCP) Tutorial

## Introduction to MCP

[The Model Control Protocol (MCP)](https://modelcontextprotocol.io/introduction) in the DXA framework is a powerful feature that enables your agents to interact with external services and tools through a standardized server-client architecture. MCP provides a flexible way to extend your agent's capabilities by allowing them to communicate with custom services running as separate processes.

This tutorial will guide you through setting up and using the Model Control Protocol (MCP) in the DXA framework.

## 1. Installation and Setup

### 1.1 Clone the Repository

First, clone the DXA repository to your local machine:

```bash
git clone https://github.com/aitomatic/dxa.git
cd dxa
```

### 1.2 Set Up the Environment

Before running the setup script, ensure you have the following prerequisites installed:

1. **Python 3.12+** - The DXA framework requires Python 3.12 or newer
   ```bash
   python --version  # Should show Python 3.12.x or higher
   ```

2. **Git** - For cloning the repository
   ```bash
   git --version  # Verify git is installed
   ```

3. **Pip** - Python package manager (usually comes with Python)
   ```bash
   pip --version  # Verify pip is installed
   ```

Run the setup script to create a virtual environment and install dependencies:

```bash
# Set up development environment
bash setup_env.sh

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 1.3 Set Up Environment Variables

The DXA framework requires certain environment variables to be set, especially for LLM services. Create a `.env` file in the root directory with the following variables:

```bash
# Required for LLM functionality
OPENAI_API_KEY=your_openai_api_key_here

# Optional alternative providers
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# MCP configuration (optional)
# Logging Configuration (Optional)
LOG_LEVEL=INFO                          # Optional: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

Make sure to replace the placeholder values with your actual API keys. At minimum, you'll need an OpenAI API key for the LLM functionality.

### 1.4 Install Package in Development Mode

Install the DXA package in development mode to make it available in your environment:

```bash
pip install -e .
```


## 2. Creating an MCP Server

MCP servers provide tools that can be called by clients. Let's create a simple echo server to demonstrate the basics.

### 2.1 Create a Server File
**An MCP server is a Python class that extends `BaseMcpService` and implements methods that are decorated as tools**. These tools become available for clients to call remotely.

Create a new Python file named `my_mcp_server.py` with the following code:

```python
"""A simple MCP server that provides basic tools."""

from dxa.agent.resource.mcp import BaseMcpService

class MyMcpServer(BaseMcpService):
    """Simple MCP server implementation with basic tools."""
    
    @BaseMcpService.tool(name="add", description="Add two numbers together")
    def add(self, a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b

if __name__ == "__main__":
    # Start the server
    print("Starting MCP Server...")
    MyMcpServer().run()
```


#### Key Components of an MCP Server

1. **BaseMcpService**: The base class that provides the MCP protocol implementation
2. **Tool Decorator**: The `@BaseMcpService.tool` decorator that exposes methods as mcp tools
3. **Tool Methods**: Methods that implement the functionality of your server
4. **Server Runner**: Code that initializes and runs the server

#### Best Practices for Tool Design

When designing tools for your MCP server:

- Use clear, descriptive names for tools
- Provide detailed docstrings and descriptions
- Define proper type annotations for parameters and return values
- Implement robust error handling
- Keep tools focused on a single responsibility

### 2.3 MCP Server examples
- [mcp_echo.py](./02_core_concepts/mcp_servers/mcp_echo.py)
- [mcp_sqlite.py](./02_core_concepts/mcp_servers/mcp_sqlite.py)

## 3. Creating an MCP Client

Now that we have an MCP server running, let's create a client to interact with it.

### 3.1 Create a Client Script

Here are the essential components for connecting to an MCP server:

#### Connection Requirements

1. **MCP Resource Object**: Create a custom resource class that extends `McpResource`
2. **Connection Parameters**: Specify how to connect to the server

#### Connection Parameters

For local MCP (stdio) servers, you need to provide:
- **Transport Type**: The type of transport to use (STDIO for local, HTTP for remote)
- **Command**: The executable to run (usually `python`)
- **Args**: Command-line arguments, including the server script path
- **Environment Variables**: Optional environment variables for the server process

Create a new Python file named `my_mcp_client.py` with the following code:

```python
"""A simple MCP client that interacts with our server."""

import asyncio
from dxa.agent.resource.mcp import McpResource, McpTransportType, McpConnectionParams

async def main():
    """Run the MCP client to interact with our server."""
    print("Starting MCP Client...")
    
    # Create a local MCP resource that connects to our server
    mcp_resource = McpResource(
        name="my_mcp_resource",
        connection_params=McpConnectionParams(
            transport_type=McpTransportType.STDIO,
            command="python", 
            args=["/path/to/my_mcp_server.py"]
        ),
    )
    
    # Initialize the connection
    await mcp_resource.initialize()
    
    # Discover available tools
    print("\nDiscovering available tools...")
    tools = await mcp_resource.list_tools()
    print(f"Found {len(tools)} tools:")
    
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
        print(f"    Parameters: {', '.join(tool.inputSchema.get('required', []))}")
    
    # Use the add tool
    print("\nTesting add tool...")
    add_response = await mcp_resource.query({
        "tool": "add", 
        "arguments": {"a": 5, "b": 7}
    })
    print(f"Add response: {add_response.content}")
    
    print("\nMCP client operations completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
```

#### Query Structure

When calling an MCP tool, you need to specify:
1. **Tool name**: The name of the tool to call
2. **Arguments**: A dictionary of arguments matching the tool's expected parameters

```python
response = await mcp_resource.query({
    "tool": "tool_name",
    "arguments": {
        "param1": value1,
        "param2": value2
    }
})
```

### 3.2 Remote MCP Servers

For remote MCP servers using HTTP transport, you need to provide different connection parameters:

```python
# Create a remote MCP resource
remote_resource = McpResource(
    name="remote_mcp_resource",
    connection_params=McpConnectionParams(
        transport_type=McpTransportType.HTTP,
        url="https://mcp.example.com",
        timeout=5.0,
        headers={"Authorization": "Bearer your-token"}
    ),
)
```

The key differences for remote servers are:
- Use `McpTransportType.HTTP` for transport type
- Provide a URL instead of command and args
- Optionally specify timeout and headers
- No need for environment variables

### 3.3 Error Handling

Always implement proper error handling when working with MCP resources:

```python
try:
    response = await mcp_resource.query({
        "tool": "tool_name",
        "arguments": {"param": "value"}
    })
    if response.success:
        print(f"Tool execution successful: {response.content}")
    else:
        print(f"Tool execution failed: {response.error}")
except Exception as e:
    print(f"Error occurred: {e}")
```

## 4. Advanced MCP Features

### 4.1 Tool Discovery

MCP provides a way to discover available tools at runtime:

```python
# List all available tools
tools = await mcp_resource.list_tools()
for tool in tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print("Parameters:")
    for param_name, param_details in tool.inputSchema["properties"].items():
        print(f"  - {param_name}: {param_details.get('type')}")
```

### 4.2 Tool Schema Validation

MCP automatically validates tool arguments against their schemas:

```python
# This will fail if the arguments don't match the schema
try:
    response = await mcp_resource.query({
        "tool": "add",
        "arguments": {"a": "not a number", "b": 7}  # Will fail validation
    })
except Exception as e:
    print(f"Validation error: {e}")
```

### 4.3 Environment Variables

You can pass environment variables to local MCP servers:

```python
mcp_resource = McpResource(
    name="my_mcp_resource",
    connection_params=McpConnectionParams(
        transport_type=McpTransportType.STDIO,
        command="python",
        args=["/path/to/my_mcp_server.py"],
        env={"MY_VAR": "my_value"}
    ),
)
```

## 5. Best Practices

1. **Server Design**
   - Keep servers focused on specific functionality
   - Implement proper error handling
   - Use type hints and docstrings
   - Follow the single responsibility principle

2. **Client Usage**
   - Always initialize resources before use
   - Implement proper error handling
   - Use appropriate timeouts for remote servers
   - Validate tool arguments before calling

3. **Security**
   - Use HTTPS for remote servers
   - Implement proper authentication
   - Validate all inputs
   - Use environment variables for sensitive data

4. **Performance**
   - Keep tool implementations efficient
   - Use appropriate timeouts
   - Implement connection pooling for remote servers
   - Cache tool results when appropriate

## 6. Troubleshooting

Common issues and solutions:

1. **Connection Issues**
   - Check server is running
   - Verify connection parameters
   - Check network connectivity for remote servers
   - Verify environment variables

2. **Tool Execution Errors**
   - Check tool arguments match schema
   - Verify server implementation
   - Check server logs
   - Validate input data

3. **Performance Issues**
   - Check server resource usage
   - Verify network connectivity
   - Implement caching if appropriate
   - Use connection pooling

## 7. Next Steps

1. Explore the example MCP servers in the codebase
2. Create your own MCP server for specific functionality
3. Integrate MCP resources into your agents
4. Implement advanced features like streaming and batching

## 8. Additional Resources

- [MCP Specification](https://modelcontextprotocol.io/specification)
- [DXA Documentation](https://dxa.docs.aitomatic.com)
- [Example MCP Servers](https://github.com/aitomatic/dxa/tree/main/examples)
- [Community Resources](https://community.aitomatic.com)