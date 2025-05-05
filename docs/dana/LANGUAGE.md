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

### `reason(prompt: str, context: list|var, temperature: float, format: str)`

Invokes the LLM with the `prompt`, optionally scoped to the `context` variables.
Returns a value to be stored or checked.

```python
# Basic usage
temp.analysis = reason("Is this machine in a failure state?")

# With context
temp.analysis = reason("Is this machine in a failure state?", context=world)

# With multiple context variables
temp.analysis = reason("Analyze this situation", context=[sensor, metrics, history])

# With temperature control
temp.ideas = reason("Generate creative solutions", temperature=0.9)

# With specific format (supports "json" or "text")
temp.data = reason("List 3 potential causes", format="json")
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

### 4. Logging Statements
```python
# Set log level
log_level = DEBUG  # Options: DEBUG, INFO, WARN, ERROR

# Log messages
log("message")  # INFO level by default
log(f"The temperature is {temp.value}")  # Supports f-strings
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
log_level = DEBUG  # Options: DEBUG, INFO, WARN, ERROR

# Log statements
log("Basic message")  # INFO level by default
log(f"The temperature is {temp.value}")  # With variable interpolation
```

Log levels determine which messages are displayed:
- DEBUG: Detailed information for debugging
- INFO: General information about program execution
- WARN: Warning messages for potentially harmful situations
- ERROR: Error messages for serious problems

Messages with a level lower than the set level will be filtered out. For example, if the level is set to "WARN", only WARN and ERROR messages will be displayed.

### How to Set Log Level

```python
# Set global log level to DEBUG
log_level = DEBUG

# Set global log level to INFO
log_level = INFO

# Set global log level to WARN
log_level = WARN

# Set global log level to ERROR
log_level = ERROR
```

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

* `foreach` loops
* `function` definitions
* Inline validations or constraints
* Data types: JSON schema-based records
* Policy flags (e.g., confidence threshold on `reason()`)

### Recently Added Features

* `while` loops - For repeating actions while a condition is true
```python
while temp.counter < 10:
    temp.counter = temp.counter + 1
    log(f"Counter is now {temp.counter}")
```

* Enhanced `reason()` function with additional parameters:
  - `temperature` - Controls randomness of LLM output
  - `format` - Allows specifying output format (e.g., "json", "text")
  - Support for multiple context variables via lists

---

## 🧪 Example Programs

### Basic Reasoning Example

```python
if world.system.temperature > 90:
    temp.eval = reason("Is this temperature abnormal?", context=world.system)
    if temp.eval == "yes":
        use("kb.maintenance.dispatch.v2")
        log(f"High temperature detected: {world.system.temperature}°C")
```

### Advanced Reasoning with Options

```python
// Use temperature parameter for more creative responses
ideas = reason("Generate solution ideas for the issue", temperature=0.8)

// Using the format parameter to get structured JSON
analysis = reason("Analyze system state and list problems", 
                 context=[world.sensors, world.alerts],
                 format="json")

// Present the analysis
log(f"Analysis found {analysis.problem_count} problems")
```

### Using While Loops

```python
counter = 0
while counter < 5:
    log(f"Checking sensor {counter}")
    reading = world.sensors[counter].value
    if reading > threshold:
        alert = reason(f"Analyze reading: {reading}", context=world.sensors[counter])
        log(f"Analysis result: {alert}")
    counter = counter + 1
```

---

## 🧰 Formal Grammar (Minimal EBNF)

```
program       ::= statement+
statement     ::= assignment | function_call | conditional | while_loop | log_statement | loglevel_statement | comment
assignment    ::= identifier '=' expression
expression    ::= literal | identifier | function_call | binary_expression | fstring_expression
function_call ::= 'reason' '(' string [',' 'context=' (identifier | list_expression)] [',' param '=' value]* ')'
                  | 'use' '(' string ')'
                  | 'set' '(' string ',' expression ')'
log_statement ::= 'log' '(' expression ')'
loglevel_statement ::= 'log_level' '=' level
conditional   ::= 'if' expression ':' NEWLINE INDENT program DEDENT [ 'else:' NEWLINE INDENT program DEDENT ]
while_loop    ::= 'while' expression ':' NEWLINE INDENT program DEDENT
comment       ::= ('//' | '#') .*

identifier    ::= [a-zA-Z_][a-zA-Z0-9_.]*
literal       ::= string | number | boolean | none
list_expression ::= '[' expression (',' expression)* ']'
fstring_expression ::= 'f' string
binary_expression ::= expression binary_op expression
binary_op     ::= '==' | '!=' | '<' | '>' | '<=' | '>=' | 'and' | 'or' | 'in' | '+' | '-' | '*' | '/'
level         ::= 'DEBUG' | 'INFO' | 'WARN' | 'ERROR'
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

## Recommendations for Improvement

  1. Complete the Parser Generator Transition
    - Fully implement and transition to the Lark-based parser
    - This would make syntax extensions far more manageable
    - Keep regex as fallback for backward compatibility
  2. Enhance the Type System
    - Introduce structured data types (records/objects)
    - Add collections (lists, maps) as first-class citizens
    - Consider gradual typing with optional annotations
  3. Formalize Extension Points
    - Develop a plugin system for language extensions
    - Standardize the registration of new language features
    - Create configuration-based extension loading
  4. Strengthen Error Recovery
    - Implement more robust error recovery during parsing
    - Add a repair mechanism for common syntax mistakes
    - Enhance debugging with better error visualization
  5. Complete the Knowledge Base
    - Develop the KB storage and retrieval mechanisms
    - Integrate program fragments as reusable components
    - Add versioning and dependency management

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
