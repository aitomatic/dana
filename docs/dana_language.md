# DANA Language Specification

This document describes the syntax and semantics of the DANA language, used for defining simple state manipulation and execution flow within OpenDXA.

## Overview

DANA is designed to be a minimal, human-readable language focused on setting and getting values within a structured runtime context. It supports basic assignments, comments, and logging.

## Syntax

DANA programs consist of a sequence of statements executed line by line.

### 1. Assignment Statements

Assigns a value to a variable within a specific scope.

**Syntax:**
```dana
scope_name.variable_name = value
```

- `scope_name`: An identifier (letters, numbers, underscore, starting with a letter).
- `variable_name`: An identifier.
- `value`: Can be an integer (e.g., `10`, `-5`) or a string literal (e.g., `"hello"`, `"active"`). Strings must be enclosed in double quotes.

**Example:**
```dana
sensor1.temperature = 25
status.message = "System OK"
```

### 2. Comments

Lines starting with `#` are treated as comments and ignored during execution.

**Syntax:**
```dana
# This is a comment
```

**Example:**
```dana
# Set the initial configuration
config.port = 8080 # Use standard web port
```

### 3. Log Statements

Outputs a message to the console during program execution. This is primarily used for debugging or providing simple feedback on the program's progress.

**Syntax:**
```dana
log("message_string")
```

- `message_string`: A string literal enclosed in double quotes.

**Example:**
```dana
log("Starting sensor calibration...")
sensor.status = "calibrating"
# ... calibration steps ...
log("Calibration complete.")
```

## Runtime Context

DANA operates on a `RuntimeContext` which stores state in named scopes. Assignments modify this context, and future language features may read from it.

## Future Enhancements

Potential future additions include:
- Expressions (arithmetic, logical)
- Conditional statements (`if`)
- Reading variables from the context
- Function calls
- Loops 