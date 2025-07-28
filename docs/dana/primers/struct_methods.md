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

**What it is**: A clean, Go-inspired way to define methods that belong to specific struct types. Think of it as giving your structs superpowers - you can call methods directly on them with dot notation, and they work with multiple types at once.

## Why Should You Care?

If you're coming from Python, you're probably used to classes with methods:

```python
# Python way
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def translate(self, dx, dy):
        return Point(self.x + dx, self.y + dy)
    
    def distance_from_origin(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

# Usage
point = Point(3, 4)
moved = point.translate(2, 1)  # Nice and clean
```

In Dana, we have structs (like dataclasses) instead of classes. Struct methods give you the same intuitive experience:

```dana
# Dana way - structs with methods
struct Point:
    x: int
    y: int

# Methods attached to the data - just like Python!
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def (point: Point) distance_from_origin() -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

# Usage - familiar Python-style dot notation
point = Point(x=3, y=4)
moved = point.translate(2, 1)  # Just like Python!
```

**Struct methods give you the Python experience in Dana:**

- **Familiar dot notation**: `point.translate(2, 1)` just like Python
- **Methods belong to data**: No more floating functions
- **Type safety**: Better than Python's duck typing
- **Union types**: Like Python's `Union[Point, Circle]` but built-in

## The Big Picture

```dana
# Define your structs (like Python dataclasses)
struct Point:
    x: int
    y: int

struct Circle:
    radius: float
    center: Point

# Give them methods - just like Python classes!
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def (point: Point) distance_from_origin() -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

# Union methods - like Python's Union types but better
def (shape: Point | Circle) area() -> float:
    shape_type = shape._type.name
    if shape_type == "Point":
        return 0.0
    elif shape_type == "Circle":
        return 3.14159 * shape.radius * shape.radius

# Use them naturally - just like Python!
point = Point(x=3, y=4)
circle = Circle(radius=5.0, center=Point(x=0, y=0))

moved_point = point.translate(2, 1)  # Point(x=5, y=5) - feels right!
point_area = point.area()            # 0.0
circle_area = circle.area()          # 78.53975
```

## Why You'll Love This

- **No more guessing**: You know exactly which types a method works with
- **Catch bugs early**: Method existence is checked when you write the code, not when you run it
- **Work with multiple types**: One method can handle `Point | Circle | Rectangle` 
- **Lightning fast**: Direct lookup, no searching through scopes
- **Familiar syntax**: If you know Python, you'll feel right at home

## How to Write Methods

### Basic Method (One Type) - Like Python Instance Methods
```dana
def (receiver: Type) method_name(parameters) -> return_type:
    # your code here
```

### Union Method (Multiple Types) - Like Python's Union but Better
```dana
def (receiver: Type1 | Type2 | Type3) method_name(parameters) -> return_type:
    # check the type and handle each case
```

### Method with Defaults - Just Like Python Default Arguments
```dana
def (receiver: Type) method_name(param1: type, param2: type = default) -> return_type:
    # your code here
```

## Handling Multiple Types (The Cool Part)

In Python, you might do this:
```python
def area(shape):
    if isinstance(shape, Point):
        return 0.0
    elif isinstance(shape, Circle):
        return 3.14159 * shape.radius * shape.radius
    else:
        raise TypeError(f"Unknown shape type: {type(shape)}")
```

In Dana, it's cleaner and type-safe:
```dana
def (shape: Point | Circle | Rectangle) area() -> float:
    shape_type = shape._type.name  # This tells you the actual type
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

### Building a Geometry Library (Python-Style)
```dana
struct Point:
    x: int
    y: int

struct Circle:
    radius: float
    center: Point

struct Rectangle:
    width: float
    height: float

# Point-specific methods - like Python instance methods
def (point: Point) distance_from_origin() -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

def (point: Point) scale(factor: float) -> Point:
    return Point(x=int(point.x * factor), y=int(point.y * factor))

# Works with any shape - like Python's Union but built-in
def (shape: Point | Circle | Rectangle) area() -> float:
    shape_type = shape._type.name
    if shape_type == "Point":
        return 0.0
    elif shape_type == "Circle":
        return 3.14159 * shape.radius * shape.radius
    elif shape_type == "Rectangle":
        return shape.width * shape.height

# Try it out - feels just like Python!
point = Point(x=3, y=4)
circle = Circle(radius=5.0, center=Point(x=0, y=0))

log(f"Distance: {point.distance_from_origin()}")  # 5.0
log(f"Scaled: {point.scale(2.0)}")               # Point(x=6, y=8)
log(f"Areas: {point.area()}, {circle.area()}")   # 0.0, 78.53975
```

### Building a Business App (Python-Style)
```dana
struct User:
    name: str
    email: str
    age: int

struct Product:
    name: str
    price: float
    category: str

# User methods - like Python class methods
def (user: User) is_adult() -> bool:
    return user.age >= 18

def (user: User) display_name() -> str:
    return f"{user.name} ({user.email})"

# Product methods
def (product: Product) is_expensive() -> bool:
    return product.price > 100.0

def (product: Product) apply_discount(percent: float = 10.0) -> float:
    return product.price * (1.0 - percent / 100.0)

# Works with both users and products - like Python's Union
def (entity: User | Product) to_json() -> str:
    entity_type = entity._type.name
    if entity_type == "User":
        return f'{{"type": "user", "name": "{entity.name}", "email": "{entity.email}"}}'
    elif entity_type == "Product":
        return f'{{"type": "product", "name": "{entity.name}", "price": {entity.price}}}'

# Usage - familiar Python-style dot notation
user = User(name="Alice", email="alice@example.com", age=25)
product = Product(name="Laptop", price=999.99, category="Electronics")

log(f"Adult: {user.is_adult()}")                    # true
log(f"Expensive: {product.is_expensive()}")         # true
log(f"Discounted: {product.apply_discount(20.0)}")  # 799.992
log(f"JSON: {user.to_json()}")                      # {"type": "user", "name": "Alice", ...}
```

## What Happens When Things Go Wrong

### Method Doesn't Exist - Like Python's AttributeError
```dana
point = Point(x=1, y=2)
result = point.nonexistent_method()  
# Error: Object Point(x=1, y=2) has no method 'nonexistent_method'
# (Similar to Python's AttributeError)
```

### Validation Methods - Like Python Property Decorators
```dana
def (point: Point) validate() -> bool:
    return point.x >= 0 and point.y >= 0

point = Point(x=-1, y=2)
is_valid = point.validate()  # false
```

## Pro Tips

### 1. Pick Clear Names (Python Style)
```dana
# Good - tells you exactly what it does
def (point: Point) translate_by_vector(dx: int, dy: int) -> Point:

# Meh - too vague
def (point: Point) move(x: int, y: int) -> Point:
```

### 2. Use Union Types for Related Operations (Like Python's Union)
```dana
# One method handles multiple shapes
def (shape: Circle | Rectangle) perimeter() -> float:
    shape_type = shape._type.name
    if shape_type == "Circle":
        return 2 * 3.14159 * shape.radius
    elif shape_type == "Rectangle":
        return 2 * (shape.width + shape.height)
```

### 3. Default Parameters Make Life Easier (Just Like Python)
```dana
def (point: Point) shift(dx: int = 0, dy: int = 0) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

# No arguments needed - just like Python!
same_point = point.shift()  # No movement
```

### 4. Keep Things Immutable (Python Best Practice)
```dana
# Good - returns new instance (like Python's str methods)
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

# Avoid - modifies the original (like Python's list.sort())
def (point: Point) move(dx: int, dy: int):
    point.x += dx  # Changes the original point
    point.y += dy
```

## Performance Wins

- **Instant lookup**: No more searching through scopes
- **Early error detection**: Catch missing methods when you write code
- **No runtime magic**: Eliminates the `obj.method()` → `method(obj)` transformation

**Bottom line**: Struct methods give you the familiar Python experience in Dana - clean, intuitive method calls with better type safety and performance. It's like having Python's object-oriented feel without the complexity of classes. 