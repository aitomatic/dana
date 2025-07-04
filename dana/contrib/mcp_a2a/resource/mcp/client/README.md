# Enhanced MCPClient Implementation

This directory contains an enhanced implementation of the Model Context Protocol (MCP) client that automatically detects and initializes appropriate transport mechanisms based on the provided arguments.

## Overview

The `MCPClient` class inherits from `fastmcp.Client` and provides intelligent transport detection and initialization. It meets the following requirements:

- ✅ **Receive any kind of arguments**: Accepts URLs, file paths, FastMCP instances, MCP configs, and more
- ✅ **Identify SSE or Streamable HTTP**: Automatically detects transport type based on URL patterns  
- ✅ **Initialize transport correctly**: Creates and configures the appropriate transport instance

## Key Features

### 1. Automatic Transport Detection

The client automatically detects the appropriate transport based on input arguments:

```python
from mcp_client import MCPClient

# FastMCP server instance → FastMCPTransport
server = FastMCP("MyServer")
client = MCPClient(server)

# SSE URL patterns → SSETransport  
client = MCPClient("https://example.com/sse")
client = MCPClient("https://api.com/events")

# HTTP URL patterns → StreamableHttpTransport
client = MCPClient("https://example.com/mcp")
client = MCPClient("https://api.com/rpc")

# File paths → StdioTransport
client = MCPClient("server.py")
client = MCPClient("handler.js")

# MCP configuration → MCPConfigTransport
config = {"mcpServers": {"server1": {"url": "https://example.com/mcp"}}}
client = MCPClient(config)
```

### 2. Explicit Transport Override

You can explicitly specify the transport type when automatic detection isn't sufficient:

```python
# Force SSE transport for a URL that would normally use HTTP
client = MCPClient("https://example.com/api", transport_type="sse")

# Force HTTP transport for a URL that would normally use SSE
client = MCPClient("https://example.com/sse", transport_type="streamable-http")

# Force stdio transport
client = MCPClient("my_command", transport_type="stdio")
```

### 3. Transport Information and Utilities

The client provides methods to inspect the current transport:

```python
client = MCPClient("https://example.com/mcp")

# Get detailed transport information
info = client.get_transport_info()
print(info)
# {
#   "transport_class": "StreamableHttpTransport",
#   "transport_type": "Streamable HTTP", 
#   "url": "https://example.com/mcp"
# }

# Check transport type
assert client.is_http_transport()
assert not client.is_sse_transport()
assert not client.is_stdio_transport()
assert not client.is_fastmcp_transport()
```

## Transport Detection Logic

### URL Pattern Detection

The client uses regex patterns to identify transport types from URLs:

**SSE Transport Patterns:**
- `/sse` or `/sse/`
- `/events` or `/events/`
- `/stream` or `/stream/`
- Paths ending with `-sse`
- Paths ending with `.sse`

**Streamable HTTP Transport Patterns:**
- `/mcp` or `/mcp/`
- `/api` or `/api/`
- `/rpc` or `/rpc/`
- Paths ending with `-mcp`
- Paths ending with `.mcp`
- **Default for unknown URL patterns** (aligns with FastMCP 2.3.0+ behavior)

### File Path Detection

For file paths, the client detects the appropriate interpreter:

- `.py` files → `python` command
- `.js`, `.mjs` files → `node` command  
- `.ts` files → `tsx` command (fallback to `ts-node`)
- Other files → treated as executable commands

### Argument Type Detection

The detection follows this priority order:

1. **FastMCP/FastMCP1Server instances** → `FastMCPTransport`
2. **MCP configuration dicts** → `MCPConfigTransport`
3. **URL strings** → SSE or HTTP based on patterns
4. **File path strings** → `StdioTransport`
5. **Fallback** → Use fastmcp's built-in inference

## Usage Examples

### Basic Usage

```python
import asyncio
from mcp_client import MCPClient

async def main():
    # Connect to an HTTP MCP server
    client = MCPClient("https://api.example.com/mcp")
    
    async with client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Call a tool
        result = await client.call_tool("my_tool", {"param": "value"})
        print(f"Result: {result[0].text}")
        
        # Read a resource
        resource = await client.read_resource("data://example")
        print(f"Resource: {resource[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Multi-Server Configuration

```python
# Connect to multiple MCP servers through a single client
config = {
    "mcpServers": {
        "weather": {
            "url": "https://weather-api.example.com/mcp",
            "transport": "streamable-http"
        },
        "calendar": {
            "url": "https://calendar-api.example.com/sse", 
            "transport": "sse"
        }
    }
}

client = MCPClient(config)

async with client:
    # Access tools from different servers with prefixes
    weather = await client.call_tool("weather_get_forecast", {"city": "London"})
    event = await client.call_tool("calendar_create_event", {"title": "Meeting"})
```

### Testing with FastMCP

```python
from fastmcp import FastMCP

# Create a test server
server = FastMCP("TestServer")

@server.tool()
def echo(message: str) -> str:
    return f"Echo: {message}"

# Connect client directly to server instance (in-memory)
client = MCPClient(server)

async with client:
    result = await client.call_tool("echo", {"message": "Hello"})
    print(result[0].text)  # "Echo: Hello"
```

## Error Handling

The client provides clear error messages for common issues:

```python
try:
    # Invalid transport type
    client = MCPClient("https://example.com", transport_type="invalid")
except ValueError as e:
    print(f"Error: {e}")  # "Unknown transport type: invalid"

try:
    # Incompatible argument and transport type
    client = MCPClient(123, transport_type="sse")
except ValueError as e:
    print(f"Error: {e}")  # "SSE transport requires URL string, got <class 'int'>"

try:
    # Nonexistent file
    client = MCPClient("/nonexistent/file.py")
except ValueError as e:
    print(f"Error: {e}")  # "File does not exist: /nonexistent/file.py"
```

## Files in this Directory

- **`mcp_client.py`** - Main MCPClient implementation
- **`examples/mcp_client_examples.py`** - Comprehensive usage examples
- **`tests/test_mcp_client.py`** - Unit tests covering all functionality
- **`README.md`** - This documentation file

## Running Examples and Tests

### Run Examples

```bash
cd opendxa/contrib/mcp_a2a/common/resource/mcp/client/examples
python mcp_client_examples.py
```

### Run Tests

```bash
cd opendxa/contrib/mcp_a2a/common/resource/mcp/client
pytest tests/test_mcp_client.py -v
```

## Dependencies

The implementation requires:

- `fastmcp` - FastMCP library with transport implementations
- `mcp` - Official MCP Python SDK (for FastMCP 1.0 compatibility)
- `pydantic` - For URL validation
- `pathlib` - For file path handling

## Integration with Dana

This enhanced MCPClient is designed to integrate seamlessly with the Dana framework as part of the MCP/A2A protocol support. It provides a robust foundation for:

1. **Resource Integration** - MCP servers as Dana resources
2. **Protocol Federation** - Connecting different MCP implementations  
3. **Development Testing** - Easy testing with in-memory FastMCP servers
4. **Production Deployment** - Robust HTTP-based connections

## References

- [FastMCP Documentation](https://gofastmcp.com/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Transport Documentation](https://gofastmcp.com/clients/transports)
- [Dana MCP/A2A Integration Design](../../../../../../../../docs/designs/mcp-a2a-resources.md) 