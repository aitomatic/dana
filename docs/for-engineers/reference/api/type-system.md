# Type System API Reference

Dana's type hinting system provides clear type annotations for variables and functions to help AI code generators write better Dana code. The system follows KISS (Keep It Simple, Stupid) principles with basic types and straightforward syntax.

## Table of Contents
- [Overview](#overview)
- [Basic Types](#basic-types)
- [Variable Type Annotations](#variable-type-annotations)
- [Function Type Signatures](#function-type-signatures)
- [Type Validation](#type-validation)
- [AI Function Types](#ai-functions)
- [Data Types](#data-types)
- [Type Compatibility](#type-compatibility)
- [Best Practices](#best-practices)
- [Implementation Status](#implementation-status)

---

## Overview

### Design Philosophy
- KISS/YAGNI approach: Basic types only, no generics (`list[int]`), no unions, no complex types
- Prompt optimization focus: Help AI code generators write better Dana code
- Security preservation: Type hints are documentation only, don't affect runtime security
- Backward compatibility: All existing Dana code continues working

### Key Features
- ✅ **Variable type annotations**: `x: int = 42`, `y: str = "hello"`
- ✅ **Function parameter types**: `def func(x: int, y: str):`
- ✅ **Function return types**: `def func() -> dict:`
- ✅ **Type hint validation**: Validates type hints match assigned values
- ✅ **Mixed typed/untyped code**: Full backward compatibility
- ✅ **All 10 basic types**: int, float, str, bool, list, dict, tuple, set, None, any

---

## Basic Types

Dana supports 10 fundamental types for type annotations:

| Type | Description | Example Values | Use Cases |
|------|-------------|----------------|-----------|
| `int` | Integer numbers | `42`, `-17`, `0` | Counters, indices, IDs |
| `float` | Floating-point numbers | `3.14`, `-2.5`, `0.0` | Measurements, calculations |
| `str` | Text strings | `"hello"`, `'world'`, `""` | Names, messages, text data |
| `bool` | Boolean values | `true`, `false` | Flags, conditions, states |
| `list` | Ordered collections | `[1, 2, 3]`, `["a", "b"]` | Sequences, arrays |
| `dict` | Key-value mappings | `{"name": "Alice"}` | Objects, configurations |
| `tuple` | Immutable sequences | `(1, 2, 3)`, `("x", "y")` | Coordinates, fixed data |
| `set` | Unique collections | `{1, 2, 3}` | Unique items, membership |
| `None` | Null/empty value | `None` | Optional values, initialization |
| `any` | Any type (escape hatch) | Any value | Flexible typing, unknown types |

### Type Examples
```dana
# Basic type annotations
count: int = 42
temperature: float = 98.6
name: str = "Alice"
is_active: bool = true
numbers: list = [1, 2, 3, 4, 5]
user_data: dict = {"name": "Bob", "age": 25}
coordinates: tuple = (10, 20, 30)
unique_ids: set = {1, 2, 3}
optional_value: None = None
flexible_data: any = "could be anything"
```

---

## Variable Type Annotations

### Syntax
```dana
variable_name: type = value
```

### Examples
```dana
# Numeric types
age: int = 25
height: float = 5.9
weight: float = 150.5

# Text and boolean
username: str = "alice_smith"
email: str = "alice@example.com"
is_verified: bool = true
is_admin: bool = false

# Collections
scores: list = [85, 92, 78, 96]
user_profile: dict = {
 "name": "Alice",
 "age": 25,
 "role": "engineer"
}
rgb_color: tuple = (255, 128, 0)
tags: set = {"python", "dana", "ai"}

# Special types
result: None = None
dynamic_data: any = {"could": "be", "anything": 123}
```

### Type Inference
When no type hint is provided, Dana infers the type from the value:
```dana
# These work without type hints
count = 42 # Inferred as int
name = "Alice" # Inferred as str
active = true # Inferred as bool
items = [1, 2, 3] # Inferred as list
```

---

## Function Type Signatures

### Parameter Type Hints
```dana
def function_name(param1: type1, param2: type2) -> return_type:
 # function body
```

### Examples
```dana
# Simple function with typed parameters
def greet(name: str, age: int) -> str:
 return f"Hello {name}, you are {age} years old"

# Function with multiple parameter types
def calculate_bmi(weight: float, height: float) -> float:
 return weight / (height * height)

# Function with collection parameters
def process_scores(scores: list, threshold: int) -> dict:
 passed = []
 failed = []
 for score in scores:
 if score >= threshold:
 passed.append(score)
 else:
 failed.append(score)

 return {
 "passed": passed,
 "failed": failed,
 "pass_rate": len(passed) / len(scores)
 }

# Function with optional parameters (using any for flexibility)
def log_event(message: str, level: str, metadata: any) -> None:
 # Log implementation
 print(f"[{level}] {message}")
 if metadata:
 print(f"Metadata: {metadata}")

# Function returning None (procedures)
def update_user_status(user_id: int, status: bool) -> None:
 # Update implementation
 print(f"User {user_id} status updated to {status}")
```

### Mixed Typed/Untyped Parameters
```dana
# You can mix typed and untyped parameters
def flexible_function(required_id: int, name, optional_data: dict):
 return f"Processing {name} with ID {required_id}"

# Untyped functions still work
def legacy_function(a, b, c):
 return a + b + c
```

---

## Type Validation

Dana validates type hints at runtime and provides helpful error messages:

### Validation Examples
```dana
# ✅ Valid type assignments
user_age: int = 25
user_name: str = "Alice"
scores: list = [85, 92, 78]

# ❌ Type validation errors
user_age: int = "twenty-five" # TypeError: Type hint mismatch: expected int, got string
temperature: float = [98, 6] # TypeError: Type hint mismatch: expected float, got list
is_active: bool = "yes" # TypeError: Type hint mismatch: expected bool, got string
```

### Function Parameter Validation
```dana
def calculate_area(length: float, width: float) -> float:
 return length * width

# ✅ Valid calls
area = calculate_area(10.5, 8.2)
area = calculate_area(10, 8) # int is compatible with float

# ❌ Invalid calls would cause type errors
# area = calculate_area("10", "8") # TypeError: expected float, got string
# area = calculate_area([10], [8]) # TypeError: expected float, got list
```

### Return Type Validation
```dana
def get_user_count() -> int:
 return 42 # ✅ Valid

def get_user_name() -> str:
 return "Alice" # ✅ Valid

def get_user_data() -> dict:
 return {"name": "Alice", "age": 25} # ✅ Valid

# ❌ Return type mismatches would cause errors
def bad_function() -> int:
 return "not a number" # TypeError: expected int return, got string
```

---

## AI Function Types {#ai-functions}

Special considerations for AI-related functions:

### Core AI Functions
```dana
# reason() function - LLM integration
def analyze_data(data: dict, query: str) -> str:
 # Type-safe AI reasoning
 analysis: str = reason(f"Analyze this data: {data} for: {query}")
 return analysis

# log() function - Structured logging
def process_with_logging(items: list, operation: str) -> dict:
 log(f"Starting {operation} on {len(items)} items", "info")

 results: list = []
 for item in items:
 processed = f"processed_{item}"
 results.append(processed)

 log(f"Completed {operation}", "info")
 return {"results": results, "count": len(results)}
```

### AI-Generated Code Patterns
```dana
# Pattern: Data analysis with type safety
def ai_data_analysis(dataset: dict, analysis_type: str) -> dict:
 # Validate inputs with type hints
 log(f"Analyzing dataset with {len(dataset)} fields", "info")

 # AI reasoning with proper types
 prompt: str = f"Perform {analysis_type} analysis on: {dataset}"
 analysis: str = reason(prompt, {
 "temperature": 0.3,
 "format": "json"
 })

 # Return structured result
 result: dict = {
 "analysis": analysis,
 "dataset_size": len(dataset),
 "analysis_type": analysis_type,
 "timestamp": "2025-01-01T12:00:00Z"
 }

 return result

# Pattern: Multi-step AI workflow
def ai_workflow(input_data: list, steps: list) -> dict:
 current_data: any = input_data
 results: list = []

 for step in steps:
 step_name: str = step["name"]
 step_prompt: str = step["prompt"]

 log(f"Executing step: {step_name}", "info")

 # AI processing with type safety
 step_result: str = reason(f"{step_prompt}: {current_data}")
 results.append({
 "step": step_name,
 "result": step_result
 })

 # Update current data for next step
 current_data = step_result

 return {
 "final_result": current_data,
 "step_results": results,
 "total_steps": len(steps)
 }
```

---

## Data Types {#data-types}

### Collection Types in Detail

#### Lists
```dana
# List type annotations
numbers: list = [1, 2, 3, 4, 5]
names: list = ["Alice", "Bob", "Charlie"]
mixed: list = [1, "hello", true, [1, 2]]

# List operations with type safety
def process_numbers(data: list) -> dict:
 total: int = sum(data)
 count: int = len(data)
 average: float = total / count

 return {
 "total": total,
 "count": count,
 "average": average
 }
```

#### Dictionaries
```dana
# Dictionary type annotations
user: dict = {"name": "Alice", "age": 25, "role": "engineer"}
config: dict = {
 "debug": true,
 "max_retries": 3,
 "timeout": 30.0
}

# Dictionary operations with type safety
def merge_user_data(base_data: dict, updates: dict) -> dict:
 merged: dict = base_data.copy()
 for key, value in updates.items():
 merged[key] = value

 return merged
```

#### Tuples
```dana
# Tuple type annotations
point_2d: tuple = (10, 20)
point_3d: tuple = (10, 20, 30)
rgb_color: tuple = (255, 128, 0)

# Tuple operations with type safety
def calculate_distance(point1: tuple, point2: tuple) -> float:
 x_diff: float = point1[0] - point2[0]
 y_diff: float = point1[1] - point2[1]

 distance: float = (x_diff * x_diff + y_diff * y_diff) ** 0.5
 return distance
```

#### Sets
```dana
# Set type annotations
unique_ids: set = {1, 2, 3, 4, 5}
tags: set = {"python", "dana", "ai", "ml"}

# Set operations with type safety
def find_common_tags(tags1: set, tags2: set) -> set:
 common: set = tags1.intersection(tags2)
 return common
```

---

## Type Compatibility

### Arithmetic Compatibility
Dana supports arithmetic compatibility between `int` and `float`:

```dana
# Mixed int/float arithmetic
x: int = 10
y: float = 3.14

# These operations work and return appropriate types
sum_result: float = x + y # int + float = float
product: float = x * y # int * float = float
division: float = x / y # int / float = float

# Type checker understands compatibility
def calculate_total(base: int, multiplier: float) -> float:
 return base * multiplier # Returns float (correct)
```

### Type Coercion Rules
1. **int + float = float**
2. **int * float = float**
3. **int / float = float**
4. **float + int = float**
5. **int operations = int** (when both operands are int)

### The `any` Type
Use `any` as an escape hatch for flexible typing:

```dana
# When you need flexibility
def process_dynamic_data(data: any) -> any:
 # Can handle any type of input
 if isinstance(data, list):
 return len(data)
 elif isinstance(data, dict):
 return data.keys()
 else:
 return str(data)

# Useful for configuration or API responses
config: any = load_config() # Could be dict, list, or other types
api_response: any = call_external_api() # Unknown structure
```

---

## Best Practices

### 1. Always Use Type Hints for Public Functions
```dana
# ✅ Good: Clear function signature
def calculate_bmi(weight: float, height: float) -> float:
 return weight / (height * height)

# ❌ Avoid: Unclear function signature
def calculate_bmi(weight, height):
 return weight / (height * height)
```

### 2. Use Descriptive Variable Names with Types
```dana
# ✅ Good: Clear intent
user_count: int = 150
average_score: float = 87.5
error_message: str = "Invalid input provided"

# ❌ Avoid: Unclear purpose
x: int = 150
y: float = 87.5
msg: str = "Invalid input provided"
```

### 3. Type Complex Data Structures
```dana
# ✅ Good: Typed complex data
user_profile: dict = {
 "personal_info": {
 "name": "Alice",
 "age": 25
 },
 "preferences": {
 "theme": "dark",
 "notifications": true
 }
}

# Function that processes complex data
def update_user_preferences(profile: dict, new_prefs: dict) -> dict:
 updated_profile: dict = profile.copy()
 updated_profile["preferences"].update(new_prefs)
 return updated_profile
```

### 4. Use `any` Sparingly
```dana
# ✅ Good: Specific types when possible
def process_user_data(name: str, age: int, metadata: dict) -> dict:
 return {"name": name, "age": age, "metadata": metadata}

# ✅ Acceptable: Use any when truly needed
def handle_api_response(response: any) -> dict:
 # When dealing with unknown external data
 return {"status": "processed", "data": response}
```

### 5. Type AI Function Calls
```dana
# ✅ Good: Typed AI interactions
def ai_content_analysis(content: str, analysis_type: str) -> dict:
 # Clear input types
 prompt: str = f"Analyze this {analysis_type}: {content}"

 # Typed AI call
 analysis: str = reason(prompt, {
 "temperature": 0.5,
 "max_tokens": 500
 })

 # Structured return
 result: dict = {
 "content": content,
 "analysis": analysis,
 "type": analysis_type,
 "confidence": 0.85
 }

 return result
```

---

## Implementation Status

| Feature | Status | Description |
|---------|--------|-------------|
| **Basic Types** | ✅ Complete | All 10 basic types: int, float, str, bool, list, dict, tuple, set, None, any |
| **Variable Annotations** | ✅ Complete | `variable: type = value` syntax |
| **Function Parameters** | ✅ Complete | `def func(param: type):` syntax |
| **Function Returns** | ✅ Complete | `def func() -> type:` syntax |
| **Type Validation** | ✅ Complete | Runtime validation with helpful error messages |
| **Mixed Typed/Untyped** | ✅ Complete | Full backward compatibility |
| **Arithmetic Compatibility** | ✅ Complete | int/float compatibility in operations |
| **Set Literals** | ✅ Complete | `{1, 2, 3}` syntax working correctly |
| **AST Integration** | ✅ Complete | TypeHint and Parameter objects in AST |
| **Parser Integration** | ✅ Complete | Grammar and transformer support |

### Testing Status
- ✅ **133/133 parser tests passed**
- ✅ **364/366 Dana tests passed** (2 pre-existing failures unrelated to type hints)
- ✅ **Zero regressions** in core functionality
- ✅ **Comprehensive type validation** testing
- ✅ **End-to-end integration** testing

---

## See Also

- [Core Functions](core-functions.md) - Essential Dana functions with type signatures
- [Built-in Functions](built-in-functions.md) - Pythonic built-in functions with type validation
- [Function Calling](function-calling.md) - Function calling and import system
- [Scoping System](scoping.md) - Variable scopes and security model

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>