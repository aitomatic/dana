# Dana Cheatsheet

## Quick Reference

```dana
# Basic Dana usage
import opendxa.dana as dana

# Create a simple agent
name = "Dana"
agent = dana.Agent(name)
```

## Core Functions

### AI and Reasoning
```dana
# Basic reasoning
result = reason("What is machine learning?")

# Structured reasoning with context
analysis = reason(f"Analyze this data: {data}")

# Set reasoning parameters
result = reason("Explain quantum computing", {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 500
})
```

### Logging and Output
```dana
# Basic logging
log("Processing started", level="INFO")
log("Debug information", level="DEBUG")
log("Warning message", level="WARNING")
log("Error occurred", level="ERROR")

# Print output
print("Hello, world!")
print("Multiple", "values", "separated", "by", "spaces")

# Set log levels
log_level("INFO")  # Set global level
log_level("ERROR", "opendxa")  # Set framework level
```

### Built-in Functions
```dana
# Collection operations
length = len([1, 2, 3, 4, 5])  # 5
total = sum([1, 2, 3, 4, 5])  # 15
maximum = max([1, 2, 3, 4, 5])  # 5
minimum = min([1, 2, 3, 4, 5])  # 1

# Mathematical functions
absolute = abs(-42)  # 42
rounded = round(3.14159, 2)  # 3.14
```

## POET Decorators

### Python Functions
```python
from opendxa.dana.poet import poet

@poet(domain="manufacturing", timeout=30.0, retries=3)
def optimize_production(schedule, constraints):
    """Optimize production schedule with domain intelligence."""
    # Function implementation
    return optimized_schedule
```

### Dana Functions
```dana
@poet(domain="finance", timeout=60.0)
def analyze_portfolio(assets, risk_tolerance):
    # Portfolio analysis with financial domain intelligence
    analysis = reason(f"Analyze portfolio: {assets}")
    return analysis
```

### Runtime Enhancement
```dana
# Enhance existing function at runtime
result = poet("analyze_data", [data], domain="healthcare", timeout=45.0)
```

## Type System

### Basic Types
```dana
# Variable type annotations
user_data: dict = {"name": "Alice", "age": 25}
temperature: float = 98.6
is_active: bool = true
count: int = 42
message: str = "Hello, Dana!"

# Collections
numbers: list = [1, 2, 3, 4, 5]
settings: dict = {"debug": true, "timeout": 30}
coordinates: tuple = (10.5, 20.3)
unique_items: set = {1, 2, 3, 4, 5}
```

### Function Signatures
```dana
# Function with typed parameters and return type
def analyze_user_data(data: dict, threshold: float) -> dict:
    # Function implementation
    return {"analysis": "complete", "confidence": 0.95}

# Function with multiple return types
def process_data(data: list) -> dict | str:
    if len(data) > 100:
        return {"status": "processed", "count": len(data)}
    else:
        return "insufficient_data"
```

## Scoping System

### Scope Types
```dana
# Private scope (function-local, secure)
private:sensitive_data = load_sensitive_data()
private:api_key = "secret_key_123"

# Public scope (shared across contexts)
public:user_preferences = {"theme": "dark", "language": "en"}
public:session_data = {"user_id": 12345}

# System scope (runtime configuration)
system:debug_mode = true
system:log_level = "INFO"

# Local scope (default for function parameters)
def process_data(local:data, local:options):
    # Parameters are automatically in local scope
    return transform_data(local:data)
```

### Scope Usage Patterns
```dana
# Secure data processing
private:raw_data = fetch_sensitive_data()
public:summary = reason(f"Summarize: {private:raw_data}")
return public:summary

# Configuration management
system:api_timeout = 30
system:retry_attempts = 3

# Session management
public:user_session = {"start_time": "2025-01-24T10:00:00Z"}
```

## Error Handling

### Try-Catch Blocks
```dana
try:
    result = risky_operation()
    log("Operation successful", level="INFO")
    return result
except Exception as error:
    log(f"Operation failed: {error}", level="ERROR")
    return {"error": "operation_failed", "details": error}
```

### Error Prevention
```dana
# Validate inputs
if len(data) == 0:
    log("Empty data provided", level="WARNING")
    return {"error": "empty_data"}

# Check for required fields
if not "user_id" in user_data:
    log("Missing user_id", level="ERROR")
    return {"error": "missing_user_id"}
```

## Common Patterns

### Data Processing Pipeline
```dana
# Load and validate data
data = load_data()
validation = validate_data(data)

if validation.valid:
    # Process data
    processed = process_data(data)
    
    # Analyze results
    analysis = reason(f"Analyze results: {processed}")
    
    # Store results
    store_results(processed, analysis)
    
    return {"status": "success", "analysis": analysis}
else:
    log(f"Validation failed: {validation.issues}", level="ERROR")
    return {"status": "failed", "issues": validation.issues}
```

### AI-Powered Decision Making
```dana
# Gather context
context = gather_context()
user_input = get_user_input()

# Make AI-powered decision
decision = reason(f"""
Context: {context}
User Input: {user_input}

Based on this information, what should be the next action?
Provide a clear recommendation with reasoning.
""")

# Execute decision
if decision.action == "proceed":
    execute_action(decision.parameters)
    log("Action executed successfully", level="INFO")
else:
    log(f"Decision: {decision.reasoning}", level="INFO")
```

### Configuration Management
```dana
# Load configuration
config = load_config()

# Set up logging
log_level(config.log_level)

# Initialize resources
llm = initialize_llm(config.llm_settings)
memory = initialize_memory(config.memory_settings)

# Validate configuration
if not validate_config(config):
    log("Invalid configuration", level="ERROR")
    exit(1)
```

## Performance Optimization

### Caching
```dana
# Simple caching pattern
cache_key = hash(data)
if cache_key in cache:
    return cache[cache_key]

result = expensive_operation(data)
cache[cache_key] = result
return result
```

### Batch Processing
```dana
# Process items in batches
def process_batch(items, batch_size=10):
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_result = process_items(batch)
        results.extend(batch_result)
    return results
```

### Resource Management
```dana
# Proper resource cleanup
try:
    resource = acquire_resource()
    result = use_resource(resource)
    return result
finally:
    cleanup_resource(resource)
```

## Debugging

### Debug Mode
```dana
# Enable debug mode
import opendxa.dana as dana
sandbox = dana.DanaSandbox(debug=true)

# Debug output will show execution details
result = sandbox.run("""
    x = 10
    y = 20
    z = x + y
    log(f"Debug: x={x}, y={y}, z={z}", level="DEBUG")
    return z
""")
```

### Logging Strategies
```dana
# Structured logging
log(f"Processing user {user_id} with {len(data)} items", level="INFO")

# Debug logging
log(f"Data structure: {type(data)}", level="DEBUG")
log(f"Function parameters: {locals()}", level="DEBUG")

# Error logging with context
try:
    result = risky_operation()
except Exception as error:
    log(f"Operation failed for user {user_id}: {error}", level="ERROR")
    log(f"Context: {context}", level="DEBUG")
```

## Integration Examples

### Python Integration
```dana
# Call Python from Dana
def python_function(data):
    return process_data(data)

result = dana.run("""
    result = python_function([1, 2, 3, 4, 5])
    return result
""")
```

### API Integration
```dana
# HTTP requests
response = http_get("https://api.example.com/data")
data = parse_json(response.body)

# Process with AI
analysis = reason(f"Analyze API data: {data}")
return analysis
```

### Database Operations
```dana
# Database queries
users = query_database("SELECT * FROM users WHERE active = true")
user_count = len(users)

# AI analysis of database results
insights = reason(f"Analyze user data: {users}")
return {"user_count": user_count, "insights": insights}
```

---

*For more detailed information, see the [Dana Language Reference](../reference/dana-syntax.md) and [API Documentation](../reference/api/README.md).* 