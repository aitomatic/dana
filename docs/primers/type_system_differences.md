# Dana Type System Differences: agent_blueprint vs agent vs resource

## Overview

Dana's type system has important distinctions between different declaration forms that affect how types are created and instantiated. Understanding these differences is crucial for effective Dana programming.

## Key Type System Patterns

### 1. agent_blueprint - Creates Constructors

```dana
agent_blueprint Abc:
    name: str = "An Agent"

# Type analysis:
type(Abc)  # Constructor[agent_constructor]
a = Abc()
type(a)    # AgentInstance[Abc]
```

**Behavior:**
- `agent_blueprint` creates a **constructor function**
- The constructor returns `StructInstance[TypeName]` when called
- This follows the traditional "class-like" pattern where you define a type and then instantiate it

### 2. agent - Creates Singleton Instances Directly

```dana
agent AA(Abc)  # Inherits from Abc blueprint

# Type analysis:
type(AA)  # AgentInstance[AA]
```

**Behavior:**
- `agent` creates a **singleton instance directly**
- No constructor is created - you get the instance immediately
- The instance inherits fields from the blueprint (if specified)
- This is useful for creating named, persistent agents

### 3. resource - Creates Constructors

```dana
resource R:
    name: str = "A Resource"

# Type analysis:
type(R)  # Constructor[resource_constructor]
r = R()
type(r)  # ResourceInstance[R]
```

**Behavior:**
- `resource` creates a **constructor function**
- The constructor returns `ResourceInstance[TypeName]` when called
- Resources have additional lifecycle management capabilities beyond regular structs

## Complete Example

```dana
# 1. Agent Blueprint - creates constructor
agent_blueprint Abc:
    name: str = "An Agent"

# 2. Create instance from blueprint
a = Abc()

# 3. Singleton agent - creates instance directly
agent AA(Abc)

# 4. Resource - creates constructor
resource R:
    name: str = "A Resource"

# 5. Create instance from resource
r = R()

# Type analysis results:
print(type(Abc))  # Constructor[agent_constructor]
print(type(a))    # AgentInstance[Abc]
print(type(AA))   # AgentInstance[AA]
print(type(R))    # Constructor[resource_constructor]
print(type(r))    # ResourceInstance[R]
```

## When to Use Each Pattern

### Use `agent_blueprint` when:
- You want to create multiple instances of the same agent type
- You need a reusable template for agent creation
- You want to follow traditional class-like patterns

```dana
agent_blueprint CustomerServiceAgent:
    domain: str = "customer_service"
    expertise_level: str = "senior"

# Create multiple instances
agent1 = CustomerServiceAgent(domain="technical_support")
agent2 = CustomerServiceAgent(expertise_level="expert")
```

### Use `agent` when:
- You want a single, named agent instance
- You need a persistent agent with a specific identity
- You want to avoid the constructor pattern

```dana
agent Alice(CustomerServiceAgent):
    expertise_level = "expert"

# Alice is now a persistent singleton
response = Alice.chat("Hello!")
```

### Use `resource` when:
- You need lifecycle management capabilities
- You want to manage system resources (files, databases, etc.)
- You need resource-specific methods and state management

```dana
resource DatabaseConnection:
    host: str = "localhost"
    port: int = 5432
    
    def connect():
        # Resource-specific logic
        pass

db = DatabaseConnection(host="prod.example.com")
db.connect()
```

## Type System Implications

### Constructor Functions
- `agent_blueprint` and `resource` create constructor functions
- These constructors are callable and return instances
- Useful for creating multiple instances with different configurations

### Direct Instances
- `agent` creates instances directly
- No constructor step - you get the instance immediately
- Useful for singletons and named entities

### Instance Types
- Agent instances: `AgentInstance[AgentName]`
- Resource instances: `ResourceInstance[ResourceName]`
- Regular struct instances: `StructInstance[StructName]`

## Practical Considerations

### Memory and Performance
- Constructors (from `agent_blueprint`/`resource`) are lightweight functions
- Direct instances (from `agent`) are full objects that consume memory immediately
- Choose based on whether you need multiple instances or a single persistent instance

### Naming and Identity
- `agent` creates named singletons that persist in the context
- Constructors allow you to create anonymous instances
- Consider the naming and identity requirements of your use case

### Inheritance and Composition
- `agent` can inherit from `agent_blueprint` to get field definitions
- Resources can have methods and lifecycle management
- Choose the pattern that best fits your architectural needs

## Summary

The key insight is that Dana provides three distinct patterns:

1. **`agent_blueprint`** → Constructor → Instance (traditional class pattern)
2. **`agent`** → Instance directly (singleton pattern)  
3. **`resource`** → Constructor → Resource Instance (resource management pattern)

Understanding these differences helps you choose the right pattern for your specific use case and write more effective Dana code.
