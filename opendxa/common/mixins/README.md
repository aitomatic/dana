<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../../README.md) | [Main Documentation](../../../docs/README.md) | [Mixins Architecture](../../../docs/core-concepts/mixins.md)

# Mixins Module Implementation (`opendxa.common.mixins`)

This module provides the implementation of reusable mixin classes that add common capabilities to OpenDXA components through multiple inheritance.

> **Note:** For conceptual information about the mixin architecture, design philosophy, and usage patterns, please see the [Mixins Architecture Documentation](../../../docs/core-concepts/mixins.md).

## Implementation Details

### Available Mixins

| Mixin | File | Purpose | Dependencies |
|-------|------|---------|--------------|
| `Loggable` | `loggable.py` | Standardized logging | None |
| `Identifiable` | `identifiable.py` | Object identification | None |
| `Configurable` | `configurable.py` | Configuration management | None |
| `Registerable` | `registerable.py` | Registration in registries | `Identifiable` |
| `ToolCallable` | `tool_callable.py` | Tool calling interface | `Registerable`, `Loggable` |
| `Queryable` | `queryable.py` | Query interface | `ToolCallable` |
| `Capable` | `capable.py` | Capability management | None |

### Class Initialization Order

When implementing a class that uses multiple mixins, initialize them in the following order:

```python
def __init__(self):
    # Base mixins first
    Loggable.__init__(self)
    Identifiable.__init__(self)
    Configurable.__init__(self)
    
    # Dependent mixins next
    Registerable.__init__(self)
    
    # Most dependent mixins last
    ToolCallable.__init__(self)
    Queryable.__init__(self)
    
    # Custom initialization last
    # ...your code...
```

## API Reference

### Loggable

```python
class Loggable:
    def __init__(self, logger_name=None, prefix=None)
    def debug(self, msg, *args, **kwargs)
    def info(self, msg, *args, **kwargs)
    def warning(self, msg, *args, **kwargs)
    def error(self, msg, *args, **kwargs)
    @classmethod
    def get_class_logger(cls)
```

#### Parameters

- `logger_name`: Optional custom logger name
- `prefix`: Optional prefix for log messages

### Identifiable

```python
class Identifiable:
    def __init__(self, id=None, name=None, description=None)
    def get_id(self)
    def set_id(self, id)
    def get_name(self)
    def set_name(self, name)
    def get_description(self)
    def set_description(self, description)
```

#### Parameters

- `id`: Optional unique identifier (auto-generated if None)
- `name`: Optional human-readable name
- `description`: Optional description of the object

### Configurable

```python
class Configurable:
    def __init__(self, config=None, config_path=None)
    def get(self, key, default=None)
    def set(self, key, value)
    def update(self, config_dict)
    def to_dict(self)
    def save(self, path=None)
    def load_config(self, path)
    def get_prompt(self, prompt_key, default=None)
```

#### Parameters

- `config`: Optional initial configuration dictionary
- `config_path`: Optional path to configuration file

### Registerable

```python
class Registerable(Identifiable):
    def __init__(self, id=None, name=None, description=None, registry=None)
    def register(self, registry=None)
    def unregister(self, registry=None)
    @classmethod
    def get_registered(cls, registry=None)
```

#### Parameters

- `id`, `name`, `description`: From Identifiable
- `registry`: Optional registry to register with

### ToolCallable

```python
class ToolCallable(Registerable, Loggable):
    def __init__(self, id=None, name=None, description=None, registry=None)
    def tool(self, **kwargs)
    def can_handle(self, tool_name)
    def list_tools(self)
```

#### Parameters

- `id`, `name`, `description`, `registry`: From Registerable

### Queryable

```python
class Queryable(ToolCallable):
    def __init__(self, id=None, name=None, description=None, registry=None, 
                 query_strategy='default', query_max_iterations=3)
    def query(self, query_input, **kwargs)
    def get_query_strategy(self)
    def get_query_max_iterations(self)
```

#### Parameters

- `id`, `name`, `description`, `registry`: From ToolCallable
- `query_strategy`: Strategy to use for query processing
- `query_max_iterations`: Maximum iterations for query attempts

### Capable

```python
class Capable:
    def __init__(self)
    def add_capability(self, capability)
    def remove_capability(self, capability_id)
    def has_capability(self, capability_id)
    def get_capability(self, capability_id)
    def list_capabilities(self)
```

## Implementation Examples

### Complete Agent Implementation

```python
from opendxa.common.mixins import Configurable, Loggable, ToolCallable
from opendxa.base.capability import Capable

class CompleteAgent(Configurable, Loggable, Capable, ToolCallable):
    def __init__(self, config=None, id=None, name="Agent", description="A complete agent"):
        # Initialize all mixins
        Configurable.__init__(self, config)
        Loggable.__init__(self)
        Capable.__init__(self)
        ToolCallable.__init__(self, id, name, description)
        
        # Agent-specific initialization
        self.initialize()
    
    def initialize(self):
        """Agent-specific initialization logic."""
        self.debug("Initializing agent...")
        # Load capabilities, connect resources, etc.
    
    @ToolCallable.tool(description="Run a simple task")
    def run_task(self, task_input):
        """Example tool method."""
        self.info(f"Running task with input: {task_input}")
        return {"status": "complete", "result": f"Processed {task_input}"}
```

### Simple Resource with Configuration and Logging

```python
from opendxa.common.mixins import Configurable, Loggable

class SimpleResource(Configurable, Loggable):
    def __init__(self, config_path="resource_config.yaml"):
        Configurable.__init__(self, config_path=config_path)
        Loggable.__init__(self)
        
        self.resource_url = self.get("resource_url", "default_url")
        self.debug(f"Initialized resource with URL: {self.resource_url}")
    
    def connect(self):
        self.info("Connecting to resource...")
        # Connection logic here
```

For more complex examples and advanced usage patterns, please refer to the test files in `tests/common/mixins/`.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>