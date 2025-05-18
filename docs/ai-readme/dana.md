# DANA (Domain-Aware NeuroSymbolic Architecture)

## Overview

DANA is an imperative programming language and execution runtime designed specifically for agent reasoning. It enables intelligent agents to reason, act, and collaborate through structured, interpretable programs. DANA serves as the missing link between natural language objectives and tool-assisted, stateful action.

## Key Features

- 🧠 **Imperative Programming Language**: Clear, explicit control flow and state modification
- 📦 **Shared State Management**: Explicit state containers (`private`, `public`, `system`, `local`) 
- 🧩 **Structured Function Calling**: Clean interface to tools and knowledge bases
- 🧾 **First-Class Agent Reasoning**: Explicit LLM reasoning as a language primitive
- 📜 **Bidirectional Mapping with Natural Language**: Translation between code and plain English

## Core Components

### Parser

**Module**: `opendxa.dana.sandbox.parser`

The DANA language parser uses a grammar-based implementation with the Lark parsing library to convert DANA source code into an abstract syntax tree (AST). This provides:

- Robust error reporting with detailed error messages
- Extensibility through the formal grammar definition
- Strong type checking capabilities
- Support for language evolution and new features

```python
from opendxa.dana.sandbox.parser.dana_parser import DanaParser

parser = DanaParser()
result = parser.parse("private.x = 42\nprint(private.x)")

if result.is_valid:
    print("Parsed program:", result.program)
else:
    print("Errors:", result.errors)
```

### Interpreter

**Module**: `opendxa.dana.sandbox.interpreter`

The DANA interpreter executes DANA programs by evaluating the AST. Key components include:

- **Interpreter**: Main entry point for program execution
- **StatementExecutor**: Executes statements (assignments, conditionals, loops, etc.)
- **ExpressionEvaluator**: Evaluates expressions (arithmetic, logical, identifiers, literals)
- **ContextManager**: Manages variable scope and sandbox state
- **LLMIntegration**: Integrates with language models for advanced reasoning
- **FunctionRegistry**: Handles function and tool registrations

```python
from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Create context
ctx = SandboxContext(private={}, public={}, system={}, local={})

# Initialize interpreter
interpreter = Interpreter(ctx)

# Execute program from AST
output = interpreter.execute_program(ast)
```

### Transcoder

**Module**: `opendxa.dana.transcoder`

The DANA transcoder provides bidirectional translation between natural language and DANA code:

- **NL → DANA**: Convert natural language descriptions to valid DANA programs
- **DANA → NL**: Generate human-readable explanations of DANA code

```python
from opendxa.dana.transcoder.transcoder import Transcoder
from opendxa.common.resource.llm_resource import LLMResource

# Initialize transcoder
llm = LLMResource()
transcoder = Transcoder(llm)

# Convert natural language to DANA
nl_prompt = "If temperature exceeds 100 degrees, activate cooling system"
dana_code = transcoder.to_dana(nl_prompt)

# Explain DANA code in natural language
explanation = transcoder.to_natural_language(dana_code)
```

## DANA Language Syntax

DANA is an imperative programming language with syntax similar to Python, but with important differences:

```dana
# Variable assignment with explicit scopes
private.temperature = 98.6
public.weather = "sunny"

# Conditional logic
if private.temperature > 100:
    log.warn("Temperature exceeding threshold: {private.temperature}")
    private.status = "overheating"
    
    # Function calling
    use("tools.cooling.activate")
else:
    log.info("Temperature normal: {private.temperature}")
    
# Explicit reasoning with LLMs
private.analysis = reason("Should we recommend a jacket?", 
                        context=[private.temperature, public.weather])

# Looping constructs
count = 0
while count < 5:
    log.info("Count: {count}")
    count = count + 1
```

Key syntax elements:
- Explicit scope prefixes (`private.`, `public.`, `system.`, `local.`)
- Standard imperative control flow (if/else, while)
- First-class `reason()` function for LLM integration
- Built-in logging with formatted strings
- Function/tool calling via `use()`

## State Management

DANA's imperative nature is evident in its explicit state management system. Every variable belongs to one of four scopes:

| Scope      | Description                                                      |
|------------|------------------------------------------------------------------|
| `local:`   | Local to the current agent/resource/tool/function (default scope)|
| `private:` | Private to the agent, resource, or tool itself                   |
| `public:`  | Openly accessible world state (time, weather, etc.)              |
| `system:`  | System-related mechanical state with controlled access           |

This enables clear, auditable state transitions and explicit data flow:

```dana
# Read from public state
if public.sensor.temp > 100:
    # Modify private state
    private.result = reason("Is this overheating?")
    
    # Conditionally modify system state
    if private.result == "yes":
        system.alerts.append("Overheat detected")
```

## Function System

DANA includes a robust function system that supports both DANA-native and Python functions:

### Local DANA Functions
```dana
func double(x):
    return x * 2
result = double(5)
```

### Importing DANA Modules
```dana
import "my_utils.na" as util
result = util.double(10)
```

### Importing Python Modules
```dana
import "my_python_module.py" as py
sum = py.add(1, 2)
```

## Integration with OpenDXA

DANA serves as the foundational execution layer within OpenDXA:
- Agents express their reasoning and actions through DANA programs
- The planning layer generates DANA code for execution
- Tool and resource integration happens through DANA function calls
- Debugging and tracking state changes is facilitated by DANA's explicit state model

## Common Tasks

### Running DANA Code

```python
from opendxa.dana import run
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Create runtime context
ctx = SandboxContext(private={}, public={}, system={}, local={})

# Run DANA code
dana_code = """
private.result = reason("What is the meaning of life?")
log.info("The meaning of life is {private.result}")
"""
run(dana_code, ctx)
```

### Using the DANA REPL

```bash
# Start the DANA REPL
python -m opendxa.dana.repl.repl
```

### Converting Natural Language to DANA Code

```python
from opendxa.dana import compile_nl

# Compile natural language to DANA
nl_prompt = "If temperature is over 100, alert operations"
dana_code = compile_nl(nl_prompt)
print(dana_code)
```

## Benefits of DANA's Imperative Approach

- ✅ Clear, auditable program flow and state changes
- ✅ Familiar programming model for developers
- ✅ Explicit reasoning steps with traceable context
- ✅ Deterministic execution for predictable agent behavior
- ✅ Human-readable and explainable code
- ✅ Reusable logic patterns and modules
- ✅ Easy integration with existing tools and APIs