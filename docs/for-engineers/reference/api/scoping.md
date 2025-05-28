<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../../../README.md) | [For Engineers](../../README.md) | [Reference](../README.md) | [API Reference](README.md)

# Scoping System API Reference

Dana's scoping system provides structured variable organization with four distinct scopes: `local`, `private`, `public`, and `system`. This system ensures clear data flow, security boundaries, and auditable state transitions.

## Table of Contents
- [Overview](#overview)
- [Scope Types](#scope-types)
- [Syntax and Notation](#syntax-and-notation)
- [Scope Access Rules](#scope-access-rules)
- [Security Model](#security-model)
- [Context Management](#context-management)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Implementation Details](#implementation-details)

---

## Overview

### Design Philosophy
- **Explicit scoping**: Clear separation of variable contexts
- **Security boundaries**: Controlled access to sensitive data
- **Auditable state**: Trackable state transitions
- **Hierarchical organization**: Nested variable paths supported

### Key Features
- ✅ **Four distinct scopes**: local, private, public, system
- ✅ **Colon notation**: `scope:variable` syntax
- ✅ **Auto-scoping**: Unscoped variables default to local
- ✅ **Nested paths**: Support for `scope:path.to.variable`
- ✅ **Security isolation**: Sensitive scopes can be sanitized
- ✅ **Context inheritance**: Parent-child context relationships

---

## Scope Types

| Scope | Purpose | Access Level | Use Cases |
|-------|---------|--------------|-----------|
| `local` | Function/execution local | Current context only | Temporary variables, calculations |
| `private` | Agent/resource private | Agent-specific | Internal state, sensitive data |
| `public` | World state | Globally accessible | Shared data, observations |
| `system` | System state | Controlled access | Runtime status, configuration |

### Scope Characteristics

#### `local` Scope
- **Purpose**: Local to the current function, tool, or execution context
- **Lifetime**: Exists only during current execution
- **Access**: Current context only
- **Default**: Unscoped variables automatically use local scope

```dana
# These are equivalent
result = calculate_value()
local:result = calculate_value()

# Local variables are isolated
def process_data():
    temp_value = 42  # local:temp_value
    return temp_value * 2
```

#### `private` Scope
- **Purpose**: Private to the agent, resource, or tool
- **Lifetime**: Persists across function calls within the same agent
- **Access**: Agent-specific, not shared
- **Security**: Considered sensitive, can be sanitized

```dana
# Agent internal state
private:agent_status = "processing"
private:internal_config = {"debug": true, "retries": 3}
private:user_session = {"id": "abc123", "authenticated": true}

# Nested private data
private:analysis.current_step = 1
private:analysis.total_steps = 5
private:analysis.results = []
```

#### `public` Scope
- **Purpose**: Shared world state accessible to all agents
- **Lifetime**: Persists globally
- **Access**: Readable and writable by all agents
- **Use cases**: Environmental data, shared observations

```dana
# Shared environmental state
public:weather.temperature = 72.5
public:weather.humidity = 65
public:time.current = "2025-01-01T12:00:00Z"

# Shared observations
public:sensor.motion_detected = true
public:sensor.last_reading = "2025-01-01T11:59:30Z"

# Collaborative data
public:task_queue = ["task1", "task2", "task3"]
public:shared_results = {"analysis": "complete", "confidence": 0.95}
```

#### `system` Scope
- **Purpose**: System-related runtime state and configuration
- **Lifetime**: Persists for system lifetime
- **Access**: Controlled, typically read-only for user code
- **Security**: Considered sensitive, can be sanitized

```dana
# System runtime state
system:execution_status = "running"
system:memory_usage = 85
system:log_level = "info"

# System configuration
system:max_retries = 3
system:timeout_seconds = 30
system:debug_mode = false

# Execution history
system:history = [
    {"action": "function_call", "timestamp": "2025-01-01T12:00:00Z"},
    {"action": "variable_set", "timestamp": "2025-01-01T12:00:01Z"}
]
```

---

## Syntax and Notation

### Colon Notation (Recommended)
```dana
# Explicit scope specification
private:variable_name = value
public:shared_data = value
system:config_option = value
local:temp_result = value

# Nested paths
private:user.profile.name = "Alice"
public:sensor.temperature.current = 72.5
system:config.logging.level = "debug"
```

### Auto-scoping (Default)
```dana
# Unscoped variables default to local scope
result = 42              # Equivalent to local:result = 42
user_name = "Alice"      # Equivalent to local:user_name = "Alice"
is_complete = true       # Equivalent to local:is_complete = true
```

### Dot Notation (Internal)
> **Note**: Dot notation is used internally by the system but colon notation is recommended for user code.

```dana
# Internal representation (not recommended for user code)
private.variable_name = value  # Internally stored as private:variable_name
```

---

## Scope Access Rules

### Read Access
1. **Local scope**: Current context and parent contexts
2. **Private scope**: Current agent/resource only
3. **Public scope**: All agents and contexts
4. **System scope**: All contexts (read-only for most operations)

### Write Access
1. **Local scope**: Current context only
2. **Private scope**: Current agent/resource only
3. **Public scope**: All agents and contexts
4. **System scope**: Controlled access, typically system operations only

### Inheritance Rules
```dana
# Parent-child context relationships
def parent_function():
    local:parent_var = "parent value"
    private:shared_state = "accessible to child"
    
    def child_function():
        # Can access parent's local variables
        parent_value = local:parent_var  # Inherits from parent
        
        # Can access shared private state
        shared = private:shared_state
        
        # Child's local variables don't affect parent
        local:child_var = "child only"
    
    child_function()
    # parent_var and shared_state still accessible
    # child_var is not accessible here
```

### Global Scope Sharing
```dana
# Global scopes (private, public, system) are shared across contexts
def function_a():
    private:shared_data = {"step": 1}
    public:status = "processing"

def function_b():
    # Can access global scopes set by function_a
    step = private:shared_data["step"]  # Gets 1
    status = public:status              # Gets "processing"
    
    # Modifications affect global state
    private:shared_data["step"] = 2
    public:status = "complete"
```

---

## Security Model

### Sensitive Scopes
The `private` and `system` scopes are considered sensitive and can be sanitized for security:

```dana
# Sensitive data in private scope
private:api_key = "secret-key-123"
private:user_credentials = {"username": "admin", "password": "secret"}

# Sensitive system state
system:internal_config = {"debug_mode": true, "admin_access": true}
```

### Sanitization
The context manager provides sanitization capabilities:

```python
# Python API for context sanitization
context_manager = ContextManager(context)
sanitized_context = context_manager.get_sanitized_context()

# Sanitized context removes private and system scopes
# Only local and public scopes remain
```

### Security Boundaries
```dana
# Public data - safe to share
public:weather_data = {"temperature": 72, "humidity": 65}
public:sensor_readings = [1, 2, 3, 4, 5]

# Private data - agent-specific, can be sanitized
private:internal_state = "processing_step_3"
private:user_session = {"authenticated": true, "role": "admin"}

# System data - runtime state, can be sanitized
system:execution_context = {"thread_id": 12345, "memory_usage": 85}
```

---

## Context Management

### Context Creation
```python
# Python API for context management
from opendxa.dana.sandbox.sandbox_context import SandboxContext
from opendxa.dana.sandbox.context_manager import ContextManager

# Create new context
context = SandboxContext()
manager = ContextManager(context)

# Create child context
child_context = SandboxContext(parent=context)
```

### Variable Operations
```python
# Set variables in specific scopes
manager.set_in_context("variable_name", "value", scope="private")
manager.set_in_context("shared_data", {"key": "value"}, scope="public")

# Get variables from specific scopes
value = manager.get_from_scope("variable_name", scope="private")
shared = manager.get_from_scope("shared_data", scope="public")

# Check if variables exist
exists = manager.context.has("private:variable_name")
```

### Context Inheritance
```python
# Parent context
parent = SandboxContext()
parent.set("private:shared_state", "parent value")
parent.set("public:global_data", "accessible to all")

# Child context inherits global scopes
child = SandboxContext(parent=parent)

# Child can access parent's global scopes
shared_state = child.get("private:shared_state")  # "parent value"
global_data = child.get("public:global_data")     # "accessible to all"

# Child's local scope is independent
child.set("local:child_data", "child only")
# parent.get("local:child_data") would raise StateError
```

---

## Best Practices

### 1. Use Auto-scoping for Local Variables
```dana
# ✅ Good: Simple and clear
result = calculate_value()
temp_data = process_input()
is_complete = check_status()

# ❌ Avoid: Unnecessary explicit local scope
local:result = calculate_value()
local:temp_data = process_input()
local:is_complete = check_status()
```

### 2. Be Explicit with Global Scopes
```dana
# ✅ Good: Clear intent for shared data
private:agent_config = {"retries": 3, "timeout": 30}
public:sensor_data = {"temperature": 72, "humidity": 65}
system:log_level = "debug"

# ❌ Avoid: Unclear scope for important data
config = {"retries": 3, "timeout": 30}  # Goes to local scope
```

### 3. Use Nested Paths for Organization
```dana
# ✅ Good: Organized hierarchical data
private:user.profile.name = "Alice"
private:user.profile.email = "alice@example.com"
private:user.preferences.theme = "dark"
private:user.preferences.notifications = true

public:sensor.temperature.current = 72.5
public:sensor.temperature.max = 85.0
public:sensor.humidity.current = 65
public:sensor.humidity.max = 80
```

### 4. Minimize Private Scope Usage
```dana
# ✅ Good: Use local scope for temporary data
def process_data(input_data):
    # Temporary processing variables
    cleaned_data = clean_input(input_data)
    processed_result = transform_data(cleaned_data)
    
    # Only use private for persistent agent state
    private:last_processed_count = len(processed_result)
    
    return processed_result

# ❌ Avoid: Overusing private scope
def process_data(input_data):
    private:temp_data = clean_input(input_data)      # Should be local
    private:temp_result = transform_data(temp_data)  # Should be local
    private:final_count = len(temp_result)           # OK for persistence
    
    return private:temp_result
```

### 5. Document Scope Usage
```dana
# ✅ Good: Clear documentation of scope purpose
def ai_analysis_workflow(data):
    # Local processing variables
    cleaned_data = preprocess(data)
    
    # Private agent state for tracking
    private:analysis.current_step = 1
    private:analysis.total_steps = 3
    
    # Public shared results
    public:analysis.status = "in_progress"
    public:analysis.start_time = get_current_time()
    
    # Process each step
    for step in range(3):
        private:analysis.current_step = step + 1
        step_result = process_step(cleaned_data, step)
        public:analysis.results.append(step_result)
    
    # Final status
    public:analysis.status = "complete"
    public:analysis.end_time = get_current_time()
    
    return public:analysis.results
```

---

## Examples

### Basic Scope Usage
```dana
# Local variables (default scope)
user_input = "analyze this data"
processing_step = 1
is_complete = false

# Private agent state
private:session_id = "abc123"
private:user_preferences = {"format": "json", "verbose": true}
private:internal_cache = {}

# Public shared data
public:current_temperature = 72.5
public:system_status = "operational"
public:shared_queue = []

# System configuration
system:max_memory_mb = 1024
system:log_level = "info"
system:debug_enabled = false
```

### AI Workflow with Scoping
```dana
def ai_data_analysis(dataset):
    # Local processing variables
    start_time = get_current_time()
    analysis_id = generate_id()
    
    # Private agent state
    private:current_analysis.id = analysis_id
    private:current_analysis.dataset_size = len(dataset)
    private:current_analysis.start_time = start_time
    
    # Public status for monitoring
    public:analysis_status = "starting"
    public:analysis_progress = 0
    
    # System resource tracking
    system:active_analyses.append(analysis_id)
    
    # Perform analysis
    log(f"Starting analysis {analysis_id}", "info")
    
    # Step 1: Data preprocessing
    public:analysis_progress = 25
    cleaned_data = preprocess_data(dataset)
    private:current_analysis.preprocessing_complete = true
    
    # Step 2: AI reasoning
    public:analysis_progress = 50
    analysis_prompt = f"Analyze this dataset: {cleaned_data}"
    ai_result = reason(analysis_prompt, {
        "temperature": 0.3,
        "max_tokens": 1000
    })
    private:current_analysis.ai_result = ai_result
    
    # Step 3: Post-processing
    public:analysis_progress = 75
    final_result = postprocess_result(ai_result)
    
    # Final results
    public:analysis_progress = 100
    public:analysis_status = "complete"
    public:latest_analysis = {
        "id": analysis_id,
        "result": final_result,
        "timestamp": get_current_time()
    }
    
    # Update private state
    private:current_analysis.complete = true
    private:current_analysis.end_time = get_current_time()
    
    # Clean up system resources
    system:active_analyses.remove(analysis_id)
    
    log(f"Analysis {analysis_id} completed", "info")
    return final_result
```

### Multi-Agent Coordination
```dana
# Agent A: Data collector
def collect_sensor_data():
    # Local processing
    raw_data = read_sensors()
    timestamp = get_current_time()
    
    # Private agent state
    private:collector.last_reading = timestamp
    private:collector.readings_count += 1
    
    # Public shared data for other agents
    public:sensor.temperature = raw_data["temp"]
    public:sensor.humidity = raw_data["humidity"]
    public:sensor.last_update = timestamp
    
    # System monitoring
    system:sensor_readings.append({
        "timestamp": timestamp,
        "agent": "collector",
        "data": raw_data
    })

# Agent B: Data analyzer
def analyze_sensor_trends():
    # Access public data from Agent A
    current_temp = public:sensor.temperature
    current_humidity = public:sensor.humidity
    last_update = public:sensor.last_update
    
    # Private analysis state
    private:analyzer.last_analysis = get_current_time()
    
    # Perform trend analysis
    if current_temp > 80:
        trend_analysis = reason(f"Temperature is {current_temp}°F. Is this concerning?")
        
        # Share analysis results publicly
        public:analysis.temperature_trend = trend_analysis
        public:analysis.alert_level = "high" if "concerning" in trend_analysis else "normal"
        
        # Log to system
        system:alerts.append({
            "type": "temperature",
            "level": public:analysis.alert_level,
            "timestamp": get_current_time(),
            "agent": "analyzer"
        })
```

---

## Implementation Details

### Runtime Scopes
```python
# Scope definitions in RuntimeScopes class
LOCAL = ["local"]
GLOBAL = ["private", "public", "system"]
ALL = LOCAL + GLOBAL
SENSITIVE = ["private", "system"]
NOT_SENSITIVE = ["local", "public"]
```

### Context State Structure
```python
# Internal context state structure
_state = {
    "local": {},     # Fresh for each context
    "private": {},   # Shared across agent contexts
    "public": {},    # Shared globally
    "system": {      # Shared globally, controlled access
        "execution_status": ExecutionStatus.IDLE,
        "history": [],
    }
}
```

### Variable Resolution
1. **Parse scope**: Extract scope and variable name from `scope:variable`
2. **Validate scope**: Ensure scope is in `RuntimeScopes.ALL`
3. **Route to context**: Global scopes use root context, local uses current
4. **Set/get value**: Store or retrieve from appropriate scope dictionary

### Error Handling
```python
# Common errors and their meanings
StateError("Unknown scope: invalid_scope")
StateError("Variable 'scope:variable' not found")
StateError("Invalid key format: malformed_key")
```

---

## See Also

- **[Core Functions](core-functions.md)** - Essential Dana functions with scoping considerations
- **[Type System](type-system.md)** - Type annotations work with all scopes
- **[Function Calling](function-calling.md)** - Function calls and scope inheritance
- **[Built-in Functions](built-in-functions.md)** - Built-in functions and scope access

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 