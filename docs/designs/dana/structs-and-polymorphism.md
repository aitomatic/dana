# Dana Language Evolution: Structs and Polymorphic Functions

## 1. Overview and Motivation

This document proposes an evolution of the Dana language, drawing inspiration from Golang's design principles, particularly:

1.  **Clear separation of data and behavior**: Data will be primarily managed in `struct` types (data containers), and functions will operate on instances of these structs.
2.  **Structured data types**: Introducing user-defined `structs` for better data organization and explicitness.
3.  **Flexible function dispatch**: Enabling `polymorphic functions` that can have multiple signatures and dispatch based on argument types.

The goal is to enhance Dana's capability to model complex data and logic in a clean, maintainable, and explicit way, further empowering its use in agent reasoning and structured programming. This aligns with Dana's philosophy of being an imperative and interpretable language.

**Key Motivations for this Direction (vs. Traditional Pythonic Object-Orientation):**

*   **Alignment with Neurosymbolic Architecture**:
    *   **Fault-Tolerant Inference (Input)**: The neuro/LLM side of OpenDXA deals with converting potentially unstructured or variably structured user input/external data into actionable information. `Structs` provide well-defined schemas for the symbolic side to target. Polymorphic functions can then robustly handle different types of structured data derived from the inference process (e.g., different intents, entities, or structured outputs from the `reason()` primitive).
    *   **Symbolically Deterministic Processing**: Once data is encapsulated in `structs`, functions operating on them can be designed for deterministic behavior, a cornerstone of the symbolic processing aspect. The separation of "plain data" from "processing logic" reinforces this determinism.

*   **Simplified State Management within `SandboxRuntime`**:
    *   Dana's `SandboxRuntime` is responsible for managing state across different scopes (`local:`, `private:`, `public:`, `system:`).
    *   Proposed `structs` are primarily data containers. Instances of structs are state variables that live directly within these managed scopes (e.g., `local:my_data: MyStruct = MyStruct(...)`).
    *   This contrasts with traditional OO objects which bundle state *and* behavior, potentially creating internal object state that is less transparent or managed independently of the `SandboxRuntime`. The proposed model keeps state management flatter, more explicit, and centrally controlled.

*   **Clarity, Simplicity, and Explicitness**:
    *   Separating data (structs) from the logic operating on them (functions) leads to simpler, more understandable code. Functions explicitly declare the data they operate on through their parameters, making data flow highly transparent.
    *   This reduces the cognitive load compared to object methods where behavior can implicitly depend on a wide array of internal object state.

*   **Enhanced Composability and Functional Paradigm**:
    *   Free functions operating on data structures are inherently more composable, aligning well with Dana's pipe operator (`|`) for building processing pipelines (e.g., `data_struct | func1 | func2`).
    *   This encourages a more functional approach to data transformation, which is beneficial for complex reasoning chains and an agent's decision-making processes.

*   **Improved Testability**:
    *   Functions that primarily accept data structures as input and produce data structures as output (or explicitly modify mutable inputs) are generally easier to unit test in isolation.

*   **Serialization and Data Interchange**:
    *   Plain data structs are more straightforward to serialize, deserialize, and transfer (e.g., for communication with LLMs, tools, or other agent components).

*   **Discouraging Overly Complex Objects**:
    *   This design naturally discourages the creation of overly large objects with excessive internal state and methods. Functions can be organized logically into modules based on functionality, rather than all being tied to a single class definition.

In essence, this Golang-inspired direction steers Dana towards a more data-centric and explicit functional programming style. `Structs` serve as the "nouns" (the data), and polymorphic functions serve as the "verbs" (the operations), leading to a system that is arguably easier to reason about, manage, and evolve, especially within OpenDXA's specific architectural context.

## 2. Structs in Dana

Structs are user-defined types that group together named fields, each with its own type. They are envisioned to be similar in spirit to Python's dataclasses or Go's structs.

### 2.1. Definition

Structs are defined using the `struct` keyword, followed by the struct name and a block containing field definitions. Each field consists of a name and a type annotation.

**Syntax:**

```dana
struct <StructName>:
    <field1_name>: <type1>
    <field2_name>: <type2>
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
    metadata: dict
```

### 2.2. Instantiation

Struct instances are created by calling the struct name as if it were a function, providing arguments for its fields. Named arguments will be the standard way.

**Syntax:**

```dana
<variable_name>: <StructName> = <StructName>(<field1_name>=<value1>, <field2_name>=<value2>, ...)
```

**Example:**

```dana
p1: Point = Point(x=10, y=20)
main_user: UserProfile = UserProfile(
    user_id="usr_123",
    display_name="Alex Example",
    email="alex@example.com",
    is_active=true,
    tags=["beta_tester", "vip"],
    metadata={"last_login": "2024-05-27"}
)
```
Consideration: Positional arguments for instantiation could be a future enhancement if a clear ordering of fields is established, but named arguments provide more clarity initially.

### 2.3. Field Access

Fields of a struct instance are accessed using dot notation.

**Syntax:**

```dana
<struct_instance>.<field_name>
```

**Example:**

```dana
print(f"Point coordinates: ({p1.x}, {p1.y})")

if main_user.is_active:
    log(f"User {main_user.display_name} ({main_user.email}) is active.")

# Fields can also be modified if the struct is mutable
p1.x = p1.x + 5
```

### 2.4. Mutability

By default, Dana structs will be **mutable**. This aligns with Dana's imperative nature and the common behavior of structs in languages like Go and default behavior of Python dataclasses.

Future Consideration: A `frozen_struct` or a modifier (`frozen struct Point: ...`) could be introduced later if immutable structs are deemed necessary for specific use cases.

### 2.5. Integration with Scopes and Type System

-   **Scopes**: Struct instances are variables and adhere to Dana's existing scoping rules (`local:`, `private:`, `public:`, `system:`).
    ```dana
    private:admin_profile: UserProfile = UserProfile(...)
    local:current_location: Point = Point(x=0, y=0)
    ```
-   **Type System**: Each `struct` definition introduces a new type name into Dana's type system. This type can be used in variable annotations, function parameters, and return types. The `types.md` document would need to be updated to reflect user-defined types.

### 2.6. Underlying Implementation (Conceptual)

Internally, when Dana is hosted in a Python environment, these structs could be dynamically translated to Python `dataclasses` or equivalent custom classes, managed by the Dana runtime.

## 3. Polymorphic Functions

Polymorphic functions allow a single function name to have multiple distinct implementations (signatures), with the runtime dispatching to the correct implementation based on the types (and potentially number) of arguments provided during a call.

### 3.1. Definition

A polymorphic function is defined by providing multiple `def` blocks with the same function name but different type annotations for their parameters.

**Syntax:**

```dana
def <function_name>(<param1>: <typeA>, <param2>: <typeB>) -> <returnTypeX>:
    # Implementation for TypeA, TypeB
    ...

def <function_name>(<param1>: <typeC>, <param2>: <typeD>) -> <returnTypeY>:
    # Implementation for TypeC, TypeD
    ...

def <function_name>(<param_struct>: <UserDefinedStructType>) -> <returnTypeZ>:
    # Implementation for a specific struct type
    ...
```

**Example:**

```dana
# Polymorphic function 'describe'
def describe(item: str) -> str:
    return f"This is a string: '{item}'"

def describe(item: int) -> str:
    return f"This is an integer: {item}"

def describe(item: Point) -> str:
    return f"This is a Point at ({item.x}, {item.y})"

def describe(profile: UserProfile) -> str:
    return f"User: {profile.display_name} (ID: {profile.user_id})"
```

### 3.2. Dispatch Rules

-   The Dana runtime will select the function implementation that **exactly matches** the types of the arguments passed in the call.
-   The number of arguments must also match.
-   If no exact match is found, a runtime error will be raised.
-   Order of definition of polymorphic signatures does not currently affect dispatch for exact matches. If subtyping or type coercion were introduced later, order might become relevant.

**Example Calls:**

```dana
my_point: Point = Point(x=5, y=3)
my_user: UserProfile = UserProfile(user_id="u001", display_name="Test", email="test@example.com", is_active=false, tags=[], metadata={})

print(describe("hello"))  # Calls describe(item: str)
print(describe(100))      # Calls describe(item: int)
print(describe(my_point)) # Calls describe(item: Point)
print(describe(my_user))  # Calls describe(profile: UserProfile)

# describe([1,2,3]) # This would cause a runtime error if no describe(item: list) is defined.
```

### 3.3. Return Types

Each signature of a polymorphic function can have a different return type. The type system must be able to track this.

### 3.4. Interaction with Structs

Polymorphic functions are particularly powerful when combined with structs, allowing functions to operate on different data structures in a type-safe manner, while maintaining a clear separation of data (structs) and behavior (functions).

**Example: Geometric operations**

```dana
struct Circle:
    radius: float

struct Rectangle:
    width: float
    height: float

def area(shape: Circle) -> float:
    # Using system:pi if available, or a local constant
    # local:pi_val: float = 3.1415926535
    return 3.1415926535 * shape.radius * shape.radius # For simplicity here

def area(shape: Rectangle) -> float:
    return shape.width * shape.height

c: Circle = Circle(radius=5.0)
r: Rectangle = Rectangle(width=4.0, height=6.0)

log(f"Area of circle: {area(c)}")     # Dispatches to area(shape: Circle)
log(f"Area of rectangle: {area(r)}") # Dispatches to area(shape: Rectangle)
```

## 4. Combined Usage Example: Agent Task Processing

```dana
struct EmailTask:
    task_id: str
    recipient: str
    subject: str
    body: str

struct FileProcessingTask:
    task_id: str
    file_path: str
    operation: str # e.g., "summarize", "translate"

# Polymorphic function to handle different task types
def process_task(task: EmailTask) -> dict:
    log(f"Processing email task {task.task_id} for {task.recipient}")
    # ... logic to send email ...
    # result_send = system:email.send(to=task.recipient, subject=task.subject, body=task.body)
    return {"status": "email_sent", "recipient": task.recipient}

def process_task(task: FileProcessingTask) -> dict:
    log(f"Processing file task {task.task_id} for {task.file_path} ({task.operation})")
    content: str = "" # system:file.read(task.file_path)
    processed_content: str = ""
    if task.operation == "summarize":
        processed_content = reason(f"Summarize this content: {content}")
    elif task.operation == "translate":
        processed_content = reason(f"Translate to Spanish: {content}")
    else:
        return {"status": "error", "message": "Unsupported file operation"}
    
    # system:file.write(f"{task.file_path}_processed.txt", processed_content)
    return {"status": "file_processed", "path": task.file_path, "operation": task.operation}

# Example task instances
email_job: EmailTask = EmailTask(task_id="e001", recipient="team@example.com", subject="Update", body="Project Alpha is on schedule.")
file_job: FileProcessingTask = FileProcessingTask(task_id="f001", file_path="/data/report.txt", operation="summarize")

# Processing tasks
email_result = process_task(email_job)
file_result = process_task(file_job)

print(f"Email result: {email_result}")
print(f"File result: {file_result}")
```

## 5. Impact and Considerations

### 5.1. Grammar & Parser
The Dana grammar (e.g., `dana_grammar.lark`) will need extensions:
-   A new rule for `struct_definition`.
-   Potentially adjust rules for function calls and definitions to accommodate type-based dispatch lookups.

### 5.2. Abstract Syntax Tree (AST)
New AST nodes will be required:
-   `StructDefinitionNode` (capturing name, fields, and types).
-   `StructInstantiationNode`.
The `FunctionDefinitionNode` might need to be adapted or the `FunctionRegistry` made more complex to handle multiple definitions under one name.

### 5.3. Function Registry
The `FunctionRegistry` will require significant changes:
-   It must store multiple function implementations for a single function name.
-   The dispatch mechanism will need to inspect argument types at runtime and match them against the registered signatures.
-   A strategy for handling "no match" errors is crucial.

### 5.4. Type System
-   The concept of user-defined types (from structs) needs to be added to the type system.
-   The existing `types.md` states "Type-based function overloading" as a non-goal. This proposal explicitly revisits and implements it. The document should be updated to reflect this change in philosophy, justified by the benefits of this more expressive model.
-   Type checking (if any beyond runtime dispatch) would become more complex.

### 5.4.1. Dana's Dynamic Typing Philosophy and Caller-Informed Schemas

It is crucial to reiterate that **Dana remains a fundamentally dynamically-typed language**, akin to Python. The introduction of type hints for structs and polymorphic functions serves specific purposes without imposing rigid static typing that would hinder the fault-tolerant nature of LLM interactions.

**Key Principles:**

1.  **Role of Type Hints**:
    *   **Clarity and Documentation**: Type hints (`var: type`, `param: type`, `-> ReturnType`) primarily enhance code readability and serve as documentation for developers and AI code generators.
    *   **Enabling Polymorphism**: They provide the necessary information for the Dana runtime to dispatch calls to the correct polymorphic function signature based on argument types.
    *   **Not Strict Static Enforcement**: Type hints do *not* typically lead to traditional ahead-of-time (AOT) static type checking that would automatically reject code. Instead, they are more like runtime assertions or guides, especially for return types. The primary enforcement is at the boundary of polymorphic function dispatch (matching argument types).

2.  **Declared Return Types (`-> ReturnType`) as Author Intent**:
    *   When a function is defined with `-> ReturnType`, this signals the author's primary intention for the function's output.
    *   Functions should generally strive to return data conforming to this type.
    *   The interpreter *may* perform light coercion or validation against this declared type upon return, especially if the caller hasn't provided a more specific desired type.

3.  **Caller-Informed Return Types (via `system:__dana_desired_type`)**:
    To enhance flexibility, especially for functions interacting with dynamic sources like LLMs (e.g., `reason()`), Dana supports a mechanism for callers to suggest a desired return structure/type. This allows a single function to adapt its output format based on the caller's specific needs.

    *   **Mechanism**: When a Dana expression implies a specific desired type for a function's return value (e.g., through assignment to a typed variable: `private:my_var: MyStruct = some_function(...)`), the Dana interpreter makes this desired type available to the called function.
    *   **Passing via `SandboxContext`**: The interpreter conveys this information by placing the desired type into the `system:` scope of the `SandboxContext` for that specific function call. It will be accessible via the key `system:__dana_desired_type`.
    *   **Access by Functions**:
        *   **Built-in functions** (implemented in Python) can retrieve this value from the `SandboxContext` object they receive (e.g., `context.get("system:__dana_desired_type")`).
        *   **User-defined Dana functions** can, if necessary, inspect `system:__dana_desired_type` directly in their code, although this is expected to be an advanced use case.
    *   **Precedence**: If `system:__dana_desired_type` is present, it generally takes precedence over the function's declared `-> ReturnType` in guiding the function's output formatting and validation, especially for adaptable functions like `reason()`. If absent, the function's declared `-> ReturnType` is the primary guide.
    *   **Best-Effort Basis**: Functions, particularly those like `reason()` that generate complex data, should attempt to honor `system:__dana_desired_type` on a best-effort basis. It's a hint to guide output, not a strict contract that will fail compilation if not perfectly met by the function's internal logic. The final validation might occur by the interpreter upon return, comparing against the `system:__dana_desired_type` if present, or the function's declared `-> ReturnType`.
    *   **Example with `reason()`**:
        ```dana
        # Caller desires a string
        private:summary_text: str = reason("Summarize the input")

        # Caller desires a list of strings
        private:key_points: list[str] = reason("Extract key points")

        # Caller desires a custom struct
        struct MyData {
            name: str
            value: int
        }
        private:structured_data: MyData = reason("Extract name and value from the report")
        ```
        In these examples, the `reason()` function would find `str`, `list[str]`, or `MyData` respectively in `system:__dana_desired_type` within its execution context and tailor its LLM prompt and output parsing accordingly.

4.  **Error Handling and Type Mismatches**:
    *   While Dana is dynamically typed, mismatches encountered at runtime (e.g., a function returning a string when an integer was strongly expected by the caller and cannot be coerced) will result in runtime errors, similar to Python.
    *   The goal is to provide flexibility for LLM outputs while still allowing for structured data processing where needed.

This approach maintains Dana's dynamic nature while providing robust hints for both AI code generation and runtime behavior, especially for functions that need to adapt their output structure.

### 5.5. Backward Compatibility
-   Existing Dana code that does not use `struct`s or polymorphic functions should remain fully compatible.
-   Defining a struct or a polymorphic function should not conflict with existing syntax or semantics unless a name clashes, which is standard behavior.

## 6. Future Considerations (Brief)

-   **Struct Methods (Syntactic Sugar)**: While the core idea is separation, `instance.method(args)` could be syntactic sugar for `method(instance, args)`, common in languages like Go (receivers) or Rust.
-   **Interfaces/Protocols**: A way to define that a struct "satisfies" an interface, enabling more abstract polymorphism.
-   **Generics**: Generic structs (`struct List<T>: ...`) or functions (`def process<T>(item: T): ...`) are a distant future possibility if complex use cases demand them.
-   **Default Field Values for Structs**: `struct Point: x: int = 0, y: int = 0`.
-   **Construction from Dictionaries**: A built-in way to instantiate a struct from a dictionary, e.g., `Point.from_dict({"x": 10, "y": 20})`.

This design aims to provide a solid foundation for these features, keeping complexity manageable initially while allowing for future growth. 