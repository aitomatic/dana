# Structs Primer

## TL;DR (1 minute read)

```dana
# Instead of this (loose dictionaries):
user_data = {"name": "Alice", "age": 30, "email": "alice@example.com"}
user_name = user_data["name"]
user_data["age"] = 31

# Do this (structured data):
struct User: name: str, age: int, email: str

user = User(name="Alice", age=30, email="alice@example.com")
user_name = user.name
user.age = 31
```

---

**What it is**: Structured data containers with type safety, validation, and clean dot notation access. Dana's way of organizing related data into cohesive units.

## Key Syntax

**Struct Definition**:
```dana
struct StructName: field1: type1, field2: type2, field3: type3
```

**Instantiation**:
```dana
instance = StructName(field1=value1, field2=value2, field3=value3)
```

**Field Access**:
```dana
value = instance.field_name
```

**Field Assignment**:
```dana
instance.field_name = new_value
```

## Real-World Examples

### User Management
```dana
struct User: name: str, age: int, email: str, is_active: bool

# Create users
alice = User(name="Alice", age=30, email="alice@example.com", is_active=true)
bob = User(name="Bob", age=25, email="bob@example.com", is_active=false)

# Access fields
log(f"User: {alice.name} ({alice.email})")
log(f"Active: {alice.is_active}")

# Update fields
alice.age = 31
bob.is_active = true
```

### Configuration Objects
```dana
struct DatabaseConfig: 
    host: str, 
    port: int, 
    username: str, 
    password: str, 
    ssl_enabled: bool

config = DatabaseConfig(
    host="localhost",
    port=5432,
    username="admin",
    password="secret123",
    ssl_enabled=true
)

log(f"Connecting to {config.host}:{config.port}")
```

### Geometry
```dana
struct Point: x: int, y: int
struct Rectangle: width: float, height: float, color: str

point = Point(x=10, y=20)
rectangle = Rectangle(width=100.5, height=50.0, color="blue")

log(f"Point at ({point.x}, {point.y})")
log(f"Rectangle: {rectangle.width}x{rectangle.height} {rectangle.color}")
```

## Type Safety and Validation

**Automatic Type Validation**:
```dana
struct Product: name: str, price: float, in_stock: bool

# ✅ Valid
product = Product(name="Widget", price=19.99, in_stock=true)

# ❌ Type errors (caught at runtime)
product = Product(name=123, price="expensive", in_stock="yes")
# Error: Field 'name': expected str, got int (123)
# Error: Field 'price': expected float, got str ("expensive")
```

**Type Coercion**:
```dana
struct Measurement: value: float, unit: str

# ✅ Int automatically coerced to float
measurement = Measurement(value=42, unit="meters")
log(measurement.value)  # 42.0 (float)
```

## Struct Composition

**Nested Structs**:
```dana
struct Address: street: str, city: str, zip_code: str
struct Person: name: str, age: int, address: Address

# Create nested structure
address = Address(street="123 Main St", city="Anytown", zip_code="12345")
person = Person(name="John", age=30, address=address)

# Access nested fields
log(f"{person.name} lives at {person.address.street}")
log(f"City: {person.address.city}")
```

**Lists and Dictionaries**:
```dana
struct ShoppingCart: 
    items: list, 
    metadata: dict, 
    customer_id: str

cart = ShoppingCart(
    items=["apple", "banana", "orange"],
    metadata={"created_at": "2024-01-15", "store": "grocery"},
    customer_id="cust_123"
)

log(f"Cart has {len(cart.items)} items")
log(f"Store: {cart.metadata['store']}")
```

## Field Defaults and Optional Values

**Default Values**:
```dana
struct Settings: 
    theme: str = "light",
    notifications: bool = true,
    language: str = "en"

# Use defaults
settings = Settings()
log(settings.theme)  # "light"

# Override defaults
dark_settings = Settings(theme="dark", notifications=false)
log(dark_settings.theme)  # "dark"
log(dark_settings.language)  # "en" (default)
```

## Error Handling

**Missing Fields**:
```dana
struct User: name: str, age: int

user = User(name="Alice", age=30)

# ❌ Access non-existent field
try:
    email = user.email
except AttributeError as e:
    log(f"Error: {e}")
    # Error: Struct 'User' has no field 'email'. Available fields: ['name', 'age']
```

**Invalid Assignment**:
```dana
struct Product: name: str, price: float

product = Product(name="Widget", price=19.99)

# ❌ Assign wrong type
try:
    product.price = "expensive"
except TypeError as e:
    log(f"Error: {e}")
    # Error: Field assignment failed for 'Product.price': expected float, got str
```

## Best Practices

### 1. Use Descriptive Names
```dana
# ✅ Good
struct UserProfile: name: str, email: str, created_at: str

# ❌ Avoid
struct Data: a: str, b: str, c: str
```

### 2. Group Related Fields
```dana
# ✅ Logical grouping
struct Order: 
    order_id: str,
    customer_name: str,
    items: list,
    total_amount: float,
    order_date: str

# ❌ Scattered fields
struct Order: 
    order_id: str,
    random_field: int,
    customer_name: str,
    unrelated_data: dict,
    items: list
```

### 3. Use Appropriate Types
```dana
# ✅ Specific types
struct Product: 
    name: str,
    price: float,
    in_stock: bool,
    categories: list

# ❌ Too generic
struct Product: 
    name: any,
    price: any,
    in_stock: any,
    categories: any
```

### 4. Keep Structs Focused
```dana
# ✅ Single responsibility
struct User: name: str, email: str, age: int
struct UserPreferences: theme: str, notifications: bool
struct UserAddress: street: str, city: str, zip_code: str

# ❌ Too many responsibilities
struct User: 
    name: str, 
    email: str, 
    age: int,
    theme: str,
    notifications: bool,
    street: str,
    city: str,
    zip_code: str
```

## Summary

Structs provide:
- **Type safety**: Automatic validation and coercion
- **Clean syntax**: Dot notation for field access
- **Structured data**: Organized, related information
- **Composition**: Build complex data structures
- **Validation**: Runtime error checking

Perfect for: Data modeling, configuration objects, API responses, and any structured data needs.

**Next**: See `struct_functions.md` for how to operate on structs with functions and methods.
