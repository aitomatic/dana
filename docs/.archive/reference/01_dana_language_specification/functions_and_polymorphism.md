# Dana Functions and Polymorphism

This document describes how functions are defined and used in the Dana language, with a special focus on polymorphic functions and the mechanisms for flexible function behavior.

## 1. Function Definition

Functions in Dana are defined using the `def` keyword, followed by the function name, a list of parameters in parentheses, an optional return type annotation, and an indented block of code constituting the function's body.

Syntax:

```dana
def <function_name>(<param1>: <type1>, <param2>: <type2>, ...) -> <ReturnType>:
 # Function body
 local:result = ...
 return local:result
```

* Parameters: Parameters can have type annotations (e.g., `count: int`). Default values for parameters are also supported (e.g., `level: str = "info"`).
* Return Type: The `-> <ReturnType>` annotation specifies the intended type of the value the function will return. If a function does not explicitly return a value, its implicit return type is `None`. `-> None` can be used to make this explicit.
* Return Statement: The `return` statement is used to exit a function and optionally pass back a value.

Example:

```dana
def greet(name: str) -> str:
 return "Hello, " + name

def add_numbers(a: int, b: int = 0) -> int:
 local:sum_val = a + b
 return local:sum_val

def log_message(message: str, severity: str = "info") -> None:
 log(f"[{severity.upper()}] {message}") # Assuming 'log' is a core/built-in function
```

## 2. Function Calling

Functions are called by using their name followed by parentheses containing arguments.

Syntax:

```dana
<function_name>(<arg1>, <arg2_name>=<value2>, ...)
```

* Arguments: Arguments can be passed positionally or by name (keyword arguments).

Example:

```dana
local:greeting: str = greet(name="Alice")
local:total: int = add_numbers(5, 3)
local:another_total: int = add_numbers(a=10)
log_message("System started.")
log_message(message="An error occurred", severity="error")
```

## 3. Polymorphic Functions

Polymorphic functions in Dana allow a single function name to be associated with multiple distinct implementations (or signatures). This is a key feature for writing flexible and intuitive code, as it enables the same conceptual operation to behave differently and appropriately based on the types of data it receives.

**The core benefits of polymorphism are enhanced code clarity and adaptability.** By using the same function name for operations that are semantically similar but apply to different data types (especially user-defined `structs`), developers can create more readable and maintainable code. The Dana runtime automatically dispatches a function call to the correct underlying implementation based on the types (and potentially number) of arguments provided by the caller.

### 3.1. Definition

A polymorphic function is defined by providing multiple `def` blocks with the **same function name** but **different type annotations for their parameters**.

Syntax:

```dana
# Signature 1
def <function_name>(<param1>: <TypeA>, <param2>: <TypeB>) -> <ReturnTypeX>:
 # Implementation for TypeA, TypeB
 ...

# Signature 2
def <function_name>(<param1>: <TypeC>, <param2>: <TypeD>) -> <ReturnTypeY>:
 # Implementation for TypeC, TypeD
 ...

# Signature for a specific struct type
def <function_name>(<param_struct>: <UserDefinedStructType>) -> <ReturnTypeZ>:
 # Implementation for UserDefinedStructType
 ...
```
Example: Polymorphic `describe` function
```dana
struct Point:
 x: int
 y: int

def describe(item: str) -> str:
 return f"This is a string: '{item}'"

def describe(item: int) -> str:
 return f"This is an integer: {item}"

def describe(item: Point) -> str:
 return f"This is a Point at ({item.x}, {item.y})"
```

### 3.2. Dispatch Rules

* Exact Type Match: The Dana runtime selects the function implementation whose parameter types exactly match the types of the arguments passed in the call.
* Number of Arguments: The number of arguments must also match the number of parameters in the signature.
* No Match: If no signature provides an exact match for the argument types and count, a runtime error will be raised.
* Order of Definition: For exact matches, the order in which polymorphic signatures are defined does not affect dispatch. (If subtyping or more complex type coercion rules were introduced for dispatch, order might become relevant, but this is not currently the case).

Example Calls:

```dana
local:my_point: Point = Point(x=5, y=3)

print(describe("hello")) # Calls describe(item: str)
print(describe(100)) # Calls describe(item: int)
print(describe(my_point)) # Calls describe(item: Point)

# describe([1,2,3]) # This would cause a runtime error if no describe(item: list) is defined.
```

### 3.3. Return Types

Each signature of a polymorphic function can have its own distinct return type. The caller should be aware of this, or the type system and POET framework's `expected_output_type` mechanism (for POET-enabled functions) can guide the expected return.

## 4. Built-in and Core Functions

Dana provides a set of built-in functions (e.g., `len()`, `print()`, `int()`, `str()`) and core functions that are essential for agent operations (e.g., `reason()`, `log()`). These functions are globally available.

Their specific signatures and behaviors are documented in the API reference materials.

## 5. Guiding Function Output: Type Hinting and POET

Previously, a system-level variable `system:__dana_desired_type` was used as a general mechanism for callers to suggest a desired return structure or type, especially for dynamic functions like those interacting with LLMs. This mechanism is now deprecated in favor of more integrated approaches:

1. **Standard Type Hinting**: For regular Dana functions, the primary way to indicate expected return types is through the function's own return type annotation (e.g., `-> MyStruct`) and the type hint at the assignment site (e.g., `local:my_var: MyStruct = my_func()`). The Dana type system will enforce these where possible.

2. **POET's `expected_output_type`**: For functions using the POET (Perceive → Operate → Enforce → Train) execution model, the desired output type is a formal part of the POET configuration. It can be specified as a parameter to the `@poet` decorator (e.g., `@poet(expected_output_type=MyStruct, ...)`). This `expected_output_type` is then available in the `poet_status` context and is used by the `Enforce` phase to ensure the function's output conforms to the expectation.

This shift provides a clearer and more robust way to manage function return types, either through static type checking or through the explicit contract of the POET framework for functions requiring advanced, robust execution.

## 6. Decorators

Decorators provide a way to modify or enhance functions and methods in a declarative way. They are a form of metaprogramming where a function (the decorator) wraps another function to extend its behavior without explicitly modifying its core implementation.

### 6.1. Syntax

A decorator is applied to a function definition by placing the decorator's name (prefixed with `@`) on the line immediately preceding the `def` statement. Decorators can optionally accept arguments.

Basic Syntax:

```dana
@my_decorator
def some_function():
 # ... function body ...
```

Syntax with Decorator Arguments:

```dana
@another_decorator(arg1="value", arg2=100)
def another_function(param: str) -> str:
 # ... function body ...
```

### 6.2. Behavior

In Dana, a decorator is itself a higher-order function. When a function `decorated_func` is decorated with `@decorator_name`, it is equivalent to:

`decorated_func = decorator_name(decorated_func)`

If the decorator takes arguments (e.g., `@decorator_with_args(dec_arg)`), then `decorator_with_args` must be a function that returns the actual decorator function. So, it becomes:

`actual_decorator = decorator_with_args(dec_arg)`
`decorated_func = actual_decorator(decorated_func)`

The `decorated_func` then refers to the function returned by the decorator (which is typically a wrapper around the original function).
Example: A simple logging decorator
```dana
def log_calls(original_function):
 def wrapper(*args, **kwargs):
 log(f"Calling {original_function.__name__} with args: {args}, kwargs: {kwargs}") # Assuming 'log' is a core/built-in function
 local:result = original_function(*args, **kwargs)
 log(f"{original_function.__name__} returned: {result}")
 return local:result
 return wrapper

@log_calls
def add(a: int, b: int) -> int:
 return a + b

# Calling add(5, 3) will now also produce log messages.
local:sum_val = add(5,3)
```

### 6.3. Decorators for POET (Perceive → Operate → Enforce → Train)

A key application of decorators in Dana is to enable and configure the **POET (Perceive → Operate → Enforce → Train)** execution model for user-defined Dana functions. This allows Dana functions to benefit from robust, context-aware execution with built-in retry and enforcement logic.

Refer to the full [POET Execution Model documentation](../02_dana_runtime_and_execution/poet_functions.md) for details on POET.

Conceptual Usage:

Dana might provide a built-in `@poet` decorator or allow for custom POET-configuring decorators.

```dana
# Example: Using a hypothetical built-in @poet decorator

# Dana function to be used for the 'Perceive' phase
def my_perceiver(raw_input: str) -> dict:
 # ... normalize input, gather context ...
 local:perceived = {"text": raw_input.lower(), "length": len(raw_input)}
 # This 'perceived' dict becomes poet_status.perceived_input for Operate and Enforce
 return local:perceived

# Dana function to be used for the 'Enforce' phase
def my_enforcer(operate_output: any, poet_status: dict) -> bool:
 # poet_status contains {attempt, last_failure, max_retries, successful, perceived_input, raw_output, expected_output_type}
 # Here, operate_output is the same as poet_status.raw_output
 log(f"Attempt {poet_status.attempt} to enforce: {operate_output} against type {poet_status.expected_output_type}") # Assuming 'log' is a core/built-in function

 # Example: Check against a specific type if provided in poet_status
 if poet_status.expected_output_type and typeof(operate_output) != poet_status.expected_output_type:
 poet_status.last_failure = f"Output type {typeof(operate_output)} does not match expected type {poet_status.expected_output_type}."
 return False

 # Original example encoding logic (can be combined with type check)
 if typeof(operate_output) == "str" and len(operate_output) > poet_status.perceived_input.length / 2:
 return True
 else:
 poet_status.last_failure = "Output string too short or not a string (and/or type mismatch)."
 return False

@poet(
 perceive=my_perceiver, # Reference to a Dana function
 enforce=my_enforcer, # Reference to a Dana function
 max_retries=2,
 expected_output_type="str" # Example: explicitly requesting a string output
)
def process_text_with_poet(data: str) -> str: # 'data' is the raw_input to my_perceiver
 # This is the 'Operate' phase.
 # It receives the output of 'my_perceiver' as its input argument.
 # In this setup, 'data' would actually be the dictionary from my_perceiver.
 # Let's assume POET handles passing perceived_input to Operate.
 # Or, the signature might be: def process_text_with_poet(perceived_data: dict) -> str:
 # For now, assume 'data' is the perceived input.
 return f"OPERATED ON: {data.text.upper()}"

# When process_text_with_poet("Hello World") is called:
# 1. my_perceiver("Hello World") runs.
# 2. The Operate phase (process_text_with_poet body) runs with perceived input.
# 3. my_enforcer(output_of_operate, poet_status) runs.
# 4. Retries occur if my_enforcer returns false, up to max_retries.
```

Key Aspects for POET Decorators in Dana:

* Specifying P/O/E/T Functions: Decorators allow clear association of Dana functions for the Perceive, Operate (the decorated function itself), Enforce, and Train stages.
* POET Profiles: Decorators might also select pre-configured POET profiles that define default P/O/E/T stages or behaviors (e.g., `@poet_profile("llm_reasoning")`).
* `poet_status` Availability: As shown in `my_enforcer`, the `poet_status` dictionary (containing `attempt`, `last_failure`, `perceived_input`, etc.) is made available to Dana functions participating in the POET lifecycle, enabling adaptive logic.
* Integration with Python Runtime: The underlying POET execution loop (managing retries, calling P/O/E/T stages) is implemented in Python (as described in the POET execution model), but Dana decorators provide the language-level syntax to hook Dana functions into this system.

The exact naming and parameters of the built-in POET-related decorators will be finalized as the POET runtime is implemented.

## 7. Function Composition (Declarative Functions)

Function composition is a powerful capability in Dana for building complex operations by chaining simpler, reusable functions. This approach enhances code clarity, promotes modularity, and simplifies the management of sequential data processing tasks.

### 7.1. Declarative Function Composition

Dana supports function composition through declarative function definitions using the `def` keyword with the `=` operator for composition:

```dana
# Define base functions
def add_ten(x: int) -> int:
    return x + 10

def double(x: int) -> int:
    return x * 2

def stringify(x: int) -> str:
    return f"Result: {x}"

def analyze(x: int) -> dict:
    return {"value": x, "is_even": x % 2 == 0}

def format(x: int) -> str:
    return f"Formatted: {x}"
```

### 7.2. Sequential Composition

Chain functions in sequence using the `|` operator in declarative function definitions:

```dana
# Sequential composition with declarative syntax
def sequential_pipeline(x: int) -> str = add_ten | double | stringify
result = sequential_pipeline(5)  # "Result: 30"

# Complex sequential pipeline
def complex_processor(x: int) -> str = add_ten | double | analyze | format
result = complex_processor(5)  # "Formatted: 30"
```

### 7.3. Parallel Composition

Execute multiple functions in parallel using list syntax in declarative function definitions:

```dana
# Parallel composition with declarative syntax
def parallel_pipeline(x: int) -> list = [analyze, format]
result = parallel_pipeline(10)  # [{"value": 10, "is_even": true}, "Formatted: 10"]

# Mixed sequential + parallel
def mixed_pipeline(x: int) -> list = add_ten | [analyze, format] | stringify
result = mixed_pipeline(5)  # "Result: [{"value": 15, "is_even": false}, "Formatted: 15"]"
```

### 7.4. Complex Multi-Stage Pipelines

Combine sequential and parallel operations in complex workflows using declarative syntax:

```dana
# Complex multi-stage pipeline with declarative syntax
def complex_workflow(x: int) -> list = (
    add_ten | 
    [analyze, double] | 
    format | 
    [stringify, analyze]
)
result = complex_workflow(5)  # [{"value": 30, "is_even": true}, {"value": 30, "is_even": true}]
```

### 7.5. Reusable Pipeline Functions

Create reusable pipeline functions that can be applied to different data:

```dana
# Create reusable pipeline function
def data_processor(x: int) -> list = add_ten | [analyze, format]

# Apply to different datasets
result1 = data_processor(5)   # [{"value": 15, "is_even": false}, "Formatted: 15"]
result2 = data_processor(10)  # [{"value": 20, "is_even": true}, "Formatted: 20"]
result3 = data_processor(15)  # [{"value": 25, "is_even": false}, "Formatted: 25"]
```

### 7.6. Why Use Declarative Function Composition?

* **Clear Signatures**: Function parameters and return types are explicitly defined
* **Readability**: Chains like `def pipeline(x: int) -> str = process_data | filter_results | format_output` clearly express the flow of data and operations
* **Reusability**: Individual functions in the chain remain simple and can be reused in other compositions or standalone
* **Modularity**: Complex tasks are broken down into smaller, manageable, and testable units
* **Maintainability**: Changes to one step in the pipeline are localized to the specific function, reducing the risk of unintended side effects
* **Expressiveness**: It provides a natural way to represent sequential workflows and data transformations directly in the language
* **Parallel Processing**: Support for parallel execution enables efficient processing of multiple operations simultaneously
* **Type Safety**: Explicit type annotations improve code reliability

### 7.7. Syntax and Behavior: The `|` Operator

Dana uses the `|` (pipe) operator for function composition in declarative function definitions:

```dana
# Declarative function composition
def composed_function(x: int) -> int = function_one | function_two | function_three

# Parallel composition in declarative functions
def parallel_function(x: int) -> list = [function_one, function_two, function_three]

# Mixed composition in declarative functions
def mixed_function(x: int) -> list = function_one | [function_two, function_three] | function_four
```

**Execution Behavior:**
* **Sequential Execution**: Functions are executed from left to right, with each function's output becoming the input to the next
* **Parallel Execution**: Functions in lists execute conceptually in parallel, with results collected as a list for the next stage
* **Data Flow**: The return value of each function is passed as the first argument to the next function in the chain
* **Type Compatibility**: For a composition to be valid, the return type of each function (except the last) must be compatible with the input parameter type of the immediately following function

**Composed Function Signature:**
* The composed function accepts the same arguments as the *first* function in the chain
* The return type of the composed function is the return type of the *last* function in the chain
* Parallel functions return lists of results that are passed to subsequent functions

### 7.8. Error Handling and Validation

Dana provides comprehensive error handling for function composition:

```dana
# Missing function error
def invalid_pipeline(x: int) -> int = add_ten | non_existent_function  # ❌ Error: "Function 'non_existent_function' not found"

# Non-function composition error  
def invalid_pipeline(x: int) -> int = add_ten | 42  # ❌ Error: "Cannot use non-function 42 of type int in pipe composition"

# Clear error messages help with debugging
def invalid_pipeline(x: int) -> int = func1 | not_a_function  # ❌ Error: "not_a_function is not callable"
```

**Validation Features:**
* **Function-Only Composition**: Only callable functions can be used in composition chains
* **Missing Function Detection**: Clear error messages when functions are not found
* **Type Validation**: Automatic validation of function signatures and return types
* **Parallel Function Validation**: Ensures all items in parallel lists are callable functions

### 7.9. Design Philosophy: Declarative Function Composition

Dana's function composition follows a declarative approach with clear function signatures:

```dana
# ✅ SUPPORTED: Declarative function composition
def pipeline(x: int) -> int = f1 | f2 | f3    # Clear signature with composition
result = pipeline(data)                       # Clean application

# ✅ SUPPORTED: Parallel functions in declarative definitions
def parallel_pipeline(x: int) -> list = [f1, f2, f3]  # Parallel execution
result = parallel_pipeline(data)

# ✅ SUPPORTED: Mixed composition in declarative functions
def mixed_pipeline(x: int) -> list = f1 | [f2, f3] | f4  # Mixed sequential and parallel
result = mixed_pipeline(data)

# ❌ NOT SUPPORTED: Assignment-based composition (removed for clarity)
# pipeline = f1 | f2 | f3                     # REJECTED - no clear signature
# 5 | double                                  # REJECTED - mixed data/function
# data | [func1, func2]                       # REJECTED - mixed data/function  
```

**Benefits of This Approach:**
* **Clear Signatures**: Function parameters and return types are explicitly defined
* **Reduced Ambiguity**: No confusion between data pipelines and function composition
* **Better Debugging**: Clear error messages and predictable execution flow
* **Functional Programming**: Follows functional programming best practices
* **Maintainability**: Simpler, more focused implementation
* **Type Safety**: Explicit type annotations improve code reliability

## 8. Modules and Imports

Dana code can be organized into multiple files and imported using the `import` statement. This allows for better code organization and reusability. (Further details on module resolution and namespacing will be provided in `modules_and_imports.md`).

Basic Example:

```dana
# In file: my_utils.dna
def utility_function(data: str) -> str:
 return "Processed: " + data
```

```dana
# In file: main.dna
import my_utils.dna as utils

local:result: str = utils.utility_function("sample")
print(local:result)
```