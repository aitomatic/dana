# Dana Language Reference

**Dana (Domain-Aware NeuroSymbolic Architecture)** is a Python-like programming language designed for AI-driven automation and agent systems. This comprehensive reference covers all syntax, conventions, and usage patterns.

## Overview

Dana is built for building domain-expert multi-agent systems with key AI-first features:
- Explicit scoping for agent state management
- Pipeline-based function composition
- Built-in AI reasoning capabilities
- Seamless Python interoperability
- Type safety with modern syntax
- **Agent Blueprints** for domain-specific expertise infusion
- **Struct Functions** for clean data operations

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

### Agent Blueprint System

The `agent_blueprint` keyword in Dana creates reusable agent types with built-in intelligence capabilities:

```dana
# agent_blueprint creates a new agent type
agent_blueprint ProSEAAgent:
    # Declarative properties define agent capabilities
    process_type: str = "semiconductor_manufacturing"
    tolerance_threshold: float = 0.02
    alert_channels: list[str] = ["email", "slack"]

# Create instances from blueprint
inspector = ProSEAAgent(process_type="etch", tolerance_threshold=0.015)
validator = ProSEAAgent(process_type="deposition", tolerance_threshold=0.025)

# Use built-in methods
plan = inspector.plan("Inspect wafer batch WB-2024-001")
solution = validator.solve("High defect rate in etching process")
```

### Function Parameters and Agent Usage

Functions that work with agents receive the agent instance as an explicit parameter:

```dana
# Functions explicitly receive agent as parameter (GoLang-style)
def solve_request(agent: ProSEAAgent, request: str) -> str:
    # Access agent properties
    if request in agent.process_type:
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

## Struct Functions

Dana provides two patterns for operating on structs:

### 1. Struct Functions (Main Pattern)
Functions that take structs as their first parameter, with automatic transformation:

```dana
struct Point:
    x: int
    y: int

# Define functions that operate on Point structs
def translate_point(point: Point, dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def point_distance(point: Point) -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

# Usage - Dana transforms automatically
point = Point(x=3, y=4)
moved = point.translate_point(2, 1)      # Transforms to translate_point(point, 2, 1)
distance = point.point_distance()        # Transforms to point_distance(point)
```

### 2. Struct Methods (Receiver Syntax)
Functions with explicit receiver syntax for direct method calls:

```dana
# Receiver syntax for direct method calls
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def (point: Point) distance_from_origin() -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

# Usage - direct method calls
point = Point(x=3, y=4)
moved = point.translate(2, 1)            # Direct method call
distance = point.distance_from_origin()  # Direct method call
```

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

def analyze(x):
    return {"value": x, "is_even": x % 2 == 0}

def format(x):
    return f"Formatted: {x}"
```

### Function Composition
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

Dana provides flexible ways to pass arguments in pipelines:

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
```

**Pipeline Operators:**
- `|` - Pipe operator for sequential function composition
- `[func1, func2]` - List syntax for parallel function execution
- `$$` - Placeholder for explicit parameter positioning
- `as parameter_name=value` - Named parameter binding
- Supports both sequential and parallel composition in clean two-statement approach
- Left-to-right data flow similar to Unix pipes
- **Function-only validation**: Only callable functions allowed in composition chains

## Benefits of Conditional Pipelines
- **Declarative Logic**: Clear branching without nested if/else statements
- **Composable**: Can be combined with other pipeline operations
- **Reusable**: Conditional logic can be defined once and reused
- **Type Safe**: Maintains type safety throughout the pipeline
- **Readable**: Complex branching logic is easy to understand


## Concurrency-by-Default

Dana implements **concurrent-by-default** execution through transparent Promise[T] wrapping, enabling automatic parallelism without explicit async/await syntax.

### Core Philosophy

Dana functions are concurrent by default through transparent Promise[T] wrapping:
- **Automatic Promise Creation**: Return statements automatically create Promise objects when needed
- **Transparent Typing**: Promise[T] appears and behaves exactly like type T
- **Zero Syntax Overhead**: No async/await keywords needed
- **Background Execution**: Computations run in background threads automatically

### Basic Concurrency
```dana
# Functions automatically return Promise[T] for concurrent execution
def fetch_user_data(user_id: int) -> UserData:
    # All three API calls start immediately in parallel
    profile = fetch_profile(user_id)      # return creates Promise
    posts = fetch_posts(user_id)          # return creates Promise  
    friends = fetch_friends(user_id)      # return creates Promise
    
    # Promises resolve when accessed
    return UserData(
        profile=profile,    # Blocks here if not ready
        posts=posts,        # Blocks here if not ready
        friends=friends     # Blocks here if not ready
    )

# Usage - completely transparent
user_data = fetch_user_data(123)  # Promise[UserData] that behaves like UserData
print(user_data.profile.name)     # Automatic resolution when accessed
```

### Transparent Promise Behavior
```dana
# Promise[Int] behaves exactly like Int
def compute_value() -> int:
    return expensive_calculation()  # Returns Promise[Int] that appears as Int

# Usage is completely transparent
result = compute_value()  # Promise[Int]
doubled = result * 2      # Works immediately, returns Promise[Int]
if result > 10:          # Comparison works, blocks if needed
    print(result)        # Automatic resolution when value needed
```

### Automatic Parallelism
Collections automatically process elements in parallel:

```dana
# Lists automatically process elements in parallel
users = [fetch_user(1), fetch_user(2), fetch_user(3)]    # All three calls run concurrently

# Dictionaries automatically process values in parallel
stats = {"users": count_users(), "posts": count_posts()} # Both counts run in parallel

# Sets automatically process elements in parallel
tags = {fetch_tag("python"), fetch_tag("dana"), fetch_tag("concurrency")}

# F-strings automatically resolve promises in parallel
user = fetch_user(123)
post = fetch_post(456)
message = f"User {user.name} posted: {post.title}"  # Both promises resolve in parallel
```

### Conditional Computation
Promises enable efficient conditional computation where expensive work is skipped if not needed:

```dana
def analyze_data(data: Data) -> Report:
    basic_stats = compute_basic_stats(data)     # Always computed (eager)
    
    if basic_stats.needs_deep_analysis:
        deep_analysis = return run_ml_analysis(data)  # Only computed if accessed
        return create_full_report(basic_stats, deep_analysis)
    else:
        return create_simple_report(basic_stats)       # deep_analysis never computed
```

### Mixed Sync/Async Operations
```dana
def smart_fetch(key: str) -> Value:
    if cache.has(key):
        return cache.get(key)  # Sync return, no Promise
    return database.query(key)  # Concurrent database call

def process_data(data: Data) -> Result:
    if data.is_cached():
        return data.cached_result  # Synchronous, no Promise
    
    # Only create Promise for expensive operation
    return expensive_computation(data)  # Concurrent execution
```

### Promise Chaining
Functions can work with promises transparently:

```dana
def process_chain(input: str) -> Result:
    parsed = parse_data(input)      # return → Promise
    validated = validate(parsed)     # Works on Promise transparently
    transformed = transform(validated)  # Chain continues
    return transformed              # Final return
```

### Agent Communication
Agents communicate through method calls that look blocking but are concurrent:

```dana
def coordinate_agents():
    # All agent calls start immediately in parallel
    plan = inspector.plan("Inspect wafer batch WB-2024-001")
    solution = validator.solve("High defect rate in etching process")
    report = analyzer.analyze("Process optimization")
    
    # Results resolve when accessed
    return combine_results(plan, solution, report)
```

### Error Handling
Promises preserve error semantics transparently:

```dana
def may_fail() -> int:
    return 1 / 0  # Division by zero in Promise

try:
    value = may_fail()      # No error yet (Promise created)
    result = value * 2      # Error occurs here when Promise resolves
except ZeroDivisionError:
    print("Caught division by zero")
```

### Performance Characteristics

**Promise Creation Overhead:**
- EagerPromise: ~1-2ms for thread pool task submission
- Transparent operations: Near-zero overhead until resolution needed
- Memory: Small object overhead + computation closure

**Concurrency Benefits:**
- Parallel I/O: 60-80% speedup for multiple API calls
- Resource utilization: CPU available during I/O waits
- Scalability: Thread pool prevents resource exhaustion

**Resolution Costs:**
- First access: Blocks until computation complete
- Subsequent access: Cached result, zero cost
- Failed computations: Exception cached and re-raised

### Best Practices

1. **Use return for all function completions**: Return statements automatically handle Promise creation when needed
2. **Don't worry about Promise types**: The transparent proxy handles all operations
3. **Let collections auto-resolve**: Don't manually resolve Promises in collections
4. **Trust the system**: Write natural code and get concurrent execution automatically
5. **Use conditional computation**: Leverage lazy evaluation for expensive operations

### Concurrency Rules
1. **Automatic Promise Creation**: Return statements create EagerPromise for background execution
2. **Transparent Access**: Promises behave like regular values - accessing blocks if not ready
3. **Background Execution**: Computations run in background threads automatically
4. **Thread Safety**: All Promise operations are thread-safe with internal locking
5. **Error Transparency**: Background exceptions are captured and re-raised on access
6. **Collection Parallelism**: Lists, dicts, sets, and f-strings automatically process elements in parallel

### Benefits of Concurrency-by-Default
- **Natural Code**: Write synchronous-looking code that executes concurrently
- **Automatic Parallelism**: Collections and multiple operations run in parallel automatically
- **Zero Cognitive Overhead**: No async/await syntax to manage
- **Performance**: 60-80% faster for I/O-heavy operations
- **Agent-Optimized**: Perfect for agent workloads with multiple API calls and I/O operations
- **Resource Efficient**: Thread pool prevents resource exhaustion


## Global Registry System

Dana provides a comprehensive global registry system that manages all language components through specialized registries with unified access patterns.

### Core Registries

#### **GLOBAL_REGISTRY** - Unified Registry Interface
The main entry point that consolidates all specialized registries:

```dana
# Access the global registry singleton
from dana.registry import GLOBAL_REGISTRY

# Register types
GLOBAL_REGISTRY.register_agent_type(my_agent_type)
GLOBAL_REGISTRY.register_resource_type(my_resource_type)
GLOBAL_REGISTRY.register_struct_type(my_struct_type)

# Access sub-registries
types = GLOBAL_REGISTRY.types
functions = GLOBAL_REGISTRY.functions
modules = GLOBAL_REGISTRY.modules
```

#### **TYPE_REGISTRY** - Type Definitions
Manages agent, resource, and struct type definitions:

```dana
from dana.registry import TYPE_REGISTRY

# Register type definitions
TYPE_REGISTRY.register_agent_type(MyAgentType)
TYPE_REGISTRY.register_resource_type(MyResourceType)
TYPE_REGISTRY.register_struct_type(MyStructType)

# Retrieve types
agent_type = TYPE_REGISTRY.get_agent_type("MyAgent")
resource_type = TYPE_REGISTRY.get_resource_type("MyResource")
struct_type = TYPE_REGISTRY.get_struct_type("MyStruct")
```

#### **FUNCTION_REGISTRY** - Function Registration
Handles function registration and dispatch, including struct functions:

```dana
from dana.registry import FUNCTION_REGISTRY

# Register regular functions
FUNCTION_REGISTRY.register("my_function", my_func)

# Register struct functions (methods)
FUNCTION_REGISTRY.register_struct_function("Point", "translate", translate_point)
FUNCTION_REGISTRY.register_struct_function("Point", "distance", point_distance)

# Lookup functions
func = FUNCTION_REGISTRY.lookup("my_function")
struct_func = FUNCTION_REGISTRY.lookup_struct_function("Point", "translate")
```

#### **MODULE_REGISTRY** - Module Management
Tracks module loading, dependencies, and aliases:

```dana
from dana.registry import MODULE_REGISTRY

# Register modules
MODULE_REGISTRY.register_module(my_module)
MODULE_REGISTRY.register_spec(my_spec)

# Set up aliases
MODULE_REGISTRY.set_alias("short_name", "full_module_name")

# Track dependencies
MODULE_REGISTRY.add_dependency("module_a", "module_b")
```

#### **AGENT_REGISTRY** - Agent Instance Tracking
Manages agent instances and their lifecycle:

```dana
from dana.registry import AGENT_REGISTRY

# Track agent instances
agent_id = AGENT_REGISTRY.track_agent_instance(my_agent, "my_agent_name")

# Retrieve instances
agent = AGENT_REGISTRY.get_agent_instance(agent_id)
agent_by_name = AGENT_REGISTRY.get_agent_instance_by_name("my_agent_name")

# List all agents
all_agents = AGENT_REGISTRY.list_agent_instances()
```

#### **RESOURCE_REGISTRY** - Resource Instance Management
Handles resource instances and their configurations:

```dana
from dana.registry import RESOURCE_REGISTRY

# Track resource instances
resource_id = RESOURCE_REGISTRY.track_resource_instance(my_resource, "my_resource_name")

# Retrieve resources
resource = RESOURCE_REGISTRY.get_resource_instance(resource_id)
resource_by_name = RESOURCE_REGISTRY.get_resource_instance_by_name("my_resource_name")

# List all resources
all_resources = RESOURCE_REGISTRY.list_resource_instances()
```

#### **WORKFLOW_REGISTRY** - Workflow Instance Tracking
Manages workflow instances and their execution state:

```dana
from dana.registry import WORKFLOW_REGISTRY

# Track workflow instances
workflow_id = WORKFLOW_REGISTRY.track_instance(my_workflow, "my_workflow_name")

# Retrieve workflows
workflow = WORKFLOW_REGISTRY.get_instance(workflow_id)
workflow_by_name = WORKFLOW_REGISTRY.get_instance_by_name("my_workflow_name")
```

### Framework-Specific Registries

#### **KORegistry** - Knowledge Organization Registry
Manages knowledge organization types and configurations in the KNOWS framework:

```dana
from dana.frameworks.knows.core.registry import ko_registry

# Register knowledge organization types
ko_registry.register_ko_type("vector", VectorKO)
ko_registry.register_ko_type("relational", RelationalKO)

# Register configurations
ko_registry.register_ko_config("vector", {"dimensions": 768, "metric": "cosine"})

# Create instances
ko_instance = ko_registry.create_ko_instance("vector", dimensions=512)
```

#### **DomainRegistry** - Domain Template Registry
Manages domain templates in the POET framework:

```dana
from dana.frameworks.poet.domains.registry import get_registry

registry = get_registry()

# Get domain templates
computation_domain = registry.get_domain("computation")
scientific_domain = registry.get_domain("computation:scientific")

# List available domains
available_domains = registry.list_domains()
```

### Registry Usage Patterns

#### **Automatic Registration**
Most Dana components are automatically registered when defined:

```dana
# Agent blueprints are automatically registered
agent_blueprint MyAgent:
    field: str = "default"

# Structs are automatically registered
struct MyStruct:
    field: int

# Functions are automatically registered when imported
import my_module  # Functions in my_module are registered automatically
```

#### **Manual Registration**
For custom components, manual registration is available:

```dana
from dana.registry import TYPE_REGISTRY, FUNCTION_REGISTRY

# Register custom types
class CustomAgent:
    name = "CustomAgent"
    # ... implementation

TYPE_REGISTRY.register_agent_type(CustomAgent)

# Register custom functions
def custom_function(x: int) -> int:
    return x * 2

FUNCTION_REGISTRY.register("custom_function", custom_function)
```

#### **Registry Cleanup**
For testing and development, registries can be cleared:

```dana
from dana.registry import clear_all

# Clear all registries
clear_all()
```

### Registry Benefits

- **Centralized Management**: All Dana components tracked in one place
- **Type Safety**: Registry ensures proper type registration and lookup
- **Lifecycle Management**: Automatic tracking of component instances
- **Dependency Resolution**: Module registry handles import dependencies
- **Framework Integration**: Specialized registries for different frameworks
- **Testing Support**: Easy registry cleanup for isolated testing
- **Performance**: Optimized lookup patterns for different component types

### Registry Rules

1. **Singleton Pattern**: All registries use singleton pattern for global access
2. **Automatic Registration**: Most components register automatically
3. **Type-Specific Storage**: Different registries use optimized storage for their component types
4. **Unified Interface**: GLOBAL_REGISTRY provides unified access to all registries
5. **Framework Extensibility**: Framework-specific registries can be added as needed
6. **Thread Safety**: All registry operations are thread-safe


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

## Agent System

Dana introduces **Agent Blueprints** - comprehensive packages that define reusable agent types with built-in intelligence capabilities.

### Agent Blueprint Structure
```dana
# Define reusable agent blueprints (like struct definitions)
agent_blueprint QualityInspector:
    domain: str = "semiconductor"
    expertise_level: str = "senior"
    tolerance_threshold: float = 0.015
    alert_channels: list[str] = ["email", "slack"]

# Create instances from blueprints
inspector = QualityInspector()
custom_inspector = QualityInspector(expertise_level="expert", tolerance_threshold=0.01)

# Create singleton agents
agent Solo                          # Simple singleton
agent Jimmy(QualityInspector)       # Singleton from blueprint
agent Config(QualityInspector):     # Singleton with field overrides
    expertise_level = "expert"
```

### Built-in Agent Methods
```dana
# All agents have built-in intelligence methods
plan = inspector.plan("Inspect wafer batch WB-2024-001")
solution = Jimmy.solve("High defect rate in etching process")

# Memory operations (isolated per agent instance)
inspector.remember("common_defects", ["misalignment", "surface_roughness"])
defects = inspector.recall("common_defects")

# Chat method (for simple agents)
response = agent.chat("message")
```

### Agent Declaration with Capabilities
```dana
# agent_blueprint - Agent type definition with declarative properties
agent_blueprint ProSEAAgent:
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

### Knowledge Integration
```dana
# Direct knowledge store references
specs_db = SqlResource(dsn = "postgres://prx_specs")           # Direct DB reference
cases_db = VectorDBResource(index = "prx_cases")              # Direct vector DB
docs_store = DocStoreResource(bucket = "prx_docs")            # Direct document store
lab_api = MCPResource(url = "http://lab-controller:9000")     # Direct API

# Agent-bound functions using knowledge sources
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

**Key Benefits:**
- **Domain Expertise**: Agents gain specialized knowledge and capabilities
- **Modular Design**: Agent blueprints can be shared, versioned, and reused
- **Declarative Properties**: Clear definition of what agents can do and what knowledge they use
- **Knowledge Optimization**: Knowledge is organized for specific tasks and domains
- **Built-in Intelligence**: Immediate AI-powered planning, problem-solving, and memory capabilities

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
agent_blueprint MyAgent:         # Agent blueprint definition
    field: str = "default"
```

### ❌ Incorrect (Python-style)
```dana
state = "agent data"             # Missing scope (auto-scoped to local:)
result = "Value: " + str(count)  # String concatenation instead of f-strings
import math                      # Missing .py for Python modules
def func(x):                     # Missing type hints
    return "Result: " + str(x)
point = Point(5, 10)             # Positional arguments not supported
class MyAgent:                   # Use agent_blueprint instead of class
    def __init__(self):
        pass
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
6. **Use agent_blueprint** for reusable agent types
7. **Use struct functions** for clean data operations

### Performance Considerations
1. **Pipeline composition** is more efficient than nested function calls
2. **Explicit scoping** helps with memory management in long-running agents
3. **Type hints** enable better optimization by the Dana runtime
4. **Agent blueprints** provide efficient agent creation and reuse

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