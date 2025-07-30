| [← Dana-to-Python](./dana-to-python.md) | [Python Integration Overview →](./python_integration.md) |
|---|---|

# Design Document: Python-to-Dana Integration

```text
Author: Christopher Nguyen
Version: 0.1
Status: Design Phase
Module: opendxa.dana.python
```

## Problem Statement

Python applications need to call Dana functions and access Dana runtime capabilities. This requires embedding the Dana runtime within Python processes while maintaining security boundaries and clean interface design.

### Core Challenges
1. **Runtime Embedding**: Safely embed Dana runtime in Python processes
2. **Security Model**: Maintain Dana sandbox security when called from Python
3. **Type Mapping**: Map Dana types to Python types cleanly
4. **Context Management**: Handle Dana execution contexts properly

## Goals

1. **Simple Python API**: Make calling Dana from Python feel natural
2. **Runtime Safety**: Maintain Dana sandbox security model
3. **Type Safety**: Clear and predictable type conversions
4. **Resource Management**: Explicit and clean resource handling
5. **Context Isolation**: Separate Dana execution contexts per Python thread/request

## Non-Goals

1. ❌ Complete Python-Dana type mapping
2. ❌ Automatic context management
3. ❌ Multi-tenant isolation in initial implementation

## Proposed Solution

**Goal**: Enable Python applications to call Dana functions with proper security boundaries and context management.

### Directional Design Choice

This is the companion to [Dana → Python](./dana-to-python.md) integration, focusing on:

- Python code calling Dana functions
- Dana runtime embedding in Python
- Dana sandbox security model maintenance

## Proposed Design

### Example Code

```python
from opendxa.dana import DanaRuntime, DanaContext

# Initialize Dana runtime
runtime = DanaRuntime()

# Create execution context
with runtime.create_context() as ctx:
    # Load Dana module
    math_utils = ctx.import_module("math_utils")
    
    # Call Dana function
    result = math_utils.calculate_area(width=10, height=5)
    
    # Access result
    area = result.as_float()
```

```python
# Direct function calling
from opendxa.dana import dana_function

@dana_function("analytics.process_data")
def process_data(data_path: str) -> dict:
    # This decorator handles Dana function invocation
    pass

result = process_data("/path/to/data.csv")
```

### Core Runtime Components

| Component | Purpose | Usage |
|-----------|---------|--------|
| **`DanaRuntime`** | Manages Dana interpreter lifecycle | Singleton per Python process |
| **`DanaContext`** | Isolated execution environment | One per thread/request |
| **`DanaModule`** | Represents imported Dana module | Module-level function access |
| **`DanaFunction`** | Callable Dana function wrapper | Direct function invocation |
| **`DanaObject`** | Dana struct/object wrapper | Property and method access |

### Security Model

1. **Sandbox Maintenance**: Each `DanaContext` runs in its own Dana sandbox
2. **Resource Isolation**: Contexts cannot access each other's resources
3. **Permission Control**: Python code specifies allowed capabilities per context
4. **Lifecycle Management**: Contexts are properly cleaned up on exit

### Context Management

```python
# Explicit context management
runtime = DanaRuntime()
ctx = runtime.create_context(
    allowed_capabilities=["file_read", "network"],
    max_memory="100MB",
    timeout="30s"
)

try:
    result = ctx.eval_dana("calculate_metrics(data=load_csv('data.csv'))")
finally:
    ctx.cleanup()

# Context manager pattern (preferred)
with runtime.create_context() as ctx:
    result = ctx.eval_dana("process_pipeline()")
    # Automatic cleanup
```

### Type Mapping

| Dana Type | Python Type | Conversion |
|-----------|------------|------------|
| `int` | `int` | Direct mapping |
| `float` | `float` | Direct mapping |
| `string` | `str` | Direct mapping |
| `bool` | `bool` | Direct mapping |
| `list[T]` | `list[T]` | Recursive conversion |
| `dict[K,V]` | `dict[K,V]` | Recursive conversion |
| `struct` | `DanaObject` | Wrapper object |
| `function` | `DanaFunction` | Callable wrapper |

### Future Enhancements

1. **Multi-tenant Isolation**: Separate runtime instances per tenant
2. **Async Support**: Async/await patterns for Dana function calls
3. **Stream Processing**: Iterator patterns for large datasets
4. **Hot Reloading**: Dynamic module reloading during development

## Implementation Notes

- Uses existing Dana interpreter core
- Maintains security sandbox boundaries
- Provides clean Python-native API
- Supports both sync and async patterns
- Enables proper resource cleanup

## Design Review Checklist

- [ ] Security model validated
  - [ ] Sandbox isolation verified
  - [ ] Context separation tested
  - [ ] Resource cleanup confirmed
- [ ] Performance considerations
  - [ ] Context creation overhead measured
  - [ ] Type conversion performance optimized
- [ ] API usability reviewed
  - [ ] Python idioms followed
  - [ ] Error handling patterns established 