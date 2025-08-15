<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

| [← Infrastructure](./infrastructure.md) | [IO System →](./io.md) |
|---|---|

# Resource System Specification

**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 2.0.0  
**Status:** Implementation

This specification defines the pluggable resource architecture for Dana, including the core resource system, plugin mechanisms, and extension points.

Resources represent concrete tools, services, data sources, or interfaces (like LLMs, databases, APIs, human input) that agent capabilities can access.

For detailed explanations and usage examples, please refer to the **[Resource System Primer](../../../docs/primers/resource.md)**.

## Architecture Overview

The resource system follows a pluggable architecture with three layers:

### 1. Core Resource System (`dana.core.resource`)

The foundation providing base classes and essential infrastructure:

- **`BaseResource`**: Abstract base class defining the standard resource interface
- **`ResourceRegistry`**: Manages resource instances and lifecycles
- **`ResourceLoader`**: Discovers and loads resource plugins from multiple sources
- **`ResourceHandle`**: Enables resource transfer between agents
- **`ResourceContextIntegrator`**: Integrates resources with the Dana runtime

### 2. Plugin Sources

Resources can be loaded from three sources:

#### Core Resources (`dana.core.resource.plugins`)
Essential Python implementations that serve as reference implementations:
- `MCPResource` - Model Context Protocol client
- `BaseLLMResource` - Base LLM integration resource

These core resources are minimal and provide fallback options when Dana implementations aren't feasible.

#### Standard Library Resources (`dana.libs.stdlib.resources`)
Resources implemented in Dana (.na) or Python (.py):
- Automatically discovered at startup
- Can be extended without modifying core code
- Examples: RAG, knowledge, human, cache, webhook, SQL resources

#### User Resources
Custom resources loaded from:
- Directories in `DANAPATH` environment variable
- Paths added via `add_resource_search_path()`
- Runtime registration via `register_resource()`

### 3. Runtime Integration

Resources integrate with Dana's runtime through:
- Agent context validation (resources only accessible within agents)
- Lifecycle management (initialize, start, stop, cleanup)
- Standard query interface for uniform access
- Resource transfer via handles

## Core Components

### BaseResource

The abstract base class all resources inherit from:

```python
@dataclass
class BaseResource:
    # Core metadata
    kind: str = "base"
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    domain: str = "general"
    
    # Runtime state
    state: ResourceState = ResourceState.CREATED
    owner_agent: str = ""
    
    # Standard interface methods
    def initialize(self) -> bool
    def cleanup(self) -> bool
    def query(self, request: BaseRequest) -> BaseResponse
    def start(self) -> bool
    def stop(self) -> bool
    def is_running(self) -> bool
    def get_metadata(self) -> Dict[str, Any]
```

### ResourceLoader

Discovers and loads resource plugins:

```python
class ResourceLoader:
    def load_builtin_resources()  # Load Python blueprints
    def load_stdlib_resources()   # Load from stdlib/resources
    def register_user_resource()  # Runtime registration
    def add_search_path()         # Add custom directories
    def create_resource_instance() # Factory for instances
```

### ResourceRegistry

Manages resource instances with enhanced plugin support:

```python
class ResourceRegistry:
    def register_blueprint()  # Register Python classes
    def register_factory()    # Register factory functions
    def create_resource()     # Create instances
    def list_available_kinds() # List all resource types
    def get_plugin_metadata() # Get plugin information
```

## Plugin Development

### Dana Resource Pattern (.na files)

```dana
resource MyResource:
    kind: str = "my_type"
    name: str = ""
    state: str = "created"
    config: dict = {}
    
def (resource: MyResource) initialize() -> bool:
    resource.state = "initialized"
    return true
    
def (resource: MyResource) query(request: str) -> str:
    if resource.state != "running":
        return "Resource not available"
    return f"Processing: {request}"
```

### Python Resource Pattern (.py files)

```python
from dana.core.resource import BaseResource

class MyResource(BaseResource):
    kind = "my_type"
    
    def initialize(self):
        self.state = ResourceState.RUNNING
        return True
    
    def query(self, request):
        if not self.is_running():
            return {"error": "Not running"}
        return {"result": f"Processing: {request}"}
```

## Resource Discovery

The ResourceLoader follows this discovery sequence:

1. **Core Plugins**: Load from `dana/core/resource/plugins/`
2. **Standard Library**: Scan `dana/libs/stdlib/resources/`
3. **DANAPATH**: Search directories in environment variable
4. **Custom Paths**: Search programmatically added paths
5. **Runtime Registration**: Load dynamically registered resources

## Helper Functions

The `dana.core.resource.resource_helpers` module provides utilities:

- `register_resource()` - Register factory function
- `register_resource_class()` - Register Python class
- `add_resource_search_path()` - Add search directory
- `reload_resources()` - Reload from disk
- `list_available_resources()` - List all resources
- `get_resource_stats()` - System statistics

## Configuration

### Environment Variables

- `DANAPATH`: Colon-separated directories to search for resources
  ```bash
  export DANAPATH="/project/resources:/home/user/dana-resources"
  ```

### Directory Structure

Resource directories should follow this structure:
```
my-project/
  resources/
    cache_resource.na      # Dana implementation
    database_resource.py   # Python implementation
    __init__.py           # Optional initialization
```

## Security Model

### Agent-Only Access

Resources enforce agent-only access through:
- Context validation before any resource operation
- Ownership tracking per resource instance
- Transfer authorization between agents

### Resource Isolation

Each resource instance is:
- Owned by a single agent at a time
- Isolated from other resource instances
- Transferable only by the owning agent

## Lifecycle Management

Resources follow a defined lifecycle:

1. **DEFINED**: Type registered but not instantiated
2. **CREATED**: Instance created, not initialized
3. **INITIALIZED**: Resources allocated, not started
4. **RUNNING**: Active and available for use
5. **SUSPENDED**: Temporarily unavailable
6. **TERMINATED**: Permanently shut down

## Best Practices

### Resource Implementation

1. **State Management**: Always validate state before operations
2. **Error Handling**: Return meaningful errors for invalid states
3. **Initialization**: Allocate resources in `initialize()`, not constructor
4. **Cleanup**: Release resources properly in `cleanup()`
5. **Query Interface**: Implement standard `query()` for uniform access

### Plugin Development

1. **Naming**: Use descriptive, unique resource kinds
2. **Documentation**: Include docstrings and usage examples
3. **Dependencies**: Declare external dependencies clearly
4. **Testing**: Test resources independently before integration
5. **Versioning**: Use semantic versioning for compatibility

## Future Enhancements

- Agent `.use()` method for resource access
- Resource dependency management
- Hot-reloading during development
- Resource composition and inheritance
- Resource marketplace/registry
- Performance monitoring and metrics

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../../../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
