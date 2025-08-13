# Struct Delegation Primer

## TL;DR (1 minute read)

```dana
# Instead of this (manual field access):
struct EmbeddedStruct: data: str, value: int
struct MainStruct: _embedded: EmbeddedStruct = EmbeddedStruct()

comp = MainStruct()
data = comp._embedded.data
value = comp._embedded.value
result = comp._embedded.process()

# Do this (automatic delegation):
struct EmbeddedStruct: data: str, value: int
struct MainStruct: _embedded: EmbeddedStruct = EmbeddedStruct()

comp = MainStruct()
data = comp.data        # Delegates to comp._embedded.data
value = comp.value      # Delegates to comp._embedded.value
result = comp.process() # Delegates to comp._embedded.process()

# Explicit access still works:
explicit_data = comp._embedded.data
```

---

**What it is**: Automatic field and method access through underscore-prefixed fields. When you access a field or method that doesn't exist on a struct, Dana automatically checks delegatable fields (those starting with `_`) and forwards the access to the embedded struct.

## Key Concepts

### Delegation Convention
- **Underscore prefix**: Fields starting with `_` are delegatable
- **Declaration order**: First declared delegatable field wins conflicts
- **Automatic forwarding**: Access is automatically forwarded to embedded structs
- **Explicit access**: Direct access to `_field.property` still works

### Delegation Types
- **Field delegation**: `comp.data` → `comp._embedded.data`
- **Method delegation**: `comp.process()` → `comp._embedded.process()`
- **Assignment delegation**: `comp.data = "new"` → `comp._embedded.data = "new"`

## Real-World Examples

### API Wrapper Pattern
```dana
struct APIClient: 
    base_url: str, 
    api_key: str

def (client: APIClient) get_user(user_id: str) -> dict:
    return {"id": user_id, "name": "John Doe"}

def (client: APIClient) create_user(user_data: dict) -> dict:
    return {"id": "new_123", "name": user_data["name"]}

struct UserService: 
    _api_client: APIClient = APIClient(base_url="https://api.example.com", api_key="secret")

# Usage - delegation makes it feel like UserService has these methods
service = UserService()
user = service.get_user("123")        # Delegates to service._api_client.get_user("123")
new_user = service.create_user({"name": "Alice"})  # Delegates to service._api_client.create_user(...)
```

### Configuration Composition
```dana
struct DatabaseConfig: 
    host: str, 
    port: int, 
    username: str

struct LoggingConfig: 
    level: str, 
    file_path: str

struct AppConfig: 
    _database: DatabaseConfig = DatabaseConfig(host="localhost", port=5432, username="admin")
    _logging: LoggingConfig = LoggingConfig(level="info", file_path="/var/log/app.log")
    app_name: str = "MyApp"

# Usage - access database and logging config directly
config = AppConfig()
db_host = config.host        # Delegates to config._database.host
log_level = config.level     # Delegates to config._logging.level
app_name = config.app_name   # Direct access (no delegation)
```

### Business Logic Composition
```dana
struct UserValidator: 
    min_age: int = 18

def (validator: UserValidator) validate_user(user: any) -> bool:
    return user.age >= validator.min_age

struct UserNotifier: 
    email_enabled: bool = true

def (notifier: UserNotifier) send_welcome_email(user: any) -> str:
    return f"Welcome {user.name}!" if notifier.email_enabled else "Email disabled"

struct UserService: 
    _validator: UserValidator = UserValidator(min_age=21)
    _notifier: UserNotifier = UserNotifier(email_enabled=true)

# Usage - service appears to have validation and notification methods
service = UserService()
is_valid = service.validate_user({"name": "Alice", "age": 25})  # Delegates to _validator
welcome = service.send_welcome_email({"name": "Alice"})         # Delegates to _notifier
```

## Conflict Resolution

### Declaration Order Priority
```dana
struct FirstStruct: shared_field: str = "from_first", unique_field: str = "first_only"
struct SecondStruct: shared_field: str = "from_second", unique_field: str = "second_only"

struct ComposedStruct: 
    _first: FirstStruct = FirstStruct()   # Declared first
    _second: SecondStruct = SecondStruct() # Declared second

comp = ComposedStruct()

# First declared field wins conflicts
shared_value = comp.shared_field  # "from_first" (from _first)
first_unique = comp.unique_field  # "first_only" (from _first)

# Access specific field explicitly
second_shared = comp._second.shared_field  # "from_second"
second_unique = comp._second.unique_field  # "second_only"
```

### Multiple Delegatable Fields
```dana
struct Logger: level: str = "info"
struct Metrics: enabled: bool = true
struct Cache: ttl: int = 3600

struct Service: 
    _logger: Logger = Logger(level="debug")
    _metrics: Metrics = Metrics(enabled=false)
    _cache: Cache = Cache(ttl=1800)
    service_name: str = "MyService"

service = Service()

# Each delegatable field provides its own properties
log_level = service.level      # "debug" (from _logger)
metrics_on = service.enabled   # false (from _metrics)
cache_time = service.ttl       # 1800 (from _cache)
name = service.service_name    # "MyService" (direct access)
```

## Field vs Method Delegation

### Field Delegation
```dana
struct DataStore: 
    data: dict = {"key": "value", "count": 42}

struct Wrapper: 
    _store: DataStore = DataStore()

wrapper = Wrapper()

# Field access delegation
value = wrapper.data["key"]    # Delegates to wrapper._store.data["key"]
count = wrapper.data["count"]  # Delegates to wrapper._store.data["count"]

# Field assignment delegation
wrapper.data["new_key"] = "new_value"  # Delegates to wrapper._store.data["new_key"] = "new_value"
```

### Method Delegation
```dana
struct Calculator: 
    precision: int = 2

def (calc: Calculator) add(a: float, b: float) -> float:
    return round(a + b, calc.precision)

def (calc: Calculator) multiply(a: float, b: float) -> float:
    return round(a * b, calc.precision)

struct MathService: 
    _calculator: Calculator = Calculator(precision=3)

service = MathService()

# Method delegation
result1 = service.add(3.14159, 2.71828)      # Delegates to service._calculator.add(...)
result2 = service.multiply(3.14159, 2.71828) # Delegates to service._calculator.multiply(...)
```

## Error Handling

### Missing Fields/Methods
```dana
struct SimpleStruct: data: str = "test"
struct Wrapper: _simple: SimpleStruct = SimpleStruct()

wrapper = Wrapper()

# ❌ Access non-existent field
try:
    missing = wrapper.nonexistent_field
except AttributeError as e:
    log(f"Error: {e}")
    # Error: Struct 'Wrapper' has no field or delegated access 'nonexistent_field'. 
    # Available fields: ['_simple']
    # Available through delegation: ['_simple.data']
```

### Enhanced Error Messages
```dana
struct EmbeddedStruct: available_field: str = "test"
struct MainStruct: _embedded: EmbeddedStruct = EmbeddedStruct()

main = MainStruct()

# ❌ Access non-existent field (with delegation info)
try:
    missing = main.nonexistent_field
except AttributeError as e:
    log(f"Error: {e}")
    # Error: Struct 'MainStruct' has no field or delegated access 'nonexistent_field'. 
    # Available fields: ['_embedded']
    # Available through delegation: ['_embedded.available_field']
```

## Best Practices

### 1. Use Descriptive Names for Delegatable Fields
```dana
# ✅ Good - clear purpose
struct Service: 
    _api_client: APIClient = APIClient()
    _logger: Logger = Logger()
    _cache: Cache = Cache()

# ❌ Avoid - unclear purpose
struct Service: 
    _a: APIClient = APIClient()
    _b: Logger = Logger()
    _c: Cache = Cache()
```

### 2. Consider Declaration Order for Conflicts
```dana
# ✅ Good - intentional order
struct Composed: 
    _primary: PrimaryStruct = PrimaryStruct()    # Most important first
    _secondary: SecondaryStruct = SecondaryStruct() # Less important second

# ❌ Avoid - unclear priority
struct Composed: 
    _secondary: SecondaryStruct = SecondaryStruct() # Less important first
    _primary: PrimaryStruct = PrimaryStruct()    # Most important second
```

### 3. Use Explicit Access When Needed
```dana
struct Composed: 
    _first: FirstStruct = FirstStruct()
    _second: SecondStruct = SecondStruct()

comp = Composed()

# Use explicit access to avoid confusion
first_data = comp._first.data
second_data = comp._second.data

# Use delegation for convenience
data = comp.data  # Gets from _first (declaration order)
```

### 4. Keep Delegation Simple
```dana
# ✅ Good - simple delegation
struct Service: 
    _client: APIClient = APIClient()

# ❌ Avoid - deeply nested delegation
struct Service: 
    _wrapper: Wrapper = Wrapper()  # Wrapper contains _client, which contains _api

# Better approach - flatten the structure
struct Service: 
    _client: APIClient = APIClient()
    _logger: Logger = Logger()
```

### 5. Document Delegation Intent
```dana
struct Service: 
    # Delegates API operations to embedded client
    _api_client: APIClient = APIClient()
    
    # Delegates logging operations to embedded logger  
    _logger: Logger = Logger()
    
    # Direct service configuration
    service_name: str = "MyService"
```

## Performance Considerations

### Delegation Overhead
```dana
# Delegation has minimal overhead
struct Wrapper: _data: DataStruct = DataStruct()

wrapper = Wrapper()

# These are equivalent in performance:
direct = wrapper._data.field      # Direct access
delegated = wrapper.field         # Delegated access (slightly more overhead)
```

### Multiple Delegatable Fields
```dana
# Declaration order affects lookup performance
struct Composed: 
    _first: FirstStruct = FirstStruct()   # Checked first
    _second: SecondStruct = SecondStruct() # Checked second (only if not found in _first)
    _third: ThirdStruct = ThirdStruct()   # Checked third (only if not found in _first or _second)

comp = Composed()

# Most frequently accessed fields should be in earlier delegatable fields
frequent_field = comp.frequent_field  # Check _first first
rare_field = comp.rare_field         # Check _first, then _second, then _third
```

## Summary

Struct delegation provides:
- **Automatic forwarding**: Access fields/methods through underscore-prefixed fields
- **Clean composition**: Build complex services from simpler components
- **Declaration order priority**: Clear conflict resolution
- **Explicit access**: Direct access still works when needed
- **Enhanced error messages**: Helpful debugging information

**Key Benefits**:
- **Simplified API**: Complex services appear to have all methods directly
- **Composition over inheritance**: Build functionality through composition
- **Backward compatibility**: Existing code continues to work
- **Performance**: Minimal overhead for delegation

Perfect for: Service composition, API wrappers, configuration management, and building complex systems from simpler components.

**Prerequisites**: See `structs.md` for basic struct concepts and `struct_functions.md` for struct operations.
