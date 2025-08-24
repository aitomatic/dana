# Lambda Expressions Primer

## TL;DR (1 minute read)

```dana
# Basic syntax: lambda params :: expression
double = lambda x :: x * 2
add = lambda x, y :: x + y
typed_add = lambda x: int, y: int :: x + y

# Struct receivers (method-like behavior)
translate_point = lambda (point: Point) dx, dy :: Point(x=point.x + dx, y=point.y + dy)

# Conditional expressions (ternary operator)
get_first = lambda lst :: lst[0] if len(lst) > 0 else None
max_func = lambda a, b :: a if a > b else b
classify = lambda x :: "positive" if x > 0 else ("zero" if x == 0 else "negative")

# Pipeline integration
pipeline = (lambda x :: x * 2) | (lambda y :: y + 1) | (lambda z :: z * z)
result = pipeline(5)  # 5 → 10 → 11 → 121

# Union types
area_calc = lambda (shape: Point | Circle | Rectangle) :: {
    return 0.0 if shape._type.name == "Point"
    else 3.14159 * shape.radius ** 2 if shape._type.name == "Circle"
    else shape.width * shape.height
}
```

---

**What it is**: Lambda expressions in Dana are concise, anonymous functions with full type safety, struct receivers, conditional expressions, and pipeline integration.

## Key Syntax

**Dana vs Python**:
```python
# Python: lambda x: x * 2
```
```dana
# Dana: lambda x :: x * 2  (uses :: instead of :)
```

**Syntax Patterns**:
```dana
# Basic: lambda params :: expression
square = lambda x :: x * x

# Type hints: lambda x: int, y: float :: expression
typed_add = lambda x: int, y: float :: x + y

# Struct receiver: lambda (receiver: Type) params :: expression
translate = lambda (point: Point) dx, dy :: Point(x=point.x + dx, y=point.y + dy)

# Conditional: lambda params :: expr if condition else expr
safe_divide = lambda a, b :: a / b if b != 0 else float('inf')

# Complex body: lambda params :: { statements }
complex_calc = lambda x, y :: {
    temp = x * y
    return temp + x + y
}
```

## Conditional Expressions

Lambda expressions support ternary operators for concise decision-making:

```dana
# Basic conditionals
get_first = lambda lst :: lst[0] if len(lst) > 0 else None
max_func = lambda a, b :: a if a > b else b

# Nested conditionals (right-associative)
classify = lambda x :: "positive" if x > 0 else ("zero" if x == 0 else "negative")
grade_calc = lambda score :: "A" if score >= 90 else ("B" if score >= 80 else "F")

# Safe operations
safe_divide = lambda a, b :: a / b if b != 0 else float('inf')
safe_sqrt = lambda x :: x ** 0.5 if x >= 0 else 0
safe_reciprocal = lambda x :: 1.0 / x if x != 0 else float('inf')

# String operations
string_ops = lambda s :: s.strip().lower() if s else ""
format_name = lambda name :: name.title() if name else "Unknown"
```

## Struct Receivers

Lambda expressions can have struct receivers for method-like behavior:

```dana
struct Point:
    x: float
    y: float

# Lambda with receiver
translate_point = lambda (point: Point) dx, dy :: Point(x=point.x + dx, y=point.y + dy)
scale_point = lambda (point: Point) factor :: Point(x=point.x * factor, y=point.y * factor)

# Usage
point = Point(x=3, y=4)
moved = translate_point(point, 2, 1)    # Point(x=5, y=5)
scaled = scale_point(point, 2.0)        # Point(x=6, y=8)

# Conditional struct operations
get_display_name = lambda (person: Person) :: person.name if person.name else "Anonymous"
get_domain = lambda (person: Person) :: person.email.split("@")[1] if "@" in person.email else ""
```

## Union Types

Lambda expressions handle multiple types using union receivers:

```dana
# Lambda with union receiver
calculate_area = lambda (shape: Point | Circle | Rectangle) :: {
    return 0.0 if shape._type.name == "Point"
    else 3.14159 * shape.radius ** 2 if shape._type.name == "Circle"
    else shape.width * shape.height
}

# Usage
point = Point(x=3, y=4)
circle = Circle(radius=5, center=Point(x=0, y=0))
point_area = calculate_area(point)      # 0.0
circle_area = calculate_area(circle)    # 78.54...
```

## Pipeline Integration

Lambda expressions integrate seamlessly with Dana's pipeline syntax:

```dana
# Simple pipeline
number_pipeline = (lambda x :: x * 2) | (lambda y :: y + 1) | (lambda z :: z * z)
result = number_pipeline(5)  # 5 → 10 → 11 → 121

# Text processing pipeline
text_pipeline = (lambda x :: x.strip()) | (lambda x :: x.upper()) | (lambda x :: f"PROCESSED: {x}")
result = text_pipeline("  hello world  ")  # "PROCESSED: HELLO WORLD"

# Conditional filtering in pipeline
filter_pipeline = (lambda x :: x if x > 0 else None) | (lambda x :: x * 2 if x else 0)
```

## Common Patterns

**Data Transformation**:
```dana
# Simple transformations
to_uppercase = lambda s :: s.upper()
square = lambda x :: x * x
absolute = lambda x :: x if x >= 0 else -x

# Conditional transformations
get_first = lambda lst :: lst[0] if len(lst) > 0 else None
get_last = lambda lst :: lst[-1] if len(lst) > 0 else None
```

**Validation and Safe Operations**:
```dana
# Validation
is_positive = lambda x :: x > 0
is_even = lambda x :: x % 2 == 0
is_valid_score = lambda score :: True if 0 <= score <= 100 else False

# Safe operations
safe_divide = lambda x, y :: x / y if y != 0 else float('inf')
safe_sqrt = lambda x :: x ** 0.5 if x >= 0 else 0
safe_reciprocal = lambda x :: 1.0 / x if x != 0 else float('inf')
```

**Struct Operations**:
```dana
struct Person:
    name: str
    age: int
    email: str

# Struct transformations
get_name = lambda (person: Person) :: person.name
is_adult = lambda (person: Person) :: person.age >= 18
format_info = lambda (person: Person) :: f"{person.name} ({person.age})"

# Conditional struct operations
get_display_name = lambda (person: Person) :: person.name if person.name else "Anonymous"
get_domain = lambda (person: Person) :: person.email.split("@")[1] if "@" in person.email else ""
```

## Best Practices

**When to Use**:
```dana
# ✅ Good: Simple transformations
double = lambda x :: x * 2

# ✅ Good: Pipeline components
pipeline = (lambda x :: x.strip()) | (lambda x :: x.upper())

# ✅ Good: Struct receivers
translate = lambda (point: Point) dx, dy :: Point(x=point.x + dx, y=point.y + dy)

# ✅ Good: Conditional logic
safe_divide = lambda a, b :: a / b if b != 0 else float('inf')

# ❌ Avoid: Complex logic (use regular functions instead)
# complex_lambda = lambda x, y, z :: { # 20+ lines of logic }
```

**Naming Conventions**:
```dana
# ✅ Good: Descriptive names
double_number = lambda x :: x * 2
calculate_distance = lambda x1, y1, x2, y2 :: ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

# ❌ Avoid: Generic names
f = lambda x :: x * 2
func = lambda a, b :: a + b
```

## Summary

Lambda expressions in Dana provide:
- **Concise syntax** with `::` separator
- **Full type safety** with type hints
- **Struct receivers** for method-like behavior
- **Conditional expressions** for decision-making
- **Union type support** for multiple types
- **Pipeline integration** for data processing

Perfect for: simple transformations, conditional logic, pipeline components, struct operations, and type-safe data processing. 