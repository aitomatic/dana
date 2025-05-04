<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DANA Language Specification

## 📜 Purpose

DANA is a minimal, interpretable, and LLM-friendly program format for reasoning and tool-based execution. This document specifies the syntax, structure, and semantics of valid DANA programs.

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

### `reason(prompt: str, context: dict)`

Invokes the LLM with the `prompt`, scoped to the `context` substate.
Returns a value to be stored or checked.

```python
temp.analysis = reason("Is this machine in a failure state?", context=world)
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
reason("prompt", context=scope)
use("kb.entry.id")
set("key", value)
```

### 3. Conditional Statements
```python
if condition:
    # statements
elif condition:
    # statements
else:
    # statements
```

### 4. Logging Statements
```python
# Set log level
log.setLevel("DEBUG")  # Options: DEBUG, INFO, WARN, ERROR

# Log messages
log("message")  # INFO level by default
log.debug("message")
log.info("message")
log.warn("message")
log.error("message")
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
```python
agent:     # Agent identity and long-term traits
ltmem:     # Long-term memory
stmem:     # Short-term memory
temp:      # Ephemeral memory
world:     # External facts
execution: # Plan status
custom:    # User-defined scopes
```

---

## 📘 State Model

State variables are referenced using dot-scoped prefixes, organized by memory scope:

| Scope        | Description                                |
| ------------ | ------------------------------------------ |
| `agent:`     | Agent identity and long-term traits        |
| `ltmem:`     | Long-term memory — historical records      |
| `stmem:`     | Short-term memory — working session state  |
| `temp:`      | Ephemeral memory (step-local, volatile)    |
| `world:`     | External facts, observations               |
| `execution:` | Plan status, logs, transient execution     |
| *Custom:*    | User-defined scopes for isolated workflows |

Users may define workflow-specific scopes for clarity and modularity. These are treated like named namespaces within the runtime, e.g.:

```python
risk.temp_score = reason("Evaluate application risk", context=agent)
```

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

DANA supports logging statements with different severity levels and global log level configuration:

```python
# Set minimum level for log display
log.setLevel("DEBUG")  # Options: DEBUG, INFO, WARN, ERROR

# Log statements
log("Basic message")  # INFO level by default
log.debug("Debug message")
log.info("Info message")
log.warn("Warning message")
log.error("Error message")
```

Log levels determine which messages are displayed:
- DEBUG: Detailed information for debugging
- INFO: General information about program execution
- WARN: Warning messages for potentially harmful situations
- ERROR: Error messages for serious problems

Messages with a level lower than the set level will be filtered out. For example, if the level is set to "WARN", only WARN and ERROR messages will be displayed.

---

## 🔐 Safety

* `reason(...)` and `use(...)` should be treated as potentially fallible operations.
* Default behavior on error is soft-fail (e.g., `None` or default return) without interrupting program execution.
* Future support may include policies for retries or fallback logic outside the language core.
* All state changes occur via explicit `assign` or `set`
* No side-effects outside `context`
* Programs can be sandboxed by the host runtime

---

## 🔧 Future Extensions

The following features are **intentionally deferred** to preserve DANA's simplicity and clarity in early implementation. They may be added later as use cases justify their complexity.

* `loop`, `foreach`, `function` definitions
* Inline validations or constraints
* Data types: JSON schema-based records
* Policy flags (e.g., confidence threshold on `reason()`)

---

## 🧪 Example Program

```python
if world.system.temperature > 90:
    temp.eval = reason("Is this temperature abnormal?", context=world.system)
    if temp.eval == "yes":
        use("kb.maintenance.dispatch.v2")
        log.warn(f"High temperature detected: {world.system.temperature}°C")
```

---

## 🧰 Formal Grammar (Minimal EBNF)

```
program       ::= statement+
statement     ::= assignment | function_call | conditional | log_statement | comment
assignment    ::= identifier '=' expression
expression    ::= literal | identifier | function_call | binary_expression | fstring_expression
function_call ::= 'reason' '(' string ',' 'context=' identifier ')'
                  | 'use' '(' string ')'
                  | 'set' '(' string ',' expression ')'
log_statement ::= 'log' ('.' level)? '(' expression ')'
conditional   ::= 'if' expression ':' NEWLINE INDENT program DEDENT [ 'else:' NEWLINE INDENT program DEDENT ]
comment       ::= '#' .*

identifier    ::= [a-zA-Z_][a-zA-Z0-9_.]*
literal       ::= string | number | boolean | none
fstring_expression ::= 'f' string
binary_expression ::= expression binary_op expression
binary_op     ::= '==' | '!=' | '<' | '>' | '<=' | '>=' | 'and' | 'or' | 'in' | '+' | '-' | '*' | '/'
level         ::= 'debug' | 'info' | 'warn' | 'error'
```

* All blocks must be indented consistently
* No nested function calls (e.g. `if reason(...) == ...` not allowed)
* One instruction per line
* F-strings support expressions inside curly braces: `f"Value: {x}"`

---

## 🛯️ Fallback Handling Patterns

Fallback behavior can be encoded in programs via explicit branching:

```python
temp.result = reason("Diagnose failure", context=world)
if temp.result == None:
    temp.result = reason("Try again: Diagnose failure", context=world)
```

Or by delegating to alternate KB entries:

```python
if temp.result == "uncertain":
    use("kb.diagnostics.retry_logic.v1")
```

In the future, `reason(...)` or `use(...)` may accept optional fallback parameters:

```python
temp.result = reason("Classify", context=world.sensor, fallback="retry once")
```

Until then, soft failure + manual retry logic is preferred for clarity and control.

---

## 📤 Integration Notes

* DANA can be parsed from JSON or DSL
* AST structure mirrors the above
* Runtime evaluates node-by-node, mutating shared context

---

## 📚 Related Modules

* `dana.language.parser`: Converts text/JSON to AST
* `dana.runtime.interpreter`: Executes AST step-by-step
* `dana.transcoder.compiler`: Converts NL to DANA
* `dana.kb.loader`: Resolves `use(...)` entries

---

This spec will evolve with runtime capabilities, real-world use, and expressiveness requirements.

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
