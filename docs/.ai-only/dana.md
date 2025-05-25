<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)

# Dana (Domain-Aware NeuroSymbolic Architecture)

> **⚠️ IMPORTANT FOR AI CODE GENERATORS:**
> Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
> NEVER use dot notation: `private.x`, `public.x`, etc.
> Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.

## Overview

Dana is an imperative programming language and execution runtime designed specifically for agent reasoning. It enables intelligent agents to reason, act, and collaborate through structured, interpretable programs. Dana serves as the missing link between natural language objectives and tool-assisted, stateful action.

## Key Features

- 🧠 **Imperative Programming Language**: Clear, explicit control flow and state modification
- 📦 **Shared State Management**: Explicit state containers (`private`, `public`, `system`, `local`) 
- 🧩 **Structured Function Calling**: Clean interface to tools and knowledge bases
- 🧾 **First-Class Agent Reasoning**: Explicit LLM reasoning as a language primitive
- 📜 **Bidirectional Mapping with Natural Language**: Translation between code and plain English

## Core Components

### Parser

**Module**: `opendxa.dana.sandbox.parser`

The Dana language parser uses a grammar-based implementation with the Lark parsing library to convert Dana source code into an abstract syntax tree (AST). This provides:

- Robust error reporting with detailed error messages
- Extensibility through the formal grammar definition
- Strong type checking capabilities
- Support for language evolution and new features

```python
from opendxa.dana.sandbox.parser.dana_parser import DanaParser

parser = DanaParser()
result = parser.parse("private:x = 42\nprint(private:x)")

if result.is_valid:
    print("Parsed program:", result.program)
else:
    print("Errors:", result.errors)
```

### Interpreter

**Module**: `opendxa.dana.sandbox.interpreter`

The Dana interpreter executes Dana programs by evaluating the AST. Key components include:

- **DanaInterpreter**: Main entry point for program execution
- **StatementExecutor**: Executes statements (assignments, conditionals, loops, etc.)
- **ExpressionEvaluator**: Evaluates expressions (arithmetic, logical, identifiers, literals)
- **ContextManager**: Manages variable scope and sandbox state
- **SandboxContext**: Provides access to LLMResource for reasoning capabilities
- **FunctionRegistry**: Handles function and tool registrations

```python
from dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Create context
ctx = SandboxContext(private={}, public={}, system={}, local={})

# Initialize interpreter
interpreter = DanaInterpreter(ctx)

# Execute program from AST
output = interpreter.execute_program(ast)
```

### Transcoder

**Module**: `opendxa.dana.transcoder`

The Dana transcoder provides bidirectional translation between natural language and Dana code:

- **NL → Dana**: Convert natural language descriptions to valid Dana programs
- **Dana → NL**: Generate human-readable explanations of Dana code

```python
from opendxa.dana.transcoder.transcoder import Transcoder
from opendxa.common.resource.llm_resource import LLMResource

# Initialize transcoder
llm = LLMResource()
transcoder = Transcoder(llm)

# Convert natural language to Dana
nl_prompt = "If temperature exceeds 100 degrees, activate cooling system"
dana_code = transcoder.to_dana(nl_prompt)

# Explain Dana code in natural language
explanation = transcoder.to_natural_language(dana_code)
```

## Dana Language Syntax

Dana is an imperative programming language with syntax similar to Python, but with important differences:

```dana
# Variable assignment with explicit scopes
temperature = 98.6  # Auto-scoped to local (preferred)
public:weather = "sunny"

# Conditional logic
if temperature > 100:
    log.warn("Temperature exceeding threshold: {temperature}")
    status = "overheating"  # Auto-scoped to local
    
    # Function calling
    use("tools.cooling.activate")
else:
    log.info("Temperature normal: {temperature}")
    
# Explicit reasoning with LLMs - use private: only when needed for agent state
private:analysis = reason("Should we recommend a jacket?", 
                        context=[temperature, public:weather])

# Looping constructs
count = 0  # Auto-scoped to local
while count < 5:
    log.info("Count: {count}")
    count = count + 1
```

Key syntax elements:
- Explicit scope prefixes (`private:`, `public:`, `system:`, `local:`) - use colon notation only
- Prefer unscoped variables (auto-scoped to local) over explicit private: scope
- Standard imperative control flow (if/else, while)
- First-class `reason()` function for LLM integration
- Built-in logging with formatted strings
- Function/tool calling via `use()`

## State Management

Dana's imperative nature is evident in its explicit state management system. Every variable belongs to one of four scopes:

| Scope      | Description                                                      |
|------------|------------------------------------------------------------------|
| `local:`   | Local to the current agent/resource/tool/function (default scope)|
| `private:` | Private to the agent, resource, or tool itself                   |
| `public:`  | Openly accessible world state (time, weather, etc.)              |
| `system:`  | System-related mechanical state with controlled access           |

This enables clear, auditable state transitions and explicit data flow:

```dana
# Read from public state
if public:sensor_temp > 100:
    # Modify local state (preferred over private:)
    result = reason("Is this overheating?")
    
    # Conditionally modify system state
    if result == "yes":
        system:alerts.append("Overheat detected")
```

## Function System

Dana includes a robust function system that supports both Dana-native and Python functions:

### Local Dana Functions
```dana
func double(x):
    return x * 2
result = double(5)
```

### Importing Dana Modules
```dana
import my_utils.na as util
result = util.double(10)
```

### Importing Python Modules
```dana
import my_python_module.py as py
sum = py.add(1, 2)
```

## Integration with OpenDXA

Dana serves as the foundational execution layer within OpenDXA:
- Agents express their reasoning and actions through Dana programs
- The planning layer generates Dana code for execution
- Tool and resource integration happens through Dana function calls
- Debugging and tracking state changes is facilitated by Dana's explicit state model

## Common Tasks

### Running Dana Code

```python
from opendxa.dana import run
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Create runtime context
ctx = SandboxContext(private={}, public={}, system={}, local={})

# Run Dana code
dana_code = """
result = reason("What is the meaning of life?")
log.info("The meaning of life is {result}")
"""
run(dana_code, ctx)
```

### Using the Dana REPL

```bash
# Start the Dana REPL
python -m opendxa.dana.exec.repl.repl
```

### Converting Natural Language to Dana Code

```python
from opendxa.dana import compile_nl

# Compile natural language to Dana
nl_prompt = "If temperature is over 100, alert operations"
dana_code = compile_nl(nl_prompt)
print(dana_code)
```

## Benefits of Dana's Imperative Approach

- ✅ Clear, auditable program flow and state changes
- ✅ Familiar programming model for developers
- ✅ Explicit reasoning steps with traceable context
- ✅ Deterministic execution for predictable agent behavior
- ✅ Human-readable and explainable code
- ✅ Reusable logic patterns and modules
- ✅ Easy integration with existing tools and APIs

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>