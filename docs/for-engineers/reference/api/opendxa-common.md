# OpenDXA Common Module API Reference

The OpenDXA Common module provides shared functionality used across the OpenDXA framework, including exceptions, resources, mixins, configuration, and utilities.

## Quick Start

```python
# Import the common module
from opendxa.common import DXA_LOGGER, ConfigLoader, LLMResource

# Configure logging
DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG, console=True)

# Load configuration
config = ConfigLoader().get_default_config()

# Create an LLM resource
llm = LLMResource()
```

## Core Components

### Exceptions

Standard exception hierarchy for OpenDXA applications.

#### OpenDXAError

Base class for all OpenDXA exceptions.

```python
from opendxa.common import OpenDXAError

try:
    # OpenDXA operations
    pass
except OpenDXAError as e:
    print(f"OpenDXA error: {e}")
```

#### Specific Exceptions

| Exception | Description | Use Case |
|-----------|-------------|----------|
| `ConfigurationError` | Configuration-related errors | Invalid config files, missing settings |
| `LLMError` | LLM operation failures | API failures, model errors |
| `ResourceError` | Resource access problems | Unavailable resources, connection issues |
| `NetworkError` | Network-related failures | Connection timeouts, HTTP errors |
| `ReasoningError` | AI reasoning failures | Failed inference, invalid prompts |
| `AgentError` | Agent operation failures | Agent initialization, communication issues |
| `ValidationError` | Data validation failures | Invalid inputs, type mismatches |
| `StateError` | State management problems | Invalid state transitions, corrupted data |

**Example:**
```python
from opendxa.common import LLMError, ConfigurationError

try:
    # LLM operation
    result = llm.generate("some prompt")
except LLMError as e:
    print(f"LLM failed: {e}")
except ConfigurationError as e:
    print(f"Configuration problem: {e}")
```

### Resources

#### LLMResource

Interface for Large Language Model operations.

```python
from opendxa.common import LLMResource

# Create LLM resource
llm = LLMResource()

# Generate text
response = llm.generate("Explain machine learning")
print(response)

# With parameters
response = llm.generate(
    "Write a summary",
    max_tokens=100,
    temperature=0.7
)
```

#### MemoryResource

Memory management for agent systems.

```python
from opendxa.common import MemoryResource, STMemoryResource, LTMemoryResource

# Short-term memory
st_memory = STMemoryResource()
st_memory.store("key", "value")
value = st_memory.retrieve("key")

# Long-term memory
lt_memory = LTMemoryResource()
lt_memory.store("permanent_data", {"important": "info"})
```

#### McpResource

Model Context Protocol resource for external tool integration.

```python
from opendxa.common import McpResource, StdioTransportParams

# Create MCP resource with stdio transport
transport_params = StdioTransportParams(
    command="python",
    args=["-m", "mcp_server"]
)

mcp = McpResource(transport_params)

# Call MCP tools
result = mcp.call_tool("search_web", {"query": "OpenDXA"})
```

### Configuration

#### ConfigLoader

Configuration management with standardized loading.

```python
from opendxa.common import ConfigLoader

# Load default configuration
loader = ConfigLoader()
config = loader.get_default_config()

# Load specific configuration file
config = loader.load_config("custom_config.json")

# Configuration search order:
# 1. OPENDXA_CONFIG environment variable
# 2. Current working directory/opendxa_config.json
# 3. Project root/opendxa_config.json
```

**Example Configuration:**
```json
{
    "llm": {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "${OPENAI_API_KEY}"
    },
    "logging": {
        "level": "INFO",
        "console": true
    },
    "resources": {
        "memory_backend": "redis",
        "cache_size": 1000
    }
}
```

### Mixins

Reusable functionality for classes.

#### Loggable

Adds logging capabilities to any class.

```python
from opendxa.common import Loggable

class MyClass(Loggable):
    def __init__(self):
        super().__init__()
    
    def process_data(self, data):
        self.info("Starting data processing")
        self.debug(f"Processing {len(data)} items")
        
        try:
            # Process data
            result = self.transform(data)
            self.info("Data processing completed")
            return result
        except Exception as e:
            self.error(f"Processing failed: {e}")
            raise

# Usage
processor = MyClass()
processor.process_data([1, 2, 3, 4, 5])
```

#### ToolCallable

Enables classes to be called as tools by AI agents.

```python
from opendxa.common import ToolCallable

class Calculator(ToolCallable):
    def add(self, a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

# Register as tool
calc = Calculator()
tool_definition = calc.to_tool_definition()

# Use in agent context
result = calc.call_tool("add", {"a": 5, "b": 3})  # Returns 8
```

#### Configurable

Adds configuration management to classes.

```python
from opendxa.common import Configurable

class ConfigurableService(Configurable):
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        
        # Access configuration
        self.api_url = self.config.get("api_url", "https://default.api.com")
        self.timeout = self.config.get("timeout", 30)
    
    def connect(self):
        self.info(f"Connecting to {self.api_url} with timeout {self.timeout}s")

# Usage
service = ConfigurableService("service_config.json")
service.connect()
```

### Data Types

#### BaseRequest and BaseResponse

Standard request/response patterns.

```python
from opendxa.common import BaseRequest, BaseResponse

# Define request
class AnalysisRequest(BaseRequest):
    data: list
    parameters: dict

# Define response
class AnalysisResponse(BaseResponse):
    results: dict
    confidence: float

# Usage
request = AnalysisRequest(
    data=[1, 2, 3, 4, 5],
    parameters={"method": "statistical"}
)

response = AnalysisResponse(
    results={"mean": 3.0, "std": 1.58},
    confidence=0.95
)
```

### Graph Utilities

Graph data structures and algorithms.

#### DirectedGraph

Graph representation and traversal.

```python
from opendxa.common import DirectedGraph, Node, Edge, BreadthFirstTraversal

# Create graph
graph = DirectedGraph()

# Add nodes
node1 = Node("start", data={"type": "entry"})
node2 = Node("process", data={"type": "operation"})
node3 = Node("end", data={"type": "exit"})

graph.add_node(node1)
graph.add_node(node2)
graph.add_node(node3)

# Add edges
edge1 = Edge(node1, node2, weight=1.0)
edge2 = Edge(node2, node3, weight=2.0)

graph.add_edge(edge1)
graph.add_edge(edge2)

# Traverse graph
traversal = BreadthFirstTraversal()
path = traversal.traverse(graph, start=node1)

for node in path:
    print(f"Visiting: {node.id}")
```

### IO Utilities

Input/output handling for different interfaces.

#### ConsoleIO

Console-based input/output.

```python
from opendxa.common import ConsoleIO

# Create console IO
console = ConsoleIO()

# Get user input
user_input = console.get_input("Enter your name: ")

# Send output
console.send_output(f"Hello, {user_input}!")

# Send formatted data
data = {"name": user_input, "timestamp": "2025-01-24"}
console.send_output(data, format="json")
```

#### WebSocketIO

WebSocket-based communication.

```python
from opendxa.common import WebSocketIO

# Create WebSocket IO
ws_io = WebSocketIO("ws://localhost:8080/chat")

# Handle incoming messages
def handle_message(message):
    print(f"Received: {message}")
    return f"Echo: {message}"

ws_io.set_message_handler(handle_message)

# Send messages
ws_io.send_output("Hello WebSocket!")

# Start listening
ws_io.start()
```

### Database Utilities

Database abstractions and models.

#### MemoryDBStorage

In-memory database storage.

```python
from opendxa.common import MemoryDBStorage, MemoryDBModel

# Define model
class UserModel(MemoryDBModel):
    name: str
    email: str
    age: int

# Create storage
storage = MemoryDBStorage[UserModel]()

# Store data
user = UserModel(name="Alice", email="alice@example.com", age=30)
storage.save(user)

# Query data
users = storage.find({"name": "Alice"})
print(f"Found {len(users)} users")
```

### Logging and Analysis

#### DXALogger

Advanced logging with prefixes and configuration.

```python
from opendxa.common import DXA_LOGGER

# Configure logger
DXA_LOGGER.configure(
    level=DXA_LOGGER.INFO,
    console=True,
    fmt="%(asctime)s - [%(name)s] %(levelname)s - %(message)s"
)

# Use logger
DXA_LOGGER.info("Application started")
DXA_LOGGER.debug("Debug information")
DXA_LOGGER.warning("Warning message")
DXA_LOGGER.error("Error occurred")

# With prefix
logger_with_prefix = DXA_LOGGER.with_prefix("API")
logger_with_prefix.info("Request received")  # Output: [API] Request received
```

#### LLMInteractionAnalyzer

Analyze LLM interactions for performance and patterns.

```python
from opendxa.common import LLMInteractionAnalyzer

# Create analyzer
analyzer = LLMInteractionAnalyzer()

# Record interactions
analyzer.record_interaction(
    prompt="Analyze this data",
    response="Data shows positive trend",
    tokens_used=50,
    response_time=1.2
)

# Get analysis
stats = analyzer.get_statistics()
print(f"Average response time: {stats['avg_response_time']:.2f}s")
print(f"Total tokens used: {stats['total_tokens']}")

# Get recommendations
recommendations = analyzer.get_recommendations()
for rec in recommendations:
    print(f"Recommendation: {rec}")
```

## Usage Patterns

### Resource Management

```python
from opendxa.common import LLMResource, MemoryResource

class AIService:
    def __init__(self):
        self.llm = LLMResource()
        self.memory = MemoryResource()
    
    def process_request(self, user_input: str):
        # Store input in memory
        self.memory.store("last_input", user_input)
        
        # Get context from memory
        context = self.memory.retrieve("conversation_context", default=[])
        
        # Generate response with LLM
        prompt = f"Context: {context}\nUser: {user_input}\nAssistant:"
        response = self.llm.generate(prompt)
        
        # Update context
        context.append({"user": user_input, "assistant": response})
        self.memory.store("conversation_context", context)
        
        return response

# Usage
service = AIService()
response = service.process_request("What is the weather today?")
```

### Error Handling Patterns

```python
from opendxa.common import (
    OpenDXAError, LLMError, ResourceError, NetworkError,
    DXA_LOGGER
)

def robust_ai_operation(prompt: str):
    """Demonstrate robust error handling."""
    try:
        # Attempt LLM operation
        llm = LLMResource()
        result = llm.generate(prompt)
        return result
        
    except LLMError as e:
        DXA_LOGGER.error(f"LLM operation failed: {e}")
        return "Sorry, I'm having trouble processing your request."
        
    except NetworkError as e:
        DXA_LOGGER.error(f"Network error: {e}")
        return "Network connection issue. Please try again."
        
    except ResourceError as e:
        DXA_LOGGER.error(f"Resource unavailable: {e}")
        return "Service temporarily unavailable."
        
    except OpenDXAError as e:
        DXA_LOGGER.error(f"OpenDXA error: {e}")
        return "An unexpected error occurred."

# Usage
response = robust_ai_operation("Explain quantum computing")
print(response)
```

### Configuration Patterns

```python
from opendxa.common import ConfigLoader, Configurable, DXA_LOGGER

class ApplicationService(Configurable):
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        
        # Configure logging from config
        log_level = self.config.get("logging", {}).get("level", "INFO")
        DXA_LOGGER.configure(level=getattr(DXA_LOGGER, log_level))
        
        # Initialize components
        self.setup_resources()
    
    def setup_resources(self):
        llm_config = self.config.get("llm", {})
        self.llm = LLMResource(
            provider=llm_config.get("provider", "openai"),
            model=llm_config.get("model", "gpt-4")
        )
        
        memory_config = self.config.get("memory", {})
        self.memory = MemoryResource(
            backend=memory_config.get("backend", "local"),
            cache_size=memory_config.get("cache_size", 1000)
        )

# Usage
app = ApplicationService("app_config.json")
```

### Tool Integration

```python
from opendxa.common import ToolCallable, Loggable

class WeatherService(ToolCallable, Loggable):
    """Weather service that can be used as an AI tool."""
    
    def get_weather(self, location: str) -> dict:
        """Get current weather for a location.
        
        Args:
            location: The city or location name
            
        Returns:
            Weather information dictionary
        """
        self.info(f"Getting weather for {location}")
        
        # Simulate weather API call
        weather_data = {
            "location": location,
            "temperature": 22,
            "condition": "sunny",
            "humidity": 65
        }
        
        return weather_data
    
    def get_forecast(self, location: str, days: int = 5) -> list:
        """Get weather forecast for multiple days.
        
        Args:
            location: The city or location name
            days: Number of days to forecast
            
        Returns:
            List of daily forecasts
        """
        self.info(f"Getting {days}-day forecast for {location}")
        
        # Simulate forecast data
        forecast = []
        for day in range(days):
            forecast.append({
                "day": day + 1,
                "temperature": 20 + day,
                "condition": "partly cloudy"
            })
        
        return forecast

# Usage as tool
weather = WeatherService()

# Get tool definition for AI agent
tool_def = weather.to_tool_definition()

# Use directly
current_weather = weather.get_weather("San Francisco")
forecast = weather.get_forecast("San Francisco", 3)
```

## Integration Examples

### FastAPI Application

```python
from fastapi import FastAPI, HTTPException
from opendxa.common import (
    ConfigLoader, LLMResource, DXA_LOGGER,
    OpenDXAError, LLMError
)

app = FastAPI()

# Global configuration and resources
config = ConfigLoader().get_default_config()
DXA_LOGGER.configure(level=DXA_LOGGER.INFO, console=True)
llm = LLMResource()

@app.post("/analyze")
async def analyze_text(text: str):
    """Analyze text using LLM."""
    try:
        DXA_LOGGER.info(f"Analyzing text: {text[:50]}...")
        
        result = llm.generate(f"Analyze this text: {text}")
        
        return {
            "success": True,
            "analysis": result,
            "text_length": len(text)
        }
        
    except LLMError as e:
        DXA_LOGGER.error(f"LLM analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")
        
    except OpenDXAError as e:
        DXA_LOGGER.error(f"OpenDXA error: {e}")
        raise HTTPException(status_code=500, detail="Service error")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "config_loaded": config is not None,
        "llm_available": llm is not None
    }
```

### Agent Class Example

```python
from opendxa.common import (
    Loggable, Configurable, ToolCallable,
    LLMResource, MemoryResource
)

class IntelligentAgent(Loggable, Configurable, ToolCallable):
    """Example of a complete agent using OpenDXA common components."""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        
        # Initialize resources
        self.llm = LLMResource()
        self.memory = MemoryResource()
        
        # Agent configuration
        self.agent_name = self.config.get("agent_name", "Assistant")
        self.max_memory_items = self.config.get("max_memory_items", 100)
        
        self.info(f"Agent {self.agent_name} initialized")
    
    def process(self, user_input: str) -> str:
        """Process user input and generate response."""
        self.debug(f"Processing input: {user_input}")
        
        # Retrieve relevant memories
        memories = self.memory.search(user_input, limit=5)
        context = "\n".join([m["content"] for m in memories])
        
        # Generate response with context
        prompt = f"""
        Agent: {self.agent_name}
        Context: {context}
        User: {user_input}
        
        Provide a helpful response:
        """
        
        response = self.llm.generate(prompt)
        
        # Store interaction in memory
        self.memory.store("interaction", {
            "user_input": user_input,
            "response": response,
            "timestamp": "2025-01-24T10:00:00Z"
        })
        
        self.info("Response generated successfully")
        return response
    
    def search_memory(self, query: str, limit: int = 10) -> list:
        """Search memory for relevant information.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of relevant memory items
        """
        return self.memory.search(query, limit=limit)
    
    def clear_memory(self) -> None:
        """Clear agent memory."""
        self.memory.clear()
        self.info("Memory cleared")

# Usage
agent = IntelligentAgent("agent_config.json")

# Process user input
response = agent.process("What's the weather like?")
print(response)

# Search memory
memories = agent.search_memory("weather")
print(f"Found {len(memories)} relevant memories")
```

## Error Handling Guide

### Exception Hierarchy

```
OpenDXAError
├── ConfigurationError
├── LLMError
├── ResourceError
├── NetworkError
├── WebSocketError
├── ReasoningError
├── AgentError
├── CommunicationError
├── ValidationError
├── StateError
├── DXAMemoryError
└── DXAContextError
```

### Best Practices

1. **Catch Specific Exceptions:** Always catch the most specific exception first
2. **Log Errors:** Use DXA_LOGGER to log errors with appropriate levels
3. **Graceful Degradation:** Provide fallback behavior when possible
4. **User-Friendly Messages:** Convert technical errors to user-friendly messages

```python
from opendxa.common import *

def resilient_operation():
    """Example of resilient error handling."""
    try:
        # Primary operation
        result = primary_llm_operation()
        return result
        
    except LLMError as e:
        DXA_LOGGER.warning(f"Primary LLM failed, trying fallback: {e}")
        try:
            # Fallback operation
            return fallback_operation()
        except Exception as fallback_error:
            DXA_LOGGER.error(f"Fallback also failed: {fallback_error}")
            raise LLMError("All LLM operations failed")
            
    except NetworkError as e:
        DXA_LOGGER.error(f"Network error: {e}")
        return "Network connection unavailable"
        
    except OpenDXAError as e:
        DXA_LOGGER.error(f"OpenDXA error: {e}")
        raise
```

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 