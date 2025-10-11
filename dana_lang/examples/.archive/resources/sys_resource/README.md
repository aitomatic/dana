# Dana Sys Resource Examples

This directory contains examples demonstrating the `sys_resource` system in Dana.

## Sys Resource Overview

### **`sys_resource`** (`dana/common/sys_resource/`)
- **Purpose**: Low-level system resource abstractions
- **Implementation**: Python-based with sophisticated functionality
- **Usage**: Created via `use()` function
- **Features**: Advanced async support, error handling, complex state management

## Available Sys Resources

The following resource types are supported via the `use()` function:

| Resource Type | Description | Example Usage |
|---------------|-------------|---------------|
| `mcp` | Model Context Protocol resources | `use("mcp", url="http://localhost:8880")` |
| `rag` | Retrieval-Augmented Generation | `use("rag", ["doc1.txt", "doc2.pdf"])` |
| `knowledge` | Knowledge base resources | `use("knowledge")` |
| `finance_rag` | Financial statement RAG | `use("finance_rag")` |
| `coding` | Code generation and execution | `use("coding")` |
| `tabular_index` | Tabular data indexing | `use("tabular_index")` |

## Usage Syntax

### Basic Resource Creation
```dana
# Create resource using use() function
rag = use("rag", ["document1.txt", "document2.pdf"])
coding = use("coding", name="my_coding_resource")

# Call methods directly (async handled automatically)
rag.initialize()
result = rag.query("What is Dana?")
```

### Resource Lifecycle
```dana
# 1. Create resource
resource = use("resource_type", *args, **kwargs)

# 2. Initialize (if needed)
resource.initialize()

# 3. Use the resource
result = resource.query("your_query")
# or call specific methods
result = resource.specific_method()

# 4. Cleanup (automatic in most cases)
resource.stop()
```

## Examples

### RAG Resource Example (`rag_example.na`)
Demonstrates RAG (Retrieval-Augmented Generation) using the RAGResource:

```dana
# Create a RAG resource
rag = use("rag", ["This is a sample document about Dana programming language."])

# Initialize and use
rag.initialize()
result = rag.query("What is Dana?")
```

### Coding Resource Example (`coding_example.na`)
Demonstrates code generation and execution using the CodingResource:

```dana
# Create a coding resource
coding = use("coding")

# Initialize and execute code
coding.initialize()
result = coding.execute_code("Calculate the factorial of 5")
```

## Key Features

### Advanced Functionality
- **Async Support**: Automatic handling of async operations via `Misc.safe_asyncio_run`
- **Error Handling**: Sophisticated error handling with detailed error messages
- **State Management**: Complex state management with initialization, running, and cleanup states
- **Resource Context**: Resources are automatically registered with the execution context

### Python-Based Implementation
- Built on `BaseSysResource` class
- Leverages Python's advanced features
- Optimized for complex system-level operations
- Full integration with Dana's sandbox environment

## Error Handling

Sys resources provide advanced error handling:
- Detailed error messages with context
- Graceful degradation when possible
- Automatic resource cleanup on errors
- Comprehensive logging and debugging information

## Best Practices

1. **Always initialize** resources before use (when required)
2. **Handle async operations** - they're automatically managed
3. **Check resource state** before operations when needed
4. **Use appropriate resource type** for your use case
5. **Clean up resources** when done (automatic in most cases)

## Architecture Notes

- **Base Class**: All sys resources inherit from `BaseSysResource`
- **Context Integration**: Resources are automatically registered with `SandboxContext`
- **Function Registry**: Resources are created through the `use()` function in `py_use.py`
- **Async Handling**: Uses `Misc.safe_asyncio_run` for seamless async operation

## Running Examples

```bash
# Run RAG example
dana examples/12_resources/sys_resource/rag_example.na

# Run coding example
dana examples/12_resources/sys_resource/coding_example.na
```

This sys resource system provides the foundation for sophisticated system-level operations in Dana, offering Python-level functionality while maintaining Dana's simplicity and safety.
