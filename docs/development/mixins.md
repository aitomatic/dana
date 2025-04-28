<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md) | [Main Documentation](../README.md)

# OpenDXA Mixin Classes

OpenDXA utilizes mixin classes extensively to provide common functionalities like logging, configuration handling, identification, and registration to various core components (Agents, Resources, Capabilities) in a composable and maintainable way. This avoids deep inheritance trees and promotes code reuse.

These mixins typically follow a naming pattern ending in "-able" (e.g., `Loggable`, `Configurable`).

## Overview

Mixins are designed to:

*   Add specific, reusable capabilities to classes.
*   Provide consistent interfaces for these capabilities.
*   Enable composition through multiple inheritance.
*   Maintain separation of concerns.

## Available Mixins (`opendxa.common.mixins`)

*(Note: This list might not be exhaustive)*

*   **`Loggable`**: The foundation mixin providing standardized logging capabilities. Automatically configures a logger instance (`self.logger`) with appropriate naming based on the class hierarchy.
*   **`Configurable`**: Adds configuration management capabilities, often including YAML loading, validation, default/override handling, and access methods (`self.config`, `get`, `set`).
*   **`Identifiable`**: Adds unique identification (`id`, `name`) and description capabilities.
*   **`Registerable`**: Provides registration capabilities for components needing discovery (e.g., via a factory or registry). Depends on `Identifiable`.
*   **`ToolCallable`**: Enables objects or their methods to be exposed and called as "tools" within the framework, often involving schema generation and standardized calling conventions. Depends on `Loggable`.
*   **`Queryable`**: Adds a standardized `query` method, often used by Resources. Typically inherits from `ToolCallable` to allow querying via the tool mechanism as well.
*   **`Capable`**: Adds capability management (`add_capability`, `get_capability`, etc.), typically used by the `Agent` class.

## Mixin Hierarchy & Usage in Core Classes (Conceptual)

This diagram shows how various mixins are commonly incorporated into core OpenDXA classes like `Agent`, `BaseResource`, and `BaseCapability`.

```mermaid
classDiagram
    direction BT

    class Mixins {
        <<Mixin>>
        Loggable
        Configurable
        Identifiable
        Registerable
        ToolCallable
        Queryable
        Capable
    }

    class Agent {
        +name
        +description
        +run()
        +ask()
        +capabilities
        +tools
    }

    class BaseResource {
        +name
        +description
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

    class BaseCapability {
        +name
        +description
        +is_enabled
        +enable()
        +disable()
        +apply()
        +can_handle()
    }

    Agent --|> Configurable
    Agent --|> Loggable
    Agent --|> Capable
    Agent --|> ToolCallable

    BaseResource --|> Configurable
    BaseResource --|> Loggable
    BaseResource --|> Identifiable
    BaseResource --|> Registerable
    BaseResource --|> Queryable

    McpResource --|> BaseResource # McpResource inherits BaseResource

    BaseCapability --|> Configurable
    BaseCapability --|> Loggable
    BaseCapability --|> Identifiable

    Queryable --|> ToolCallable # Queryable extends ToolCallable
    Registerable --|> Identifiable # Registerable needs Identifiable
    ToolCallable --|> Loggable # ToolCallable needs Loggable

```

## Usage Examples

Mixins are added to a class definition via multiple inheritance. It's crucial to call their respective initializers (or use `super().__init__()` correctly if the mixins are designed for it) within the inheriting class's `__init__` method.

```python
from opendxa.common.mixins import Loggable, Identifiable, Configurable

class MySimpleComponent(Loggable, Identifiable, Configurable):
    def __init__(self, name: str = "DefaultName", config_path: str = None):
        # It's often best practice for mixins to handle their own init
        # or rely on super() if designed that way. Check mixin source.
        # Example explicit calls (adapt based on actual mixin __init__): 
        Loggable.__init__(self) 
        Identifiable.__init__(self, name=name)
        Configurable.__init__(self, config_path=config_path)
        
        self.logger.info(f"Initialized {self.name} with ID {self.id}")
        db_host = self.config.get("database.host", "localhost") # Use Configurable method
        self.logger.info(f"Database host: {db_host}")
```

```python
from opendxa.common.mixins import (
    Loggable, Identifiable, Configurable, Registerable, Queryable
)
# Assuming Queryable inherits ToolCallable which needs Loggable,
# and Registerable needs Identifiable.

class MyAdvancedResource(Configurable, Registerable, Queryable):
    # Inheritance order matters for MRO (Method Resolution Order)
    # List less dependent mixins first generally.
    # Queryable likely brings ToolCallable, which brings Loggable.
    # Registerable brings Identifiable.

    def __init__(self, name="AdvRes", config_path=None):
        # Using super() relies on cooperative multiple inheritance design
        super().__init__(name=name, config_path=config_path) 
        # Mixin initializers are called via MRO
        
        self.logger.info(f"Initialized advanced resource: {self.name}")

    async def query(self, request: dict) -> dict:
        self.logger.debug(f"Query received: {request}")
        # ... actual query logic ...
        return {"result": "some data"}
```

## Best Practices

1.  **Initialization Order:** If calling `__init__` explicitly, ensure dependent mixins are initialized after their dependencies. If using `super()`, ensure the MRO and mixin designs are compatible.
2.  **Minimalism:** Only include the mixins necessary for the class's required functionality.
3.  **Clarity:** Document which mixins a class uses and the capabilities they provide.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 