# DANA Language Syntax Reference

DANA is a domain-specific language designed for AI-driven automation and reasoning. This document provides a comprehensive reference for DANA's syntax and language features.

## Basic Syntax

### Comments
```dana
# This is a single-line comment
```

### Variables and Scoping

DANA has a structured scoping system with three standard scopes:
- `private`: Private to the agent, resource, or tool itself
- `public`: Openly accessible world state (time, weather, etc.)
- `system`: System-related mechanical state with controlled access

Variables must be prefixed with their scope:
```dana
private.my_variable = value
public.shared_data = value
system.status = value
```

For convenience in the REPL environment, variables without a scope prefix are automatically placed in the `private` scope:
```dana
my_variable = value  # Equivalent to private.my_variable = value
```

### Basic Data Types
- Strings: `"double quoted"` or `'single quoted'`
- Numbers: `42` or `3.14`
- Booleans: `true` or `false`
- Null: `null`
- Arrays: `[1, 2, 3]`

### String Interpolation (F-strings)
```dana
f"Hello {name}!"
```

## Statements

### Print Statement
```dana
print("Hello, World!")
```

### Logging
```dana
log("Info message")  # Default level is INFO
log.info("Info message")
log.debug("Debug message")
log.warn("Warning message")
log.error("Error message")

# Set global log level
log.setLevel("INFO")  # or "DEBUG", "WARN", "ERROR"
```

### Conditional Statements
```dana
if condition:
    # statements
else:
    # statements
```

### While Loops
```dana
while condition:
    # statements
```

### Reasoning Statements
```dana
# Basic reasoning
reason("What is the capital of France?")

# Store result in variable
result = reason("What is 2 + 2?")

# With context variables
reason("Analyze this data", context=[private.data_variable])

# With options
reason("Generate a response", temperature=0.7, max_tokens=100)
```

## Expressions

### Binary Operators
- Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Logical: `and`, `or`
- Arithmetic: `+`, `-`, `*`, `/`, `%`

### Operator Precedence
1. Parentheses `()`
2. Multiplication/Division/Modulo `*`, `/`, `%`
3. Addition/Subtraction `+`, `-`
4. Comparison `<`, `>`, `<=`, `>=`, `==`, `!=`
5. Logical `and`, `or`

### Function Calls
```dana
function_name(arg1, arg2)
function_name(named_arg=value)
function_name(pos_arg, named_arg=value)
```

## Best Practices

1. Always use explicit scope prefixes for clarity
2. Use meaningful variable names
3. Add comments for complex logic
4. Use appropriate log levels for debugging
5. Structure complex reasoning tasks with clear prompts
6. Use context variables to provide relevant information to reasoning tasks

## Examples

### Basic Program with Scoping
```dana
# Set up logging
log.setLevel("INFO")

# Define variables with explicit scopes
private.name = "World"
public.count = 5
system.status = "active"

# Use f-strings
message = f"Hello {private.name}!"

# Print and log
print(message)
log.info(f"Count is {public.count}")

# Conditional logic
if public.count > 3:
    log.warn("Count is high")
else:
    log.info("Count is normal")

# Reasoning with context
result = reason("Analyze the count", context=[public.count], temperature=0.7)
```

### Complex Reasoning with Scoped Variables
```dana
# Define data in appropriate scopes
private.data = [1, 2, 3, 4, 5]
public.threshold = 3
system.analysis_mode = "detailed"

# Analyze with reasoning
analysis = reason(
    "Analyze if the data exceeds the threshold",
    context=[private.data, public.threshold],
    temperature=0.5
)

# Use the result
if analysis:
    log.info("Analysis complete")
```
