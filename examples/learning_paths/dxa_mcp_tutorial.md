# DXA Framework: Model Control Protocol (MCP) Tutorial

This tutorial will guide you through setting up and using the Model Control Protocol (MCP) in the DXA framework. MCP allows you to create server-client architectures that enable your agents to interact with external services and tools.

## 1. Installation and Setup

### 1.1 Clone the Repository

First, clone the DXA repository to your local machine:

```bash
git clone https://github.com/aitomatic/dxa.git
cd dxa
```

### 1.2 Set Up the Environment

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
An MCP server is a Python class that extends `BaseMcpService` and implements methods that are decorated as tools. These tools become available for clients to call remotely. Let's break down the key components:




#### Key Components of an MCP Server

1. **BaseMcpService**: The base class that provides the MCP protocol implementation
2. **Tool Decorator**: The `@BaseMcpService.tool` decorator that exposes methods as callable tools
3. **Tool Methods**: Methods that implement the functionality of your server
4. **Server Runner**: Code that initializes and runs the server

#### Best Practices for Tool Design

When designing tools for your MCP server:

- Use clear, descriptive names for tools
- Provide detailed docstrings and descriptions
- Define proper type annotations for parameters and return values
- Implement robust error handling
- Keep tools focused on a single responsibility

Create a new Python file named `my_mcp_server.py` with the following code:

```python
"""A simple MCP server that provides basic tools."""

from dxa.agent.resource.mcp.mcp_services import BaseMcpService

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

#### Anatomy of an MCP Tool

Each tool in your MCP server follows this pattern:

```python
@BaseMcpService.tool(name="tool_name", description="Tool description")
def tool_name(self, param1: type1, param2: type2, ...) -> return_type:
    """Detailed docstring explaining what the tool does."""
    # Tool implementation
    return result
```

### 2.2 Run the Server

To run your MCP server, execute the Python script:

```bash
python my_mcp_server.py
```

The server will start and display information about available tools. Keep this terminal window open as the server needs to be running for clients to connect to it.

### 2.3 MCP Server examples
- [mcp_echo.py](examples/learning_paths/02_core_concepts/mcp_servers/mcp_echo.py)
- [mcp_sqlite.py](examples/learning_paths/02_core_concepts/mcp_servers/mcp_sqlite.py)

## 3. Creating an MCP Client

Now that we have an MCP server running, let's create a client to interact with it.

### 3.1 Create a Client Script

Connecting to an MCP server requires setting up a client that can establish communication, discover available tools, and make requests. Here are the essential components for connecting to an MCP server:

#### Connection Requirements

1. **MCP Resource Object**: Create an `McpLocalResource` or `McpRemoteResource` object depending on whether the server is local or remote
2. **Connection Parameters**: Specify how to connect to the server

#### Connection Parameters

For local MCP servers, you need to provide:
- **Command**: The executable to run (usually `python`)
- **Args**: Command-line arguments, including the server script path
- **Environment Variables**: Optional environment variables for the server process

For remote MCP servers, you need:
- **URL**: The endpoint of the remote MCP server
- **Authentication**: Optional authentication credentials if required


Create a new Python file named `my_mcp_client.py` with the following code:

```python
"""A simple MCP client that interacts with our server."""

import asyncio
from dxa.agent.resource import McpLocalResource

async def main():
    """Run the MCP client to interact with our server."""
    print("Starting MCP Client...")
    
    # Create a local MCP resource that connects to our server
    mcp_resource = McpLocalResource(
        name="my_server",
        connection_params={
            "command": "python", 
            "args": ["my_mcp_server.py"]
        },
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

#### Error Handling

Handle potential errors that may occur during MCP communication:

```python
try:
    response = await mcp_resource.query({
        "tool": "add", 
        "arguments": {"a": 5, "b": 7}
    })
    print(f"Result: {response.content}")
except Exception as e:
    print(f"Error querying MCP server: {e}")
```

#### Remote MCP Servers

For connecting to remote MCP servers:

```python
from dxa.agent.resource import McpRemoteResource

remote_resource = McpRemoteResource(
    name="remote_calculator",
    url="https://example.com/mcp/calculator"
)
await remote_resource.initialize()
```

### 3.2 Run the Client

In a new terminal window (while keeping the server running), activate your virtual environment and run the client:

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python my_mcp_client.py
```

You should see the client discover the available tools on the server and execute them, displaying the results.

### 3.3 MCP Client Example
- [06_mcp_resource.py](examples/learning_paths/02_core_concepts/06_mcp_resource.py)

## 4. Using MCP in Real Scenarios

Now let's explore how to use MCP in a real agent-based application. We'll create a simple agent that uses our MCP server to perform operations.

### 4.1 Create an Agent Application

Create a file named `my_agent_app.py` with the following code:

```python
""""An agent application that uses MCP resources."""

from dxa.agent import Agent
from dxa.agent.resource import McpLocalResource


def main():
    """Run an agent that uses MCP resources."""
    print("Starting Agent Application...")
    # Set up our MCP resource
    mcp_resource = McpLocalResource(
        name="calculator",
        connection_params={
            "command": "python", 
            "args": ["my_mcp_server.py"]
        },
    )
    
    
    # Create an agent
    agent = Agent(name="mcp_agent")
    # Set up an LLM resource (required for agent operations)
    agent.with_llm({"model": "openai:gpt-4o-mini", "temperature": 0.7, "max_tokens": 1000})
    # Add the MCP resource to the agent
    agent.with_resources({mcp_resource.name: mcp_resource})
    
    # Example 1: Simple calculation query
    print("\nExample 1: Simple Calculation")
    result = agent.ask("What is 15 + 27?")
    print(f"Calculation result: {result}")
    
    print("\nAgent operations completed successfully.")

if __name__ == "__main__":
    main()
```

### 4.2 Run the Agent Application

In a terminal window (while keeping the server running), run the agent application:

```bash
python my_agent_app.py
```

### 4.3 Example
- [07_resource_selection.py](examples/learning_paths/02_core_concepts/07_resource_selection.py)


## Conclusion

You've now learned how to create and use MCP servers and clients in the DXA framework. This powerful pattern allows you to extend your agents with custom tools and services, enabling more complex and specialized capabilities.