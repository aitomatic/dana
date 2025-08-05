# Dana Core Library

The Dana Core Library (`dana/libs/corelib`) contains fundamental mathematical and utility functions that are essential to the Dana language.

## Structure

```
dana/libs/corelib/
├── __init__.py                    # Package initialization
├── register_corelib_functions.py  # Auto-registration
├── py/                            # Python function files (preloaded)
│   ├── __init__.py
│   ├── py_math.py                 # Mathematical utilities
│   ├── py_text.py                 # Text processing functions
│   ├── py_str.py                  # String conversion
│   ├── py_print.py                # Print function
│   ├── py_cast.py                 # Type casting
│   ├── py_log.py                  # Logging function
│   ├── py_log_level.py            # Log level setting
│   ├── py_noop.py                 # No-operation function
│   ├── py_use.py                  # Resource management
│   ├── py_llm.py                  # LLM interactions
│   ├── py_reason.py               # LLM reasoning
│   ├── py_enhanced_reason.py      # Enhanced reasoning
│   ├── py_set_model.py            # Model configuration
│   ├── py_poet.py                 # POET enhancements
│   ├── py_feedback.py             # POET feedback
│   └── py_decorators.py           # Function decorators
└── README.md                      # This file
```

## Available Functions

### Math Functions

- **`sum_range(start, end)`** - Sum numbers in a range (inclusive)
- **`is_odd(n)`** - Check if a number is odd
- **`is_even(n)`** - Check if a number is even  
- **`factorial(n)`** - Calculate factorial of a number

### Text Functions

- **`capitalize_words(text)`** - Capitalize each word in the text
- **`title_case(text)`** - Convert text to title case

### Core Functions

- **`str(value)`** - Convert value to string
- **`print(*values)`** - Print values to stdout
- **`cast(target_type, value)`** - Cast value to specified type
- **`log(message, level)`** - Log a message
- **`log_level(level)`** - Set logging level
- **`noop(*args, **kwargs)`** - No-operation function
- **`use(function_name, *args, **kwargs)`** - Create and manage resources

### AI/LLM Functions

- **`llm(prompt, model, temperature, max_tokens)`** - Generate text using LLM
- **`reason(prompt, options, use_mock)`** - LLM reasoning with POET enhancements
- **`context_aware_reason(prompt, options, use_mock)`** - Enhanced reasoning
- **`set_model(model)`** - Configure LLM model

### POET Functions

- **`poet(func_name, args, kwargs, domain, timeout, retries)`** - Apply POET enhancements
- **`apply_poet(operation, config)`** - Apply POET to callable
- **`feedback(result, feedback_payload)`** - Submit POET feedback

### Decorators

- **`log_calls(func)`** - Log function calls and results
- **`log_with_prefix(prefix, include_result)`** - Log with custom prefix
- **`repeat(times)`** - Repeat function execution
- **`validate_args(**validators)`** - Validate function arguments

## Usage

The core library functions are automatically available in Dana programs without explicit imports:

```dana
# Math functions are globally available
result = sum_range(1, 10)  # 55
is_odd(7)                  # true
is_even(8)                 # true
factorial(5)               # 120

# Text functions are globally available
capitalize_words("hello world")  # "Hello World"
title_case("dana language")      # "Dana Language"

# Core functions are globally available
str(123)                   # "123"
print("Hello world")       # prints "Hello world"
cast(int, "456")          # 456
log("Debug message", "DEBUG")
log_level("ERROR")

# AI/LLM functions are globally available
llm("What is 2+2?")       # generates response
reason("Analyze this data") # enhanced reasoning
set_model("gpt-4")        # configure model

# POET functions are globally available
poet("reason", ["Analyze this"], domain="financial")
feedback(result, "Excellent prediction!")
```

## Registration

Core library functions are registered with the highest priority in the Dana interpreter, ensuring they are always available and take precedence over other function definitions.

## Adding New Functions

To add new functions to the core library:

1. Create a new Python file in `dana/libs/corelib/py/` with `py_` prefix (e.g., `py_my_function.py`)
2. Define functions with names starting with `py_` prefix
3. Add functions to `__all__` list
4. Follow the pattern established in `py_math.py`

Example:
```python
# py_my_function.py
__all__ = ["py_my_function"]

def py_my_function(context: SandboxContext, arg1, arg2):
    """My new core library function."""
    # Function implementation
    return result
```

## Testing

Core library functions are tested in `tests/unit/core/stdlib/test_math_functions.py`. 