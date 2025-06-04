# Dana Data Types, Structs, and Type System

This document details the Dana language's approach to data types, including its dynamic typing philosophy, built-in types, user-defined `struct`s, type hinting, and automatic type coercion mechanisms.

## 1. Core Typing Philosophy

Dana is a **fundamentally dynamically-typed language**, similar to Python. This provides flexibility, especially when interacting with less predictable inputs, such as those from Large Language Models (LLMs).

Type hints in Dana (`var: type`, `param: type`, `-> ReturnType`) serve several key purposes but do **not** impose rigid, ahead-of-time (AOT) static type checking that would lead to compilation errors for type mismatches. Instead, they are primarily for:

1.  **Clarity and Documentation**: Making code easier for humans to understand and maintain.
2.  **AI Assistance**: Providing crucial information to AI code generators (like an AI assistant helping to write Dana code) to produce more accurate and contextually relevant Dana scripts.
3.  **Enabling Polymorphism**: Allowing the runtime to dispatch function calls to the correct polymorphic function signature based on argument types (see `functions_and_polymorphism.md`).
4.  **Guiding Runtime Coercion**: Informing the `__dana_desired_type` mechanism and potentially other runtime type coercion behaviors.

Runtime type errors may still occur if an operation is performed on an incompatible type (e.g., attempting arithmetic on a string that cannot be coerced to a number), but type hints themselves are not a strict contract enforced before execution.

## 2. Built-in Data Types

Dana supports a set of basic built-in data types:

*   **`int`**: Integer numbers (e.g., `42`, `-100`).
*   **`float`**: Floating-point numbers (e.g., `3.14`, `-0.001`).
*   **`str`**: Strings of text, enclosed in single (`'...'`) or double (`"..."`) quotes (e.g., `'hello'`, `"world"`).
    *   **F-Strings**: Dana supports f-strings for embedding expressions within string literals, prefixed with `f` (e.g., `f"Value is {local:my_var + 10}"`).
*   **`bool`**: Boolean values, `true` or `false`.
*   **`list`**: Ordered, mutable collections of items (e.g., `[1, "apple", true]`).
*   **`dict`**: Unordered collections of key-value pairs (e.g., `{"name": "Alice", "age": 30}`). Keys are typically strings.
*   **`tuple`**: Ordered, immutable collections of items (e.g., `(10, 20)`). *Initial support for tuples might be as a variant of lists; full immutability details TBD.*
*   **`set`**: Unordered collections of unique items (e.g., `{1, 2, 3}`).
*   **`None`**: Represents the absence of a value (e.g., `local:x = None`).
*   **`any`**: A special type hint indicating that a variable or parameter can be of any type. This is an escape hatch for maximal flexibility.

## 3. User-Defined Structs

Structs are user-defined types that group together named fields, each with its own type. They provide a way to create more complex, organized data structures.

### 3.1. Definition

Structs are defined using the `struct` keyword:

```dana
struct <StructName>:
    <field1_name>: <typeAnnotation1>
    <field2_name>: <typeAnnotation2>
    # ... more fields
```

**Example:**

```dana
struct Point:
    x: int
    y: int

struct UserProfile:
    user_id: str
    display_name: str
    email: str
    is_active: bool
    tags: list  # e.g., list of strings
    metadata: dict # e.g., {"last_login": "YYYY-MM-DD"}
```

### 3.2. Instantiation

Struct instances are created by calling the struct name, providing arguments for its fields (typically as named arguments):

```dana
local:p1: Point = Point(x=10, y=20)
local:main_user: UserProfile = UserProfile(
    user_id="usr_123",
    display_name="Alex Example",
    email="alex@example.com",
    is_active=true,
    tags=["beta_tester", "vip"],
    metadata={"last_login": "2024-05-27"}
)
```

### 3.3. Field Access

Fields of a struct instance are accessed using dot notation:

```dana
print(f"Point X: {local:p1.x}")
local:main_user.email = "new_email@example.com"
```

### 3.4. Mutability

By default, Dana structs are **mutable**. Their field values can be changed after instantiation.

### 3.5. Integration with Scopes and Type System

*   **Scopes**: Struct instances are variables and reside within Dana's standard scopes (`local:`, `private:`, `public:`, `system:`).
*   **Type System**: Each `struct` definition introduces a new type name into Dana's type system. This type can be used in variable annotations, function parameters, and return types.

## 4. Type Hinting Syntax

Dana supports type hints for:

*   **Variable Declarations**:
    ```dana
    local:count: int = 0
    private:user_settings: UserProfile = UserProfile(...)
    ```
*   **Function Parameters**:
    ```dana
    def process_data(data: dict, threshold: float = 0.5):
        # ...
    ```
*   **Function Return Types**:
    ```dana
    def get_user(user_id: str) -> UserProfile:
        # ...
        return local:found_user
    
    def log_action(message: str) -> None:
        # ... (no explicit return value)
    ```

## 5. Automatic Type Casting and Coercion

To support a "Do What I Mean" (DWIM) philosophy, especially for agent reasoning and interactions with LLMs, Dana implements several automatic type coercion rules. The goal is to make the language more intuitive while preserving safety.

### 5.1. General Coercion Principles

*   **Conservative Safety First**: Automatic conversions are generally those that are mathematically or logically safe and non-lossy by default for internal operations.
*   **Intuitive Behavior**: Aim for common-sense conversions (e.g., mixed-type arithmetic, string building).
*   **Explicit for Lossy**: Conversions that would lose information (e.g., `float` to `int` truncation) typically require explicit casting functions like `int()`, `str()`, etc.
    ```dana
    local:x_float: float = 3.14
    local:x_int: int = int(local:x_float) # Explicit, results in 3
    ```

### 5.2. Standard Coercion Rules

1.  **Numeric Promotion (Upward)**:
    *   In arithmetic operations, an `int` can be automatically promoted to a `float` if the other operand is a `float`.
      ```dana
      local:i: int = 5
      local:f: float = 3.14
      local:result: float = local:i + local:f  # result is 8.14 (float)
      ```

2.  **String Building Convenience**:
    *   Numbers (`int`, `float`) and booleans (`bool`) can be automatically converted to strings when used with the `+` operator if one of the operands is a string.
      ```dana
      local:count: int = 42
      local:message: str = "Items: " + local:count  # result: "Items: 42"
      
      local:value: float = 9.99
      local:status_msg: str = "Price: " + local:value + " Active: " + true # result: "Price: 9.99 Active: true"
      ```
    *   F-strings are the preferred way for more complex string formatting.

3.  **Flexible Comparisons (Numbers and Numeric Strings)**:
    *   When comparing a number with a string, if the string can be unambiguously interpreted as that numeric type, coercion may occur for the comparison.
      ```dana
      local:count_val: int = 42
      if local:count_val == "42": # Evaluates to true
          log("Match found")
      
      local:price_val: float = 9.99
      if local:price_val == "9.99": # Evaluates to true
          log("Price match")
      ```
    *   **Caution**: This should be well-defined to avoid ambiguity. Direct comparison between types without implicit coercion is the default; this rule applies to make common cases ergonomic.

4.  **Boolean Contexts (Truthiness)**:
    *   In conditional statements (`if`, `while`), various types are evaluated for truthiness:
        *   **`bool`**: `false` is false; `true` is true.
        *   **`None`**: `None` is false.
        *   **Numbers (`int`, `float`)**: Zero (0, 0.0) is false; all other numbers are true.
        *   **Strings (`str`)**: An empty string (`""`) is false; all other strings are true.
        *   **Collections (`list`, `dict`, `set`, `tuple`)**: Empty collections are false; non-empty collections are true.
      ```dana
      local:items: list = []
      if local:items: # false, because items is empty
          # ...
      
      local:name: str = "Dana"
      if local:name: # true, because name is not empty
          # ...
      ```

### 5.3. LLM Response Coercion (Primarily for `reason()` outputs)

Function return values, especially from LLM interactions via `reason()`, often arrive as strings but may represent other data types. Dana applies intelligent coercion to these string outputs:

1.  **Boolean-like Responses**:
    *   Strings like `"yes"`, `"true"`, `"1"`, `"correct"`, `"valid"`, `"ok"` are coerced to `true`.
    *   Strings like `"no"`, `"false"`, `"0"`, `"incorrect"`, `"invalid"` are coerced to `false`.
    ```dana
    local:decision: bool = reason("Should we proceed? Answer yes or no") # e.g., LLM returns "yes"
    if local:decision: # decision is now boolean true
        log("Proceeding.")
    ```

2.  **Numeric Responses**:
    *   Strings representing integers (e.g., `"42"`, `"-10"`) are coerced to `int`.
    *   Strings representing floats (e.g., `"3.14"`, `".5"`) are coerced to `float`.
    ```dana
    local:count_str: str = reason("How many items?") # e.g., LLM returns "7"
    local:total: int = local:count_str + 3          # total becomes 10 (int)
    ```

3.  **Default Behavior**: If a string response from an LLM doesn't match common boolean or numeric patterns, it remains a string. More complex parsing (e.g., for JSON, or specific struct formats) might require explicit parsing functions or be influenced by the `__dana_desired_type` mechanism.

### 5.4. Configuration

The specifics of auto-coercion, especially for LLM responses (e.g., "conservative" vs. "smart" modes for extracting numbers from text), might be configurable via system settings or IPV profiles, but the general rules above form the baseline.

## 6. Caller-Informed Desired Type (`__dana_desired_type`)

While detailed in `functions_and_polymorphism.md` and `pav_execution_model.md`, it's relevant to note here that functions (especially `reason()` and other IPV-enabled functions) can be informed of an expected return type or structure by the caller. This is achieved via a special `system:__dana_desired_type` variable passed in the `SandboxContext`.

This mechanism allows functions to attempt to format their output according to the caller's needs, further enhancing the synergy between dynamic typing and context-aware execution. For example, `reason("Extract user details", __dana_desired_type=UserProfile)` might guide the LLM to return a structure compatible with the `UserProfile` struct.

This is a hint and a best-effort mechanism, not a strict compile-time or runtime cast enforced on all functions. 