# This is a placeholder for the pov-usage-guide.md content.
# The original ipv-usage-guide.md content will be moved here and updated.

# POET Usage Guide: Complete Reference

## Overview

POET (Perceive-Operate-Enforce-Train) is Dana's intelligent execution pattern that automatically enhances AI interactions with **fault-tolerant context processing**, **self-learning optimization**, and **enterprise-grade reliability**. This guide provides comprehensive usage examples and best practices.

## Core Concepts

### The POET Flow

```mermaid
graph LR
    A[Input Data] --> B[Perceive<br/>Fault-tolerant<br/>Context Processing]
    B --> C[Operate<br/>Business Logic<br/>Engineer-Written]
    C --> D[Enforce<br/>Error-free<br/>Deterministic Output]
    D --> E[Output Results]
    D --> F[Train<br/>Self-Learning<br/>Feedback Loop]
    F --> B
    
    style B fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    style C fill:#fff3e0,stroke:#f57c00,stroke-width:3px,color:#000
    style D fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style F fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000
```

### What Engineers Write vs. What Runtime Provides

**Engineers Write (Operate):**
- Business logic and decision-making code
- The core operational intelligence

**Runtime Provides Automatically:**
- **Perceive**: Fault-tolerant contextual input processing
- **Enforce**: Error-free deterministic output generation  
- **Train**: Continuous adaptation based on feedback signals

### Comment-Aware Context Analysis
POET automatically extracts and analyzes:
- Comments in your Dana code
- Type hints from variable assignments
- Surrounding code context
- Domain indicators and **intent signals**

## Basic Usage

### 1. Simple Reasoning with POET

```dana
# Extract financial data from text
price = reason("Find the cost: Item sells for $29.99") -> float

# POET automatically:
# - PERCEIVE: Detects financial domain from "$" symbol and context
# - OPERATE: Applies your business logic for numerical extraction
# - ENCODE: Validates and formats result as float type
# - TRAIN: Learns from successful extractions to improve future performance
```

### 2. Comment-Driven Optimization

```dana
# Medical data extraction - requires high accuracy
# Patient temperature should be in Celsius
temperature = reason("Patient reports feeling feverish at 101.5°F") -> float

# POET leverages comments to:
# - PERCEIVE: Understand medical context and accuracy requirements
# - Apply temperature conversion logic
# - Ensure precise numerical extraction
```

### 3. Complex Type Handling

```dana
# Extract structured customer data
# Return as key-value pairs for database storage
customer_info = reason("John Smith, age 30, email john@example.com") -> dict

# POV will:
# - Parse natural language into structured data
# - Return: {"name": "John Smith", "age": 30, "email": "john@example.com"}
# - Validate dictionary structure
```

### 4. Output Type Adaptability with `reason()`

A key strength of POV-enabled functions like `reason()` is their ability to adapt the output based on the `expected_output_type` inferred from your Dana code (e.g., via type hints on assignment). The same conceptual prompt can yield different, type-appropriate results.
Example: Describing Pi
Consider the task of getting information about Pi:

```dana
# Scenario 1: Requesting a string description
# POV's Perceive phase notes the '-> str' (or type hint on assignment).
# Validate phase ensures a string is returned.
local:pi_description: str = reason("Tell me about Pi.")
# Expected: "Pi is a mathematical constant, approximately 3.14159..."

# Scenario 2: Requesting a floating-point value
# POV's Perceive phase notes '-> float'.
# Validate phase ensures a float is returned, potentially parsing it from a more verbose LLM output.
local:pi_float: float = reason("Tell me about Pi.")
# Expected: 3.14159 (or similar float representation)

# Scenario 3: Requesting an integer value (perhaps the whole number part)
# POV's Perceive phase notes '-> int'.
# Validate phase ensures an integer, possibly truncating or rounding.
local:pi_integer: int = reason("Tell me about Pi.")
# Expected: 3

# Scenario 4: Requesting a more structured representation (e.g., a dict)
# POV's Perceive phase notes '-> dict'.
# Validate phase ensures a dictionary.
local:pi_details: dict = reason("Tell me about Pi.")
# Expected: {"symbol": "π", "value": 3.14159, "type": "mathematical constant"} (or similar structure)
```

In each case, the `reason()` function, powered by POV:
1. **Perceives** the core request ("Tell me about Pi.") and also the `expected_output_type` from the Dana code context.
2. **Operates** by querying an LLM, possibly providing the desired output type as a hint in the prompt to the LLM.
3. **Validates** that the LLM's output can be successfully coerced or represented as the `expected_output_type` (string, float, int, dict), performing necessary transformations or retrying if the initial output isn't suitable.

This demonstrates how POV allows functions to be flexible in what they accept (the general intent) while being conservative and precise in what they produce, aligning with the caller's specific needs.

## The Purpose of POV: Robust and Intelligent Execution

You've seen POV in action with functions like `reason()`. But why is this model so central to Dana?

POV (Perceive → Operate → Validate) is designed to address common challenges in building reliable AI-powered workflows, especially when interacting with probabilistic systems like Large Language Models (LLMs). Its core goals are to:

1. **Embrace Intent, Enforce Precision (Postel's Law)**:
 * Perceive: Flexibly interpret ambiguous inputs, user intent, and diverse data formats. This phase can gather rich context from your code (comments, type hints via a `CodeContextAnalyzer`) and the environment. Crucially, it can also *transform and optimize* the initial input, for example, by **rewriting a vague user prompt into a more detailed and effective prompt** for an LLM, or by selecting the best strategy for the `Operate` phase.
 * Operate: Execute the primary task (e.g., calling an LLM with the optimized prompt, running a tool, or executing a Dana function) using the refined input from the `Perceive` stage.
 * Validate: Rigorously check the output of the `Operate` phase against expected types (using `expected_output_type`), structures, or other quality criteria. This ensures that downstream components receive reliable, predictable data.

2. **Automate Resilience**:
 * The built-in **retry loop** automatically re-attempts the `Operate` (and subsequently `Validate`) phase upon validation failure. This handles transient issues or allows for iterative refinement.
 * The `pov_status` object provides context about attempts and failures, enabling more intelligent retry strategies or fallback mechanisms within custom P/O/V functions.

3. **Enhance Developer Experience**:
 * By standardizing this robust execution pattern, POV reduces boilerplate code for error handling, input sanitization, output validation, and retry logic.
 * It allows Dana engineers to focus on the core logic of their `Operate` functions, while leveraging POV for the surrounding scaffolding.
 * Features like automatic context gathering and prompt optimization aim to make interactions with complex AI services more powerful and less error-prone.

In essence, POV provides a structured, configurable, and resilient "wrapper" around core operations, making them more dependable and "smarter" by systematically handling the complexities of real-world AI interactions.

## 🎛️ Advanced Usage (Python Customization)

This section details how developers can customize the POV framework using Python, for instance by creating custom POV executors or configurations. For general Dana usage of POV-enabled functions, refer to the Dana-level decorator documentation and examples.

### 1. Multiple POV Executors/Profiles

```python
from opendxa.dana.pov.executor import POVReason, POVDataProcessor, POVAPIIntegrator # Note: Path and class names are illustrative

# Reasoning tasks
reasoner = POVReason()
result = reasoner.execute("Analyze this financial report...", context) # `execute` signature may vary

# Data processing tasks
processor = POVDataProcessor()
analysis = processor.execute("Find trends in sales data", context, data=sales_data)

# API integration tasks
integrator = POVAPIIntegrator()
api_result = integrator.execute("Get weather for San Francisco", context)
```

### 2. Custom POV Configuration

```python
from opendxa.dana.pov.config import POVConfig # Note: Path and class name are illustrative

# Create custom configuration
config = POVConfig(
 max_retries=3, # Default from POV decorator, can be part of a profile
 enable_caching=True, # Caching strategy would be specific to POV profile/executor
 fallback_strategy="simple", # Fallback strategy would be specific to POV profile/executor
 custom_system_message="You are a financial analysis expert..." # Relevant for LLM-based POV profiles
)

# Use with POV executor (illustrative)
reasoner = POVReason() # Or some base POV executor
# result = reasoner.execute(intent, context, config=config) # Actual API TBD
```

### 3. Debug Mode and Monitoring (Framework Level)

```python
# Debugging and monitoring are generally part of the POV framework itself or specific executor/profile implementations.
# Dana-level functions decorated with @pov would benefit from this automatically.

# Illustrative Python-level access if directly using executors:
# reasoner = POVReason()
# reasoner.set_debug_mode(True)

# result = reasoner.execute("Complex analysis task...", context)

# history = reasoner.get_execution_history()
# print(f"Processed {len(history)} requests")

# stats = reasoner.get_performance_stats()
# print(f"Average processing time: {stats['average_duration']:.2f}s")
# print(f"Success rate: {stats['success_rate']:.1%}")
```

## 📊 Type-Driven Validation Examples (Leveraging `expected_output_type`)

The POV framework's `Validate` phase is strongly guided by the `expected_output_type` defined in the `@pov` decorator or inferred during the `Perceive` phase. Dana's `reason()` function inherently benefits from this type-driven validation.

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

## Integration Patterns (Dana-centric View)

This section focuses on how Dana engineers interact with POV-enabled functions and contribute to the POV lifecycle, primarily through Dana code.
For details on the POV architecture itself, see the [POV Execution Model documentation](../../design/02_dana_runtime_and_execution/poet_functions.md).

### 1. Using POV-enabled Functions (e.g., `reason()`)

Many core Dana functions, like `reason()`, are implicitly POV-enabled. You use them like regular functions, and POV works behind the scenes.

```dana
# User provides minimal prompt with context and type hint
# Extract total price from medical invoice
# POV's Perceive phase uses comments, code context, and the -> float hint
# to determine the expected_output_type and guide validation.
private:price: float = reason("get price from 'Invoice total: $125.50'")
```

### 2. Authoring Dana Functions for POV Stages (`@pov` decorator)

Dana functions can be designated as `Perceive` or `Validate` stages for a POV-enabled operation using Dana's `@pov` decorator. The decorated function itself becomes the `Operate` stage.

```dana
# (Conceptual example, see Dana Language Spec for definitive @pov syntax)

# Dana function for the 'Perceive' phase
def my_input_parser(raw_text: str, pov_status: dict) -> dict:
 # pov_status might provide initial context like expected_output_type from decorator
 local:parsed = {"input": raw_text.lower(), "char_count": len(raw_text)}
 # This dict becomes pov_status.perceived_input for Operate and Validate
 return local:parsed

# Dana function for the 'Validate' phase
def my_output_checker(operate_result: any, pov_status: dict) -> bool:
 # pov_status includes {attempt, perceived_input, raw_output, expected_output_type, ...}
 log(f"Attempt {pov_status.attempt} validating {operate_result} against {pov_status.expected_output_type}")
 if pov_status.expected_output_type and typeof(operate_result) != pov_status.expected_output_type:
 return False
 # Further custom checks...
 return len(operate_result) > 5

@pov(
 perceive=my_input_parser,
 validate=my_output_checker,
 expected_output_type="str" # Explicitly state the final desired type
)
def process_complex_text(parsed_input: dict) -> str:
 # This is the 'Operate' phase.
 # 'parsed_input' is the output from my_input_parser (pov_status.perceived_input)
 return f"PROCESSED ({parsed_input.char_count} chars): {parsed_input.input.upper()}"

# Usage
local:final_result = process_complex_text("Some initial text.")
```

### 3. Leveraging `pov_status` in Dana

Dana functions used in `Perceive` and `Validate` stages (and potentially `Operate` if structured to receive it) can access the `pov_status` dictionary. This allows for adaptive logic based on retry attempts, last failure reasons, perceived input, and the expected output type.

See the `pov_status` structure in the [POV Execution Model documentation](../../design/02_dana_runtime_and_execution/poet_functions.md#pov_status-in-dana).

## 🎨 Best Practices for Dana Engineers with POV

### 1. Write Effective Comments and Use Type Hints

The `Perceive` phase of POV (especially its `CodeContextAnalyzer` component) relies heavily on good comments and clear type hints in your Dana code to infer intent and `expected_output_type`.

```dana
# ✅ Good: Specific, actionable context, clear type hint for POV
# Financial analysis - extract currency values in USD.
# Result should be a floating point number.
local:revenue: float = reason("Q3 revenue was $1.2M")

# ❌ Poor: Vague comments, no type hint for POV to leverage
# Get some number
local:value = reason("Extract the number")
```

### 2. Design Clear `Perceive` and `Validate` Functions
When using the `@pov` decorator with custom Dana functions for P and V stages:
* Perceive: Focus on normalizing input and gathering all necessary context. The output of `Perceive` (`pov_status.perceived_input`) is critical for `Operate` and `Validate`.
* Validate: Be strict. Use `pov_status.expected_output_type` and `pov_status.perceived_input` to perform thorough checks. Set `pov_status.last_failure` clearly on validation failure to aid retries or debugging.

### 3. Understand `expected_output_type`
This is a key part of the POV contract. Ensure it is specified correctly in `@pov` decorators, or provide strong type hints at assignment sites for POV-enabled functions like `reason()` so the `Perceive` phase can infer it accurately. This drives the `Validate` phase.

### 4. Error Handling for POV-enabled functions
While POV aims to handle many transient errors with retries, fundamental issues or repeated validation failures will still result in errors. Use standard Dana `try-catch` blocks if you need to handle failures from POV-enabled function calls.

```dana
# (Conceptual, assuming POV-decorated function can raise an error after max_retries)
try:
 local:processed_data = process_complex_text("some input")
catch Error as e:
 log(f"POV processing failed after multiple attempts: {e.message}")
 # Handle the error, e.g., use a fallback or notify user
```