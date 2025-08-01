# Struct Methods Primer

## TL;DR (1 minute read)

```dana
# Instead of this (floating functions):
struct Point: x: int, y: int

def translate_point(point: Point, dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def point_distance(point: Point) -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

# Do this (methods attached to data):
struct Point: x: int, y: int

def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def (point: Point) distance_from_origin() -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

# Union methods (one method, multiple types):
def (shape: Point | Circle) area() -> float:
    return 0.0 if shape._type.name == "Point" else 3.14159 * shape.radius ** 2

# Usage (just like Python):
point = Point(x=3, y=4)
moved = point.translate(2, 1)      # Point(x=5, y=5)
distance = point.distance_from_origin()  # 5.0
area = point.area()                # 0.0
```

---

**What it is**: A clean, Go-inspired way to define methods that belong to specific struct types. Methods are attached to data with dot notation, just like Python classes.

## Key Syntax

**Basic Method**:
```dana
def (receiver: Type) method_name(parameters) -> return_type:
    # your code here
```

**Union Method**:
```dana
def (receiver: Type1 | Type2 | Type3) method_name(parameters) -> return_type:
    # check the type and handle each case
```

**Method with Defaults**:
```dana
def (receiver: Type) method_name(param1: type, param2: type = default) -> return_type:
    # your code here
```

## Handling Multiple Types

**Type-Safe Union Methods**:
```dana
def (shape: Point | Circle | Rectangle) area() -> float:
    shape_type = shape._type.name
    if shape_type == "Point":
        return 0.0
    elif shape_type == "Circle":
        return 3.14159 * shape.radius * shape.radius
    elif shape_type == "Rectangle":
        return shape.width * shape.height
    else:
        return 0.0  # Compile-time guarantee this won't happen
```

## Real-World Examples

### Geometry Library
```dana
struct Point: x: int, y: int
struct Circle: radius: float, center: Point
struct Rectangle: width: float, height: float

# Point-specific methods
def (point: Point) distance_from_origin() -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

def (point: Point) scale(factor: float) -> Point:
    return Point(x=int(point.x * factor), y=int(point.y * factor))

# Works with any shape
def (shape: Point | Circle | Rectangle) area() -> float:
    shape_type = shape._type.name
    if shape_type == "Point":
        return 0.0
    elif shape_type == "Circle":
        return 3.14159 * shape.radius * shape.radius
    elif shape_type == "Rectangle":
        return shape.width * shape.height

# Usage
point = Point(x=3, y=4)
circle = Circle(radius=5.0, center=Point(x=0, y=0))

log(f"Distance: {point.distance_from_origin()}")  # 5.0
log(f"Scaled: {point.scale(2.0)}")               # Point(x=6, y=8)
log(f"Areas: {point.area()}, {circle.area()}")   # 0.0, 78.53975
```

### Business App
```dana
struct User: name: str, email: str, age: int
struct Product: name: str, price: float, category: str

# User methods
def (user: User) is_adult() -> bool:
    return user.age >= 18

def (user: User) display_name() -> str:
    return f"{user.name} ({user.email})"

# Product methods
def (product: Product) is_expensive() -> bool:
    return product.price > 100.0

def (product: Product) apply_discount(percent: float = 10.0) -> float:
    return product.price * (1.0 - percent / 100.0)

# Works with both users and products
def (entity: User | Product) to_json() -> str:
    entity_type = entity._type.name
    if entity_type == "User":
        return f'{{"type": "user", "name": "{entity.name}", "email": "{entity.email}"}}'
    elif entity_type == "Product":
        return f'{{"type": "product", "name": "{entity.name}", "price": {entity.price}}}'

# Usage
user = User(name="Alice", email="alice@example.com", age=25)
product = Product(name="Laptop", price=999.99, category="Electronics")

log(f"Adult: {user.is_adult()}")                    # true
log(f"Expensive: {product.is_expensive()}")         # true
log(f"Discounted: {product.apply_discount(20.0)}")  # 799.992
log(f"JSON: {user.to_json()}")                      # {"type": "user", "name": "Alice", ...}
```

## Error Handling

**Method Doesn't Exist**:
```dana
point = Point(x=1, y=2)
result = point.nonexistent_method()  
# Error: Object Point(x=1, y=2) has no method 'nonexistent_method'
```

**Validation Methods**:
```dana
def (point: Point) validate() -> bool:
    return point.x >= 0 and point.y >= 0

point = Point(x=-1, y=2)
is_valid = point.validate()  # false
```

## Best Practices

### 1. Pick Clear Names
```dana
# ✅ Good - tells you exactly what it does
def (point: Point) translate_by_vector(dx: int, dy: int) -> Point:

# ❌ Avoid - too vague
def (point: Point) move(x: int, y: int) -> Point:
```

### 2. Use Union Types for Related Operations
```dana
# One method handles multiple shapes
def (shape: Circle | Rectangle) perimeter() -> float:
    shape_type = shape._type.name
    if shape_type == "Circle":
        return 2 * 3.14159 * shape.radius
    elif shape_type == "Rectangle":
        return 2 * (shape.width + shape.height)
```

### 3. Default Parameters Make Life Easier
```dana
def (point: Point) shift(dx: int = 0, dy: int = 0) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

# No arguments needed
same_point = point.shift()  # No movement
```

### 4. Keep Things Immutable
```dana
# ✅ Good - returns new instance
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

# ❌ Avoid - modifies the original
def (point: Point) move(dx: int, dy: int):
    point.x += dx  # Changes the original point
    point.y += dy
```

## Summary

Struct methods provide:
- **Familiar dot notation**: `point.translate(2, 1)` just like Python
- **Methods belong to data**: No more floating functions
- **Type safety**: Better than Python's duck typing
- **Union types**: Handle multiple types in one method
- **Fast lookup**: Direct method resolution

Perfect for: Python developers, object-oriented design, and type-safe method calls. 