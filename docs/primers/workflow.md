# Workflow Primer

## TL;DR (1 minute read)

```dana
# Instead of this (Python):
data = load_data(source)
analysis = analyze_data(data)
report = create_report(analysis)

# Do this (Dana):

def data_pipeline(source: str) -> str = load_data | analyze_data | create_report
result = data_pipeline("data.csv")

# With placeholders:
def format_message(prefix: str, text: str, suffix: str) -> str:
    return f"{prefix}{text}{suffix}"

def pipeline(text: str) = format_message("Start: ", $$, " :End")
result = pipeline("hello")  # "Start: hello :End"

# With named parameter capture:
def add_ten(x: int) -> int:
    return x + 10

def multiply_by(x: int, factor: int) -> int:
    return x * factor

def add_values(a: int, b: int) -> int:
    return a + b

def named_pipeline(x: int) = add_ten as base | multiply_by(2) as doubled | add_values(base, doubled)
result = named_pipeline(5)  # 45 (base=15, doubled=30, 15+30=45)
```

---

**What it is**: Python's function composition, but with declarative pipeline syntax. Think of it as Python's `functools.reduce` or method chaining, but using the familiar `|` operator in declarative function definitions to create data processing pipelines.

## Why Should You Care?

If you're coming from Python, you're probably used to this pattern:

```python
# Python way - function composition
def load_data(source):
    return load(source)

def analyze_data(data):
    return analyze(data)

def create_report(analysis):
    return report(analysis)

# Manual composition - verbose!
data = load_data(source)
analysis = analyze_data(data)
report = create_report(analysis)
```

Or maybe you've used `functools.reduce`:

```python
# Python's reduce - functional but verbose
from functools import reduce

def pipeline(data, func):
    return func(data)

result = reduce(pipeline, [load_data, analyze_data, create_report], source)
```

**Dana workflows give you Python's function composition with declarative pipeline syntax:**

- **Familiar functions**: Same function definitions, same logic
- **Declarative pipelines**: Use `def func() = f1 | f2 | f3` syntax (like Unix pipes)
- **Single callable**: Your workflow becomes one function
- **Enterprise features**: Add safety, validation, context via advanced frameworks

## The Big Picture

```dana
# Your functions (exactly like Python functions)
def load_data(source: str) -> dict:
    return load(source)

def analyze_data(data: dict) -> dict:
    return analyze(data)

def create_report(analysis: dict) -> str:
    return report(analysis)

# Create workflow with declarative function syntax
def data_pipeline(source: str) -> str = load_data | analyze_data | create_report

# Call like any function - just like Python!
result = data_pipeline("data_source.csv")
```

**What happens behind the scenes**:
1. `load_data("data_source.csv")` → `{"raw": "data"}`
2. `analyze_data({"raw": "data"})` → `{"analysis": "results"}`
3. `create_report({"analysis": "results"})` → `"Final Report"`

## Parameter Passing in Pipelines

Dana supports three modes of parameter passing in pipelines:

### 1. Implicit First-Argument Mode (Default)

In implicit mode, the pipeline value is automatically passed as the first argument to each function:

```dana
def add_one(x: int) -> int:
    return x + 1

def double(x: int) -> int:
    return x * 2

def to_string(x: int) -> str:
    return str(x)

# Simple pipeline - each function gets the result of the previous function
def simple_pipeline(x: int) -> str = add_one | double | to_string
result = simple_pipeline(5)  # "12" (5+1=6, 6*2=12, "12")
```

**What happens:**
1. `add_one(5)` → `6`
2. `double(6)` → `12` 
3. `to_string(12)` → `"12"`

### 2. Explicit Placeholder Mode

Use the `$$` placeholder to explicitly control where the pipeline value is inserted:

```dana
def format_message(prefix: str, text: str, suffix: str) -> str:
    return f"{prefix}{text}{suffix}"

# Simple placeholder example - put the pipeline value in the middle
def simple_placeholder(text: str) = format_message("Start: ", $$, " :End")
result = simple_placeholder("hello")  # "Start: hello :End"
```

**What happens:**
- The `$$` gets replaced with the input value `"hello"`
- `format_message("Start: ", "hello", " :End")` → `"Start: hello :End"`

### 3. Named Parameter Capture Mode

Use the `as name` syntax to capture intermediate results for reuse in later pipeline stages:

```dana
def add_ten(x: int) -> int:
    return x + 10

def multiply_by(x: int, factor: int) -> int:
    return x * factor

def add_values(a: int, b: int) -> int:
    return a + b

# Capture and reuse intermediate values
def named_capture_pipeline(x: int) = add_ten as base | multiply_by(2) as doubled | add_values(base, doubled)
result = named_capture_pipeline(5)  # 45 (base=15, doubled=30, 15+30=45)
```

**What happens:**
1. `add_ten(5)` → `15` (saved as `base`)
2. `multiply_by(15, 2)` → `30` (saved as `doubled`)
3. `add_values(15, 30)` → `45` (using captured values)

### 4. Mixed Mode

You can combine all three modes in the same pipeline:

```dana
def add_prefix(text: str, prefix: str) -> str:
    return f"{prefix}{text}"

def wrap_with_brackets(text: str, left: str, right: str) -> str:
    return f"{left}{text}{right}"

def format_result(text: str, original: str) -> str:
    return f"{text} (was: {original})"

# Mix implicit, explicit, and named capture modes
def mixed_pipeline(text: str) = add_prefix("INFO: ") as prefixed | wrap_with_brackets("[", $$, "]") | format_result($$, prefixed)
result = mixed_pipeline("data")  # "[INFO: data] (was: INFO: data)"
```

**What happens:**
1. `add_prefix("data", "INFO: ")` → `"INFO: data"` (saved as `prefixed`)
2. `wrap_with_brackets("[", "INFO: data", "]")` → `"[INFO: data]"` (explicit with $$)
3. `format_result("[INFO: data]", "INFO: data")` → `"[INFO: data] (was: INFO: data)"` (using captured `prefixed`)

## More Complex Examples

Once you understand the basics, here are more advanced patterns:

### Advanced Implicit Mode
```dana
def add_prefix(text: str, prefix: str = "Prefix: ") -> str:
    return f"{prefix}{text}"

def to_uppercase(text: str) -> str:
    return text.upper()

def add_suffix(text: str, suffix: str = "!!!") -> str:
    return f"{text}{suffix}"

# Pipeline with fixed parameters
def advanced_pipeline(text: str) = add_prefix("Data: ") | to_uppercase | add_suffix("?")
result = advanced_pipeline("hello")  # "DATA: HELLO?"

# Pipeline with default arguments
def default_pipeline(text: str) = add_prefix | to_uppercase
result = default_pipeline("world")  # "PREFIX: WORLD"
```

### Advanced Placeholder Mode
```dana
# Placeholder in first position
def first_placeholder_pipeline(text: str) = format_message($$, "MIDDLE", "!!!")
result = first_placeholder_pipeline("world")  # "worldMIDDLE!!!"

# Placeholder in last position
def last_placeholder_pipeline(text: str) = format_message("START", "MIDDLE", $$)
result = last_placeholder_pipeline("end")  # "STARTMIDDLEend"

# Multiple placeholders
def multi_placeholder_func(a: str, b: str, c: str, d: str) -> str:
    return f"{a}-{b}-{c}-{d}"

def multi_placeholder_pipeline(text: str) = multi_placeholder_func("start", $$, "middle", $$)
result = multi_placeholder_pipeline("value")  # "start-value-middle-value"
```

### Advanced Named Parameter Capture Mode
```dana
# Complex business logic with multiple captures
def calculate_invoice(price: float) = multiply_by(1) as original | apply_discount($$, 20) as discounted | calculate_tax(discounted, 0.08) as tax | add_values(discounted, tax) as total | format_invoice(original, discounted, tax, total)

# Data transformation with validation
def transform_data(value: any) = normalize as normalized | validate($$) as validation_result | enrich(normalized, validation_result) | format_output("Processed", $$)

# Error handling with named captures
def safe_process(value: any) = validate as is_valid | process($$) if is_valid else error("Invalid input") | log_result($$, is_valid)
```

## Why You'll Love This (Python Perspective)

- **Zero learning curve**: Same function syntax, same logic
- **Declarative syntax**: `def func() = f1 | f2 | f3` makes composition obvious
- **Single callable**: Your workflow becomes one function
- **Enterprise ready**: Add validation, retries, monitoring
- **Deterministic**: Consistent, reproducible results

## How to Use Workflows (Python Style)

### Basic Pipeline - Exactly Like Python Functions
```dana
# Define your functions (just like Python)
def extract_data(source: str) -> dict:
    return {"data": source}

def process_data(data: dict) -> dict:
    return {"processed": data.data}

def format_output(result: dict) -> str:
    return f"Result: {result.processed}"

# Create pipeline with declarative function syntax
def workflow(source: str) -> str = extract_data | process_data | format_output

# Use like any function
result = workflow("input.txt")  # "Result: input.txt"
```

### With Advanced Frameworks - Like Python's Context Managers
```dana
# For advanced use cases, you can use enterprise frameworks
# that provide additional features like validation, monitoring, and context management
# These are available in the dana.frameworks namespace for complex workflows

# Basic declarative pipelines work for most use cases
def advanced_pipeline(data: any) -> str = extract_text | analyze_content | generate_summary
```

### Complex Pipeline - Like Python's Method Chaining
```dana
# Build complex pipelines
def data_workflow(source: str) -> str = (
    load_data |
    validate_data |
    transform_data |
    analyze_data |
    create_report
)

# Use with error handling (like Python's try/except)
result = data_workflow("source.csv")
```

## Real-World Examples (Python-Style)

### Data Processing Pipeline (Like Python's pandas)
```dana
# Individual functions (like Python functions)
def load_csv(file_path: str) -> dict:
    return {"data": f"loaded from {file_path}"}

def clean_data(data: dict) -> dict:
    return {"cleaned": data.data, "rows": 1000}

def calculate_stats(data: dict) -> dict:
    return {"stats": f"processed {data.rows} rows"}

def save_results(stats: dict) -> str:
    return f"Saved: {stats.stats}"

# Create pipeline (like pandas method chaining)
def data_pipeline(file_path: str) -> str = load_csv | clean_data | calculate_stats | save_results

# Execute (like pandas operations)
result = data_pipeline("sales_data.csv")
# Result: "Saved: processed 1000 rows"
```

### API Processing Pipeline (Like Python's requests + processing)
```dana
# API functions (like Python's requests)
def fetch_user_data(user_id: str) -> dict:
    return {"user": {"id": user_id, "name": "John Doe"}}

def validate_user(user_data: dict) -> dict:
    if user_data.user.id:
        return {"validated": user_data.user}
    else:
        return {"error": "Invalid user"}

def format_response(result: dict) -> str:
    if result.validated:
        return f"User: {result.validated.name}"
    else:
        return f"Error: {result.error}"

# API pipeline (like Python's API wrappers)
def user_pipeline(user_id: str) -> str = fetch_user_data | validate_user | format_response

# Use (like Python API calls)
result = user_pipeline("12345")  # "User: John Doe"
```

### Business Logic Pipeline (Like Python's business logic)
```dana
# Business functions (like Python business logic)
def calculate_loan_amount(income: float, credit_score: int) -> dict:
    return {"loan_amount": income * 3.0, "credit_score": credit_score}

def apply_credit_rules(loan_data: dict) -> dict:
    if loan_data.credit_score >= 700:
        return {"approved": true, "amount": loan_data.loan_amount}
    else:
        return {"approved": false, "amount": 0.0}

def generate_decision(decision: dict) -> str:
    if decision.approved:
        return f"Approved: ${decision.amount}"
    else:
        return "Declined: Credit score too low"

# Loan processing pipeline (like Python business workflows)
def loan_pipeline(income: float, credit_score: int) -> str = calculate_loan_amount | apply_credit_rules | generate_decision

# Process loan (like Python business applications)
result = loan_pipeline(50000.0, 750)  # "Approved: $150000"
```

## What Happens When Things Go Wrong (Python-Style Errors)

### Function Failure - Like Python's Exception Handling
```dana
def risky_function(data: str) -> dict:
    if data == "bad":
        raise "Bad data encountered"  # Like Python's raise
    return {"result": data}

def safe_function(data: dict) -> str:
    return f"Processed: {data.result}"

# Pipeline with error handling
def workflow(data: str) -> str = risky_function | safe_function

# This will fail gracefully (like Python's try/except)
result = workflow("bad")  # Error: Bad data encountered
```

### Advanced Error Handling - Like Python's Context Managers
```dana
# For advanced error handling, you can use enterprise frameworks
# that provide retry logic, logging, and monitoring capabilities

# Basic error handling works with declarative pipelines
def safe_pipeline(data: str) -> str = risky_function | safe_function
```

## Pro Tips (Python Best Practices)

### 1. Keep Functions Focused (Single Responsibility)
```dana
# ✅ Good - each function has one job (like Python best practices)
def load_data(source: str) -> dict:
    return load(source)

def validate_data(data: dict) -> dict:
    return validate(data)

def process_data(data: dict) -> dict:
    return process(data)

# ❌ Avoid - one function doing everything
def load_validate_and_process(source: str) -> dict:
    # Too many responsibilities
    pass
```

### 2. Use Descriptive Names (Python Style)
```dana
# ✅ Good - clear what each step does
def data_pipeline(file_path: str) -> str = load_csv | clean_data | calculate_stats | save_results

# ❌ Avoid - unclear what's happening
def pipeline(x: any) -> any = f1 | f2 | f3 | f4
```

### 3. Break Down Complex Pipelines (Like Python's function composition)
```dana
# ✅ Good - readable and maintainable
def data_loading(source: str) -> dict = load_csv | validate_data
def data_processing(data: dict) -> dict = transform_data | calculate_stats
def data_output(results: dict) -> str = format_results | save_results

def full_pipeline(source: str) -> str = data_loading | data_processing | data_output
```

### 4. Use Advanced Frameworks for Production (Like Python's production patterns)
```dana
# For development - simple pipelines
def dev_pipeline(x: any) -> any = func1 | func2 | func3

# For production - enterprise features available in dana.frameworks
# These provide retry logic, timeouts, validation, and monitoring
# Basic declarative pipelines work for most production use cases
def production_pipeline(data: any) -> any = func1 | func2 | func3
```

## Before vs After (Python Perspective)

### Python's Manual Composition
```python
# Python way - verbose and error-prone
def process_data_pipeline(source):
    try:
        # Step 1: Load
        data = load_data(source)
        if not data:
            return "Error: No data loaded"
        
        # Step 2: Process
        processed = process_data(data)
        if not processed:
            return "Error: Processing failed"
        
        # Step 3: Output
        result = create_output(processed)
        return result
    except Exception as e:
        return f"Error: {e}"
```

### Dana's Pipeline Composition
```dana
# Dana way - clean and declarative
def load_data(source: str) -> dict:
    return load(source)

def process_data(data: dict) -> dict:
    return process(data)

def create_output(processed: dict) -> str:
    return output(processed)

# Single pipeline - handles errors automatically
def data_pipeline(source: str) -> str = load_data | process_data | create_output
result = data_pipeline("source.csv")
```

## Performance Wins (Over Python)

- **Single callable**: No intermediate variable assignments
- **Optimized execution**: Pipeline can be optimized as a unit
- **Enterprise features**: Available via advanced frameworks
- **Deterministic**: Consistent results every time

**Bottom line**: Dana workflows are Python's function composition with declarative pipeline syntax. Same functions, same logic, but cleaner syntax and enterprise features available via advanced frameworks. It's like having Python's `functools.reduce` with Unix pipe syntax in declarative function definitions. 