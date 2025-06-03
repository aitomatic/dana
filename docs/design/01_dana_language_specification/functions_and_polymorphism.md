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

Each signature of a polymorphic function can have its own distinct return type. The caller should be aware of this, or the `__dana_desired_type` mechanism can be used to guide the expected return.

## 4. Built-in and Core Functions

Dana provides a set of built-in functions (e.g., `len()`, `print()`, `int()`, `str()`) and core functions that are essential for agent operations (e.g., `reason()`, `log()`). These functions are globally available.

Their specific signatures and behaviors are documented in the API reference materials.

## 5. Caller-Informed Return Types (`__dana_desired_type`)

To enhance the flexibility of functions, especially those that interact with dynamic data sources like LLMs (e.g., the `reason()` core function), Dana supports a mechanism for callers to suggest a desired return structure or type.

*   **Mechanism**: This is achieved by the interpreter making a special value available within the `system:` scope of the `SandboxContext` during a function call, under the key `system:__dana_desired_type`.
*   **Access**: Python-implemented functions can access this via `context.get("system:__dana_desired_type")`. Dana functions can access it via the `system:__dana_desired_type` variable.
*   **Purpose**: A function can inspect `system:__dana_desired_type` and, on a best-effort basis, attempt to format its output to match the requested type or structure. This is particularly useful for `reason()` to guide LLM output formatting (e.g., to produce a JSON string that can be parsed into a specific Dana `struct`).
*   **Precedence**: If `system:__dana_desired_type` is present, it generally guides the function's output. If a function also has an explicit `-> ReturnType` annotation, `__dana_desired_type` can be seen as a more specific, runtime request that might override or refine the general intention of the `-> ReturnType` for that particular call.
*   **Not a Strict Cast**: This is a hint and a best-effort mechanism. It does not guarantee the return type, nor does it perform automatic casting on all function return values. The function itself must implement the logic to adhere to the hint.

**Example Usage (Conceptual):**

```dana
# Assuming UserProfile is a defined struct
# The 'reason' function might internally use __dana_desired_type
# to instruct the LLM to format its output as a UserProfile.
local:user_info: UserProfile = reason(
    prompt="Extract user details for user ID 789.",
    __dana_desired_type=UserProfile # This argument is conventional to signal the intent
                                    # The actual mechanism passes it via system: scope
)
```

## 6. Modules and Imports

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