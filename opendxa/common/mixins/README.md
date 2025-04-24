<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# OpenDXA Mixins

OpenDXA's mixins provide a powerful and flexible way to add specific "abilities" to classes in a light yet principled manner. These mixins follow a consistent naming pattern ending in "-able" to indicate the capability they add to a class.

## Overview

Mixins in OpenDXA are designed to:
- Add specific capabilities to classes without complex inheritance hierarchies
- Provide consistent interfaces for common functionality
- Enable composition of capabilities through multiple inheritance
- Maintain clean separation of concerns
- Follow the principle of least surprise with standardized patterns

## Available Mixins

### Loggable
The foundation mixin that provides standardized logging capabilities across OpenDXA. It automatically configures a logger with appropriate naming and formatting.

### Configurable
Adds configuration management capabilities, including:
- YAML file loading with defaults and overrides
- Configuration validation
- Path resolution for config files
- Configuration access methods

### ToolCallable
Enables objects to be called as tools within the tool-calling ecosystem, providing a standardized interface for tool execution.

### Queryable
Adds query capabilities to objects, allowing them to be both queried directly and called as tools. Inherits from ToolCallable.

### Registerable
Provides registration capabilities for components that need to be discoverable and accessible by name.

### Identifiable
Adds unique identification capabilities to objects, enabling tracking and referencing of specific instances.

## Mixin Hierarchy

```mermaid
classDiagram
    direction BT
    class Configurable {
        +debug()
        +info()
        +warning()
        +error()
        +get()
        +set()
        +update()
        +to_dict()
        +save()
        +load_config()
        +get_prompt()
    }

    class Queryable {
        +tool()
        +query()
        +get_query_strategy()
        +get_query_max_iterations()
    }

    class Loggable {
        +debug()
        +info()
        +warning()
        +error()
    }

    class ToolCallable {
        +@tool
        +tool()
        +can_handle()
        +list_tools()
    }

    class Registerable {
        +register()
        +unregister()
        +get_registered()
    }

    class Identifiable {
        +name
        +id
        +description
        +get_id()
        +set_id()
    }

    class BaseResource {
        +name
        +description
        +initialize()
        +cleanup()
        +query()
    }

    class McpResource {
        +name
        +description
        +transport_type
        +query()
        +list_tools()
        +call_tool()
    }

    Loggable <|-- Configurable
    ToolCallable <|-- Queryable
    Configurable <|-- BaseResource
    Queryable <|-- BaseResource
    BaseResource <|-- McpResource
```

## Usage Example

```python
from opendxa.common.mixins import Loggable, Configurable, Queryable

class MyComponent(Loggable, Configurable, Queryable):
    def __init__(self, config_path=None, **overrides):
        super().__init__(config_path=config_path, **overrides)
        
    async def query(self, params=None):
        self.info("Processing query with params: %s", params)
        return QueryResponse(success=True, content=params)
```

## Best Practices

1. **Order Matters**: When using multiple mixins, list them in order of dependency (most dependent last)
2. **Minimal Inheritance**: Use only the mixins you need to avoid unnecessary complexity
3. **Consistent Initialization**: Always call `super().__init__()` to ensure proper mixin initialization
4. **Clear Documentation**: Document which mixins are used and why in class docstrings

## License

OpenDXA is released under the [MIT License](../../../LICENSE.md). 