<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md) | [Function System](functions.md)

# Dana Pythonic Built-in Functions

## Overview

Dana provides a comprehensive set of Pythonic built-in functions that are automatically available in all Dana code. These functions provide familiar Python-like functionality while maintaining Dana's security and type safety principles through a sophisticated **Dynamic Function Factory** architecture.

## Implementation Architecture

### Central Dispatch Design

The built-in functions use a **Dynamic Function Factory** approach that provides:

- **Single Source of Truth**: All built-in functions are defined in a configuration-driven factory class
- **Central Dispatch**: `PythonicFunctionFactory` creates and manages all built-in functions
- **Type Safety**: Comprehensive type validation with clear error messages
- **Security**: Sandboxed execution with safety guards and explicit function blocking
- **Performance**: No individual module loading overhead
- **Extensibility**: Easy to add new functions by updating factory configuration

### Function Lookup Precedence

Dana follows a clear precedence order when resolving function calls:

1. **User-defined functions** (highest priority) - Functions defined in the current Dana file
2. **Core functions** (medium priority) - Essential Dana functions like `reason()`, `print()`, `log()`
3. **Built-in functions** (lowest priority) - Pythonic built-ins like `len()`, `sum()`, `max()`

This ensures that user code can override any built-in function if needed, while core Dana functions maintain their essential behavior.

## Available Built-in Functions

### Numeric Functions

| Function | Description | Example Usage | Type Validation |
|----------|-------------|---------------|-----------------|
| `len(obj)` | Returns length of sequences/collections | `len([1, 2, 3])` → `3` | `list`, `dict`, `str`, `tuple` |
| `sum(iterable)` | Returns sum of numeric iterable | `sum([1, 2, 3])` → `6` | `list`, `tuple` |
| `max(iterable)` | Returns maximum value | `max([1, 3, 2])` → `3` | `list`, `tuple` |
| `min(iterable)` | Returns minimum value | `min([1, 3, 2])` → `1` | `list`, `tuple` |
| `abs(x)` | Returns absolute value | `abs(-5)` → `5` | `int`, `float` |
| `round(x, digits=0)` | Rounds to specified digits | `round(3.14159, 2)` → `3.14` | `float`, `int` |

### Type Conversion Functions

| Function | Description | Example Usage | Type Validation |
|----------|-------------|---------------|-----------------|
| `int(x)` | Converts to integer | `int("42")` → `42` | `str`, `float`, `bool` |
| `float(x)` | Converts to float | `float("3.14")` → `3.14` | `str`, `int`, `bool` |
| `bool(x)` | Converts to boolean | `bool(1)` → `true` | `str`, `int`, `float`, `list`, `dict` |

### Collection Functions

| Function | Description | Example Usage | Type Validation |
|----------|-------------|---------------|-----------------|
| `sorted(iterable)` | Returns sorted list | `sorted([3, 1, 2])` → `[1, 2, 3]` | `list`, `tuple` |
| `reversed(iterable)` | Returns reversed list | `reversed([1, 2, 3])` → `[3, 2, 1]` | `list`, `tuple`, `str` |
| `enumerate(iterable)` | Returns enumerated pairs | `enumerate(["a", "b"])` → `[[0, "a"], [1, "b"]]` | `list`, `tuple`, `str` |
| `list(iterable)` | Converts to list | `list((1, 2, 3))` → `[1, 2, 3]` | `list`, `tuple`, `str`, `range`, iterators |

### Logic Functions

| Function | Description | Example Usage | Type Validation |
|----------|-------------|---------------|-----------------|
| `all(iterable)` | True if all elements are truthy | `all([true, 1, "yes"])` → `true` | `list`, `tuple` |
| `any(iterable)` | True if any element is truthy | `any([false, 0, "yes"])` → `true` | `list`, `tuple` |

### Range Functions

| Function | Description | Example Usage | Type Validation |
|----------|-------------|---------------|-----------------|
| `range(start, stop, step=1)` | Generates range of numbers | `range(1, 4)` → `[1, 2, 3]` | `int` (multiple signatures) |

## Security Architecture

### Multi-Layered Security Model

Dana's built-in function security follows a comprehensive multi-layered approach:

#### 1. Function Classification System

Functions are classified into three categories:

- **Supported Functions**: Safe, validated functions available in Dana
- **Explicitly Unsupported Functions**: Dangerous functions blocked with detailed explanations
- **Unknown Functions**: Unrecognized functions handled with helpful guidance

#### 2. Explicit Function Blocking

Dana explicitly blocks dangerous Python built-ins with detailed security rationales:

##### Arbitrary Code Execution (Critical Security Risk)
```python
BLOCKED_FUNCTIONS = {
    "eval": "Arbitrary code evaluation bypasses all security controls",
    "exec": "Arbitrary code execution bypasses sandbox protections", 
    "compile": "Code compilation can create executable objects",
    "__import__": "Dynamic imports can load malicious modules"
}
```

##### File System Access (High Security Risk)
```python
BLOCKED_FUNCTIONS = {
    "open": "File system access bypasses sandbox isolation",
    "input": "User input can be used for injection attacks"
}
```

##### Introspection and Reflection (Medium Security Risk)
```python
BLOCKED_FUNCTIONS = {
    "globals": "Global namespace access reveals sensitive information",
    "locals": "Local namespace access can expose private data",
    "getattr": "Dynamic attribute access bypasses access controls",
    "setattr": "Dynamic attribute modification compromises object integrity",
    "hasattr": "Attribute existence checks reveal implementation details"
}
```

##### Memory and System Access (High Security Risk)
```python
BLOCKED_FUNCTIONS = {
    "memoryview": "Direct memory access bypasses sandbox protections",
    "bytearray": "Mutable byte arrays can be used for buffer attacks",
    "bytes": "Raw byte manipulation bypasses type safety"
}
```

#### 3. Type Validation System

Every function call undergoes strict type validation:

```python
def _validate_args(name: str, args: tuple, expected_signatures: List[tuple]):
    """Validate arguments against expected type signatures."""
    valid_signature = False
    
    for signature in expected_signatures:
        if len(args) == len(signature):
            if all(isinstance(arg, sig_type) for arg, sig_type in zip(args, signature)):
                valid_signature = True
                break
    
    if not valid_signature:
        arg_types = [type(arg).__name__ for arg in args]
        expected_sigs = [f"({', '.join(t.__name__ for t in sig)})" for sig in expected_signatures]
        raise TypeError(f"Invalid arguments for '{name}': got ({', '.join(arg_types)}), expected one of: {', '.join(expected_sigs)}")
```

#### 4. Execution Guards

Functions execute with safety guards:

```python
def _execute_with_guards(func: callable, args: tuple):
    """Execute function with safety guards."""
    # Current implementation with planned enhancements:
    # TODO: Add timeout and memory limits for production
    # TODO: Consider subprocess isolation for high-security environments
    return func(*args)
```

### Security Threat Analysis

| Threat Category | Risk Level | Mitigation Strategy | Implementation |
|----------------|------------|-------------------|----------------|
| **Arbitrary Code Execution** | Critical | Complete blocking of `eval`, `exec`, `compile`, `__import__` | Explicit unsupported function list |
| **File System Access** | High | Block `open`, `input`, file I/O functions | Explicit blocking with alternatives |
| **Memory Manipulation** | High | Block `memoryview`, `bytearray`, raw memory access | Type system enforcement |
| **Introspection Abuse** | Medium | Block `globals`, `locals`, `getattr`, `dir`, `vars` | Access control validation |
| **Type System Bypass** | Medium | Strict type validation on all function calls | Signature validation system |
| **DoS via Large Inputs** | Low | Planned: Argument size limits | Future enhancement |
| **Memory Exhaustion** | Low | Planned: Memory caps during execution | Future enhancement |
| **Infinite Loops** | Low | Planned: Timeout guards | Future enhancement |

### Security Reporting

The system provides comprehensive security reporting:

```python
def get_security_report() -> Dict[str, Any]:
    """Generate a security report of function restrictions."""
    return {
        "supported_functions": 15,  # Current count
        "unsupported_functions": 25+,  # Explicitly blocked
        "unsupported_by_reason": {
            "security_risk": ["globals", "locals", "getattr", ...],
            "arbitrary_code_execution": ["eval", "exec", "compile", ...],
            "file_system_access": ["open", "input", ...],
            "memory_safety": ["memoryview", "bytearray", ...]
        },
        "security_critical": ["eval", "exec", "open", "globals", ...]
    }
```

## Type Validation and Error Handling

### Comprehensive Type Checking

All built-in functions include comprehensive type validation with clear error messages:

```dana
# Valid usage
result = len([1, 2, 3])  # Returns 3

# Type error - clear error message
result = len(42)  # Error: Invalid arguments for 'len': got (int), expected one of: (list,), (dict,), (str,), (tuple,)
```

### Error Message Design

Error messages are designed to be:
- **Specific**: Exact type mismatch information
- **Helpful**: Show expected types and signatures
- **Educational**: Guide users toward correct usage
- **Secure**: Don't reveal sensitive implementation details

### Runtime Error Handling

Functions handle both validation errors and runtime errors:

```python
def dana_wrapper(context: SandboxContext, *args, **kwargs):
    # Type validation (pre-execution)
    cls._validate_args(name, args, signatures)
    
    # Execute with safety guards
    try:
        return cls._execute_with_guards(python_func, args)
    except Exception as e:
        # Runtime error handling (post-execution)
        raise SandboxError(f"Built-in function '{name}' failed: {str(e)}")
```

## Example Usage in Dana Code

### Data Processing Pipeline

```dana
# Data processing with built-ins
data = [1, 5, 3, 9, 2]
total = sum(data)           # 20
count = len(data)           # 5
average = total / count     # 4.0
maximum = max(data)         # 9
minimum = min(data)         # 1

# Statistical analysis
sorted_data = sorted(data)  # [1, 2, 3, 5, 9]
has_positive = any(x > 0 for x in data)  # true
all_positive = all(x > 0 for x in data)  # true
```

### Type Conversion and Validation

```dana
# String and type conversion
text_num = "42"
number = int(text_num)      # 42
decimal = float("3.14")     # 3.14
is_valid = bool(number)     # true

# List operations with type safety
mixed_data = ["1", "2", "3"]
numbers = [int(x) for x in mixed_data]  # [1, 2, 3]
reversed_nums = reversed(numbers)       # [3, 2, 1]
```

### Range Generation and Iteration

```dana
# Range generation
numbers = range(1, 6)       # [1, 2, 3, 4, 5]
evens = range(0, 10, 2)     # [0, 2, 4, 6, 8]
countdown = range(5, 0, -1) # [5, 4, 3, 2, 1]

# Enumeration for indexed processing
items = ["apple", "banana", "cherry"]
indexed = enumerate(items)  # [[0, "apple"], [1, "banana"], [2, "cherry"]]
```

## Integration with Existing Examples

The built-in functions are already being used in existing Dana examples:

```dana
# From examples/dana/na/data_analysis_pipeline.na
total_sales = sum(sales_data)
num_records = len(sales_data)
max_sale = max(sales_data)
sorted_sales = sorted(sales_data)
```

## Implementation Details

### File Structure

```
opendxa/dana/sandbox/interpreter/functions/pythonic/
├── __init__.py                 # Module initialization
└── function_factory.py        # Main factory implementation

tests/dana/sandbox/interpreter/functions/
├── test_pythonic_builtins.py      # Core functionality tests
├── test_unsupported_builtins.py   # Security and blocking tests
├── test_builtin_integration.py    # Integration tests
└── test_builtin_functions_comprehensive.py  # Comprehensive test suite
```

### Registration Process

```python
def register_pythonic_builtins(registry: FunctionRegistry) -> None:
    """Register all Pythonic built-in functions using the factory."""
    factory = PythonicFunctionFactory()
    
    # Register supported functions with lowest priority
    for function_name in factory.FUNCTION_CONFIGS:
        wrapper = factory.create_function(function_name)
        metadata = FunctionMetadata(source_file="<built-in>")
        metadata.context_aware = True
        metadata.is_public = True
        
        # Register with overwrite=False to respect lookup order
        registry.register(
            name=function_name,
            func=wrapper,
            func_type="python", 
            metadata=metadata,
            overwrite=False  # Don't overwrite higher priority functions
        )
    
    # Register handlers for unsupported functions
    for function_name in factory.UNSUPPORTED_FUNCTIONS:
        handler = create_unsupported_handler(function_name)
        # Register with detailed error messages
        registry.register(name=function_name, func=handler, ...)
```

### Testing Strategy

The implementation includes comprehensive testing:

1. **Unit Tests**: Individual function behavior and validation
2. **Integration Tests**: Function registry integration and lookup order
3. **Security Tests**: Blocking of dangerous functions with proper error messages
4. **Edge Case Tests**: Error handling, type validation, and boundary conditions
5. **Performance Tests**: Factory efficiency and memory usage

## Security Considerations

### Current Security Measures

1. **Explicit Function Blocking**: 25+ dangerous functions explicitly blocked
2. **Type Validation**: Strict type checking on all function calls
3. **Sandboxed Execution**: Functions execute within Dana's sandbox environment
4. **Access Control**: Functions respect Dana's scope and permission system
5. **Error Handling**: Secure error messages that don't leak sensitive information

### Planned Security Enhancements

1. **Execution Timeouts**: Prevent infinite loops and DoS attacks
2. **Memory Limits**: Cap memory usage during function execution
3. **Argument Size Limits**: Prevent large input DoS attacks
4. **Subprocess Isolation**: Consider process-level isolation for high-security environments
5. **Audit Logging**: Log all function calls for security monitoring

### Security Best Practices

1. **Principle of Least Privilege**: Only essential functions are available
2. **Defense in Depth**: Multiple layers of security validation
3. **Fail Secure**: Unknown functions are blocked by default
4. **Clear Error Messages**: Help users understand security restrictions
5. **Regular Security Review**: Ongoing evaluation of function safety

## Future Enhancements

### Planned Function Additions

- **String Functions**: `str.upper()`, `str.lower()`, `str.split()`, `str.join()`
- **Math Functions**: `math.sqrt()`, `math.pow()`, `math.floor()`, `math.ceil()`
- **Date/Time Functions**: Safe date manipulation and formatting
- **JSON Functions**: Safe JSON parsing and serialization

### Architecture Improvements

- **Plugin System**: Allow secure third-party function extensions
- **Performance Optimization**: Caching and optimization for frequently used functions
- **Enhanced Type System**: More sophisticated type validation and conversion
- **Async Support**: Asynchronous function execution capabilities

### Security Enhancements

- **Runtime Monitoring**: Real-time security monitoring and alerting
- **Behavioral Analysis**: Detect suspicious function usage patterns
- **Sandboxing Improvements**: Enhanced isolation and containment
- **Compliance Features**: Support for security compliance frameworks

---

## References

- [Dana Function System](functions.md)
- [Dana Security Model](../security/sandbox.md)
- [Dana Type System](../core-concepts/types.md)
- [Function Registry Architecture](../architecture/function-registry.md)

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 