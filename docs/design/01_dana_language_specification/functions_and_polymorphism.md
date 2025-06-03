# Dana Functions and Polymorphism

This document describes how functions are defined and used in the Dana language, with a special focus on polymorphic functions and the mechanisms for flexible function behavior.

## 1. Function Definition

Functions in Dana are defined using the `def` keyword, followed by the function name, a list of parameters in parentheses, an optional return type annotation, and an indented block of code constituting the function's body.

**Syntax:**

```dana
def <function_name>(<param1>: <type1>, <param2>: <type2>, ...) -> <ReturnType>:
    # Function body
    local:result = ...
    return local:result
```

*   **Parameters**: Parameters can have type annotations (e.g., `count: int`). Default values for parameters are also supported (e.g., `level: str = "info"`).
*   **Return Type**: The `-> <ReturnType>` annotation specifies the intended type of the value the function will return. If a function does not explicitly return a value, its implicit return type is `None`. `-> None` can be used to make this explicit.
*   **Return Statement**: The `return` statement is used to exit a function and optionally pass back a value.

**Example:**

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

**Syntax:**

```dana
<function_name>(<arg1>, <arg2_name>=<value2>, ...)
```

*   **Arguments**: Arguments can be passed positionally or by name (keyword arguments).

**Example:**

```dana
local:greeting: str = greet(name="Alice")
local:total: int = add_numbers(5, 3)
local:another_total: int = add_numbers(a=10)
log_message("System started.")
log_message(message="An error occurred", severity="error")
```

## 3. Polymorphic Functions

Polymorphic functions allow a single function name to have multiple distinct implementations (signatures). The Dana runtime dispatches the call to the correct implementation based on the types (and potentially number) of arguments provided.

This provides a powerful way to handle different data types with the same conceptual operation, enhancing code clarity and flexibility, especially when used with user-defined `structs`.

### 3.1. Definition

A polymorphic function is defined by providing multiple `def` blocks with the **same function name** but **different type annotations for their parameters**.

**Syntax:**

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

**Example: Polymorphic `describe` function**

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

*   **Exact Type Match**: The Dana runtime selects the function implementation whose parameter types exactly match the types of the arguments passed in the call.
*   **Number of Arguments**: The number of arguments must also match the number of parameters in the signature.
*   **No Match**: If no signature provides an exact match for the argument types and count, a runtime error will be raised.
*   **Order of Definition**: For exact matches, the order in which polymorphic signatures are defined does not affect dispatch. (If subtyping or more complex type coercion rules were introduced for dispatch, order might become relevant, but this is not currently the case).

**Example Calls:**

```dana
local:my_point: Point = Point(x=5, y=3)

print(describe("hello"))  # Calls describe(item: str)
print(describe(100))      # Calls describe(item: int)
print(describe(my_point)) # Calls describe(item: Point)

# describe([1,2,3]) # This would cause a runtime error if no describe(item: list) is defined.
```

### 3.3. Return Types

Each signature of a polymorphic function can have its own distinct return type. The caller should be aware of this, or the type system and PAV framework's `expected_output_type` mechanism (for PAV-enabled functions) can guide the expected return.

## 4. Built-in and Core Functions

Dana provides a set of built-in functions (e.g., `len()`, `print()`, `int()`, `str()`) and core functions that are essential for agent operations (e.g., `reason()`, `log()`). These functions are globally available.

Their specific signatures and behaviors are documented in the API reference materials.

## 5. Guiding Function Output: Type Hinting and PAV

Previously, a system-level variable `system:__dana_desired_type` was used as a general mechanism for callers to suggest a desired return structure or type, especially for dynamic functions like those interacting with LLMs. This mechanism is now deprecated in favor of more integrated approaches:

1.  **Standard Type Hinting**: For regular Dana functions, the primary way to indicate expected return types is through the function's own return type annotation (e.g., `-> MyStruct`) and the type hint at the assignment site (e.g., `local:my_var: MyStruct = my_func()`). The Dana type system will enforce these where possible.

2.  **PAV's `expected_output_type`**: For functions using the PAV (Perceive → Act → Validate) execution model, the desired output type is a formal part of the PAV configuration. It can be specified as a parameter to the `@pav` decorator (e.g., `@pav(expected_output_type=MyStruct, ...)`). This `expected_output_type` is then available in the `pav_status` context and is used by the `Validate` phase to ensure the function's output conforms to the expectation.

This shift provides a clearer and more robust way to manage function return types, either through static type checking or through the explicit contract of the PAV framework for functions requiring advanced, robust execution.

## 6. Decorators

Decorators provide a way to modify or enhance functions and methods in a declarative way. They are a form of metaprogramming where a function (the decorator) wraps another function to extend its behavior without explicitly modifying its core implementation.

### 6.1. Syntax

A decorator is applied to a function definition by placing the decorator's name (prefixed with `@`) on the line immediately preceding the `def` statement. Decorators can optionally accept arguments.

**Basic Syntax:**

```dana
@my_decorator
def some_function():
    # ... function body ...
```

**Syntax with Decorator Arguments:**

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

**Example: A simple logging decorator**

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

### 6.3. Decorators for PAV (Perceive → Act → Validate)

A key application of decorators in Dana is to enable and configure the **PAV (Perceive → Act → Validate)** execution model for user-defined Dana functions. This allows Dana functions to benefit from robust, context-aware execution with built-in retry and validation logic.

Refer to the full [PAV Execution Model documentation](../../02_dana_runtime_and_execution/pav_execution_model.md) for details on PAV.

**Conceptual Usage:**

Dana might provide a built-in `@pav` decorator or allow for custom PAV-configuring decorators.

```dana
# Example: Using a hypothetical built-in @pav decorator

# Dana function to be used for the 'Perceive' phase
def my_perceiver(raw_input: str) -> dict:
    # ... normalize input, gather context ...
    local:perceived = {"text": raw_input.lower(), "length": len(raw_input)}
    # This 'perceived' dict becomes pav_status.perceived_input for Act and Validate
    return local:perceived

# Dana function to be used for the 'Validate' phase
def my_validator(act_output: any, pav_status: dict) -> bool:
    # pav_status contains {attempt, last_failure, max_retries, successful, perceived_input, raw_output, expected_output_type}
    # Here, act_output is the same as pav_status.raw_output
    log(f"Attempt {pav_status.attempt} to validate: {act_output} against type {pav_status.expected_output_type}") # Assuming 'log' is a core/built-in function
    
    # Example: Check against a specific type if provided in pav_status
    if pav_status.expected_output_type and typeof(act_output) != pav_status.expected_output_type:
        pav_status.last_failure = f"Output type {typeof(act_output)} does not match expected type {pav_status.expected_output_type}."
        return False

    # Original example validation logic (can be combined with type check)
    if typeof(act_output) == "str" and len(act_output) > pav_status.perceived_input.length / 2:
        return True
    else:
        pav_status.last_failure = "Output string too short or not a string (and/or type mismatch)."
        return False

@pav(
    perceive=my_perceiver,  # Reference to a Dana function
    validate=my_validator,  # Reference to a Dana function
    max_retries=2,
    expected_output_type="str" # Example: explicitly requesting a string output
)
def process_text_with_pav(data: str) -> str: # 'data' is the raw_input to my_perceiver
    # This is the 'Act' phase.
    # It receives the output of 'my_perceiver' as its input argument.
    # In this setup, 'data' would actually be the dictionary from my_perceiver.
    # Let's assume PAV handles passing perceived_input to Act.
    # Or, the signature might be: def process_text_with_pav(perceived_data: dict) -> str:
    # For now, assume 'data' is the perceived input.
    return f"ACTED ON: {data.text.upper()}"

# When process_text_with_pav("Hello World") is called:
# 1. my_perceiver("Hello World") runs.
# 2. The Act phase (process_text_with_pav body) runs with perceived input.
# 3. my_validator(output_of_act, pav_status) runs.
# 4. Retries occur if my_validator returns false, up to max_retries.
```

**Key Aspects for PAV Decorators in Dana:**

*   **Specifying P/V/A Functions**: Decorators allow clear association of Dana functions for the Perceive, Act (the decorated function itself), and Validate stages.
*   **PAV Profiles**: Decorators might also select pre-configured PAV profiles that define default P/V stages or behaviors (e.g., `@pav_profile("llm_reasoning")`).
*   **`pav_status` Availability**: As shown in `my_validator`, the `pav_status` dictionary (containing `attempt`, `last_failure`, `perceived_input`, etc.) is made available to Dana functions participating in the PAV lifecycle, enabling adaptive logic.
*   **Integration with Python Runtime**: The underlying PAV execution loop (managing retries, calling P/A/V stages) is implemented in Python (as described in the PAV execution model), but Dana decorators provide the language-level syntax to hook Dana functions into this system.

The exact naming and parameters of the built-in PAV-related decorators will be finalized as the PAV runtime is implemented.

## 7. Modules and Imports

Dana code can be organized into multiple files and imported using the `import` statement. This allows for better code organization and reusability. (Further details on module resolution and namespacing will be provided in `modules_and_imports.md`).

**Basic Example:**

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