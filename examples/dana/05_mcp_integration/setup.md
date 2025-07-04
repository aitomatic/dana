# DANA MCP Testing Setup Guide

This guide will help you set up and test DANA's Model Context Protocol (MCP) integration using the provided test servers and examples.

## Overview

This directory contains:
- **Two MCP test servers**: SSE and HTTP Streamable transports
- **DANA test scripts**: Examples showing how to use MCP resources in DANA
- **Testing tools**: Basic MCP tools for connectivity and functionality testing

## Prerequisites

### 1. Python Environment
- Python 3.8 or higher
- pip package manager

### 2. Required Dependencies
Install the FastMCP library:
```bash
pip install fastmcp
```

### 3. DANA Language Support
Ensure you have DANA interpreter/runtime installed and configured.

## Available Test Servers

### 1. SSE (Server-Sent Events) MCP Server
**File**: `start_sse_server.py`
**Port**: 8080
**Endpoint**: `http://localhost:8080/sse`

### 2. HTTP Streamable MCP Server
**File**: `start_http_streamable_server.py`
**Port**: 8081
**Endpoint**: `http://localhost:8081/mcp`

Both servers provide the same three test tools:
- **echo**: Echo messages back for basic connectivity testing
- **ping**: Test server connectivity with timestamped response
- **get_current_time**: Get current system timestamp

## Setup Instructions

### Step 1: Install Dependencies
```bash
# Navigate to the project root
cd /path/to/dana

# Install FastMCP
pip install fastmcp
```

### Step 2: Start a Test Server

#### Option A: Start SSE Server
```bash
python examples/dana/mcp/start_sse_server.py
```
This will start the server on `http://localhost:8080/sse`

#### Option B: Start HTTP Streamable Server
```bash
python examples/dana/mcp/start_http_streamable_server.py
```
This will start the server on `http://localhost:8081/mcp`

### Step 3: Verify Server is Running
You should see output similar to:
```
🚀 Starting DANA Test SSE MCP Server...
📡 Server will be available at: http://localhost:8080/sse
🔧 Available tools:
   - echo: Echo messages back
   - ping: Test connectivity
   - get_current_time: Get current timestamp

🔄 To test with DANA, use an MCP resource with SSE transport:
   HttpTransportParams(url='http://localhost:8080/sse')

Press Ctrl+C to stop the server
------------------------------------------------------------
```

## Testing with DANA

### Basic Usage Pattern
Use the provided DANA test scripts in the `na/` directory:

#### 1. Simple Use Statement (`test_use_stmt.na`)
```dana
sse_mcp = use("mcp", url="http://localhost:8080/sse")
http_mcp = use("mcp", url="http://localhost:8080/sse")

print(sse_mcp.list_openai_functions())
print(http_mcp.list_openai_functions())
```

#### 2. With Statement Pattern (`test_with_stmt.na`)
```dana
with use("mcp", url="http://localhost:8080/sse") as sse_mcp:
    print(sse_mcp.list_openai_functions())
    
with use("mcp", url="http://localhost:8080/sse") as http_mcp:
    print(http_mcp.list_openai_functions())

# The statements below should NOT work (outside of with block)
print(sse_mcp.list_openai_functions())  # Should fail
print(http_mcp.list_openai_functions()) # Should fail
```

### Running DANA Tests
```bash
# Navigate to the MCP directory
cd examples/dana/mcp

# Run the basic use statement test
dana na/test_use_stmt.na

# Run the with statement test
dana na/test_with_stmt.na
```

## Manual Testing

### 1. Test Server Connectivity
Once a server is running, you can test the MCP tools:

```dana
# Connect to the MCP server
mcp_client = use("mcp", url="http://localhost:8080/sse")

# Test basic connectivity
result = mcp_client.call_tool("ping")
print(result)

# Echo test
echo_result = mcp_client.call_tool("echo", {"message": "Hello, MCP!"})
print(echo_result)

# Get current time
time_result = mcp_client.call_tool("get_current_time")
print(time_result)
```

### 2. List Available Functions
```dana
mcp_client = use("mcp", url="http://localhost:8080/sse")
functions = mcp_client.list_openai_functions()
print(functions)
```

## Troubleshooting

### Common Issues

#### 1. Server Won't Start
- **Error**: `ModuleNotFoundError: No module named 'fastmcp'`
- **Solution**: Install FastMCP: `pip install fastmcp`

#### 2. Port Already in Use
- **Error**: `[Errno 48] Address already in use`
- **Solution**: 
  - Kill existing process using the port
  - Or modify the port number in the server script

#### 3. Connection Refused
- **Error**: Connection refused when connecting from DANA
- **Solution**: 
  - Ensure the server is running
  - Check that the URL matches the server endpoint
  - Verify firewall settings

#### 4. DANA Cannot Find MCP Resource
- **Error**: Unknown resource type 'mcp'
- **Solution**: Ensure DANA has MCP support enabled and properly configured

### Debugging Tips

1. **Check Server Logs**: The server outputs detailed logs including tool calls and errors
2. **Verify URLs**: Ensure the URL in DANA matches the server endpoint exactly
3. **Test Step by Step**: Start with simple ping/echo tests before complex operations
4. **Check Network**: Ensure localhost connections are not blocked

## Advanced Configuration

### Custom Port Configuration
To use different ports, modify the server scripts:

```python
# In start_sse_server.py
mcp.run(transport="sse", port=YOUR_PORT)

# In start_http_streamable_server.py  
mcp.run(transport="streamable-http", port=YOUR_PORT)
```

### Adding Custom Tools
Extend the servers by adding new MCP tools:

```python
@mcp.tool()
def your_custom_tool(param: str) -> str:
    """Your custom tool description."""
    return f"Custom response: {param}"
```

### Multiple Server Setup
Run both servers simultaneously for testing different transport methods:

```bash
# Terminal 1
python examples/dana/mcp/start_sse_server.py

# Terminal 2  
python examples/dana/mcp/start_http_streamable_server.py
```

## Next Steps

After successful setup:
1. **Explore Tool Integration**: Add more sophisticated MCP tools
2. **Test Error Handling**: Verify error scenarios and edge cases
3. **Performance Testing**: Test with multiple concurrent connections
4. **Custom Transport**: Experiment with different MCP transport mechanisms

## Support

If you encounter issues not covered in this guide:
1. Check the FastMCP documentation
2. Review DANA MCP integration documentation
3. Verify your Python and DANA versions meet requirements
4. Check for updated dependencies
