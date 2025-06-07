<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[▲ Runtime & Execution](./README.md) | [◀ Python-to-Dana](./python-to-dana.md) | [Sandbox ▶](./sandbox.md)

# Dana-to-Python: Pragmatic Integration Design

**Status**: Design Phase  
**Module**: `opendxa.dana.python`

## Problem Statement

Dana code needs to call Python functions and libraries, but we want to avoid the over-engineering pitfalls identified in our Python-to-Dana implementation while maintaining a clean, secure, and maintainable design.

### Core Challenges
1. **Simplicity vs. Power**: Provide a simple interface while enabling real use cases
2. **Type Mapping**: Map Dana types to Python types cleanly
3. **Resource Management**: Handle Python resources properly
4. **Error Handling**: Propagate Python errors to Dana meaningfully

### Non-Challenges (Explicitly Deferred)
1. ❌ Process isolation (future enhancement)
2. ❌ Complex module systems
3. ❌ Elaborate security boundaries
4. ❌ Bidirectional compatibility layers

## Design Goals

### Primary Goals
1. **Simple Developer Experience**: Make calling Python from Dana feel natural
2. **Type Safety**: Clear and predictable type conversions
3. **Resource Management**: Explicit and clean resource handling
4. **Error Handling**: Meaningful error propagation
5. **Future Compatibility**: Design allows for future process isolation

### Non-Goals
1. ❌ General-purpose Python import system
2. ❌ Complex security boundaries in v1
3. ❌ Complete type safety guarantees
4. ❌ Memory space isolation in initial design

## Core Design

### 1. Basic Usage

```dana
# Simple function call
let result = python.eval("len('hello')")  # Returns 5

# Module import and use
let np = python.import("numpy")
let array = np.array([1, 2, 3])
let mean = np.mean(array)  # Returns 2.0

# Resource management
with python.open("file.txt", "r") as file:
    let content = file.read()
```

### 2. Type Mapping

| Dana Type | Python Type | Notes |
|-----------|-------------|-------|
| `int` | `int` | Direct mapping |
| `float` | `float` | Direct mapping |
| `string` | `str` | Direct mapping |
| `bool` | `bool` | Direct mapping |
| `list` | `list` | Recursive conversion |
| `dict` | `dict` | Recursive conversion |
| `null` | `None` | Direct mapping |
| `any` | `Any` | Type erasure |

### 3. Resource Management

```dana
# Context manager pattern
def process_file(path: string) -> string:
    with python.open(path, "r") as file:  # Automatically closes
        return file.read()

# Explicit cleanup
def work_with_resources():
    let resource = python.create_resource()
    try:
        return resource.do_work()
    finally:
        resource.close()
```

### 4. Error Handling

```dana
# Python exceptions become Dana errors
def safe_division(a: float, b: float) -> float:
    try:
        return python.eval("a / b", {"a": a, "b": b})
    catch PythonError as e:  # Wraps Python's ZeroDivisionError
        log.error("Division error: {}", e)
        return 0.0
```

## Implementation Strategy

### Phase 1: Core Integration (Current Focus)

#### Python Bridge Module
```python
class DanaPythonBridge:
    """Simple bridge for Dana to call Python."""
    
    def eval(self, code: str, globals: dict = None) -> Any:
        """Evaluate Python code in a controlled context."""
        try:
            return eval(code, globals or {})
        except Exception as e:
            raise DanaPythonError(str(e))
    
    def import_module(self, name: str) -> Any:
        """Import a Python module for Dana use."""
        try:
            return importlib.import_module(name)
        except ImportError as e:
            raise DanaPythonError(f"Cannot import {name}: {e}")
```

#### Dana Interface
```dana
# Core Python integration module
module python {
    # Simple evaluation
    def eval(code: string, globals: dict = null) -> any

    # Module import
    def import(name: string) -> any
    
    # Resource management
    def open(path: string, mode: string) -> any
    
    # Error types
    error PythonError {
        message: string
        type: string
    }
}
```

### Phase 2: Enhanced Features

1. **Better Type Conversion**
   - Support for more complex types
   - Custom type converters
   - Type hints and validation

2. **Resource Pool**
   - Managed Python interpreter instances
   - Resource cleanup tracking
   - Memory usage optimization

3. **Error Enhancement**
   - Detailed error mapping
   - Stack trace integration
   - Debug information

### Future: Process Isolation (Deferred)

The design allows for future process isolation:

```dana
# Future: Isolated Python execution
with python.isolated() as py:
    let result = py.eval("expensive_computation()")
```

## Security Considerations

### Phase 1 (Current)
- Basic input validation
- Resource limits
- Error containment

### Phase 2 (Future)
- Process isolation
- Memory limits
- Network restrictions

## Testing Strategy

```dana
# Example test cases
test "basic python integration" {
    let result = python.eval("2 + 2")
    assert result == 4
}

test "module import" {
    let math = python.import("math")
    assert math.pi > 3.14
}

test "resource management" {
    with python.open("test.txt", "w") as f:
        f.write("test")
    # File should be closed
}
```

## Migration Path

1. **Start Simple**
   ```dana
   # Begin with basic eval and import
   let result = python.eval("simple_function()")
   ```

2. **Add Resources**
   ```dana
   # Introduce resource management
   with python.managed_resource() as r:
       r.do_work()
   ```

3. **Enhance Features**
   ```dana
   # Later: Add type conversion, etc.
   let complex_obj = python.convert(dana_obj)
   ```

## Comparison with Python-to-Dana

| Feature | Python-to-Dana | Dana-to-Python |
|---------|-------------------|-------------------|
| Import System | Over-engineered | Simple direct import |
| Security Model | Complex boundaries | Basic validation |
| Resource Management | Complex pooling | Explicit contexts |
| Type System | Over-specified | Pragmatic mapping |

## Lessons Applied

1. **Kept Simple**
   - Single entry point (`python` module)
   - Direct function calls
   - Clear resource management

2. **Avoided Over-engineering**
   - No complex module system
   - Simple security model
   - Direct type mapping

3. **Future-proofed**
   - Design allows process isolation
   - Extensible type system
   - Resource management patterns

## Next Steps

1. **Implementation Priority**
   - Core `python` module
   - Basic type conversion
   - Resource management
   - Error handling

2. **Documentation**
   - Usage examples
   - Type mapping guide
   - Resource management patterns

3. **Testing**
   - Unit test suite
   - Integration tests
   - Performance benchmarks

## Example Use Cases

### 1. Data Processing with NumPy

```dana
def process_data(data: list[float]) -> dict:
    let np = python.import("numpy")
    let array = np.array(data)
    
    return {
        "mean": np.mean(array),
        "std": np.std(array),
        "min": np.min(array),
        "max": np.max(array)
    }
```

### 2. File Operations

```dana
def save_results(results: dict, path: string):
    let json = python.import("json")
    
    with python.open(path, "w") as f:
        json.dump(results, f)
```

### 3. Web Requests

```dana
def fetch_data(url: string) -> dict:
    let requests = python.import("requests")
    
    try:
        let response = requests.get(url)
        response.raise_for_status()
        return response.json()
    catch PythonError as e:
        log.error("Failed to fetch data: {}", e)
        return {"error": e.message}
}
```

## Conclusion

This design for Dana-to-Python integration:

1. **Learns from Experience**: Avoids over-engineering seen in Python-to-Dana
2. **Stays Simple**: Focuses on core use cases with minimal complexity
3. **Maintains Power**: Enables all key integration scenarios
4. **Future-Ready**: Design allows for future security and isolation enhancements

The key insight is that by focusing on pragmatic integration patterns and deferring unnecessary complexity, we can provide a more usable and maintainable solution.

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 