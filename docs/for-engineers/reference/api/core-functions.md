# Core Functions API Reference

> **⚠️ IMPORTANT FOR AI CODE GENERATORS:**
> These are the official type signatures for Dana's core functions. Use these signatures when generating Dana code to ensure proper type checking and better code quality.

Dana provides essential core functions that are automatically available in all Dana programs. These functions have well-defined type signatures that help AI code generators write better Dana code.

## Table of Contents
- [AI/Reasoning Functions](#aireasoning-functions)
- [Output Functions](#output-functions)
- [Logging Functions](#logging-functions)
- [Function Lookup Precedence](#function-lookup-precedence)
- [Type Safety Guidelines](#type-safety-guidelines)
- [Implementation Status](#implementation-status)

---

## AI/Reasoning Functions

### `reason(prompt: str, options: dict = {}) -> str` {#reason}

LLM-powered reasoning and analysis function.

**Parameters:**
- `prompt: str` - The question or prompt to send to the LLM
- `options: dict` - Optional parameters for LLM configuration
  - `temperature: float` - Controls randomness (0.0-1.0, default: 0.7)
  - `max_tokens: int` - Maximum response length
  - `format: str` - Output format ("text" or "json")
  - `system_message: str` - Custom system message

**Returns:** `str` - The LLM's response to the prompt

**Examples:**
```dana
# Basic reasoning
analysis: str = reason("What is the weather like today?")

# With options for structured output
result: str = reason("Analyze this data", {
    "temperature": 0.3,
    "max_tokens": 200,
    "format": "json"
})

# Complex reasoning with context variables
temp: float = 75.5
humidity: int = 60
assessment: str = reason(f"Given temperature {temp}°F and humidity {humidity}%, is this comfortable?")

# Using system message for context
analysis: str = reason("What should I do next?", {
    "system_message": "You are a helpful assistant for project management.",
    "temperature": 0.5
})
```

**Security Notes:**
- The `reason()` function operates within the sandbox security model
- Prompts are sanitized before being sent to the LLM
- Response content is validated and safe for use in Dana programs

**Related Functions:**
- [`log()`](#log) - For logging reasoning operations
- [`print()`](#print) - For displaying reasoning results

---

## Output Functions

### `print(*args: any) -> None` {#print}

Print multiple values to standard output with space separation.

**Parameters:**
- `*args: any` - Variable number of arguments of any type to print

**Returns:** `None`

**Examples:**
```dana
# Print literals
print("Hello", "World", 123)
# Output: Hello World 123

# Print variables
name: str = "Alice"
age: int = 25
print("Name:", name, "Age:", age)
# Output: Name: Alice Age: 25

# Print expressions
x: int = 10
y: int = 20
print("Sum:", x + y)
# Output: Sum: 30

# Print complex data structures
user_data: dict = {"name": "Bob", "score": 95}
print("User data:", user_data)
# Output: User data: {'name': 'Bob', 'score': 95}

# Print multiple types
is_active: bool = true
scores: list = [85, 92, 78]
print("Active:", is_active, "Scores:", scores)
# Output: Active: true Scores: [85, 92, 78]
```

**Behavior:**
- Arguments are converted to string representation
- Multiple arguments are separated by single spaces
- Automatically adds newline at the end
- Handles all Dana data types (int, float, str, bool, list, dict, tuple, set, None)

**Related Functions:**
- [`log()`](#log) - For structured logging instead of simple output

---

## Logging Functions

### `log(message: str, level: str = "info") -> None` {#log}

Log a message with the specified level.

**Parameters:**
- `message: str` - The message to log
- `level: str` - Log level ("debug", "info", "warn", "error", default: "info")

**Returns:** `None`

**Examples:**
```dana
# Basic logging (info level)
log("Processing started")

# Different log levels
log("Debug information", "debug")
log("Operation completed successfully", "info")
log("Warning: High temperature detected", "warn")
log("Error occurred during processing", "error")

# Logging with variables
user_name: str = "Alice"
operation: str = "data_analysis"
log(f"Starting {operation} for user {user_name}", "info")

# Logging complex data
result: dict = {"status": "success", "count": 42}
log(f"Operation result: {result}", "info")
```

**Log Levels:**
- `"debug"` - Detailed information for debugging
- `"info"` - General information about program execution
- `"warn"` - Warning messages for potential issues
- `"error"` - Error messages for serious problems

**Behavior:**
- Messages are formatted with timestamp and level
- Log output depends on current log level setting (see [`log_level()`](#log_level))
- Messages below the current log level are filtered out

**Related Functions:**
- [`log_level()`](#log_level) - Set global logging level
- [`print()`](#print) - For simple output without log formatting

### `log_level(level: str) -> None` {#log_level}

Set the global logging level for the Dana runtime.

**Parameters:**
- `level: str` - The log level to set ("debug", "info", "warn", "error")

**Returns:** `None`

**Examples:**
```dana
# Set to show all messages
log_level("debug")
log("This debug message will be shown", "debug")

# Set to show only warnings and errors
log_level("warn")
log("This info message will be hidden", "info")
log("This warning will be shown", "warn")

# Set to show only errors
log_level("error")
log("This warning will be hidden", "warn")
log("This error will be shown", "error")

# Typical usage pattern
log_level("info")  # Set appropriate level for production
log("Application started", "info")
```

**Log Level Hierarchy:**
1. `"debug"` - Shows all messages (debug, info, warn, error)
2. `"info"` - Shows info, warn, error (hides debug)
3. `"warn"` - Shows warn, error (hides debug, info)
4. `"error"` - Shows only error messages

**Best Practices:**
- Use `"debug"` during development for detailed information
- Use `"info"` for production to see important events
- Use `"warn"` or `"error"` for production systems where you only want alerts

**Related Functions:**
- [`log()`](#log) - Log messages at specific levels

---

## Function Lookup Precedence

Dana follows a clear precedence order when resolving function calls:

1. **User-defined functions** (highest priority) - Functions defined in the current Dana file
2. **Core functions** (medium priority) - Essential Dana functions documented above
3. **Built-in functions** (lowest priority) - Pythonic built-ins like `len()`, `sum()`, `max()`

This ensures that:
- User code can override any built-in function if needed
- Core Dana functions maintain their essential behavior
- Built-in functions provide familiar Python-like functionality

**Example:**
```dana
# User-defined function overrides built-in
def len(obj):
    return "custom length function"

# This calls the user-defined function, not the built-in
result = len([1, 2, 3])  # Returns "custom length function"

# Core functions like reason() cannot be overridden for security
analysis = reason("What should I do?")  # Always calls core function
```

---

## Type Safety Guidelines

When using core functions in Dana code:

1. **Always specify types** for variables that will be passed to core functions
2. **Use type hints** on function parameters and return values
3. **Validate return types** when assigning core function results
4. **Handle optional parameters** explicitly when using options dictionaries

**Example of well-typed core function usage:**
```dana
# Type-safe core function usage
def analyze_data(data: dict, query: str) -> dict:
    # Log the operation with proper types
    log(f"Analyzing data with query: {query}", "info")
    
    # Get AI analysis with typed options
    options: dict = {
        "temperature": 0.5,
        "format": "json",
        "max_tokens": 500
    }
    analysis: str = reason(f"Analyze this data: {data} for: {query}", options)
    
    # Print results with type safety
    print("Analysis complete:", analysis)
    
    # Return structured result with proper typing
    result: dict = {
        "query": query,
        "analysis": analysis,
        "status": "complete",
        "timestamp": "2025-01-01T12:00:00Z"
    }
    return result

# Usage with type hints
user_data: dict = {"name": "Alice", "age": 25, "role": "engineer"}
search_query: str = "performance analysis"
result: dict = analyze_data(user_data, search_query)
```

---

## Implementation Status

| Function | Type Signature | Status | Notes |
|----------|---------------|--------|-------|
| `reason()` | `(prompt: str, options: dict = {}) -> str` | ✅ Complete | Full LLM integration with options |
| `print()` | `(*args: any) -> None` | ✅ Complete | Variadic arguments, any types |
| `log()` | `(message: str, level: str = "info") -> None` | ✅ Complete | Multiple log levels supported |
| `log_level()` | `(level: str) -> None` | ✅ Complete | Global log level configuration |

**📖 For implementation details and examples, see the core function modules in `opendxa/dana/sandbox/interpreter/functions/core/`**

---

## See Also

- **[Built-in Functions](built-in-functions.md)** - Pythonic built-in functions like `len()`, `sum()`, `max()`
- **[Type System](type-system.md)** - Complete type system documentation
- **[Function Calling](function-calling.md)** - Function calling and import system
- **[Scoping System](scoping.md)** - Variable scopes and security model

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 