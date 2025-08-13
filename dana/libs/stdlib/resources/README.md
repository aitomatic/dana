# Dana Pluggable Resource System

The Dana resource system now supports a pluggable architecture that allows resources to be defined and loaded from multiple sources.

## Architecture Overview

### Core Components

1. **dana/core/resource/** - Core resource system
   - `BaseResource` - Base class all resources inherit from
   - `ResourceRegistry` - Manages resource instances and lifecycles
   - `ResourceLoader` - Discovers and loads resource plugins
   - `ResourceContextIntegrator` - Integrates with Dana runtime

2. **dana/libs/stdlib/resources/** - Standard library resources
   - Dana (.na) resource implementations
   - Python (.py) resource implementations
   - Automatically discovered and loaded at startup

3. **User Resources** - Custom user-defined resources
   - Can be loaded from any directory in DANAPATH
   - Can be registered at runtime via API

## Resource Sources

Resources can come from three sources:

### 1. Built-in Resources (Python)
Located in `dana/core/resource/standard_blueprints.py`:
- MCPResource
- RAGResource
- KnowledgeResource
- HumanResource
- CodingResource
- FinancialStatementTools
- FinancialStatementRAGResource

### 2. Stdlib Resources
Located in `dana/libs/stdlib/resources/`:
- **simple_cache.na** - In-memory cache resource (Dana)
- **webhook_resource.na** - Webhook endpoint resource (Dana)
- **sql_resource.py** - SQL database resource (Python)

### 3. User Resources
Loaded from:
- Directories in DANAPATH environment variable
- Directories added via `add_resource_search_path()`
- Registered at runtime via `register_resource()`

## Creating New Resources

### Dana Resource (.na file)

```dana
# my_resource.na
resource MyCustomResource:
    kind: str = "custom"
    name: str = ""
    state: str = "created"
    config_value: str = "default"
    
def (resource: MyCustomResource) initialize() -> bool:
    resource.state = "initialized"
    return true
    
def (resource: MyCustomResource) start() -> bool:
    resource.state = "running"
    return true
    
def (resource: MyCustomResource) query(request: str) -> str:
    if resource.state != "running":
        return f"Resource not running"
    return f"Processing: {request}"
    
def (resource: MyCustomResource) stop() -> bool:
    resource.state = "terminated"
    return true
```

### Python Resource (.py file)

```python
# my_resource.py
from dana.core.resource import BaseResource

class MyCustomResource(BaseResource):
    kind = "custom"
    
    def initialize(self):
        self.state = self.state.__class__.RUNNING
        return True
    
    def query(self, request):
        if not self.is_running():
            return {"error": "Resource not running"}
        return {"result": f"Processing: {request}"}
```

## Using Resources in Dana

### Basic Usage

```dana
# Create resource instance
cache = SimpleCacheResource(name="my_cache", max_size=1000)

# Initialize and start
cache.initialize()
cache.start()

# Use the resource
result = cache.query("set:key1:value1")
print(result)

value = cache.query("get:key1")
print(value)

# Stop when done
cache.stop()
```

### With Agents (Future)

```dana
agent DataProcessor:
    name: str = "DataProcessor"
    
def (agent: DataProcessor) process(data: str) -> str:
    # Future: Use agent.use() method
    cache = SimpleCacheResource(name="agent_cache")
    cache.start()
    
    # Cache the result
    cache.query(f"set:data:{data}")
    
    return f"Processed and cached: {data}"
```

## Runtime Resource Registration

### Register a Factory Function

```dana
from dana.core.resource.resource_helpers import register_resource

def create_my_resource(name: str, kind: str, **kwargs):
    # Create custom resource
    resource = {
        "name": name,
        "kind": kind,
        "state": "created"
    }
    return resource

# Register the factory
register_resource("my_type", "my_kind", create_my_resource, {
    "description": "My custom resource type"
})
```

### Register a Python Class

```python
from dana.core.resource import BaseResource
from dana.core.resource.resource_helpers import register_resource_class

class MyResource(BaseResource):
    kind = "my_kind"
    
    def query(self, request):
        return f"Response: {request}"

# Register the class
register_resource_class(MyResource, {"description": "My resource"})
```

### Add Custom Search Paths

```dana
from dana.core.resource.resource_helpers import add_resource_search_path

# Add project-specific resources
add_resource_search_path("/my/project/resources")

# Reload to pick up new resources
from dana.core.resource.resource_helpers import reload_resources
reload_resources()
```

## Resource Discovery

The ResourceLoader automatically discovers resources in this order:

1. Load built-in Python resources from `standard_blueprints.py`
2. Scan `dana/libs/stdlib/resources/` for .na and .py files
3. Scan directories in DANAPATH environment variable
4. Load any programmatically registered resources

## Environment Configuration

### DANAPATH

Set the DANAPATH environment variable to add custom resource directories:

```bash
export DANAPATH="/path/to/my/resources:/another/path/resources"
```

Each directory in DANAPATH should have a `resources/` subdirectory containing resource files.

## Helper Functions

The `dana.core.resource.resource_helpers` module provides:

- `register_resource()` - Register a factory function
- `register_resource_class()` - Register a Python class
- `add_resource_search_path()` - Add a search directory
- `reload_resources()` - Reload all resources from disk
- `list_available_resources()` - List all registered resources
- `get_resource_stats()` - Get resource system statistics

## Best Practices

1. **Naming**: Use descriptive names for resource kinds (e.g., "cache", "webhook", "sql")
2. **State Management**: Always check resource state before operations
3. **Lifecycle**: Properly initialize, start, and stop resources
4. **Error Handling**: Return meaningful error messages when resources aren't available
5. **Documentation**: Include docstrings and comments in resource implementations
6. **Testing**: Test resources independently before integration

## Examples

See the example implementations in `dana/libs/stdlib/resources/`:
- `simple_cache.na` - Shows basic Dana resource structure
- `webhook_resource.na` - Demonstrates more complex state management
- `sql_resource.py` - Example of Python resource with external dependencies

## Future Enhancements

- Agent `.use()` method integration
- Resource dependency management
- Resource versioning and compatibility
- Resource marketplace/registry
- Hot-reloading of resource definitions
- Resource composition and inheritance in Dana