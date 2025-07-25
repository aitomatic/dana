# Pipeline Functionality - Simplified Design

## Overview
The Dana pipeline system has been simplified to support **pipeline definition only**. This means:

- **✅ Supported**: Function composition using the `|` operator
- **❌ Not Supported**: Inline execution like `5 | add(2) | multiply(3)`

## Usage Pattern

### Pipeline Definition
```dana
def add_two(n):
    return n + 2

def multiply_three(n):
    return n * 3

# Create a pipeline (function composition)
pipeline = add_two | multiply_three

# Use the pipeline
result = pipeline(5)  # Returns 21
```

### Supported Features

#### 1. Basic Function Composition
```dana
def step1(x):
    return x + 1

def step2(x):
    return x * 2

def step3(x, prefix="Result: "):
    return f"{prefix}{x}"

# Compose multiple functions
full_pipeline = step1 | step2 | step3
result = full_pipeline(5)  # Returns "Result: 12"
```

#### 2. Placeholder Support
```dana
def format_message(prefix, text, suffix):
    return f"{prefix}{text}{suffix}"

# Use placeholder to control argument position
pipeline = format_message("(", $, ")")
result = pipeline("hello")  # Returns "(hello)"
```

#### 3. Mixed Modes
```dana
def process_data(data, multiplier=2):
    return data * multiplier

def add_suffix(text, suffix="!"):
    return f"{text}{suffix}"

# Mix implicit and explicit arguments
pipeline = process_data(3) | add_suffix("?")
result = pipeline(5)  # Returns "15?"
```

## What This Means

Instead of:
```dana
# ❌ Not supported (inline execution)
result = 5 | add(2) | multiply(3)
```

Use:
```dana
# ✅ Supported (pipeline definition)
pipeline = add | multiply
result = pipeline(5, 2, 3)  # Or adjust function signatures
```

## Benefits of This Approach

1. **Simpler Implementation**: Less complex parsing and execution logic
2. **Clearer Semantics**: Explicit function composition vs. inline execution
3. **Consistent with Functional Programming**: Similar to other functional languages
4. **Easier Testing**: Clear separation between definition and execution

## Testing

Run the test suite to verify functionality:
```bash
uv run pytest tests/unit/core/pipeline/test_pipeline_expression.py -v
```

The test suite includes comprehensive tests for:
- Basic function composition
- Placeholder substitution
- Mixed argument modes
- Edge cases and error handling