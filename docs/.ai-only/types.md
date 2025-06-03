# Dana Type System: Design and Implementation

> **📖 For complete API documentation, see: [Type System API Reference](../for-engineers/reference/api/type-system.md)**

This document covers the **design and implementation details** of Dana's type hinting system. For usage examples, type signatures, and complete API documentation, please refer to the official API reference.

## Quick Links to API Documentation

| Topic | API Reference |
|-------|---------------|
| **Type System Overview** | [Type System API Reference](../for-engineers/reference/api/type-system.md) |
| **Function Type Signatures** | [Function Calling API Reference](../for-engineers/reference/api/function-calling.md#type-signatures) |
| **Core Functions with Types** | [Core Functions API Reference](../for-engineers/reference/api/core-functions.md) |
| **Built-in Functions with Types** | [Built-in Functions API Reference](../for-engineers/reference/api/built-in-functions.md) |

---

## Design Goals

### Primary Goal: Prompt Optimization
Type hints should help **AI code generators** write better Dana code by providing:
1. **Function signature clarity** - What parameters a function expects
2. **Return type clarity** - What a function returns
3. **Variable type documentation** - What data structures are expected

### Secondary Goals
1. **KISS/YAGNI Compliance** - Only implement what's needed for prompt optimization
2. **Sandbox Security** - Type hints must not compromise security model
3. **Backward Compatibility** - Existing Dana code continues to work

### Non-Goals (YAGNI)
- ❌ Complex type system with generics, unions, etc.
- ❌ Runtime type enforcement beyond current system
- ❌ Type-based function overloading
- ❌ Advanced type inference

---

## KISS Type Hinting Design

### Minimal Type Hint Syntax

#### 1. Function Parameter Hints (Primary Need)
```dana
# IMPLEMENTED: Simple parameter type hints
def process_user_data(data: dict) -> dict:
    return {"processed": data}

def calculate_area(width: float, height: float) -> float:
    return width * height

def log_message(message: str, level: str = "info") -> None:
    log(message, level)
```

#### 2. Variable Type Hints (Secondary Need)
```dana
# IMPLEMENTED: Simple variable type hints for documentation
user_data: dict = {"name": "Alice", "age": 25}
temperature: float = 98.6
is_active: bool = true
```

#### 3. Built-in Function Documentation (Critical for AI)
```dana
# Document actual return types of core functions
reasoning_result: str = reason("What should I do?")  # Usually returns str
json_result: dict = reason("Analyze data", {"format": "json"})  # Can return dict
log_result: None = log("Message", "info")  # Returns None
```

### Supported Types (KISS)

Only support the **basic types that already exist**:
- `int` - Integer numbers
- `float` - Floating point numbers  
- `str` - String literals
- `bool` - Boolean values
- `list` - List collections
- `dict` - Dictionary collections
- `tuple` - Tuple collections
- `set` - Set collections
- `None` - None/null values
- `any` - Any type (escape hatch)

**No generics, no unions, no complex types** - just basic documentation.

---

## Security Considerations

### Sandbox Security Integration

#### 1. Type Hints Don't Affect Runtime Security
```dana
# Type hints are documentation only - don't change security behavior
def process_sensitive_data(data: dict) -> dict:
    # Sandbox security still applies regardless of type hints
    private:result = sanitize(data)
    return private:result
```

#### 2. Scope Security Preserved
```dana
# Type hints work with existing scope system
private:sensitive_data: dict = {"password": "secret"}
public:safe_data: dict = {"count": 42}

def secure_function(data: dict) -> None:
    # Type checker should NOT bypass scope security
    # This should still be a security violation:
    # public:leaked = data  # Still blocked by sandbox
    pass
```

### Security Principles for Type Hints
1. **Documentation Only** - Type hints are metadata, not enforcement
2. **No Security Bypass** - Type hints cannot override scope restrictions
3. **No Privilege Escalation** - Type hints cannot grant additional permissions
4. **Sanitization Preserved** - Context sanitization still applies regardless of types

---

## Implementation Architecture

### Grammar & AST Integration

#### Grammar Changes
```lark
// Added to dana_grammar.lark
type_annotation: ":" basic_type
basic_type: "int" | "float" | "str" | "bool" | "list" | "dict" | "tuple" | "set" | "None" | "any"

// Extended function definition
function_def: "def" NAME "(" [typed_parameters] ")" [":" basic_type] ":" [COMMENT] block
typed_parameters: typed_parameter ("," typed_parameter)*
typed_parameter: NAME [":" basic_type] ["=" expr]

// Extended assignment for variable type hints
assignment: typed_target "=" expr | target "=" expr
typed_target: variable ":" basic_type
```

#### AST Extensions
- ✅ Added optional `type_hint` field to `FunctionDefinition`
- ✅ Added optional `parameter_types` to function parameters
- ✅ Added optional `type_hint` field to `Assignment`

### Parser Integration
- ✅ Updated `DanaParser` to handle type annotation syntax
- ✅ All existing Dana code still parses correctly
- ✅ Type hint information added to AST nodes

### Type Validation System
```python
def validate_type_hint(expected_type: str, actual_value: any) -> bool:
    """Validate that a value matches its type hint."""
    dana_type = get_dana_type(actual_value)
    return is_compatible_type(expected_type, dana_type)

def is_compatible_type(expected: str, actual: str) -> bool:
    """Check if types are compatible (e.g., int compatible with float)."""
    if expected == actual:
        return True
    
    # Special compatibility rules
    if expected == "float" and actual == "int":
        return True  # int can be used where float is expected
    
    if expected == "any":
        return True  # any accepts everything
    
    return False
```

---

## Implementation Status

### ✅ Completed Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Basic Types** | ✅ Complete | All 10 basic types: int, float, str, bool, list, dict, tuple, set, None, any |
| **Variable Annotations** | ✅ Complete | `variable: type = value` syntax |
| **Function Parameters** | ✅ Complete | `def func(param: type):` syntax |
| **Function Returns** | ✅ Complete | `def func() -> type:` syntax |
| **Type Validation** | ✅ Complete | Runtime validation with helpful error messages |
| **Mixed Typed/Untyped** | ✅ Complete | Full backward compatibility |
| **Arithmetic Compatibility** | ✅ Complete | int/float compatibility in operations |
| **Set Literals** | ✅ Complete | `{1, 2, 3}` syntax working correctly |
| **AST Integration** | ✅ Complete | TypeHint and Parameter objects in AST |
| **Parser Integration** | ✅ Complete | Grammar and transformer support |

### Testing Results
- ✅ **133/133 parser tests passed**
- ✅ **364/366 Dana tests passed** (2 pre-existing failures unrelated to type hints)
- ✅ **Zero regressions** in core functionality
- ✅ **Comprehensive type validation** testing
- ✅ **End-to-end integration** testing

---

## Future Enhancements

### Planned Features
- **Enhanced error messages** - More specific type mismatch descriptions
- **IDE integration** - Language server protocol support for type hints
- **Documentation generation** - Automatic API docs from type hints
- **Type inference improvements** - Better inference for complex expressions

### Advanced Type Features (Long-term)
- **Optional generics** - Basic generic support if needed for AI prompts
- **Union types** - Limited union support for common patterns
- **Type aliases** - Custom type names for complex structures

---

## Related Documentation

- **[Type System API Reference](../for-engineers/reference/api/type-system.md)** - Complete API documentation
- **[Function Calling API Reference](../for-engineers/reference/api/function-calling.md)** - Function type signatures
- **[Core Functions API Reference](../for-engineers/reference/api/core-functions.md)** - Core function types
- **[Built-in Functions API Reference](../for-engineers/reference/api/built-in-functions.md)** - Built-in function types

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 