# Dana Language Reference

**Dana (Domain-Aware NeuroSymbolic Architecture)** is a Python-like programming language designed for AI-driven automation and agent systems. This comprehensive reference covers all syntax, conventions, and usage patterns.

## Overview

Dana is built for building domain-expert multi-agent systems with key AI-first features:
- Explicit scoping for agent state management
- Pipeline-based function composition
- Built-in AI reasoning capabilities
- Seamless Python interoperability
- Type safety with modern syntax

## Core Syntax Rules

### Comments
```dana
# Comments: Single-line only
# This is a comment
```

### Variable Scoping
Dana uses explicit scoping with colon notation to manage different types of state:

```dana
# Variables: Explicit scoping with colon notation (REQUIRED)
private:agent_state = "internal data"     # Agent-specific state
public:world_data = "shared information"  # World state (time, weather, etc.)
system:config = "system settings"        # System mechanical state
local:temp = "function scope"            # Local scope (default)

# Unscoped variables auto-get local: scope (PREFERRED)
temperature = 98.6  # Equivalent to local:temperature = 98.6
result = "done"     # Equivalent to local:result = "done"
```

**Scope Types:**
- `private:` - Agent-specific internal state
- `public:` - Shared world state (time, weather, etc.)
- `system:` - System mechanical configuration
- `local:` - Function/block scope (default for unscoped variables)

## Data Types & Literals

### Basic Types
```dana
# Basic types
name: str = "Alice"           # Strings (single or double quotes)
age: int = 25                 # Integers
height: float = 5.8           # Floats
active: bool = true           # Booleans (true/false, not True/False)
data: list = [1, 2, 3]        # Lists
info: dict = {"key": "value"} # Dictionaries
empty: None = null            # Null values

# F-strings for interpolation (REQUIRED for variable embedding)
message = f"Hello {name}, you are {age} years old"
log(f"Temperature: {temperature}°F")
```

**Key Differences from Python:**
- Booleans use `true`/`false` (not `True`/`False`)
- Null values use `null` (not `None`)
- F-strings are required for variable interpolation
- Type hints are mandatory for function definitions

## Function Definitions

### Basic Functions
```dana
# Basic function with type hints
def greet(name: str) -> str:
    return "Hello, " + name

# Function with default parameters
def log_message(message: str, level: str = "info") -> None:
    log(f"[{level.upper()}] {message}")
```

### Polymorphic Functions
Dana supports function overloading based on parameter types:

```dana
# Polymorphic functions (same name, different parameter types)
def describe(item: str) -> str:
    return f"String: '{item}'"

def describe(item: int) -> str:
    return f"Integer: {item}"

def describe(point: Point) -> str:
    return f"Point at ({point.x}, {point.y})"
```

## Structs (Custom Data Types)

### Defining Structs
```dana
# Define custom data structures
struct Point:
    x: int
    y: int

struct UserProfile:
    user_id: str
    display_name: str
    email: str
    is_active: bool
    tags: list
    metadata: dict
```

### Creating and Using Structs
```dana
# Instantiation with named arguments (REQUIRED)
p1: Point = Point(x=10, y=20)
user: UserProfile = UserProfile(
    user_id="usr_123",
    display_name="Alice Example",
    email="alice@example.com",
    is_active=true,
    tags=["beta_tester"],
    metadata={"role": "admin"}
)

# Field access with dot notation
print(f"Point coordinates: ({p1.x}, {p1.y})")
user.email = "new_email@example.com"  # Structs are mutable
```

**Important:** Struct instantiation requires named arguments - positional arguments are not supported.

## Function Composition & Pipelines

Dana's pipeline system enables powerful data transformation workflows:

### Pipeline Functions
```dana
# Define pipeline functions
def add_ten(x):
    return x + 10

def double(x):
    return x * 2

def stringify(x):
    return f"Result: {x}"
```

### Function Composition
```dana
# Function composition (creates reusable pipeline)
math_pipeline = add_ten | double | stringify
result = math_pipeline(5)  # "Result: 30"

# Data pipeline (immediate execution)
result = 5 | add_ten | double | stringify  # "Result: 30"
result = 7 | add_ten | double              # 34

# Complex data processing
person_builder = create_person | set_age_25 | add_skills
alice = "Alice" | person_builder
```

**Pipeline Operators:**
- `|` - Pipe operator for data flow
- Supports both function composition (reusable) and immediate execution
- Left-to-right data flow similar to Unix pipes

## Module System

### Dana Module Imports
```dana
# Dana module imports (NO .na extension)
import simple_math
import string_utils as str_util
from data_types import Point, UserProfile
from utils.text import title_case
```

### Python Module Imports
```dana
# Python module imports (REQUIRES .py extension)
import math.py
import json.py as j
from os.py import getcwd
```

### Usage Examples
```dana
# Usage
dana_result = simple_math.add(10, 5)      # Dana function
python_result = math.sin(math.pi/2)       # Python function
json_str = j.dumps({"key": "value"})      # Python with alias
```

**Key Rules:**
- Dana modules: NO `.na` extension in import
- Python modules: REQUIRES `.py` extension
- Aliases work with both Dana and Python modules

## Control Flow

### Conditionals
```dana
# Conditionals
if temperature > 100:
    log(f"Overheating: {temperature}°F", "warn")
    status = "critical"
elif temperature > 80:
    log(f"Running hot: {temperature}°F", "info")
    status = "warm"
else:
    status = "normal"
```

### Loops
```dana
# While loops
count = 0
while count < 5:
    print(f"Count: {count}")
    count = count + 1

# For loops
for item in data_list:
    process_item(item)
```

## Built-in Functions

### Collection Functions
```dana
# Collection functions
grades = [85, 92, 78, 96, 88]
student_count = len(grades)      # Length
total_points = sum(grades)       # Sum
highest = max(grades)            # Maximum
lowest = min(grades)             # Minimum
average = total_points / len(grades)
```

### Type Conversions
```dana
# Type conversions
score = int("95")                # String to int
price = float("29.99")           # String to float
rounded = round(3.14159, 2)      # Round to 2 decimals
absolute = abs(-42)              # Absolute value
```

### Collection Processing
```dana
# Collection processing
sorted_grades = sorted(grades)
all_passing = all(grade >= 60 for grade in grades)
any_perfect = any(grade == 100 for grade in grades)
```

## AI Integration

Dana provides built-in AI reasoning capabilities:

### Reasoning Functions
```dana
# Built-in reasoning with LLMs
analysis = reason("Should we recommend a jacket?", 
                 {"context": [temperature, public:weather]})

decision = reason("Is this data pattern anomalous?",
                 {"data": sensor_readings, "threshold": 95})
```

### Logging Functions
```dana
# Logging with different levels
log("System started", "info")
log(f"High temperature: {temperature}", "warn")
log("Critical error occurred", "error")
```

**Available Log Levels:**
- `"info"` - General information
- `"warn"` - Warning messages
- `"error"` - Error conditions
- `"debug"` - Debug information

## Dana vs Python Key Differences

### ✅ Correct Dana Syntax
```dana
private:state = "agent data"     # Explicit scoping
result = f"Value: {count}"       # F-strings for interpolation
import math.py                   # Python modules need .py
import dana_module               # Dana modules no extension
def func(x: int) -> str:         # Type hints required
    return f"Result: {x}"
point = Point(x=5, y=10)         # Named arguments for structs
```

### ❌ Incorrect (Python-style)
```dana
state = "agent data"             # Missing scope (auto-scoped to local:)
result = "Value: " + str(count)  # String concatenation instead of f-strings
import math                      # Missing .py for Python modules
def func(x):                     # Missing type hints
    return "Result: " + str(x)
point = Point(5, 10)             # Positional arguments not supported
```

## Common Patterns

### Error Handling
```dana
# Error handling
try:
    result = risky_operation()
except ValueError as e:
    log(f"Error: {e}", "error")
    result = default_value
```

### Data Validation
```dana
# Data validation
if isinstance(data, dict) and "key" in data:
    value = data["key"]
else:
    log("Invalid data format", "warn")
    value = None
```

### Agent State Management
```dana
# Agent state management
def update_agent_state(new_data):
    private:last_update = get_timestamp()
    private:agent_memory.append(new_data)
    return private:agent_memory
```

### Multi-step Data Processing
```dana
# Multi-step data processing
processed_data = raw_data | validate | normalize | analyze | format_output
```

## Best Practices

### Code Style
1. **Always use f-strings** for variable interpolation
2. **Include type hints** for all function parameters and return values
3. **Use explicit scoping** when managing agent state
4. **Prefer pipelines** for data transformation workflows
5. **Use named arguments** for struct instantiation

### Performance Considerations
1. **Pipeline composition** is more efficient than nested function calls
2. **Explicit scoping** helps with memory management in long-running agents
3. **Type hints** enable better optimization by the Dana runtime

### Security Guidelines
1. **Never expose private: state** to untrusted code
2. **Validate inputs** before processing with AI reasoning functions
3. **Use proper error handling** to prevent information leakage
4. **Limit system: scope access** to authorized components only

## Development Tools

### REPL (Read-Eval-Print Loop)
```bash
# Start Dana REPL for interactive development
uv run python -m opendxa.dana.exec.repl
```

### Execution
```bash
# Execute Dana files
uv run python -m opendxa.dana.exec.dana examples/dana/na/basic_math_pipeline.na
```

### Debugging
- Use `log()` function instead of `print()` for debugging
- Enable debug logging in transformer for AST output
- Test with existing `.na` files in `examples/dana/na/`

## Grammar Reference

The complete Dana grammar is defined in:
`opendxa/dana/sandbox/parser/dana_grammar.lark`

For detailed grammar specifications and language internals, see the design documents in `docs/design/01_dana_language_specification/`.