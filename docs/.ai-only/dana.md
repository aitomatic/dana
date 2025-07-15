# Dana Language Reference

**Dana (Domain-Aware NeuroSymbolic Architecture)** is a Python-like programming language designed for AI-driven automation and agent systems. This comprehensive reference covers all syntax, conventions, and usage patterns.

## Overview

Dana is built for building domain-expert multi-agent systems with key AI-first features:
- Explicit scoping for agent state management
- Pipeline-based function composition
- Built-in AI reasoning capabilities
- Seamless Python interoperability
- Type safety with modern syntax
- **Agent Capability Packs** for domain-specific expertise infusion

## Dana's GoLang-like Functional Nature

Dana follows a **functional programming paradigm** similar to Go, where functions are **standalone entities** rather than methods bound to objects. This design promotes clean separation of concerns and composable code.

### Key Principles

1. **Functions are First-Class Citizens**: Functions can be passed as arguments, returned from other functions, and composed together
2. **Structs are Data Containers**: Structs hold data but don't contain methods
3. **Explicit Dependencies**: Functions explicitly receive the data they operate on as parameters
4. **Composable Design**: Functions can be easily combined into pipelines and workflows

### Function Definition and Usage

```dana
# Functions are standalone - they don't belong to structs
def calculate_area(rectangle: Rectangle) -> float:
    return rectangle.width * rectangle.height

def validate_rectangle(rectangle: Rectangle) -> bool:
    return rectangle.width > 0 and rectangle.height > 0

# Functions can be composed and passed around
area_calculator = calculate_area
validator = validate_rectangle

# Functions can be used in pipelines
result = rectangle | validate_rectangle | calculate_area
```

### Structs as Pure Data Containers

```dana
# Structs only contain data fields - no methods
struct Rectangle:
    width: float
    height: float
    color: str

# Creating instances with named arguments
rect = Rectangle(width=10.0, height=5.0, color="blue")

# Accessing fields
area = rect.width * rect.height
```

### Agent Keyword and Type Declaration

The `agent` keyword in Dana is a **type declaration** that creates a specialized struct type for agents:

```dana
# agent keyword creates a new agent type
agent ProSEAAgent:
    DanaAgent  # Inherits from base DanaAgent struct
    
    # Declarative properties define agent capabilities
    domains: list[str] = ["semiconductor_manufacturing"]
    tasks: list[str] = ["wafer_inspection", "defect_classification"]
    capabilities: list[str] = ["optical_analysis", "pattern_recognition"]
    knowledge_sources: list[str] = ["equipment_specs", "historical_data"]

# This creates a new type 'ProSEAAgent' that can be used in function signatures
def diagnose_wafer(agent: ProSEAAgent, image_data: bytes) -> DefectReport:
    # Function operates on the agent instance
    pass
```

### Function Parameters and Agent Usage

Functions that work with agents receive the agent instance as an explicit parameter:

```dana
# Functions explicitly receive agent as parameter (GoLang-style)
def solve_request(agent: ProSEAAgent, request: str) -> str:
    # Access agent properties
    if request in agent.tasks:
        return process_request(agent, request)
    else:
        return "Cannot handle this request"

def initialize_agent(agent: ProSEAAgent) -> bool:
    # Set up agent resources
    agent.is_active = true
    return true

# Usage - pass agent instance explicitly
my_agent = ProSEAAgent()
initialize_agent(my_agent)
response = solve_request(my_agent, "inspect wafer")
```

### Contrast with Object-Oriented Languages

```dana
# Dana (Functional/GoLang-style) - Functions are standalone
def process_data(agent: MyAgent, data: list) -> list:
    return agent.transform(data)

# Usage
result = process_data(my_agent, raw_data)

# vs Object-Oriented (Python/Java) - Methods belong to objects
# class MyAgent:
#     def process_data(self, data):
#         return self.transform(data)
# 
# result = my_agent.process_data(raw_data)
```

### Benefits of This Approach

1. **Explicit Dependencies**: It's clear what data each function needs
2. **Easy Testing**: Functions can be tested in isolation
3. **Composability**: Functions can be easily combined into pipelines
4. **No Hidden State**: All dependencies are explicit parameters
5. **Type Safety**: Clear function signatures with type hints

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

Dana's enhanced pipeline system enables powerful data transformation workflows with both sequential and parallel execution:

### Pipeline Functions
```dana
# Define pipeline functions
def add_ten(x):
    return x + 10

def double(x):
    return x * 2

def stringify(x):
    return f"Result: {x}"

def analyze(x):
    return {"value": x, "is_even": x % 2 == 0}

def format(x):
    return f"Formatted: {x}"
```

### Enhanced Function Composition
```dana
# Sequential composition (creates reusable pipeline)
math_pipeline = add_ten | double | stringify
result = math_pipeline(5)  # "Result: 30"

# Standalone parallel composition
parallel_pipeline = [analyze, format]
result = parallel_pipeline(10)  # [{"value": 10, "is_even": true}, "Formatted: 10"]

# Mixed sequential + parallel
mixed_pipeline = add_ten | [analyze, format] | stringify
result = mixed_pipeline(5)  # "Result: [{"value": 15, "is_even": false}, "Formatted: 15"]"

# Complex multi-stage pipeline
workflow = add_ten | [analyze, double] | format | [stringify, analyze]
result = workflow(5)  # [{"value": 30, "is_even": true}, {"value": 30, "is_even": true}]
```

### Reusable Pipeline Objects
```dana
# Create reusable pipeline
data_processor = add_ten | [analyze, format]

# Apply to different datasets
result1 = data_processor(5)   # [{"value": 15, "is_even": false}, "Formatted: 15"]
result2 = data_processor(10)  # [{"value": 20, "is_even": true}, "Formatted: 20"]
result3 = data_processor(15)  # [{"value": 25, "is_even": false}, "Formatted: 25"]
```

### Argument Passing in Pipelines

Dana provides three flexible ways to pass arguments in pipelines and function composition:

#### 1. Implicit First Parameter (Default)
```dana
# Functions receive the pipeline value as their first parameter
def add_ten(x: int) -> int:
    return x + 10

def double(x: int) -> int:
    return x * 2

def stringify(x: int) -> str:
    return f"Result: {x}"

# Pipeline automatically passes the value as first parameter
pipeline = add_ten | double | stringify
result = pipeline(5)  # "Result: 30"
# Flow: 5 → add_ten(5) → 15 → double(15) → 30 → stringify(30) → "Result: 30"
```

#### 2. Explicit Position with $$ Placeholder
```dana
# Use $$ to specify where the pipeline value should be inserted
def format_with_prefix(prefix: str, value: int) -> str:
    return f"{prefix}: {value}"

def multiply_by_factor(factor: int, value: int) -> int:
    return value * factor

# $$ represents the result of the immediately preceding function
pipeline = add_ten | multiply_by_factor(3, $$)
result = pipeline(10)  # 20 → 60
# Flow: 10 → add_ten(10) = 20 → multiply_by_factor(3, 20) = 60

# Example with string formatting
def format_number(value: int) -> str:
    return f"Number: {value}"

def append_suffix(text: str, suffix: str) -> str:
    return f"{text} {suffix}"

pipeline = format_number | append_suffix($$, "is ready")
result = pipeline(42)  # "Number: 42" → "Number: 42 is ready"
# Flow: 42 → format_number(42) = "Number: 42" → append_suffix("Number: 42", "is ready") = "Number: 42 is ready"

# $$ changes value at each step based on previous function's output
pipeline = add_ten | double | stringify
result = pipeline(5)  # 15 → 30 → "Result: 30"
# Step 1: $$ = 5 → add_ten(5) = 15
# Step 2: $$ = 15 → double(15) = 30  
# Step 3: $$ = 30 → stringify(30) = "Result: 30"
```

#### 3. Named Parameters with "as parameter_name"
```dana
# Named parameters persist for the duration of the pipeline
def calculate_area(width: int, height: int) -> int:
    return width * height

def format_dimensions(width: int, height: int, area: int) -> str:
    return f"{width}x{height} = {area}"

# Named parameters are available throughout the pipeline
pipeline = calculate_area(as width=10, as height=5) | format_dimensions(as width=10, as height=5, as area=$$)
result = pipeline()  # "10x5 = 50"
# Note: No input needed since all parameters are named
```

#### 4. Capturing Intermediate Results with "as result_name"
```dana
# Capture intermediate results for later use in the pipeline
def validate_input(value: int) -> bool:
    return 0 <= value <= 100

def process_data(value: int) -> str:
    return f"Processed: {value}"

def format_output(is_valid: bool, processed: str) -> str:
    return f"{processed} (valid: {is_valid})"

# Capture f2_result for use in f4
pipeline = validate_input | process_data as f2_result | format_output($$, f2_result)
result = pipeline(42)  # true → "Processed: 42" → "Processed: 42 (valid: true)"

# Multiple captures
pipeline = validate_input as validation_result | process_data as processed_result | format_output(validation_result, processed_result)
result = pipeline(42)  # true → "Processed: 42" → "Processed: 42 (valid: true)"
```

### Complex Pipeline Examples

#### Mixed Argument Passing
```dana
def validate_range(min_val: int, value: int, max_val: int) -> bool:
    return min_val <= value <= max_val

def format_validation(result: bool, value: int) -> str:
    return f"Value {value} is {'valid' if result else 'invalid'}"

# Combine implicit, explicit, and named parameters
# Combine implicit, explicit, and named parameters
pipeline = validate_range(0, $$, 100) | format_validation($$, 42)
result = pipeline(42)  # true → "Value 42 is valid"
# Flow: 42 → validate_range(0, 42, 100) = true → format_validation(true, 42) = "Value 42 is valid"
```

#### Agent Pipelines with Named Parameters
```dana
def process_image(agent: ProSEAAgent, image_data: bytes) -> DefectReport:
    pass

def validate_report(agent: ProSEAAgent, report: DefectReport) -> bool:
    pass

def format_results(agent: ProSEAAgent, report: DefectReport, is_valid: bool) -> str:
    pass

# Agent parameter persists throughout pipeline
pipeline = process_image(as agent=my_agent, as image_data=$$) | validate_report(as agent=my_agent, as report=$$) | format_results(as agent=my_agent, as report=$$, as is_valid=$$)
result = pipeline(image_bytes)

# Using captured results
pipeline = process_image(as agent=my_agent, as image_data=$$) as report | validate_report(as agent=my_agent, as report=report) as is_valid | format_results(as agent=my_agent, as report=report, as is_valid=is_valid)
result = pipeline(image_bytes)
```

### Error Handling and Validation
```dana
# Missing function error
pipeline = add_ten | non_existent_function  # ❌ Error: "Function 'non_existent_function' not found"

# Non-function composition error  
pipeline = add_ten | 42  # ❌ Error: "Cannot use non-function 42 of type int in pipe composition"

# Invalid $$ placement error
pipeline = func1($$, extra_param) | func2  # ❌ Error: "$$ placeholder must be a complete parameter"

# Missing named parameter error
pipeline = func1(as width=10) | func2(as height=$$)  # ❌ Error: "Missing required parameter 'width' in func2"

# Clear error messages help with debugging
pipeline = func1 | not_a_function  # ❌ Error: "not_a_function is not callable"
```

**Pipeline Operators:**
- `|` - Pipe operator for sequential function composition
- `[func1, func2]` - List syntax for parallel function execution
- `$$` - Placeholder for explicit parameter positioning
- `as parameter_name=value` - Named parameter binding
- Supports both sequential and parallel composition in clean two-statement approach
- Left-to-right data flow similar to Unix pipes
- **Function-only validation**: Only callable functions allowed in composition chains

**Argument Passing Rules:**
1. **Implicit First**: Default behavior - pipeline value becomes first parameter
2. **Explicit $$**: Use $$ to specify exact parameter position ($$ = result of immediately preceding function)
3. **Named as**: Bind parameters by name for pipeline duration
4. **Result Capture as**: Use `function as result_name` to capture intermediate results for later use
5. **Mixed Usage**: Combine all approaches in complex pipelines
6. **Agent Persistence**: Agent parameters can be bound once and reused

**Design Philosophy:**
- **Clean Two-Statement Approach**: Separate function composition from data application
- **No Mixed Patterns**: All `data | function` patterns removed for clarity
- **Flexible Arguments**: Multiple ways to pass parameters based on function needs
- **Parallel-Ready**: Sequential execution with parallel-ready architecture
- **Comprehensive Validation**: Clear error messages for invalid usage

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

## Agent Capabilities

Dana introduces **Agent Capability Packs** - comprehensive packages that infuse agents with domain-specific expertise, similar to Matrix "Training Packs". These packs contain all the elements needed to transform a basic agent into a specialized domain expert.

### Agent Capability Pack Structure
```dana
agent_capability_pack/
├── common.na               # Shared types and helper functions
├── agent.na                # Agent type definition with declarative properties
├── resources.na            # Direct knowledge store references
├── methods.na              # Agent-bound functions
├── workflows.na            # Reusable task patterns
└── metadata.json           # Pack metadata and load order
```

### Agent Declaration with Capabilities
```dana
# agent.na - Agent type definition with declarative properties
agent ProSEAAgent:
    DanaAgent
    
    # Domains this agent works in
    domains: list[str] = ["semiconductor_manufacturing"]
    
    # Problem domains this agent works on
    tasks: list[str] = [
        "wafer_inspection",
        "defect_classification", 
        "process_troubleshooting",
        "equipment_maintenance",
        "quality_control",
        "yield_optimization"
    ]
    
    # Specific capabilities within the domain
    capabilities: list[str] = [
        "optical_inspection_analysis",
        "defect_pattern_recognition",
        "process_parameter_optimization",
        "equipment_diagnosis",
        "quality_metric_assessment",
        "yield_prediction"
    ]
    
    # Knowledge sources this agent relies on
    knowledge_sources: list[str] = [
        "equipment_specifications",
        "process_parameters", 
        "historical_defect_data",
        "quality_standards",
        "maintenance_procedures",
        "yield_analytics"
    ]
```

### Base Agent Struct
```dana
# dana_agent.na - Base struct for all Dana agents
struct DanaAgent:
    """
    Base agent struct that all specialized agents inherit from.
    """
    id: str
    name: str
    domains: list[str]
    tasks: list[str]
    capabilities: list[str]
    knowledge_sources: list[str]
```

### Knowledge Integration
```dana
# resources.na - Direct knowledge store references
specs_db = SqlResource(dsn = "postgres://prx_specs")           # Direct DB reference
cases_db = VectorDBResource(index = "prx_cases")              # Direct vector DB
docs_store = DocStoreResource(bucket = "prx_docs")            # Direct document store
lab_api = MCPResource(url = "http://lab-controller:9000")     # Direct API

# methods.na - Agent-bound functions using knowledge sources
@poet
def diagnose_defect(agent: ProSEAAgent, image_data: bytes) -> DefectReport:
    """
    Diagnose defects using knowledge from multiple sources.
    """
    # Use equipment_specifications from specs_db
    # Use historical_defect_data from cases_db
    # Use quality_standards from docs_store
    pass
```

### Agent Creation Workflow
```dana
# dana_agent/ - The agent that creates other agents
def create_agent_workflow(agent: DanaAgent, user_request: str) -> AgentCapabilityPack:
    """
    Main workflow for creating specialized agents.
    """
    requirements = analyze_requirements(agent, user_request)
    knowledge_plan = assess_knowledge_requirements(agent, requirements)
    design = design_agent(agent, requirements, knowledge_plan)
    knowledge_pack = curate_knowledge(agent, design)
    capability_pack = generate_agent(agent, design, knowledge_pack)
    
    return capability_pack
```

**Key Benefits:**
- **Domain Expertise**: Agents gain specialized knowledge and capabilities
- **Modular Design**: Capability packs can be shared, versioned, and reused
- **Declarative Properties**: Clear definition of what agents can do and what knowledge they use
- **Knowledge Optimization**: Knowledge is organized for specific tasks and domains
- **Agent Creation**: Meta-agents can create specialized agents automatically

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
# Basic exception handling
try:
    result = risky_operation()
except ValueError:
    log("Value error occurred", "error")
    result = default_value

# Exception variable assignment - access exception details
try:
    result = process_data(user_input)
except Exception as e:
    log(f"Error: {e.message}", "error")
    log(f"Exception type: {e.type}", "debug")
    log(f"Traceback: {e.traceback}", "debug")
    result = default_value

# Multiple exception types with variables
try:
    result = complex_operation()
except ValueError as validation_error:
    log(f"Validation failed: {validation_error.message}", "warn")
    result = handle_validation_error(validation_error)
except RuntimeError as runtime_error:
    log(f"Runtime error: {runtime_error.message}", "error")
    result = handle_runtime_error(runtime_error)
except Exception as general_error:
    log(f"Unexpected error: {general_error.message}", "error")
    result = handle_general_error(general_error)

# Exception matching with specific types
try:
    result = api_call()
except (ConnectionError, TimeoutError) as network_error:
    log(f"Network issue: {network_error.message}", "warn")
    result = retry_with_backoff()

# Generic exception catching
try:
    result = unsafe_operation()
except as error:
    log(f"Caught exception: {error.type} - {error.message}", "error")
    result = fallback_value
```

**Exception Object Properties:**
When using `except Exception as e:` syntax, the exception variable provides:
- `e.type` - Exception class name (string)
- `e.message` - Error message (string) 
- `e.traceback` - Stack trace lines (list of strings)
- `e.original` - Original Python exception object

**Exception Syntax Variations:**
- `except ExceptionType as var:` - Catch specific type with variable
- `except (Type1, Type2) as var:` - Catch multiple types with variable
- `except as var:` - Catch any exception with variable
- `except ExceptionType:` - Catch specific type without variable
- `except:` - Catch any exception without variable

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
uv run python -m dana.dana.exec.repl
```

### Execution
```bash
# Execute Dana files
uv run python -m dana.dana.exec.dana examples/dana/na/basic_math_pipeline.na
```

### Debugging
- Use `log()` function instead of `print()` for debugging
- Enable debug logging in transformer for AST output
- Test with existing `.na` files in `examples/dana/na/`

## Grammar Reference

The complete Dana grammar is defined in:
`opendxa/dana/sandbox/parser/dana_grammar.lark`

For detailed grammar specifications and language internals, see the design documents in `docs/design/01_dana_language_specification/`.