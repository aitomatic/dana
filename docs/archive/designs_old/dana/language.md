# Dana Language Specification

## 📜 Purpose

Dana is a minimal, interpretable, and LLM-friendly program format for reasoning and tool-based execution. This document specifies the syntax, structure, and semantics of valid Dana programs.

For greater detail, see the [Dana Syntax](./syntax.md) document.

> **⚠️ IMPORTANT FOR AI CODE GENERATORS:**
> Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
> NEVER use dot notation: `private.x`, `public.x`, etc.
> Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.

---

## 🧱 Program Structure

A Dana program is a sequence of **instructions**, optionally organized into **blocks**, executed linearly by the runtime.

```python
if private:sensor_temp > 100:
    msg = reason("Is this overheating?", context=sensor_data)
    if msg == "yes":
        system:alerts.append("Overheat detected")
```

Supported constructs:

* Variable assignment
* Conditionals (`if`, nested)
* Calls to `reason(...)`, `use(...)`, `set(...)`
* Simple expressions: comparisons, booleans, contains

---

## 📜 Instruction Reference

### `assign`

Assign a literal, expression, or result of a function call to a state key.

```python
status = "ok"  # Auto-scoped to local (preferred)
result = reason("Explain this situation", context=system_data)
```

### `reason(prompt: str, context: list|var, temperature: float, format: str)`

Invokes the LLM with the `prompt`, optionally scoped to the `context` variables.
Returns a value to be stored or checked.

```python
# Basic usage
analysis = reason("Is this machine in a failure state?")

# With context
analysis = reason("Is this machine in a failure state?", context=world_data)

# With multiple context variables
analysis = reason("Analyze this situation", context=[sensor, metrics, history])

# With temperature control
ideas = reason("Generate creative solutions", temperature=0.9)

# With specific format (supports "json" or "text")
data = reason("List 3 potential causes", format="json")
```

### `use(id: str)`

Loads and executes a Knowledge Base (KB) entry or another sub-program.

```python
use("kb.finance.eligibility.basic_check.v1")
```

### `set(key, value)` *(Optional form)*

Directly sets a value in the runtime context.

```python
set("agent.status", "ready")
```

### `if` / `elif` / `else`

Basic conditional branching. Conditions are boolean expressions over state values.

```python
if agent.credit.score < 600:
    agent.risk.level = "high"
```

---

## 📋 Dana Commands & Statements

Here's a complete list of all valid Dana commands and statements:

### 1. Variable Assignment
```python
variable = value
scope.variable = value
```

### 2. Function Calls
```python
# Reasoning with various parameters
reason("prompt")
reason("prompt", context=scope)
reason("prompt", context=[var1, var2, var3])
reason("prompt", temperature=0.8)
reason("prompt", format="json")

# Other function calls
use("kb.entry.id")
set("key", value)
```

### 3. Conditional and Loop Statements
```python
# If/elif/else conditionals
if condition:
    # statements
elif condition:
    # statements
else:
    # statements

# While loops
while condition:
    # statements
```

### 4. Output Statements
```python
# Set log level
log_level = DEBUG  # Options: DEBUG, INFO, WARN, ERROR

# Log messages with levels and metadata
log("message")  # INFO level by default
log.debug("Debug information")
log.info("Information message")
log.warn("Warning message")
log.error("Error message")
log(f"The temperature is {temp.value}")  # Supports f-strings

# Print messages to standard output (without log metadata)
print("Hello, world!")
print(42)
print(variable_name)
print("The result is: " + result)
```

### 5. Expressions
```