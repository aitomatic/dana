# Mixin Architecture

This document explains the mixin architecture used throughout the OpenDXA framework. Mixins provide reusable capabilities to classes through multiple inheritance, enabling a modular, composable approach to building complex components.

## Overview

Mixins in OpenDXA are designed to:
- Add specific capabilities to classes without complex inheritance hierarchies
- Provide consistent interfaces for common functionality
- Enable composition of capabilities through multiple inheritance
- Maintain clean separation of concerns
- Follow the principle of least surprise with standardized patterns

## Core Mixins

OpenDXA provides several core mixins that can be combined to create powerful, feature-rich components:

### Loggable

The foundation mixin that provides standardized logging capabilities across OpenDXA. It automatically configures a logger with appropriate naming and formatting.

**Key Features:**
- Automatic logger naming based on class hierarchy
- Support for execution layer specialization
- Convenience methods for logging
- Class-level logging capabilities

### Configurable

Adds configuration management capabilities to components, enabling them to load and manage configuration data.

**Key Features:**
- YAML file loading with defaults and overrides
- Configuration validation
- Path resolution for config files
- Configuration access methods

### Identifiable

Adds unique identification capabilities to objects, enabling tracking and referencing of specific instances.

**Key Features:**
- Unique ID generation
- Name and description management
- Standardized identification attributes

### Registerable

Provides registration capabilities for components that need to be discoverable and accessible by name. Inherits from Identifiable.

**Key Features:**
- Component registration and retrieval
- Registry management
- Name-based lookup

### ToolCallable

Enables objects to be called as tools within the tool-calling ecosystem, providing a standardized interface for tool execution.

**Key Features:**
- Tool definition and registration
- Standardized calling interface
- Tool discovery and introspection

### Queryable

Adds query capabilities to objects, allowing them to be both queried directly and called as tools. Inherits from ToolCallable.

**Key Features:**
- Standardized query interface
- Query strategy management
- Result handling

### Capable

Adds capabilities management to objects, allowing them to dynamically add and use capabilities.

**Key Features:**
- Capability registration and management
- Capability discovery
- Dynamic capability application

## Mixin Hierarchy

The mixin hierarchy in OpenDXA is structured to provide a composable architecture. The key relationships are:

### Base Mixins
- `Loggable`: Foundation mixin with no dependencies
- `Identifiable`: Foundation mixin with no dependencies
- `Configurable`: Foundation mixin with no dependencies

### Mid-level Mixins
- `Registerable` extends `Identifiable`
- `ToolCallable` extends `Registerable` and `Loggable`
- `Queryable` extends `ToolCallable`

### Component Implementations
- `Agent` uses `Configurable`, `ToolCallable`, and `Capable`
- `BaseResource` uses `Configurable`, `Queryable`, and `ToolCallable`
- `McpResource` extends `BaseResource`
- `BaseCapability` uses `ToolCallable` and `Configurable`

## Major Component Compositions

### Agent
- Inherits: `Configurable`, `ToolCallable`, `Capable`
- Key methods: `run()`, `ask()`
- Properties: `name`, `description`, `tools`

### BaseResource
- Inherits: `Configurable`, `Queryable`, `ToolCallable`
- Key methods: `query()`
- Properties: `name`, `description`

### McpResource
- Extends: `BaseResource`
- Additional methods: `list_tools()`, `call_tool()`
- Additional properties: `transport_type`

### BaseCapability
- Inherits: `ToolCallable`, `Configurable`
- Key methods: `enable()`, `disable()`, `apply()`, `can_handle()`
- Properties: `name`, `description`, `is_enabled`

## Usage Patterns

### Basic Usage

```python
from opendxa.common.mixins import Loggable, Identifiable, Configurable

class MyResource(Loggable, Identifiable, Configurable):
    def __init__(self):
        Loggable.__init__(self)
        Identifiable.__init__(self)
        Configurable.__init__(self)
        # Your initialization code here
```

### Advanced Usage with Multiple Mixins

```python
from opendxa.common.mixins import (
    Loggable,
    Identifiable,
    Configurable,
    Registerable,
    Queryable
)

class AdvancedResource(Loggable, Identifiable, Configurable, Registerable, Queryable):
    def __init__(self):
        Loggable.__init__(self)
        Identifiable.__init__(self)
        Configurable.__init__(self)
        Registerable.__init__(self)
        Queryable.__init__(self)
        # Your initialization code here
```

### Agent Definition Using Mixins

```python
from opendxa.common.mixins import Configurable, Loggable, ToolCallable
from opendxa.base.capability import Capable

class Agent(Configurable, Loggable, Capable, ToolCallable):
    def __init__(self):
        Configurable.__init__(self)
        Loggable.__init__(self)
        Capable.__init__(self)
        ToolCallable.__init__(self)
        # Agent initialization code here
```

## Best Practices

### 1. Order Matters

When using multiple mixins, list them in order of dependency (most dependent last). This ensures proper method resolution order and avoids conflicts.

```python
# Correct order (ToolCallable depends on Loggable and Registerable)
class MyTool(Loggable, Registerable, ToolCallable):
    pass
```

### 2. Minimal Inheritance

Use only the mixins you need to avoid unnecessary complexity. Each mixin adds overhead and potential conflicts.

```python
# Good - using only what's needed
class SimpleAgent(Loggable, Configurable):
    pass

# Avoid - using mixins that aren't needed
class OvercomplicatedAgent(Loggable, Identifiable, Registerable, Configurable, Queryable, ToolCallable):
    pass
```

### 3. Consistent Initialization

Always ensure each mixin is properly initialized by calling its `__init__` method. This is critical for correct behavior.

```python
# Correct initialization
def __init__(self):
    Loggable.__init__(self)
    Configurable.__init__(self)
    # Your initialization code
```

### 4. Clear Documentation

Document which mixins are used and why in class docstrings. This helps other developers understand the purpose and capabilities of your class.

```python
class AnalysisAgent(Loggable, Configurable, ToolCallable):
    """Agent for data analysis tasks.
    
    Inherits:
    - Loggable: For structured logging during analysis
    - Configurable: For loading analysis parameters
    - ToolCallable: To expose analysis methods as tools
    """
```

## Implementation Details

For detailed implementation information, parameter references, and advanced usage examples, please refer to the Mixins Module source code.

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>