<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[◀ DANA](./dana.md) | [Sandbox ▶︎](./sandbox.md)

# DANA Language Specification

## 📜 Purpose

DANA is a minimal, interpretable, and LLM-friendly program format for reasoning and tool-based execution. This document specifies the syntax, structure, and semantics of valid DANA programs.

For greater detail, see the [DANA Syntax](./syntax.md) document.

---

## 🧱 Program Structure

A DANA program is a sequence of **instructions**, optionally organized into **blocks**, executed linearly by the runtime.

```python
if world.sensor.temp > 100:
    temp.msg = reason("Is this overheating?", context=world.sensor)
    if temp.msg == "yes":
        execution.alerts.append("Overheat detected")
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
temp.status = "ok"
temp.result = reason("Explain this situation", context=world.system)
```

### `reason(prompt: str, context: list|var, temperature: float, format: str)`

Invokes the LLM with the `prompt`, optionally scoped to the `context` variables.
Returns a value to be stored or checked.

```python
# Basic usage
local.analysis = reason("Is this machine in a failure state?")

# With context
local.analysis = reason("Is this machine in a failure state?", context=world)

# With multiple context variables
local.analysis = reason("Analyze this situation", context=[sensor, metrics, history])

# With temperature control
local.ideas = reason("Generate creative solutions", temperature=0.9)

# With specific format (supports "json" or "text")
local.data = reason("List 3 potential causes", format="json")
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

## 📋 DANA Commands & Statements

Here's a complete list of all valid DANA commands and statements:

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
```python
# Literals
"string"
123
4.56
true
false
none

# F-strings
f"Value: {variable}"

# Binary Operations
a == b
a != b
a < b
a > b
a <= b
a >= b
a and b
a or b
a in b
a + b
a - b
a * b
a / b
```

### 6. Comments
```python
# This is a comment
```

### 7. State Scopes

Variables are referenced using dot-scoped prefixes, organized by memory scope:

| Scope      | Description                                |
| ---------- | ------------------------------------------ |
| `local:`   | Local to the current agent/resource/tool/function |
| `private:` | Private to the agent, resource, or tool itself |
| `public:`  | Openly accessible world state (time, weather, etc.) |
| `system:`  | System-related mechanical state with controlled access |

The `RuntimeContext` enforces strict scope boundaries and provides controlled access to state variables through dot notation. For example:

```python
# Local scope - internal state
local.user = "Alice"
user = "Alice" # same as local.user

# Public scope - shared world state
public.weather.temperature = 72
public.time.current = "2024-03-20T10:00:00Z"

# System scope - runtime state
system.status = "running"
system.log_level = "DEBUG"
```

### Scope Access Rules

1. **Local Scope**
   - Accessible only to the current agent/resource/tool/function
   - Used for internal state and temporary variables
   - Default scope for unqualified variables

2. **Private Scope**
   - Accessible only to the current agent/resource
   - Used for internal state and temporary variables

2. **Public Scope**
   - Accessible to all agents and resources
   - Used for shared world state and observations
   - Requires explicit scope prefix

3. **System Scope**
   - Controlled access for runtime configuration
   - Used for execution status and logging
   - Requires explicit scope prefix

### State Management

- Variables must be declared with their scope prefix
- Nested paths are supported (e.g., `private.user.profile.name`)
- Invalid scope access raises `StateError`
- State changes are tracked in execution history

---

## ✏️ Syntax Rules

* No functions, loops (yet)
* Only one instruction per line
* Nesting via indentation (Python-like)
* Identifiers follow `[a-zA-Z_][a-zA-Z0-9_.]*`
* Comments start with `#`
* F-strings supported with `f"..."` syntax for string interpolation

---

## ✅ Types

* **Strings**: "quoted" or f"interpolated {expression}"
* **Numbers**: 123, 4.56
* **Booleans**: true / false
* **Lists**: ["a", "b"] (in limited expressions only)
* **None**: null value

---

## 📝 Logging

DANA provides built-in logging capabilities through the `log` object. You can use different log levels:

```dana
log.debug("Debug message")
log.info("Info message")
log.warn("Warning message")
log.error("Error message")
```

The log level can be set using the `log.setLevel()` function:

```dana
log.setLevel("DEBUG")  # Set to debug level
log.setLevel("INFO")   # Set to info level
log.setLevel("WARN")   # Set to warning level
log.setLevel("ERROR")  # Set to error level
```

The log level determines which messages are displayed. For example, if the level is set to "WARN", only warning and error messages will be shown.

---

## 🔧 LLM Integration

### LLM Resource Configuration

To use `reason()` and other LLM-related functions, you need to set up an LLM resource in one of these ways:

1. **Environment Variables**: Set one of these in your environment:
   - `OPENAI_API_KEY` (for OpenAI models)
   - `ANTHROPIC_API_KEY` (for Claude models)
   - `AZURE_OPENAI_API_KEY` (for Azure OpenAI models)
   - `GROQ_API_KEY` (for Groq models)
   - `GOOGLE_API_KEY` (for Google models)

2. **Configuration File**: Create an `opendxa_config.json` file with preferred models:
   ```json
   {
     "preferred_models": [
       {
         "name": "anthropic:claude-3-sonnet-20240229",
         "required_api_keys": ["ANTHROPIC_API_KEY"]
       },
       {
         "name": "openai:gpt-4o-mini",
         "required_api_keys": ["OPENAI_API_KEY"]
       }
     ]
   }
   ```

3. **Explicit Registration**: Manually create and register an LLM resource:
   ```python
   from opendxa.common.resource.llm_resource import LLMResource
   from opendxa.dana.runtime.context import RuntimeContext

   context = RuntimeContext()
   llm = LLMResource(name="reason_llm")
   await llm.initialize()  # Always initialize before use
   context.register_resource("llm", llm)
   ```

### Troubleshooting Reason Statements

If you see `Error in reason statement: Resource not found: llm`, check:

1. Your environment variables are set correctly
2. You have a valid API key for one of the supported LLM providers
3. The LLM resource was properly initialized and registered
4. Network connectivity to the LLM provider's API

For more advanced LLM configurations, refer to the `LLMResource` class documentation.

---

## 🧪 Example Programs

### Basic Reasoning Example

```python
if public.system.temperature > 90:
    eval = reason("Is this temperature abnormal?", context=public.system)
    if eval == "yes":
        use("kb.maintenance.dispatch.v2")
        log(f"High temperature detected: {public.system.temperature}°C")
```

### Advanced Reasoning with Options

```python
# Use temperature parameter for more creative responses
ideas = reason("Generate solution ideas for the issue", temperature=0.8)

# Using the format parameter to get structured JSON
analysis = reason("Analyze system state and list problems",
                 context=[public.sensors, public.alerts],
                 format="json")

# Present the analysis
log(f"Analysis found {problem_count} problems")
```

### Using While Loops

```python
counter = 0
while counter < 5:
    log(f"Checking sensor {counter}")
    reading = sensors[counter].value
    if reading > threshold:
        alert = reason(f"Analyze reading: {reading}", context=sensors[counter])
        log(f"Analysis result: {alert}")
    counter = counter + 1
```

---

## 🧰 Formal Grammar

The formal grammar for the DANA language is now maintained in [grammar.md](./grammar.md) and is kept in sync with the Lark grammar and parser implementation. Please refer to that document for the most up-to-date EBNF and syntax rules.

---

This spec will evolve with runtime capabilities, real-world use, and expressiveness requirements.

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
