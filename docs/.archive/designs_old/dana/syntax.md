# Dana Language Syntax Reference

Dana is a domain-specific language designed for AI-driven automation and reasoning. This document provides a comprehensive reference for Dana's syntax and language features, as supported by the current grammar and runtime.

## Dana vs. Python: Quick Comparison

- Dana's syntax is intentionally similar to Python: indentation, assignments, conditionals, loops, and function calls all look familiar.
- Dana requires explicit scope prefixes for variables (e.g., `private:x`, `public:y`), unlike Python.
- Dana only supports single-line comments with `#` (no docstrings).
- Dana supports f-strings with embedded expressions (e.g., `f"Value: {x+1}"`).
- Some advanced Python features (like comprehensions, decorators, or dynamic typing) are not present in Dana.

## Basic Syntax

### Comments
```dana
# This is a single-line comment
```

### Variables and Scoping

Dana has a structured scoping system with four standard scopes:
- `private`: Private to the agent, resource, or tool itself
- `public`: Openly accessible world state (time, weather, etc.)
- `system`: System-related mechanical state with controlled access
- `local`: Local scope for the current execution (implicit in most cases)

Variables must be prefixed with their scope:
```dana
private:my_variable = value
public:shared_data = value
system:status = value
```

For convenience in the REPL environment, variables without a scope prefix are automatically placed in the `local` scope:
```dana
my_variable = value  # Equivalent to local:my_variable = value
```

### Basic Data Types
- Strings: "double quoted" or 'single quoted'
- Numbers: 42 or 3.14
- Booleans: true or false
- Null: null

## Statements

### Assignment
```dana
private:x = 10
public:message = "Hello"
```

### Conditional Statements
```dana
if private:x > 5:
    print("x is greater than 5")
else:
    print("x is not greater than 5")
```

### While Loops
```dana
while private:x < 10:
    print(private:x)
    private:x = private:x + 1
```

### Function Calls
```dana
system:math.sqrt(16)
public:result = system:math.max(3, 7)
print("Hello, World!")
print(private:x)
```

### Bare Identifiers
A bare identifier (just a variable or function name) is allowed as a statement, typically for REPL inspection:
```dana
private:x
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

### Function Calls in Expressions
```dana
private:y = system:math.sqrt(private:x)
```

## Best Practices

1. Always use explicit scope prefixes for clarity
2. Use meaningful variable names
3. Add comments for complex logic
4. Structure code with clear indentation for blocks

## Examples

### Basic Program with Scoping
```dana
# Define variables with explicit scopes
private:name = "World"
public:count = 5
system:status = "active"

# Print
print("Hello, " + private:name)
print(public:count)

# Conditional logic
if public:count > 3:
    print("Count is high")
else:
    print("Count is normal")
```

### While Loop Example
```dana
private:x = 0
while private:x < 3:
    print(private:x)
    private:x = private:x + 1
```

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>