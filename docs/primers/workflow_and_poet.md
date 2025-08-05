# Workflow + POET Primer

## TL;DR (1 minute read)

```dana
# Instead of this (Python - manual composition):
try:
    data = load_data(source)
    analysis = analyze_data(data)
    report = create_report(analysis)
except Exception as e:
    handle_error(e)

# Do this (Dana - declarative + robust):
@poet(domain="data_loading", retries=3)
def load_data(source: str) -> dict: return load(source)

@poet(domain="analysis", timeout=30)
def analyze_data(data: dict) -> dict: return analyze(data)

@poet(domain="reporting", validation=true)
def create_report(analysis: dict) -> str: return report(analysis)

# Pipeline with POET enhancement:
@poet(domain="enterprise_pipeline", retries=2, timeout=120)
def data_workflow = load_data | analyze_data | create_report

result = data_workflow("data.csv")  # One call, handles everything
```

---

**What it is**: Python's function composition meets intelligent orchestration. Think of it as Python's `functools.reduce` combined with Python's `@decorator` pattern, but with built-in fault tolerance, context awareness, and adaptive learning.

## Why Should You Care? (Python Developer Edition)

If you're coming from Python, you're probably used to this pattern:

```python
# Python way - manual function composition with decorators
def load_data(source):
    return load(source)

def analyze_data(data):
    return analyze(data)

def create_report(analysis):
    return report(analysis)

# Manual composition - verbose and error-prone!
try:
    data = load_data(source)
    analysis = analyze_data(data)
    report = create_report(analysis)
except Exception as e:
    # Handle errors manually
    print(f"Error: {e}")
```

Or maybe you've used decorators for cross-cutting concerns:

```python
# Python's decorators - good but limited
from functools import wraps
import time

def retry_on_failure(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(1)
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3)
def risky_function(data):
    return process(data)
```

**Dana's POET + Workflow gives you Python's function composition with intelligent orchestration:**

- **Familiar functions**: Same function definitions, same logic
- **Pipeline operator**: Use `|` to compose functions (like Unix pipes)
- **Intelligent decorators**: `@poet()` adds context, fault tolerance, learning
- **Enterprise features**: Built-in retry, monitoring, validation, context sharing

## The Big Picture

```dana
# Your functions (exactly like Python functions)
def load_data(source: str) -> dict:
    return load(source)

def analyze_data(data: dict) -> dict:
    return analyze(data)

def create_report(analysis: dict) -> str:
    return report(analysis)

# POET enhances individual functions (like Python decorators)
@poet(domain="data_loading", retries=3)
def load_data(source: str) -> dict:
    return load(source)

@poet(domain="analysis", timeout=30)
def analyze_data(data: dict) -> dict:
    return analyze(data)

@poet(domain="reporting", validation=true)
def create_report(analysis: dict) -> str:
    return report(analysis)

# Create workflow with pipeline operator
data_pipeline = load_data | analyze_data | create_report

# POET can enhance the entire workflow too!
@poet(domain="enterprise_pipeline", retries=2, timeout=120)
def enterprise_pipeline = load_data | analyze_data | create_report

# Call like any function - just like Python!
result = enterprise_pipeline("data_source.csv")
```

**What happens behind the scenes**:
1. `load_data("data_source.csv")` → `{"raw": "data"}` (with retry logic)
2. `analyze_data({"raw": "data"})` → `{"analysis": "results"}` (with timeout)
3. `create_report({"analysis": "results"})` → `"Final Report"` (with validation)
4. **Plus**: Cross-step context sharing, adaptive learning, fault tolerance

## Why You'll Love This (Python Perspective)

- **Zero learning curve**: Same function syntax, same decorator pattern
- **Pipeline syntax**: `|` operator makes composition obvious
- **Intelligent decorators**: `@poet()` adds enterprise features automatically
- **Context awareness**: Functions learn from each other
- **Fault tolerance**: Built-in retry, timeout, validation
- **Deterministic**: Consistent, reproducible results

## How to Use POET + Workflow (Python Style)

### Basic POET Enhancement - Like Python's Decorators
```dana
# Define your functions (just like Python)
def extract_data(source: str) -> dict:
    return {"data": source}

def process_data(data: dict) -> dict:
    return {"processed": data.data}

def format_output(result: dict) -> str:
    return f"Result: {result.processed}"

# POET enhances functions (like Python decorators)
@poet(domain="extraction", retries=2)
def extract_data(source: str) -> dict:
    return {"data": source}

@poet(domain="processing", timeout=15)
def process_data(data: dict) -> dict:
    return {"processed": data.data}

@poet(domain="formatting", validation=true)
def format_output(result: dict) -> str:
    return f"Result: {result.processed}"

# Create pipeline with | operator
workflow = extract_data | process_data | format_output

# Use like any function
result = workflow("input.txt")  # "Result: input.txt"
```

### POET-Enhanced Workflows - Like Python's Class Decorators
```dana
# Individual POET-enhanced functions
@poet(domain="data_loading", retries=3)
def load_csv(file_path: str) -> dict:
    return {"data": f"loaded from {file_path}"}

@poet(domain="data_cleaning", validation=true)
def clean_data(data: dict) -> dict:
    return {"cleaned": data.data, "rows": 1000}

@poet(domain="analysis", timeout=30)
def calculate_stats(data: dict) -> dict:
    return {"stats": f"processed {data.rows} rows"}

# POET enhances the entire workflow (like Python's class decorators)
@poet(domain="enterprise_pipeline", retries=2, timeout=120)
def enterprise_pipeline = load_csv | clean_data | calculate_stats

# Execute with enterprise features
result = enterprise_pipeline("sales_data.csv")
```

### Complex POET + Workflow - Like Python's Method Chaining with Decorators
```dana
# Build complex pipelines with POET enhancement
@poet(domain="enterprise_data_processing", retries=3, timeout=300)
data_workflow = (
    load_data |
    validate_data |
    transform_data |
    analyze_data |
    create_report
)

# Use with intelligent error handling (like Python's try/except with decorators)
result = data_workflow("source.csv")
```

## Real-World Examples (Python-Style)

### Data Processing Pipeline (Like Python's pandas + decorators)
```dana
# Individual functions with POET enhancement (like Python functions with decorators)
@poet(domain="file_io", retries=3)
def load_csv(file_path: str) -> dict:
    return {"data": f"loaded from {file_path}"}

@poet(domain="data_cleaning", validation=true)
def clean_data(data: dict) -> dict:
    return {"cleaned": data.data, "rows": 1000}

@poet(domain="statistics", timeout=60)
def calculate_stats(data: dict) -> dict:
    return {"stats": f"processed {data.rows} rows"}

@poet(domain="file_output", retries=2)
def save_results(stats: dict) -> str:
    return f"Saved: {stats.stats}"

# Create pipeline (like pandas method chaining with error handling)
data_pipeline = load_csv | clean_data | calculate_stats | save_results

# POET enhances the entire pipeline
@poet(domain="enterprise_data_pipeline", retries=2, timeout=300)
def enterprise_data_pipeline = load_csv | clean_data | calculate_stats | save_results

# Execute (like pandas operations with enterprise features)
result = enterprise_data_pipeline("sales_data.csv")
# Result: "Saved: processed 1000 rows"
```

### API Processing Pipeline (Like Python's requests + decorators)
```dana
# API functions with POET enhancement (like Python's requests with decorators)
@poet(domain="api_calls", retries=3, timeout=30)
def fetch_user_data(user_id: str) -> dict:
    return {"user": {"id": user_id, "name": "John Doe"}}

@poet(domain="validation", validation=true)
def validate_user(user_data: dict) -> dict:
    if user_data.user.id:
        return {"validated": user_data.user}
    else:
        return {"error": "Invalid user"}

@poet(domain="response_formatting", timeout=10)
def format_response(result: dict) -> str:
    if result.validated:
        return f"User: {result.validated.name}"
    else:
        return f"Error: {result.error}"

# API pipeline with enterprise features
@poet(domain="enterprise_api_pipeline", retries=2, timeout=60)
def enterprise_api_pipeline = fetch_user_data | validate_user | format_response

# Use (like Python API calls with intelligent orchestration)
result = enterprise_api_pipeline("12345")  # "User: John Doe"
```

### Business Logic Pipeline (Like Python's business logic + decorators)
```dana
# Business functions with POET enhancement (like Python business logic with decorators)
@poet(domain="loan_calculation", validation=true)
def calculate_loan_amount(income: float, credit_score: int) -> dict:
    return {"loan_amount": income * 3.0, "credit_score": credit_score}

@poet(domain="credit_rules", timeout=15)
def apply_credit_rules(loan_data: dict) -> dict:
    if loan_data.credit_score >= 700:
        return {"approved": true, "amount": loan_data.loan_amount}
    else:
        return {"approved": false, "amount": 0.0}

@poet(domain="decision_formatting", validation=true)
def generate_decision(decision: dict) -> str:
    if decision.approved:
        return f"Approved: ${decision.amount}"
    else:
        return "Declined: Credit score too low"

# Loan processing pipeline with enterprise features
@poet(domain="enterprise_loan_pipeline", retries=2, timeout=60)
def enterprise_loan_pipeline = calculate_loan_amount | apply_credit_rules | generate_decision

# Process loan (like Python business applications with intelligent orchestration)
result = enterprise_loan_pipeline(50000.0, 750)  # "Approved: $150000"
```

## What Happens When Things Go Wrong (Python-Style Errors)

### Function Failure - Like Python's Exception Handling with Decorators
```dana
@poet(domain="risky_operations", retries=3)
def risky_function(data: str) -> dict:
    if data == "bad":
        raise "Bad data encountered"  # Like Python's raise
    return {"result": data}

@poet(domain="safe_operations", validation=true)
def safe_function(data: dict) -> str:
    return f"Processed: {data.result}"

# Pipeline with intelligent error handling
workflow = risky_function | safe_function

# This will retry automatically (like Python's try/except with retry decorators)
result = workflow("bad")  # Will retry 3 times before failing
```

### POET-Enhanced Workflow Error Handling - Like Python's Context Managers
```dana
# POET provides enterprise-grade error handling
@poet(domain="enterprise_pipeline", retries=3, timeout=120)
def enterprise_workflow = risky_function | safe_function

# Enterprise features: retry logic, logging, monitoring, context sharing
result = enterprise_workflow("bad")
```

## Pro Tips (Python Best Practices)

### 1. Use POET for Cross-Cutting Concerns (Like Python Decorators)
```dana
# ✅ Good - POET handles retry, timeout, validation (like Python decorators)
@poet(domain="data_loading", retries=3, timeout=30)
def load_data(source: str) -> dict:
    return load(source)

@poet(domain="validation", validation=true)
def validate_data(data: dict) -> dict:
    return validate(data)

@poet(domain="processing", timeout=60)
def process_data(data: dict) -> dict:
    return process(data)

# ❌ Avoid - manual error handling (like Python without decorators)
def load_data_manual(source: str) -> dict:
    for attempt in range(3):
        try:
            return load(source)
        except Exception as e:
            if attempt == 2:
                raise e
            time.sleep(1)
```

### 2. Combine POET with Workflows for Maximum Power
```dana
# ✅ Good - POET enhances both individual functions and workflows
@poet(domain="extraction", retries=2)
def extract_data(source: str) -> dict:
    return extract(source)

@poet(domain="processing", timeout=30)
def process_data(data: dict) -> dict:
    return process(data)

# POET enhances the entire workflow
@poet(domain="enterprise_pipeline", retries=3, timeout=120)
def enterprise_pipeline = extract_data | process_data

# ❌ Avoid - using workflows without POET for production
def basic_pipeline = extract_data | process_data  # No enterprise features
```

### 3. Use Descriptive POET Domains (Like Python's Decorator Names)
```dana
# ✅ Good - clear domain names (like Python's descriptive decorator names)
@poet(domain="financial_calculations", validation=true)
def calculate_interest(principal: float, rate: float) -> float:
    return principal * rate

@poet(domain="api_integration", retries=3, timeout=30)
def fetch_stock_price(symbol: str) -> dict:
    return api_call(symbol)

# ❌ Avoid - unclear domain names
@poet(domain="stuff", retries=3)
def do_something(data: str) -> str:
    return process(data)
```

### 4. Leverage POET's Context Sharing (Unlike Python's Decorators)
```dana
# POET provides cross-step context sharing (unlike Python's isolated decorators)
@poet(domain="data_processing", context_sharing=true)
def enterprise_pipeline = load_data | process_data | save_data

# Each step can access context from previous steps
# This is beyond what Python decorators can do
```

## Before vs After (Python Perspective)

### Python's Manual Composition with Decorators
```python
# Python way - verbose and error-prone even with decorators
from functools import wraps
import time

def retry_on_failure(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(1)
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3)
def load_data(source):
    return load(source)

@retry_on_failure(max_retries=3)
def process_data(data):
    return process(data)

@retry_on_failure(max_retries=3)
def save_data(processed):
    return save(processed)

# Manual composition - still verbose!
try:
    data = load_data(source)
    processed = process_data(data)
    result = save_data(processed)
except Exception as e:
    print(f"Error: {e}")
```

### Dana's POET + Workflow Composition
```dana
# Dana way - clean and declarative with intelligent orchestration
@poet(domain="data_loading", retries=3)
def load_data(source: str) -> dict:
    return load(source)

@poet(domain="data_processing", timeout=30)
def process_data(data: dict) -> dict:
    return process(data)

@poet(domain="data_saving", retries=2)
def save_data(processed: dict) -> str:
    return save(processed)

# Single pipeline with enterprise features
@poet(domain="enterprise_pipeline", retries=2, timeout=120)
def enterprise_pipeline = load_data | process_data | save_data

# Intelligent orchestration handles everything
result = enterprise_pipeline("source.csv")
```

## Performance Wins (Over Python)

- **Single callable**: No intermediate variable assignments
- **Intelligent orchestration**: POET provides context sharing and adaptive learning
- **Enterprise features**: Built-in retry, monitoring, validation, timeout
- **Deterministic**: Consistent results every time
- **Context awareness**: Functions learn from each other across the pipeline

**Bottom line**: Dana's POET + Workflow is Python's function composition and decorators on steroids. Same functions, same decorator pattern, but with intelligent orchestration, context sharing, and enterprise-grade features. It's like having Python's `functools.reduce` with `@decorator` syntax, plus Unix pipes, plus production-ready orchestration with adaptive learning. 