# This is a placeholder for the pav-usage-guide.md content.
# The original ipv-usage-guide.md content will be moved here and updated. 

# PAV Usage Guide: Complete Reference

## Overview

PAV (Perceive-Act-Validate) is Dana's intelligent optimization pattern that automatically enhances AI interactions with **comment-aware context analysis** and **LLM-driven optimization**. This guide provides comprehensive usage examples and best practices.

## 🎯 Core Concepts

### The PAV Pattern
```
PERCEIVE: Extract context from code, comments, and type hints
   ↓
ACT: Use LLM to analyze context and optimize prompts  
   ↓
VALIDATE: Apply type-driven validation and formatting
```

### Comment-Aware Context Analysis
PAV automatically extracts and analyzes:
- **Comments** in your Dana code
- **Type hints** from variable assignments  
- **Surrounding code context**
- **Domain indicators** and **intent signals**

## 🚀 Basic Usage

### 1. Simple Reasoning with PAV

```dana
# Extract financial data from text
price = reason("Find the cost: Item sells for $29.99") -> float

# PAV automatically:
# - Detects financial domain from "$" symbol
# - Applies numerical extraction for float type
# - Validates and cleans the result
```

### 2. Comment-Driven Optimization

```dana
# Medical data extraction - requires high accuracy
# Patient temperature should be in Celsius
temperature = reason("Patient reports feeling feverish at 101.5°F") -> float

# PAV leverages comments to:
# - Understand medical context from comment
# - Apply temperature conversion logic
# - Ensure precise numerical extraction
```

### 3. Complex Type Handling

```dana
# Extract structured customer data
# Return as key-value pairs for database storage
customer_info = reason("John Smith, age 30, email john@example.com") -> dict

# PAV will:
# - Parse natural language into structured data
# - Return: {"name": "John Smith", "age": 30, "email": "john@example.com"}
# - Validate dictionary structure
```

### 4. Output Type Adaptability with `reason()`

A key strength of PAV-enabled functions like `reason()` is their ability to adapt the output based on the `expected_output_type` inferred from your Dana code (e.g., via type hints on assignment). The same conceptual prompt can yield different, type-appropriate results.

**Example: Describing Pi**

Consider the task of getting information about Pi:

```dana
# Scenario 1: Requesting a string description
# PAV's Perceive phase notes the '-> str' (or type hint on assignment).
# Validate phase ensures a string is returned.
local:pi_description: str = reason("Tell me about Pi.")
# Expected: "Pi is a mathematical constant, approximately 3.14159..."

# Scenario 2: Requesting a floating-point value
# PAV's Perceive phase notes '-> float'.
# Validate phase ensures a float is returned, potentially parsing it from a more verbose LLM output.
local:pi_float: float = reason("Tell me about Pi.")
# Expected: 3.14159 (or similar float representation)

# Scenario 3: Requesting an integer value (perhaps the whole number part)
# PAV's Perceive phase notes '-> int'.
# Validate phase ensures an integer, possibly truncating or rounding.
local:pi_integer: int = reason("Tell me about Pi.")
# Expected: 3

# Scenario 4: Requesting a more structured representation (e.g., a dict)
# PAV's Perceive phase notes '-> dict'.
# Validate phase ensures a dictionary.
local:pi_details: dict = reason("Tell me about Pi.")
# Expected: {"symbol": "π", "value": 3.14159, "type": "mathematical constant"} (or similar structure)
```

In each case, the `reason()` function, powered by PAV:
1.  **Perceives** the core request ("Tell me about Pi.") and also the `expected_output_type` from the Dana code context.
2.  **Acts** by querying an LLM, possibly providing the desired output type as a hint in the prompt to the LLM.
3.  **Validates** that the LLM's output can be successfully coerced or represented as the `expected_output_type` (string, float, int, dict), performing necessary transformations or retrying if the initial output isn't suitable.

This demonstrates how PAV allows functions to be flexible in what they accept (the general intent) while being conservative and precise in what they produce, aligning with the caller's specific needs.

## 💡 The Purpose of PAV: Robust and Intelligent Execution

You've seen PAV in action with functions like `reason()`. But why is this model so central to Dana?

PAV (Perceive → Act → Validate) is designed to address common challenges in building reliable AI-powered workflows, especially when interacting with probabilistic systems like Large Language Models (LLMs). Its core goals are to:

1.  **Embrace Intent, Enforce Precision (Postel's Law)**:
    *   **Perceive**: Flexibly interpret ambiguous inputs, user intent, and diverse data formats. This phase can gather rich context from your code (comments, type hints via a `CodeContextAnalyzer`) and the environment. Crucially, it can also *transform and optimize* the initial input, for example, by **rewriting a vague user prompt into a more detailed and effective prompt** for an LLM, or by selecting the best strategy for the `Act` phase.
    *   **Act**: Execute the primary task (e.g., calling an LLM with the optimized prompt, running a tool, or executing a Dana function) using the refined input from the `Perceive` stage.
    *   **Validate**: Rigorously check the output of the `Act` phase against expected types (using `expected_output_type`), structures, or other quality criteria. This ensures that downstream components receive reliable, predictable data.

2.  **Automate Resilience**:
    *   The built-in **retry loop** automatically re-attempts the `Act` (and subsequently `Validate`) phase upon validation failure. This handles transient issues or allows for iterative refinement.
    *   The `pav_status` object provides context about attempts and failures, enabling more intelligent retry strategies or fallback mechanisms within custom P/A/V functions.

3.  **Enhance Developer Experience**:
    *   By standardizing this robust execution pattern, PAV reduces boilerplate code for error handling, input sanitization, output validation, and retry logic.
    *   It allows Dana engineers to focus on the core logic of their `Act` functions, while leveraging PAV for the surrounding scaffolding.
    *   Features like automatic context gathering and prompt optimization aim to make interactions with complex AI services more powerful and less error-prone.

In essence, PAV provides a structured, configurable, and resilient "wrapper" around core operations, making them more dependable and "smarter" by systematically handling the complexities of real-world AI interactions.

## 🎛️ Advanced Usage (Python Customization)

This section details how developers can customize the PAV framework using Python, for instance by creating custom PAV executors or configurations. For general Dana usage of PAV-enabled functions, refer to the Dana-level decorator documentation and examples.

### 1. Multiple PAV Executors/Profiles

```python
from opendxa.dana.pav.executor import PAVReason, PAVDataProcessor, PAVAPIIntegrator # Note: Path and class names are illustrative

# Reasoning tasks
reasoner = PAVReason()
result = reasoner.execute("Analyze this financial report...", context) # `execute` signature may vary

# Data processing tasks  
processor = PAVDataProcessor()
analysis = processor.execute("Find trends in sales data", context, data=sales_data)

# API integration tasks
integrator = PAVAPIIntegrator()
api_result = integrator.execute("Get weather for San Francisco", context)
```

### 2. Custom PAV Configuration

```python
from opendxa.dana.pav.config import PAVConfig # Note: Path and class name are illustrative

# Create custom configuration
config = PAVConfig(
    max_retries=3,             # Default from PAV decorator, can be part of a profile
    enable_caching=True,       # Caching strategy would be specific to PAV profile/executor
    fallback_strategy="simple", # Fallback strategy would be specific to PAV profile/executor
    custom_system_message="You are a financial analysis expert..." # Relevant for LLM-based PAV profiles
)

# Use with PAV executor (illustrative)
reasoner = PAVReason() # Or some base PAV executor
# result = reasoner.execute(intent, context, config=config) # Actual API TBD
```

### 3. Debug Mode and Monitoring (Framework Level)

```python
# Debugging and monitoring are generally part of the PAV framework itself or specific executor/profile implementations.
# Dana-level functions decorated with @pav would benefit from this automatically.

# Illustrative Python-level access if directly using executors:
# reasoner = PAVReason()
# reasoner.set_debug_mode(True)

# result = reasoner.execute("Complex analysis task...", context)

# history = reasoner.get_execution_history()
# print(f"Processed {len(history)} requests")

# stats = reasoner.get_performance_stats()
# print(f"Average processing time: {stats['average_duration']:.2f}s")
# print(f"Success rate: {stats['success_rate']:.1%}")
```

## 📊 Type-Driven Validation Examples (Leveraging `expected_output_type`)

The PAV framework's `Validate` phase is strongly guided by the `expected_output_type` defined in the `@pav` decorator or inferred during the `Perceive` phase. Dana's `reason()` function inherently benefits from this type-driven validation.

### Numerical Types

```dana
# Float extraction with validation (expected_output_type is float)
price = reason("The item costs twenty-nine dollars and ninety-nine cents") -> float 
# Result: 29.99

# Integer extraction (expected_output_type is int)
count = reason("We have fifteen items in stock") -> int
# Result: 15

# Boolean extraction (expected_output_type is bool)
approved = reason("The request was approved by management") -> bool  
# Result: true
```

### Structured Types

```dana
# Dictionary extraction (expected_output_type is dict or a specific Dana struct)
product = reason("iPhone 14, $999, 128GB storage, Blue color") -> dict
# Result: {"name": "iPhone 14", "price": 999, "storage": "128GB", "color": "Blue"}

# List extraction (expected_output_type is list or list[str], etc.)
colors = reason("Available in red, blue, green, and yellow") -> list
# Result: ["red", "blue", "green", "yellow"]
```

### Complex Validation

```dana
# JSON-structured response (expected_output_type is a dict or specific Dana struct)
config = reason("Set timeout to 30 seconds, retries to 3, debug mode on") -> dict
# Result: {"timeout": 30, "retries": 3, "debug": true}
```

## 🔧 Integration Patterns (Dana-centric View)

This section focuses on how Dana engineers interact with PAV-enabled functions and contribute to the PAV lifecycle, primarily through Dana code.
For details on the PAV architecture itself, see the [PAV Execution Model documentation](../../design/02_dana_runtime_and_execution/pav_execution_model.md).

### 1. Using PAV-enabled Functions (e.g., `reason()`)

Many core Dana functions, like `reason()`, are implicitly PAV-enabled. You use them like regular functions, and PAV works behind the scenes.

```dana
# User provides minimal prompt with context and type hint
# Extract total price from medical invoice
# PAV's Perceive phase uses comments, code context, and the -> float hint
# to determine the expected_output_type and guide validation.
private:price: float = reason("get price from 'Invoice total: $125.50'")
```

### 2. Authoring Dana Functions for PAV Stages (`@pav` decorator)

Dana functions can be designated as `Perceive` or `Validate` stages for a PAV-enabled operation using Dana's `@pav` decorator. The decorated function itself becomes the `Act` stage.

```dana
# (Conceptual example, see Dana Language Spec for definitive @pav syntax)

# Dana function for the 'Perceive' phase
def my_input_parser(raw_text: str, pav_status: dict) -> dict:
    # pav_status might provide initial context like expected_output_type from decorator
    local:parsed = {"input": raw_text.lower(), "char_count": len(raw_text)}
    # This dict becomes pav_status.perceived_input for Act and Validate
    return local:parsed

# Dana function for the 'Validate' phase
def my_output_checker(act_result: any, pav_status: dict) -> bool:
    # pav_status includes {attempt, perceived_input, raw_output, expected_output_type, ...}
    log(f"Attempt {pav_status.attempt} validating {act_result} against {pav_status.expected_output_type}")
    if pav_status.expected_output_type and typeof(act_result) != pav_status.expected_output_type:
        return False
    # Further custom checks...
    return len(act_result) > 5

@pav(
    perceive=my_input_parser,
    validate=my_output_checker,
    expected_output_type="str" # Explicitly state the final desired type
)
def process_complex_text(parsed_input: dict) -> str:
    # This is the 'Act' phase. 
    # 'parsed_input' is the output from my_input_parser (pav_status.perceived_input)
    return f"PROCESSED ({parsed_input.char_count} chars): {parsed_input.input.upper()}"

# Usage
local:final_result = process_complex_text("Some initial text.")
```

### 3. Leveraging `pav_status` in Dana

Dana functions used in `Perceive` and `Validate` stages (and potentially `Act` if structured to receive it) can access the `pav_status` dictionary. This allows for adaptive logic based on retry attempts, last failure reasons, perceived input, and the expected output type.

See the `pav_status` structure in the [PAV Execution Model documentation](../../design/02_dana_runtime_and_execution/pav_execution_model.md#pav_status-in-dana).

## 🎨 Best Practices for Dana Engineers with PAV

### 1. Write Effective Comments and Use Type Hints

The `Perceive` phase of PAV (especially its `CodeContextAnalyzer` component) relies heavily on good comments and clear type hints in your Dana code to infer intent and `expected_output_type`.

```dana
# ✅ Good: Specific, actionable context, clear type hint for PAV
# Financial analysis - extract currency values in USD.
# Result should be a floating point number.
local:revenue: float = reason("Q3 revenue was $1.2M")

# ❌ Poor: Vague comments, no type hint for PAV to leverage
# Get some number
local:value = reason("Extract the number")
```

### 2. Design Clear `Perceive` and `Validate` Functions
When using the `@pav` decorator with custom Dana functions for P and V stages:
*   **Perceive**: Focus on normalizing input and gathering all necessary context. The output of `Perceive` (`pav_status.perceived_input`) is critical for `Act` and `Validate`.
*   **Validate**: Be strict. Use `pav_status.expected_output_type` and `pav_status.perceived_input` to perform thorough checks. Set `pav_status.last_failure` clearly on validation failure to aid retries or debugging.

### 3. Understand `expected_output_type`
This is a key part of the PAV contract. Ensure it is specified correctly in `@pav` decorators, or provide strong type hints at assignment sites for PAV-enabled functions like `reason()` so the `Perceive` phase can infer it accurately. This drives the `Validate` phase.

### 4. Error Handling for PAV-enabled functions
While PAV aims to handle many transient errors with retries, fundamental issues or repeated validation failures will still result in errors. Use standard Dana `try-catch` blocks if you need to handle failures from PAV-enabled function calls.

```dana
# (Conceptual, assuming PAV-decorated function can raise an error after max_retries)
try:
    local:processed_data = process_complex_text("some input")
catch Error as e:
    log(f"PAV processing failed after multiple attempts: {e.message}")
    # Handle the error, e.g., use a fallback or notify user
``` 