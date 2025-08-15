# Struct Functions Primer

## TL;DR (1 minute read)

```dana
# Instead of this (floating functions):
struct Point: x: int, y: int

def translate_point(point: Point, dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def point_distance(point: Point) -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

# Do this (struct functions - Dana transforms automatically):
struct Point: x: int, y: int

def translate_point(point: Point, dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def point_distance(point: Point) -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

# Usage (Dana transforms this):
point = Point(x=3, y=4)
moved = point.translate_point(2, 1)      # Transforms to translate_point(point, 2, 1)
distance = point.point_distance()        # Transforms to point_distance(point)

# Or use receiver syntax (explicit methods):
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def (point: Point) distance_from_origin() -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

# Usage (direct method calls):
point = Point(x=3, y=4)
moved = point.translate(2, 1)            # Direct method call
distance = point.distance_from_origin()  # Direct method call
```

---

**What it is**: Two ways to operate on structs - struct functions (Dana's main pattern) and struct methods (receiver syntax). Both provide clean, type-safe ways to define operations that belong to specific struct types.

## Two Patterns

### 1. Struct Functions (Main Dana Pattern)

**Definition**: Functions that take structs as their first parameter
**Transformation**: Dana automatically transforms `obj.method()` to `method(obj)`
**Registry**: Functions are registered in the function registry for fast lookup

### 2. Struct Methods (Receiver Syntax)

**Definition**: Functions with explicit receiver syntax `def (receiver: Type)`
**Direct**: Methods are called directly on struct instances
**Registry**: Methods are registered in the method registry

## Struct Functions (Main Pattern)

### Key Syntax

**Function Definition**:
```dana
def function_name(struct_instance: StructType, param1: type, param2: type) -> return_type:
    # your code here
```

**Usage**:
```dana
# Dana transforms this automatically:
result = struct_instance.function_name(param1, param2)
# Into this:
result = function_name(struct_instance, param1, param2)
```

### Real-World Examples

**Geometry Library**:
```dana
struct Point: x: int, y: int
struct Circle: radius: float, center: Point

# Point operations
def translate_point(point: Point, dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def point_distance(point: Point) -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

def scale_point(point: Point, factor: float) -> Point:
    return Point(x=int(point.x * factor), y=int(point.y * factor))

# Circle operations
def circle_area(circle: Circle) -> float:
    return 3.14159 * circle.radius * circle.radius

def circle_perimeter(circle: Circle) -> float:
    return 2 * 3.14159 * circle.radius

# Usage (Dana transforms automatically)
point = Point(x=3, y=4)
circle = Circle(radius=5.0, center=Point(x=0, y=0))

moved = point.translate_point(2, 1)      # Point(x=5, y=5)
distance = point.point_distance()        # 5.0
scaled = point.scale_point(2.0)         # Point(x=6, y=8)
area = circle.circle_area()             # 78.53975
perimeter = circle.circle_perimeter()   # 31.4159
```

**Business Application**:
```dana
struct User: name: str, email: str, age: int
struct Product: name: str, price: float, category: str

# User operations
def validate_user(user: User) -> bool:
    return user.age >= 18 and "@" in user.email

def user_display_name(user: User) -> str:
    return f"{user.name} ({user.email})"

def is_user_adult(user: User) -> bool:
    return user.age >= 18

# Product operations
def apply_discount(product: Product, percent: float) -> float:
    return product.price * (1.0 - percent / 100.0)

def is_expensive_product(product: Product, threshold: float = 100.0) -> bool:
    return product.price > threshold

# Usage
user = User(name="Alice", email="alice@example.com", age=25)
product = Product(name="Laptop", price=999.99, category="Electronics")

is_valid = user.validate_user()                    # true
display = user.user_display_name()                 # "Alice (alice@example.com)"
is_adult = user.is_user_adult()                    # true
discounted = product.apply_discount(20.0)          # 799.992
expensive = product.is_expensive_product(500.0)    # true
```

## Struct Methods (Receiver Syntax)

### Key Syntax

**Method Definition**:
```dana
def (receiver: StructType) method_name(param1: type, param2: type) -> return_type:
    # your code here
```

**Union Methods**:
```dana
def (receiver: Type1 | Type2 | Type3) method_name(param1: type) -> return_type:
    # handle multiple types
```

### Real-World Examples

**Geometry with Methods**:
```dana
struct Point: x: int, y: int
struct Circle: radius: float, center: Point

# Point methods
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def (point: Point) distance_from_origin() -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

def (point: Point) scale(factor: float) -> Point:
    return Point(x=int(point.x * factor), y=int(point.y * factor))

# Circle methods
def (circle: Circle) area() -> float:
    return 3.14159 * circle.radius * circle.radius

def (circle: Circle) perimeter() -> float:
    return 2 * 3.14159 * circle.radius

# Union method (works with multiple types)
def (shape: Point | Circle) area() -> float:
    shape_type = shape._type.name
    if shape_type == "Point":
        return 0.0
    elif shape_type == "Circle":
        return 3.14159 * shape.radius * shape.radius

# Usage (direct method calls)
point = Point(x=3, y=4)
circle = Circle(radius=5.0, center=Point(x=0, y=0))

moved = point.translate(2, 1)            # Point(x=5, y=5)
distance = point.distance_from_origin()  # 5.0
scaled = point.scale(2.0)               # Point(x=6, y=8)
circle_area = circle.area()             # 78.53975
perimeter = circle.perimeter()          # 31.4159

# Union method works on both
point_area = point.area()               # 0.0
circle_area = circle.area()             # 78.53975
```

**Business Methods**:
```dana
struct User: name: str, email: str, age: int
struct Product: name: str, price: float, category: str

# User methods
def (user: User) is_adult() -> bool:
    return user.age >= 18

def (user: User) display_name() -> str:
    return f"{user.name} ({user.email})"

def (user: User) validate() -> bool:
    return user.age >= 18 and "@" in user.email

# Product methods
def (product: Product) apply_discount(percent: float = 10.0) -> float:
    return product.price * (1.0 - percent / 100.0)

def (product: Product) is_expensive(threshold: float = 100.0) -> bool:
    return product.price > threshold

# Union method
def (entity: User | Product) to_json() -> str:
    entity_type = entity._type.name
    if entity_type == "User":
        return f'{{"type": "user", "name": "{entity.name}", "email": "{entity.email}"}}'
    elif entity_type == "Product":
        return f'{{"type": "product", "name": "{entity.name}", "price": {entity.price}}}'

# Usage
user = User(name="Alice", email="alice@example.com", age=25)
product = Product(name="Laptop", price=999.99, category="Electronics")

is_adult = user.is_adult()                    # true
display = user.display_name()                 # "Alice (alice@example.com)"
is_valid = user.validate()                    # true
discounted = product.apply_discount(20.0)     # 799.992
expensive = product.is_expensive(500.0)       # true

# Union method
user_json = user.to_json()                    # {"type": "user", "name": "Alice", ...}
product_json = product.to_json()              # {"type": "product", "name": "Laptop", ...}
```

## When to Use Which Pattern

### Use Struct Functions When:
- **Working with existing Dana codebase** (most Dana code uses this pattern)
- **Simple operations** that don't need complex method resolution
- **Performance matters** (slightly faster lookup)
- **Consistency** with Dana's main pattern

### Use Struct Methods When:
- **Union types** (one method handles multiple struct types)
- **Object-oriented design** (methods feel more natural)
- **Complex method resolution** needed
- **Explicit receiver syntax** preferred

### Both Patterns Work Together:
```dana
struct Point: x: int, y: int

# Struct function (main Dana pattern)
def translate_point(point: Point, dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

# Struct method (receiver syntax)
def (point: Point) scale(factor: float) -> Point:
    return Point(x=int(point.x * factor), y=int(point.y * factor))

# Use both in the same codebase
point = Point(x=3, y=4)
moved = point.translate_point(2, 1)  # Struct function
scaled = point.scale(2.0)           # Struct method
```

## Error Handling

**Method/Function Not Found**:
```dana
struct Point: x: int, y: int
point = Point(x=1, y=2)

# ❌ Call non-existent method/function
try:
    result = point.nonexistent_method()
except AttributeError as e:
    log(f"Error: {e}")
    # Error: Object Point(x=1, y=2) has no method 'nonexistent_method'
```

**Type Validation**:
```dana
def (point: Point) validate() -> bool:
    return point.x >= 0 and point.y >= 0

point = Point(x=-1, y=2)
is_valid = point.validate()  # false
```

## Best Practices

### 1. Choose Clear Names
```dana
# ✅ Good - descriptive names
def translate_point(point: Point, dx: int, dy: int) -> Point:
def (point: Point) distance_from_origin() -> float:

# ❌ Avoid - vague names
def move(point: Point, x: int, y: int) -> Point:
def (point: Point) calc() -> float:
```

### 2. Use Union Types for Related Operations
```dana
# One method handles multiple shapes
def (shape: Circle | Rectangle) area() -> float:
    shape_type = shape._type.name
    if shape_type == "Circle":
        return 3.14159 * shape.radius * shape.radius
    elif shape_type == "Rectangle":
        return shape.width * shape.height
```

### 3. Default Parameters Make Life Easier
```dana
def (point: Point) shift(dx: int = 0, dy: int = 0) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

# No arguments needed
same_point = point.shift()  # No movement
```

### 4. Keep Operations Immutable
```dana
# ✅ Good - returns new instance
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

# ❌ Avoid - modifies the original
def (point: Point) move(dx: int, dy: int):
    point.x += dx  # Changes the original point
    point.y += dy
```

### 5. Be Consistent in Your Codebase
```dana
# Choose one pattern and stick with it for similar operations
# Either all struct functions:
def translate_point(point: Point, dx: int, dy: int) -> Point:
def scale_point(point: Point, factor: float) -> Point:

# Or all struct methods:
def (point: Point) translate(dx: int, dy: int) -> Point:
def (point: Point) scale(factor: float) -> Point:
```

## Summary

Struct functions and methods provide:
- **Two patterns**: Choose what fits your style
- **Type safety**: Better than Python's duck typing
- **Clean syntax**: Dot notation for both patterns
- **Fast lookup**: Direct resolution
- **Union support**: Handle multiple types in one method

**Struct Functions** (main Dana pattern):
- Automatic transformation from `obj.method()` to `method(obj)`
- Registry-based lookup
- Most Dana code uses this pattern

**Struct Methods** (receiver syntax):
- Explicit receiver syntax
- Direct method calls
- Great for union types and OO design

Perfect for: Python developers, object-oriented design, and type-safe operations on structs.

**Next**: See `struct_delegation.md` for advanced composition patterns with delegation.
