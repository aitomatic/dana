<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md) | [For Engineers](../README.md) | [Reference](README.md)

# Dana API Reference

Complete reference documentation for the Dana programming language and runtime.

## 📚 API Documentation

### Core Language Features

| Document | Description | Key Topics |
|----------|-------------|------------|
| **[Core Functions](core-functions.md)** | Essential Dana functions | `reason()`, `log()`, `print()`, `log_level()` |
| **[Built-in Functions](built-in-functions.md)** | Pythonic built-in functions | `len()`, `sum()`, `max()`, `min()`, `abs()`, `round()` |
| **[Type System](type-system.md)** | Type hints and type checking | Variable types, function signatures, validation |
| **[Scoping System](scoping.md)** | Variable scopes and security | `private:`, `public:`, `system:`, `local:` |

### Advanced Features

| Document | Description | Key Topics |
|----------|-------------|------------|
| **[Function Calling](function-calling.md)** | Function calls and imports | Dana→Dana, Dana→Python, Python→Dana |
| **[Sandbox Security](sandbox-security.md)** | Security model and restrictions | Sandboxing, context isolation, safety |

## 🚀 Quick Start

### Basic Dana Program with Type Hints
```dana
# Variable type annotations
user_data: dict = {"name": "Alice", "age": 25}
temperature: float = 98.6
is_active: bool = true

# Function with typed parameters and return type
def analyze_user_data(data: dict, threshold: float) -> dict:
    # Use core functions with proper types
    log(f"Analyzing data for user: {data['name']}", "info")
    
    # AI reasoning with type hints
    analysis: str = reason(f"Analyze user data: {data}")
    
    # Return structured result
    return {
        "user": data["name"],
        "analysis": analysis,
        "temperature_ok": temperature < threshold,
        "status": "complete"
    }

# Call function with type safety
result: dict = analyze_user_data(user_data, 100.0)
print("Analysis result:", result)
```

## 📖 Function Reference Quick Lookup

### Core Functions
- **`reason(prompt: str, options: dict = {}) -> str`** - LLM-powered reasoning
- **`print(*args: any) -> None`** - Print output with space separation
- **`log(message: str, level: str = "info") -> None`** - Log messages
- **`log_level(level: str) -> None`** - Set global log level

### Built-in Functions
- **`len(obj: any) -> int`** - Get length of collections
- **`sum(iterable: list) -> any`** - Sum numeric values
- **`max(*args: any) -> any`** - Find maximum value
- **`min(*args: any) -> any`** - Find minimum value
- **`abs(x: any) -> any`** - Absolute value
- **`round(x: float, digits: int = 0) -> any`** - Round numbers

### Type System
- **Basic Types**: `int`, `float`, `str`, `bool`, `list`, `dict`, `tuple`, `set`, `None`, `any`
- **Function Signatures**: `def func(param: type) -> return_type:`
- **Variable Annotations**: `variable: type = value`

### Scoping
- **`private:`** - Private scope (function-local, secure)
- **`public:`** - Public scope (shared across contexts)
- **`system:`** - System scope (runtime configuration)
- **`local:`** - Local scope (default for function parameters)

## 🔍 Search by Use Case

### AI and Reasoning
- [Core Functions: `reason()`](core-functions.md#reason) - LLM integration
- [Type System: AI function signatures](type-system.md#ai-functions)

### Data Processing
- [Built-in Functions: Collections](built-in-functions.md#collections) - `len()`, `sum()`, `max()`, `min()`
- [Type System: Data types](type-system.md#data-types) - `list`, `dict`, `tuple`, `set`

### Logging and Output
- [Core Functions: Logging](core-functions.md#logging-functions) - `log()`, `log_level()`
- [Core Functions: Output](core-functions.md#output-functions) - `print()`

### Security and Isolation
- [Scoping System](scoping.md) - Variable scope security
- [Sandbox Security](sandbox-security.md) - Runtime security model

### Function Integration
- [Function Calling](function-calling.md) - Dana↔Python integration
- [Type System: Function signatures](type-system.md#function-signatures)

## 🛠️ Development Tools

### Type Checking
Dana provides comprehensive type checking with helpful error messages:
```dana
# Type validation
x: int = "hello"  # TypeError: Type hint mismatch: expected int, got string

# Mixed types work where appropriate
score: float = 100 + 1.5  # int + float = float (valid)
```

### Function Lookup Precedence
1. **User-defined functions** (highest priority)
2. **Core functions** (medium priority) 
3. **Built-in functions** (lowest priority)

### Security Model
- Type hints are **documentation only** - they don't bypass security
- Scope restrictions are **always enforced** regardless of type hints
- Context sanitization **always applies**

## 📋 Implementation Status

| Feature | Status | Documentation |
|---------|--------|---------------|
| Core Functions | ✅ Complete | [core-functions.md](core-functions.md) |
| Built-in Functions | ✅ Complete | [built-in-functions.md](built-in-functions.md) |
| Type System | ✅ Complete | [type-system.md](type-system.md) |
| Scoping System | ✅ Complete | [scoping.md](scoping.md) |
| Function Calling | ✅ Complete | [function-calling.md](function-calling.md) |
| Sandbox Security | ✅ Complete | [sandbox-security.md](sandbox-security.md) |

## 🤝 Contributing

Found an error or want to improve the API documentation? See our [contribution guidelines](../../../for-contributors/README.md).

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 