# Workflow Primer

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
local:result = data_pipeline("data_source.csv")
```

**What happens behind the scenes**:
1. `load_data("data_source.csv")` → `{"raw": "data"}`
2. `analyze_data({"raw": "data"})` → `{"analysis": "results"}`
3. `create_report({"analysis": "results"})` → `"Final Report"`

## Parameter Passing in Pipelines

Dana supports two modes of parameter passing in pipelines:

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

### 3. Mixed Mode

You can combine both modes in the same pipeline:

```dana
def add_prefix(text: str, prefix: str) -> str:
    return f"{prefix}{text}"

def wrap_with_brackets(text: str, left: str, right: str) -> str:
    return f"{left}{text}{right}"

# Mix implicit and explicit modes
def mixed_pipeline(text: str) = add_prefix("INFO: ") | wrap_with_brackets("[", $$, "]")
result = mixed_pipeline("data")  # "[INFO: data]"
```

**What happens:**
1. `add_prefix("data", "INFO: ")` → `"INFO: data"` (implicit)
2. `wrap_with_brackets("[", "INFO: data", "]")` → `"[INFO: data]"` (explicit with $$)

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
local:result = workflow("input.txt")  # "Result: input.txt"
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
local:result = data_workflow("source.csv")
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
local:result = data_pipeline("sales_data.csv")
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
local:result = user_pipeline("12345")  # "User: John Doe"
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
local:result = loan_pipeline(50000.0, 750)  # "Approved: $150000"
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
local:result = workflow("bad")  # Error: Bad data encountered
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
local:result = data_pipeline("source.csv")
```

## Performance Wins (Over Python)

- **Single callable**: No intermediate variable assignments
- **Optimized execution**: Pipeline can be optimized as a unit
- **Enterprise features**: Available via advanced frameworks
- **Deterministic**: Consistent results every time

**Bottom line**: Dana workflows are Python's function composition with declarative pipeline syntax. Same functions, same logic, but cleaner syntax and enterprise features available via advanced frameworks. It's like having Python's `functools.reduce` with Unix pipe syntax in declarative function definitions. 