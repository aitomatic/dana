# Lambda Expressions Primer

## TL;DR (1 minute read)

```dana
# Instead of this (verbose function definitions):
def double(x: int) -> int:
    return x * 2

def add(x: int, y: int) -> int:
    return x + y

def complex_calc(a: float, b: float, c: float, x: float) -> float:
    return a * x * x + b * x + c

# Do this (concise lambda expressions):
double = lambda x: int :: x * 2
add = lambda x, y :: x + y
quadratic = lambda a, b, c, x :: a * x * x + b * x + c

# Lambda with struct receiver (like methods):
translate_point = lambda (point: Point) dx: float, dy: float :: Point(
    x=point.x + dx, 
    y=point.y + dy
)

# Lambda with conditional expressions (ternary operator):
get_first = lambda lst :: lst[0] if len(lst) > 0 else None
max_func = lambda a, b :: a if a > b else b
classify = lambda x :: "positive" if x > 0 else ("zero" if x == 0 else "negative")

# Lambda in pipelines:
pipeline = (lambda x :: x * 2) | (lambda y :: y + 1) | (lambda z :: z * z)
result = pipeline(5)  # 5 → 10 → 11 → 121

# Lambda with union types:
area_calc = lambda (shape: Point | Circle | Rectangle) :: {
    return 0.0 if shape._type.name == "Point"
    else 3.14159 * shape.radius ** 2 if shape._type.name == "Circle"
    else shape.width * shape.height
}
```

---

**What it is**: Lambda expressions in Dana are concise, anonymous functions that can be assigned to variables, passed as arguments, or used in pipelines. They support type hints, struct receivers, and union types - making them more powerful than Python's lambdas.

## Why Should You Care?

If you're coming from Python, you're probably familiar with lambda expressions:

```python
# Python lambdas - limited but useful
double = lambda x: x * 2
add = lambda x, y: x + y

# But Python lambdas are limited:
# - No type hints
# - No multi-line expressions
# - No complex logic
# - No method-like behavior
```

Dana lambdas are much more powerful and use a clearer syntax:

```dana
# Dana lambdas - full-featured with :: syntax
double = lambda x: int :: x * 2
add = lambda x: int, y: int :: x + y

# With type hints, complex expressions, and struct receivers:
translate_point = lambda (point: Point) dx: float, dy: float :: Point(
    x=point.x + dx, 
    y=point.y + dy
)

# Usage like methods:
point = Point(x=3, y=4)
moved = translate_point(point, 2, 1)  # Point(x=5, y=5)
```

**Key Syntax Difference**: Dana uses `::` instead of `:` for lambda bodies:
- **Python**: `lambda x: x * 2` (uses `:` for body)
- **Dana**: `lambda x :: x * 2` (uses `::` for body)

This design choice makes Dana lambdas:
- **More explicit**: `::` clearly indicates function/arrow relationship
- **Less confusing**: Avoids `:` being used for both type hints and lambda bodies
- **Consistent**: Matches Dana's function return type syntax `def func() -> int`

**Dana lambdas give you the power of full functions with the conciseness of expressions:**

- **Type safety**: Full type hint support
- **Struct receivers**: Method-like behavior on data
- **Complex expressions**: Multi-line and nested logic
- **Conditional expressions**: Ternary operator support (`expr if condition else expr`)
- **Pipeline integration**: Seamless composition
- **Union types**: Handle multiple types elegantly

## The Big Picture

Lambda expressions in Dana serve multiple purposes:

```dana
# 1. Simple anonymous functions
square = lambda x :: x * x

# 2. Conditional logic with ternary operator
get_first = lambda lst :: lst[0] if len(lst) > 0 else None
max_func = lambda a, b :: a if a > b else b
```

# 3. Type-safe operations
safe_divide = lambda x: float, y: float :: {
    return x / y if y != 0 else 0.0
}

# 4. Struct methods (receiver syntax)
scale_point = lambda (point: Point) factor: float :: Point(
    x=point.x * factor,
    y=point.y * factor
)

# 5. Pipeline components
data_processor = (lambda x :: x.strip()) | 
                (lambda x :: x.upper()) | 
                (lambda x :: f"PROCESSED: {x}")

# 6. Union type handlers
shape_analyzer = lambda (shape: Point | Circle | Rectangle) :: {
    return "point" if shape._type.name == "Point"
    else "circle" if shape._type.name == "Circle"
    else "rectangle"
}
```

## Basic Lambda Syntax

**Python vs Dana Lambda Syntax**:

```python
# Python lambda syntax (uses : for body)
double = lambda x: x * 2
add = lambda x, y: x + y
typed_add = lambda x, y: x + y  # No type hints in Python
```

```dana
# Dana lambda syntax (uses :: for body)
double = lambda x :: x * 2
add = lambda x, y :: x + y
typed_add = lambda x: int, y: int :: x + y  # Full type hints
```

**Simple Lambda Expressions**:

```dana
# No parameters
zero = lambda :: 0
constant = lambda :: "Hello, World!"

# Single parameter
double = lambda x :: x * 2
square = lambda n :: n * n

# Multiple parameters
add = lambda x, y :: x + y
multiply = lambda a, b, c :: a * b * c

# With type hints
typed_add = lambda x: int, y: int :: x + y
typed_multiply = lambda x: float, y: float :: x * y
```

**Complex Lambda Bodies**:

```dana
# Multi-line expressions with blocks
complex_calc = lambda x: float, y: float :: {
    temp = x * y
    result = temp + x + y
    return result * 2
}

# Conditional logic
safe_divide = lambda x: float, y: float :: {
    return x / y if y != 0 else 0.0
}

# Nested expressions
quadratic = lambda a, b, c, x :: a * x * x + b * x + c
```

## Conditional Expressions in Lambdas

Lambda expressions support conditional expressions (ternary operator) for concise decision-making:

```dana
# Basic conditional expressions
get_first = lambda lst :: lst[0] if len(lst) > 0 else None
max_func = lambda a, b :: a if a > b else b
min_func = lambda a, b :: a if a < b else b

# Safe operations with conditionals
safe_divide = lambda a, b :: a / b if b != 0 else float('inf')
safe_sqrt = lambda x :: x ** 0.5 if x >= 0 else 0
safe_reciprocal = lambda x :: 1.0 / x if x != 0 else float('inf')

# String operations with conditionals
string_ops = lambda s :: s.strip().lower() if s else ""
format_name = lambda name :: name.title() if name else "Unknown"

# Type-safe conversions
safe_int_convert = lambda x :: int(x) if str(x).isdigit() else 0
safe_float_convert = lambda x :: float(x) if str(x).replace('.', '').isdigit() else 0.0
```

**Nested Conditionals (Right-Associative)**:

```dana
# Multiple conditions with proper associativity
classify_number = lambda x :: "positive" if x > 0 else ("zero" if x == 0 else "negative")

# Grade calculation
grade_calc = lambda score :: "A" if score >= 90 else ("B" if score >= 80 else ("C" if score >= 70 else "F"))

# Complex classification
status_check = lambda value :: "high" if value > 100 else ("medium" if value > 50 else ("low" if value > 0 else "zero"))
```

**Conditional Expressions with Struct Receivers**:

```dana
struct Person:
    name: str
    age: int
    email: str

# Conditional logic on struct fields
get_display_name = lambda (person: Person) :: person.name if person.name else "Anonymous"
is_adult = lambda (person: Person) :: True if person.age >= 18 else False
get_domain = lambda (person: Person) :: person.email.split("@")[1] if "@" in person.email else ""
```

**Conditional Expressions in Pipelines**:

```dana
# Pipeline with conditional processing
data_pipeline = (lambda x :: x.strip() if x else "") | 
               (lambda x :: x.upper() if x else "") | 
               (lambda x :: f"PROCESSED: {x}" if x else "EMPTY")

# Conditional filtering in pipeline
filter_pipeline = (lambda x :: x if x > 0 else None) | 
                 (lambda x :: x * 2 if x else 0)
```

**Key Benefits**:
- **Concise decision-making**: No need for verbose if/else blocks
- **Functional style**: Expressions instead of statements
- **Pipeline integration**: Seamless composition with other operations
- **Type safety**: Works with Dana's type system
- **Right-associative**: Proper handling of nested conditionals

## Lambda with Struct Receivers

Lambda expressions can have struct receivers, making them behave like methods:

```dana
struct Point:
    x: float
    y: float

# Lambda with receiver (like a method)
translate_point = lambda (point: Point) dx: float, dy: float :: Point(
    x=point.x + dx,
    y=point.y + dy
)

scale_point = lambda (point: Point) factor: float :: Point(
    x=point.x * factor,
    y=point.y * factor
)

# Usage
point = Point(x=3, y=4)
moved = translate_point(point, 2, 1)    # Point(x=5, y=5)
scaled = scale_point(point, 2.0)        # Point(x=6, y=8)
```

**Receiver Syntax**:
- `lambda (receiver: Type) param1, param2 :: expression`
- The receiver is the first parameter, wrapped in parentheses
- Type hints are supported for both receiver and parameters

## Lambda with Union Types

Lambda expressions can handle multiple types using union receivers:

```dana
struct Point:
    x: float
    y: float

struct Circle:
    radius: float
    center: Point

struct Rectangle:
    width: float
    height: float

# Lambda with union receiver
calculate_area = lambda (shape: Point | Circle | Rectangle) :: {
    return 0.0 if shape._type.name == "Point"
    else 3.14159 * shape.radius ** 2 if shape._type.name == "Circle"
    else shape.width * shape.height
}

# Lambda with union receiver and parameters
transform_shape = lambda (shape: Point | Circle | Rectangle) factor: float :: {
    return Point(x=shape.x * factor, y=shape.y * factor) if shape._type.name == "Point"
    else Circle(radius=shape.radius * factor, center=shape.center) if shape._type.name == "Circle"
    else Rectangle(width=shape.width * factor, height=shape.height * factor)
}

# Usage
point = Point(x=3, y=4)
circle = Circle(radius=5, center=Point(x=0, y=0))
rectangle = Rectangle(width=10, height=5)

point_area = calculate_area(point)      # 0.0
circle_area = calculate_area(circle)    # 78.54...
rect_area = calculate_area(rectangle)   # 50.0
```

## Lambda in Pipelines

Lambda expressions integrate seamlessly with Dana's pipeline syntax:

```dana
# Simple pipeline with lambdas
number_pipeline = (lambda x :: x * 2) | (lambda y :: y + 1) | (lambda z :: z * z)
result = number_pipeline(5)  # 5 → 10 → 11 → 121

# Text processing pipeline
text_pipeline = (lambda x :: x.strip()) | 
               (lambda x :: x.upper()) | 
               (lambda x :: f"PROCESSED: {x}")

result = text_pipeline("  hello world  ")  # "PROCESSED: HELLO WORLD"

# Complex pipeline with struct receivers
shape_pipeline = (lambda (shape: Point | Circle) -> calculate_area(shape)) |
                (lambda area -> f"Area: {area:.2f}")

point = Point(x=3, y=4)
area_text = shape_pipeline(point)  # "Area: 0.00"
```

## Higher-Order Functions with Lambdas

Lambda expressions work perfectly with higher-order functions:

```dana
# Map with lambda
numbers = [1, 2, 3, 4, 5]
doubled = [lambda x -> x * 2 for item in numbers]

# Filter with lambda
evens = [item for item in numbers if lambda x -> x % 2 == 0]

# Custom higher-order functions
def map_collection(collection: list, transform):
    return [transform(item) for item in collection]

def filter_collection(collection: list, predicate):
    return [item for item in collection if predicate(item)]

# Usage with lambdas
numbers = [1, 2, 3, 4, 5]
squares = map_collection(numbers, lambda x -> x * x)
evens = filter_collection(numbers, lambda x -> x % 2 == 0)
```

## Type Safety and Validation

Lambda expressions support full type safety:

```dana
# Type hints for parameters
typed_lambda = lambda x: int, y: float -> x + int(y)

# Type hints for receiver
typed_receiver = lambda (point: Point) dx: int -> Point(
    x=point.x + dx,
    y=point.y + dx
)

# Union types with type checking
safe_processor = lambda (data: str | int | float) -> {
    return data.upper() if data._type.name == "str"
    else str(data) if data._type.name in ["int", "float"]
    else "unknown"
}

# Validation in lambda body
safe_divide = lambda x: float, y: float -> {
    return x / y if y != 0 else 0.0
}
```

## Best Practices

**When to Use Lambda Expressions**:

```dana
# ✅ Good: Simple transformations
double = lambda x -> x * 2
square = lambda x -> x * x

# ✅ Good: Pipeline components
pipeline = (lambda x -> x.strip()) | (lambda x -> x.upper())

# ✅ Good: Struct receivers for method-like behavior
translate = lambda (point: Point) dx, dy -> Point(x=point.x + dx, y=point.y + dy)

# ✅ Good: Union type handlers
processor = lambda (data: str | int) -> str(data)

# ❌ Avoid: Complex logic (use regular functions instead)
# complex_lambda = lambda x, y, z -> {
#     # 20 lines of complex logic
#     # Better as a regular function
# }
```

**Naming Conventions**:

```dana
# ✅ Good: Descriptive names
double_number = lambda x -> x * 2
calculate_distance = lambda x1, y1, x2, y2 -> ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

# ❌ Avoid: Generic names
f = lambda x -> x * 2
func = lambda a, b -> a + b
```

## Common Patterns

**Data Transformation**:

```dana
# Simple transformations
to_uppercase = lambda s -> s.upper()
to_lowercase = lambda s -> s.lower()
strip_whitespace = lambda s -> s.strip()

# Numeric transformations
square = lambda x -> x * x
cube = lambda x -> x * x * x
absolute = lambda x -> x if x >= 0 else -x

# Conditional transformations
get_first = lambda lst :: lst[0] if len(lst) > 0 else None
get_last = lambda lst :: lst[-1] if len(lst) > 0 else None
```

**Validation and Filtering**:

```dana
# Validation lambdas
is_positive = lambda x -> x > 0
is_even = lambda x -> x % 2 == 0
is_valid_email = lambda s -> "@" in s and "." in s

# Safe operations with conditionals
safe_divide = lambda x, y :: x / y if y != 0 else float('inf')
safe_sqrt = lambda x :: x ** 0.5 if x >= 0 else 0
safe_reciprocal = lambda x :: 1.0 / x if x != 0 else float('inf')
safe_len = lambda obj :: len(obj) if hasattr(obj, '__len__') else 0

# Conditional validation
is_valid_score = lambda score :: True if 0 <= score <= 100 else False
is_adult_age = lambda age :: True if age >= 18 else False
```

**Struct Operations**:

```dana
struct Person:
    name: str
    age: int
    city: str
    email: str

# Struct transformation lambdas
get_name = lambda (person: Person) -> person.name
is_adult = lambda (person: Person) -> person.age >= 18
format_info = lambda (person: Person) -> f"{person.name} ({person.age}) from {person.city}"

# Conditional struct operations
get_display_name = lambda (person: Person) :: person.name if person.name else "Anonymous"
get_domain = lambda (person: Person) :: person.email.split("@")[1] if "@" in person.email else ""
get_age_group = lambda (person: Person) :: "adult" if person.age >= 18 else "minor"
```

## Integration with Other Dana Features

**Lambda with POET**:

```dana
@poet(domain="data_processing")
def process_data(data: list, transform):
    return [transform(item) for item in data]

# Usage with lambda
numbers = [1, 2, 3, 4, 5]
squares = process_data(numbers, lambda x :: x * x)
```

**Lambda with Agents**:

```dana
agent DataProcessor:
    """Agent for processing data with lambda transformations."""
    
    def process_with_lambda(self, data: list, transform):
        return [transform(item) for item in data]

# Usage
processor = DataProcessor()
result = processor.process_with_lambda([1, 2, 3], lambda x :: x * 2)
```

**Lambda in Workflows**:

```dana
@poet(domain="data_analysis")
def data_analysis_workflow = (
    (lambda data :: data.strip()) |
    (lambda clean :: clean.upper()) |
    (lambda upper :: f"ANALYZED: {upper}")
)
```

## Summary

Lambda expressions in Dana provide:

- **Concise syntax** for simple functions
- **Full type safety** with type hints
- **Struct receivers** for method-like behavior
- **Conditional expressions** for decision-making logic
- **Union type support** for handling multiple types
- **Pipeline integration** for data processing
- **Higher-order function compatibility**

They're perfect for:
- Simple transformations and calculations
- Conditional logic and decision-making
- Pipeline components
- Struct operations
- Type-safe data processing
- Quick function definitions

Lambda expressions make Dana code more expressive and functional while maintaining type safety and readability. 