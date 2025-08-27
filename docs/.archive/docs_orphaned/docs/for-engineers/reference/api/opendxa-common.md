# Dana Common Module API Reference

## Overview

The Dana Common module provides shared functionality used across the Dana framework, including exceptions, resources, mixins, configuration, and utilities.

## Quick Start

```python
from opendxa.common import DXA_LOGGER, ConfigLoader, LLMResource

# Configure logging
DXA_LOGGER.configure(level=DXA_LOGGER.INFO)

# Load configuration
config = ConfigLoader().get_default_config()

# Create resources
llm = LLMResource()
```

## Exceptions

Standard exception hierarchy for Dana applications.

### DanaError

Base class for all Dana exceptions.

```python
from opendxa.common import OpenDXAError

try:
    # Dana operations
    result = some_dana_operation()
except OpenDXAError as e:
    print(f"Dana error: {e}")
```

### Specific Exceptions

```python
from opendxa.common import LLMError, ConfigurationError

# LLM-specific errors
try:
    llm_response = llm.generate("Hello")
except LLMError as e:
    print(f"LLM error: {e}")

# Configuration errors
try:
    config = ConfigLoader().load_config("invalid_path")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Resources

### LLMResource

Main interface for LLM interactions.

```python
from opendxa.common import LLMResource

llm = LLMResource()
response = llm.generate("What is machine learning?")
```

### Memory Resources

Short-term and long-term memory management.

```python
from opendxa.common import MemoryResource, STMemoryResource, LTMemoryResource

# Short-term memory (session-based)
st_memory = STMemoryResource()
st_memory.store("user_preference", "dark_mode")

# Long-term memory (persistent)
lt_memory = LTMemoryResource()
lt_memory.store("user_profile", {"name": "Alice", "preferences": {}})
```

### MCP Resources

Model Context Protocol integration.

```python
from opendxa.common import McpResource, StdioTransportParams

# MCP resource with stdio transport
mcp = McpResource(StdioTransportParams(command="mcp-server"))
result = mcp.call_tool("search_web", {"query": "Dana"})
```

### Configuration Management

```python
from opendxa.common import ConfigLoader

# Load configuration
config = ConfigLoader().load_config("config.yaml")

# Access configuration values
api_key = config.get("llm.api_key")
model = config.get("llm.model", "gpt-4")
```

## Mixins

### Loggable

Add logging capabilities to any class.

```python
from opendxa.common import Loggable

class MyClass(Loggable):
    def __init__(self):
        super().__init__()
        self.info("MyClass initialized")
    
    def process_data(self, data):
        self.debug(f"Processing {len(data)} items")
        # Process data
        self.info("Data processing complete")
```

### ToolCallable

Make classes callable as tools.

```python
from opendxa.common import ToolCallable

class DataProcessor(ToolCallable):
    def __init__(self):
        super().__init__()
    
    def get_tools(self):
        return {
            "process_data": self.process_data,
            "analyze_data": self.analyze_data
        }
    
    def process_data(self, data):
        return {"processed": data}
```

### Configurable

Add configuration management to classes.

```python
from opendxa.common import Configurable

class MyService(Configurable):
    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = self.get_config("api_key")
        self.endpoint = self.get_config("endpoint", "https://api.example.com")
```

## Data Structures

### Request/Response Models

```python
from opendxa.common import BaseRequest, BaseResponse

class CustomRequest(BaseRequest):
    def __init__(self, data: dict):
        super().__init__()
        self.data = data

class CustomResponse(BaseResponse):
    def __init__(self, result: any, success: bool = True):
        super().__init__()
        self.result = result
        self.success = success
```

### Graph Structures

```python
from opendxa.common import DirectedGraph, Node, Edge, BreadthFirstTraversal

# Create a directed graph
graph = DirectedGraph()

# Add nodes
node1 = Node("A", {"value": 1})
node2 = Node("B", {"value": 2})
graph.add_node(node1)
graph.add_node(node2)

# Add edge
edge = Edge(node1, node2, {"weight": 1.0})
graph.add_edge(edge)

# Traverse graph
traversal = BreadthFirstTraversal(graph)
for node in traversal.traverse(node1):
    print(f"Visited: {node.id}")
```

## I/O Utilities

### Console I/O

```python
from opendxa.common import ConsoleIO

console = ConsoleIO()
user_input = console.read("Enter your name: ")
console.write(f"Hello, {user_input}!")
```

### WebSocket I/O

```python
from opendxa.common import WebSocketIO

ws = WebSocketIO("ws://localhost:8080")
ws.connect()
ws.send({"message": "Hello"})
response = ws.receive()
```

## Database Utilities

```python
from opendxa.common import MemoryDBStorage, MemoryDBModel

# In-memory database
db = MemoryDBStorage()

# Define model
class User(MemoryDBModel):
    def __init__(self, name: str, email: str):
        super().__init__()
        self.name = name
        self.email = email

# Store and retrieve
user = User("Alice", "alice@example.com")
db.store("users", user)
retrieved_user = db.retrieve("users", user.id)
```

## Logging

### DXALogger

Advanced logging with configuration.

```python
from opendxa.common import DXA_LOGGER

# Configure logger
DXA_LOGGER.configure(
    level=DXA_LOGGER.INFO,
    console=True,
    file="app.log"
)

# Use logger
DXA_LOGGER.info("Application started")
DXA_LOGGER.error("An error occurred")
```

### LLM Interaction Analysis

```python
from opendxa.common import LLMInteractionAnalyzer

analyzer = LLMInteractionAnalyzer()
interaction = analyzer.analyze(prompt, response)
print(f"Tokens used: {interaction.token_count}")
print(f"Cost: ${interaction.cost}")
```

## Resource Management

### Resource Lifecycle

```python
from opendxa.common import LLMResource, MemoryResource

# Resource lifecycle
llm = LLMResource()
llm.initialize()
try:
    response = llm.generate("Hello")
finally:
    llm.cleanup()
```

## Error Handling Patterns

### Comprehensive Error Handling

```python
from opendxa.common import (
    OpenDXAError, LLMError, ResourceError, NetworkError,
    ConfigurationError, ValidationError
)

try:
    # Dana operations
    result = perform_operation()
except LLMError as e:
    DXA_LOGGER.error(f"LLM error: {e}")
    # Handle LLM-specific errors
except ResourceError as e:
    DXA_LOGGER.error(f"Resource error: {e}")
    # Handle resource errors
except OpenDXAError as e:
    DXA_LOGGER.error(f"Dana error: {e}")
    # Handle general Dana errors
```

### Configuration Error Handling

```python
from opendxa.common import ConfigLoader, Configurable, DXA_LOGGER

try:
    config = ConfigLoader().load_config("config.yaml")
    service = MyService(config)
except ConfigurationError as e:
    DXA_LOGGER.error(f"Configuration error: {e}")
    # Use default configuration
    service = MyService()
```

## Integration Examples

### Complete Application Example

```python
from opendxa.common import ToolCallable, Loggable

class DataAnalysisService(ToolCallable, Loggable):
    """Example of a complete agent using Dana common components."""
    
    def __init__(self, config=None):
        super().__init__()
        self.llm = LLMResource()
        self.memory = MemoryResource()
        
    def get_tools(self):
        return {
            "analyze_data": self.analyze_data,
            "store_result": self.store_result,
            "retrieve_history": self.retrieve_history
        }
    
    def analyze_data(self, data: list) -> dict:
        """Analyze data using LLM."""
        self.info(f"Analyzing {len(data)} data points")
        
        prompt = f"Analyze this data: {data}"
        response = self.llm.generate(prompt)
        
        result = {
            "data": data,
            "analysis": response,
            "timestamp": datetime.now().isoformat()
        }
        
        self.store_result(result)
        return result
    
    def store_result(self, result: dict):
        """Store analysis result in memory."""
        self.memory.store("analysis_results", result)
        self.info("Result stored in memory")
    
    def retrieve_history(self) -> list:
        """Retrieve analysis history."""
        return self.memory.retrieve_all("analysis_results")

# Usage
service = DataAnalysisService()
result = service.analyze_data([1, 2, 3, 4, 5])
```

## Best Practices

### Resource Management

```python
# Always clean up resources
try:
    resource = SomeResource()
    result = resource.process()
finally:
    resource.cleanup()
```

### Error Handling

```python
# Use specific exception types
try:
    result = operation()
except SpecificError as e:
    # Handle specific error
    pass
except OpenDXAError as e:
    # Handle general error
    pass
```

### Configuration

```python
# Use configuration with defaults
config = ConfigLoader().load_config("config.yaml")
api_key = config.get("api_key", "default_key")
timeout = config.get("timeout", 30)
```

### Logging

```python
# Use appropriate log levels
DXA_LOGGER.debug("Detailed debug information")
DXA_LOGGER.info("General information")
DXA_LOGGER.warning("Warning message")
DXA_LOGGER.error("Error message")
```

## API Reference

### Exceptions

| Exception | Purpose | When Raised |
|-----------|---------|-------------|
| OpenDXAError | Base exception | General Dana errors |
| LLMError | LLM operations | LLM API failures |
| ResourceError | Resource operations | Resource failures |
| NetworkError | Network operations | Network failures |
| ConfigurationError | Configuration | Invalid configuration |
| ValidationError | Data validation | Invalid data |

### Resources

| Resource | Purpose | Key Methods |
|----------|---------|-------------|
| LLMResource | LLM interactions | `generate()`, `chat()` |
| MemoryResource | Memory management | `store()`, `retrieve()` |
| McpResource | MCP integration | `call_tool()`, `list_tools()` |

### Mixins

| Mixin | Purpose | Key Features |
|-------|---------|--------------|
| Loggable | Logging | `info()`, `error()`, `debug()` |
| ToolCallable | Tool interface | `get_tools()`, `call_tool()` |
| Configurable | Configuration | `get_config()`, `set_config()` |

## Migration Guide

### From Custom Implementations

```python
# Before: Custom logging
import logging
logger = logging.getLogger(__name__)
logger.info("Message")

# After: Dana logging
from opendxa.common import Loggable
class MyClass(Loggable):
    def method(self):
        self.info("Message")
```

### From Direct LLM Calls

```python
# Before: Direct API calls
import openai
response = openai.ChatCompletion.create(...)

# After: Dana LLM resource
from opendxa.common import LLMResource
llm = LLMResource()
response = llm.generate("Hello")
```

---

*For more information, see the [Dana Framework Documentation](../README.md) or [API Reference](../README.md).* 