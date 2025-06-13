# Dana State Management and Scopes

This document describes how Dana manages state through its structured scoping system. This system is fundamental to how Dana programs interact with data, control execution, and manage information pertaining to agents, the environment, and the runtime itself.

## 1. Overview of Scopes

Dana employs a system of distinct scopes to organize variables and manage their lifecycle and visibility. Each scope serves a specific purpose, ensuring clarity and control over the state within a Dana program and its execution context.

The primary state scopes are:

* `local:`: For temporary, computation-specific state. This is often the default scope for variables within a function or a block if no other scope is specified, especially in REPL or simple script contexts.
* `private:`: For state that is private to a specific agent, resource, or logical component. This is for internal data that should not be directly exposed to other components.
* `public:`: For state that represents the shared environment or world, accessible by multiple components. This could include things like current time, or general environmental parameters.
* `system:`: For state related to the Dana runtime, execution mechanics, and system-level information. This scope is generally managed by the Dana system itself, though certain variables (like `system:__dana_desired_type`) can be accessed or influenced by user code or the interpreter.

This explicit scoping mechanism is a key feature of Dana, promoting clarity and avoiding naming conflicts.

## 2. Scope Definitions and Use Cases

### 2.1. `local:` Scope (Temporary/Computation State)

* Purpose: Holds temporary variables, intermediate calculation results, processing buffers, and other short-lived data relevant only to the current block of execution (e.g., within a function, loop, or a specific task step).
* Lifecycle: Variables in the `local:` scope are typically transient and may be discarded after the execution block completes, or at the end of a REPL session if not explicitly managed otherwise.
* Analogy: Similar to local variables within a function in traditional programming languages.
* Old Naming Convention: Previously referred to as `temp.` in some older design documents.

Example Usage:
```dana
# Use local: scope for intermediate calculations
local:data = public:input_data
local:processed_items = []

for item in local:data:
 local:current_item = item
 # Assuming 'analyze_item' is a function that might use more local: variables
 local:analysis_result = analyze_item(local:current_item)
 local:processed_items.append(local:analysis_result)

# Final results might be stored in a more persistent scope if needed
private:final_results = local:processed_items
```

### 2.2. `private:` Scope (Agent/Component-Specific State)

* Purpose: Manages state that is specific and internal to an agent, a custom resource, or a defined logical component. This includes configuration, internal counters, decision context, progress tracking for the agent's tasks, and any other data that defines the agent's private state.
* Lifecycle: Persists as long as the agent or component instance exists and is active.
* Analogy: Similar to instance variables in an object, or private module variables.
* Old Naming Convention: Previously referred to as `agent.` in some older design documents.

Example Usage:
```dana
# Track progress through a multi-step task for an agent
private:current_step = "data_collection"
private:items_processed_count = 0
private:total_items_to_process = 100
private:api_key = "my_secret_key" # Agent's private API key

# Check progress and make decisions
if private:items_processed_count >= private:total_items_to_process:
 private:current_step = "task_complete"
```

### 2.3. `public:` Scope (Shared Environment/World State)

* Purpose: Contains information about the external environment, shared resources, or any data that needs to be openly accessible to multiple agents or components. This could include current time, shared tool configurations, or publicly available data feeds.
* Lifecycle: Represents a more global or shared state that may persist across different operations or even different agents if they share the same world context.
* Analogy: Similar to global variables or shared configuration settings, but with a clear namespace.
* Old Naming Convention: Previously referred to as `world.` in some older design documents.

Example Usage:
```dana
# Manage shared tool authentication and session (if appropriate for public sharing)
public:shared_api_endpoint = "https://api.example.com/v1"
public:last_system_update_time = "2024-05-28T12:00:00Z"

# Access public information
log(f"Connecting to endpoint: {public:shared_api_endpoint}")
```

### 2.4. `system:` Scope (Runtime/Mechanical State)

* Purpose: Provides access to system-level information and control mechanisms related to the Dana runtime and execution. This includes execution status, runtime configuration, or special variables used by the interpreter (e.g., `__dana_desired_type`).
* Lifecycle: Managed by the Dana runtime. User code typically reads from this scope or interacts with it via specific, well-defined mechanisms.
* Analogy: Similar to environment variables or runtime flags specific to the execution engine.

Example Usage:
```dana
# Accessing a system-provided value (conceptual)
log(f"Current Dana runtime version: {system:dana_version}")

# A function checking for a caller-desired type (passed by the system)
if system:__dana_desired_type == UserProfile:
 log("Caller expects a UserProfile struct.")
 # ... function attempts to return a UserProfile
```

## 3. `SandboxContext` and Programmatic Access

At the Python implementation level (within the OpenDXA framework), the `SandboxContext` class is responsible for managing these scopes.

* Structure: The `SandboxContext` holds dictionaries for `local`, `private`, `public`, and `system` states.
* Initialization: When a Dana program or function is executed, a `SandboxContext` is provided or created, populated with the relevant state for each scope.
* API: The `SandboxContext` Python class provides methods like `get(variable_name_with_scope)` and `set(variable_name_with_scope, value)` for programmatic interaction with these scopes from the underlying Python implementation of resources or core functions.

Conceptual Python Example (Illustrative of `SandboxContext` usage):
```python
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Create context with initial state
context = SandboxContext(
 initial_private_state={"name": "analyst_agent", "objective": "Process data"},
 initial_public_state={"data_source_url": "http://example.com/data"},
 initial_local_state={}
 # system state is typically managed internally
)

# Programmatic access from Python code (e.g., a custom Resource)
agent_name = context.get("private:name")
context.set("local:processing_started", True)

# When a Dana program runs, it uses this context:
dana_program = """
log(f"Processing data for agent: {private:name}")
log(f"Data source: {public:data_source_url}")

local:results = []
private:status = "processing"
"""
# result = run_dana_program(dana_program, context) # Conceptual execution
```

## 4. Best Practices for State Management

1. **Choose the Right Scope**: Be deliberate about which scope a variable belongs to. This improves clarity and prevents unintended side effects.
 * Use `local:` for transient, block-specific data.
 * Use `private:` for data internal to an agent or component.
 * Use `public:` for genuinely shared environmental data.
 * Interact with `system:` as defined by Dana's features (e.g., for `__dana_desired_type`).
2. **Clear Naming**: Use descriptive variable names, even with scopes, to enhance readability.
3. **Minimize Global State**: Prefer passing data through function parameters and return values or using more specific `private:` or `local:` scopes over excessive use of `public:` state.
4. **Initialization**: Ensure variables are initialized before use, especially if they are expected in `private:` or `public:` scopes by different parts of a Dana program or by different agents.
5. **Lifecycle Awareness**: Understand that `local:` state is often ephemeral. If data needs to persist beyond a small computation, store it in `private:` or `public:` scopes.

By adhering to these scoping rules and practices, Dana programs can manage state effectively, leading to more robust, understandable, and maintainable agentic systems.