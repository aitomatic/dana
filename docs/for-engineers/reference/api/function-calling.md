# Function Calling API Reference

Dana's function system supports local function definitions, module imports, and a comprehensive function lookup hierarchy. This reference covers function definition, calling conventions, import system, and function resolution.

## Table of Contents
- [Overview](#overview)
- [Function Definition](#function-definition)
- [Function Calling](#function-calling)
- [Function Lookup Hierarchy](#function-lookup-hierarchy)
- [Import System](#import-system)
- [Type Signatures](#type-signatures)
- [Scope and Context](#scope-and-context)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Implementation Details](#implementation-details)

---

## Overview

### Function System Features
- ✅ **Local function definitions**: Define functions within Dana files
- ✅ **Dana module imports**: Import other Dana files as modules
- ✅ **Python module imports**: Import Python modules for extended functionality
- ✅ **Type signatures**: Full type hint support for parameters and return values
- ✅ **Function lookup hierarchy**: User → Core → Built-in function resolution
- ✅ **Scope inheritance**: Functions inherit calling context scopes
- ✅ **Function composition**: Pipeline and composition operators

### Function Types
| Type | Description | Example |
|------|-------------|---------|
| **User-defined** | Functions defined in Dana code | `def my_function():` |
| **Core functions** | Essential Dana functions | `reason()`, `log()`, `print()` |
| **Built-in functions** | Pythonic built-ins | `len()`, `sum()`, `max()` |
| **Imported Dana** | Functions from Dana modules | `import utils.na as u` |
| **Imported Python** | Functions from Python modules | `import math.py as m` |

---

## Function Definition

### Basic Syntax
```dana
def function_name(parameters) -> return_type:
 # function body
 return value
```

### Simple Functions
```dana
# Function without parameters
def greet() -> str:
 return "Hello, world!"

# Function with parameters
def add(x: int, y: int) -> int:
 return x + y

# Function with mixed typed/untyped parameters
def process(data: list, format, verbose: bool) -> dict:
 result = {"data": data, "format": format, "verbose": verbose}
 return result
```

### Functions with Type Hints
```dana
# Comprehensive type annotations
def calculate_bmi(weight: float, height: float) -> float:
 """Calculate Body Mass Index."""
 bmi = weight / (height * height)
 return bmi

# Function with collection parameters
def analyze_scores(scores: list, threshold: int) -> dict:
 """Analyze a list of scores against a threshold."""
 passed = []
 failed = []

 for score in scores:
 if score >= threshold:
 passed.append(score)
 else:
 failed.append(score)

 return {
 "passed": passed,
 "failed": failed,
 "pass_rate": len(passed) / len(scores) if scores else 0
 }

# Function returning None (procedures)
def log_event(message: str, level: str) -> None:
 """Log an event with specified level."""
 log(f"[{level}] {message}")
 private:last_log_time = get_current_time()
```

### Functions with Default Parameters
```dana
# Default parameter values
def create_user(name: str, age: int, role: str = "user") -> dict:
 """Create a user with optional role."""
 return {
 "name": name,
 "age": age,
 "role": role,
 "created_at": get_current_time()
 }

# Multiple default parameters
def configure_analysis(data: list, method: str = "standard",
 verbose: bool = false, timeout: int = 30) -> dict:
 """Configure analysis with default settings."""
 config = {
 "data_size": len(data),
 "method": method,
 "verbose": verbose,
 "timeout": timeout
 }
 return config
```

### Functions with Variable Arguments
```dana
# Using any type for flexible parameters
def log_multiple(level: str, *messages: any) -> None:
 """Log multiple messages at once."""
 for message in messages:
 log(f"[{level}] {message}")

# Function with flexible data processing
def merge_data(*datasets: any) -> list:
 """Merge multiple datasets into one."""
 merged = []
 for dataset in datasets:
 if isinstance(dataset, list):
 merged.extend(dataset)
 else:
 merged.append(dataset)
 return merged
```

---

## Function Calling

### Basic Function Calls
```dana
# Simple function calls
greeting = greet()
sum_result = add(10, 20)
user = create_user("Alice", 25)

# Function calls with keyword arguments
user_admin = create_user(name="Bob", age=30, role="admin")
config = configure_analysis(data=[1, 2, 3], verbose=true)
```

### Function Calls with Type Safety
```dana
# Type-safe function calls
def process_user_data(user_id: int, name: str, scores: list) -> dict:
 # Validate inputs through type hints
 log(f"Processing user {user_id}: {name}")

 # Call other typed functions
 analysis = analyze_scores(scores, 70)
 bmi = calculate_bmi(70.0, 1.75) # Type compatibility: int -> float

 return {
 "user_id": user_id,
 "name": name,
 "score_analysis": analysis,
 "bmi": bmi
 }

# Function calls with error handling
def safe_calculation(a: float, b: float) -> any:
 """Safely perform division with error handling."""
 if b == 0:
 log("Division by zero attempted", "error")
 return None

 result = a / b
 log(f"Calculation result: {result}", "info")
 return result
```

### Nested Function Calls
```dana
# Function composition through nesting
def complex_analysis(raw_data: list) -> dict:
 # Multi-step processing with nested calls
 cleaned_data = clean_data(raw_data)
 processed_data = process_data(cleaned_data)
 analysis_result = analyze_data(processed_data)

 # Nested function calls
 final_score = calculate_score(
 analyze_scores(
 extract_scores(analysis_result),
 get_threshold("standard")
 )
 )

 return {
 "raw_count": len(raw_data),
 "processed_count": len(processed_data),
 "final_score": final_score,
 "analysis": analysis_result
 }
```

---

## Function Lookup Hierarchy

Dana follows a clear precedence order when resolving function calls:

### 1. User-defined Functions (Highest Priority)
```dana
# User function overrides built-ins
def len(obj: any) -> str:
 return f"Custom length function called with {obj}"

# This calls the user-defined function
result = len([1, 2, 3]) # Returns "Custom length function called with [1, 2, 3]"
```

### 2. Core Functions (Medium Priority)
```dana
# Core functions cannot be overridden for security
def reason(prompt: str) -> str:
 return "This won't override the core function"

# This still calls the core reason() function
analysis = reason("What should I do?") # Calls core AI reasoning function
```

### 3. Built-in Functions (Lowest Priority)
```dana
# Built-in functions are available when not overridden
numbers = [1, 2, 3, 4, 5]
total = sum(numbers) # Calls built-in sum()
maximum = max(numbers) # Calls built-in max()
length = len(numbers) # Would call user-defined len() if defined above
```

### Function Resolution Example
```dana
# Define custom functions
def process(data: list) -> list:
 """Custom data processing."""
 return [x * 2 for x in data]

def sum(values: list) -> str:
 """Custom sum that returns a string."""
 total = 0
 for value in values:
 total += value
 return f"Total: {total}"

# Function calls demonstrate precedence
data = [1, 2, 3, 4, 5]

# 1. User-defined function (highest priority)
processed = process(data) # Calls user-defined process()
custom_sum = sum(data) # Calls user-defined sum() -> "Total: 15"

# 2. Core function (cannot be overridden)
analysis = reason("Analyze this data") # Always calls core reason()
log("Processing complete", "info") # Always calls core log()

# 3. Built-in function (when not overridden)
length = len(data) # Calls built-in len() -> 5
maximum = max(data) # Calls built-in max() -> 5
```

---

## Import System

### Dana Module Imports
```dana
# Import Dana modules
import utils.na as util
import data_processing.na as dp
import ai_helpers.na as ai

# Use imported functions
cleaned_data = util.clean_input(raw_data)
processed = dp.transform_data(cleaned_data)
analysis = ai.analyze_with_context(processed, context)
```

### Python Module Imports
```dana
# Import Python modules
import math.py as math
import json.py as json
import datetime.py as dt

# Use Python functions
result = math.sqrt(16) # 4.0
data_json = json.dumps({"key": "value"})
current_time = dt.datetime.now()
```

### Import with Aliases
```dana
# Short aliases for convenience
import very_long_module_name.na as vlmn
import data_analysis_utilities.na as dau

# Use with short names
result = vlmn.process()
analysis = dau.analyze()
```

### Selective Imports
```dana
# Import specific functions (conceptual - may not be implemented)
from utils.na import clean_data, validate_input
from math.py import sqrt, pow

# Use imported functions directly
clean = clean_data(raw_data)
valid = validate_input(user_input)
square_root = sqrt(25)
```

---

## Type Signatures

### Function Parameter Types
```dana
# Basic parameter types
def process_user(name: str, age: int, active: bool) -> dict:
 return {"name": name, "age": age, "active": active}

# Collection parameter types
def analyze_data(numbers: list, config: dict, tags: set) -> tuple:
 result = (len(numbers), config.get("method", "default"), len(tags))
 return result

# Optional parameters with any type
def flexible_function(required: str, optional: any = None) -> any:
 if optional is None:
 return f"Processing {required} with defaults"
 return f"Processing {required} with {optional}"
```

### Return Type Annotations
```dana
# Specific return types
def get_user_count() -> int:
 return 42

def get_user_name() -> str:
 return "Alice"

def get_user_data() -> dict:
 return {"name": "Alice", "age": 25}

def get_coordinates() -> tuple:
 return (10, 20, 30)

def get_tags() -> set:
 return {"python", "dana", "ai"}

# None return type for procedures
def update_status(status: str) -> None:
 private:current_status = status
 log(f"Status updated to: {status}", "info")
```

### Complex Type Signatures
```dana
# Function with complex data structures
def process_user_profile(profile: dict, preferences: dict,
 history: list) -> dict:
 """Process complete user profile data."""
 processed_profile = {
 "basic_info": {
 "name": profile.get("name", "Unknown"),
 "age": profile.get("age", 0),
 "email": profile.get("email", "")
 },
 "settings": {
 "theme": preferences.get("theme", "light"),
 "notifications": preferences.get("notifications", true),
 "language": preferences.get("language", "en")
 },
 "activity": {
 "total_actions": len(history),
 "last_action": history[-1] if history else None,
 "active_user": len(history) > 10
 }
 }
 return processed_profile

# Function with AI integration
def ai_content_analysis(content: str, analysis_type: str,
 options: dict = None) -> dict:
 """Perform AI-powered content analysis."""
 if options is None:
 options = {"temperature": 0.5, "max_tokens": 500}

 prompt = f"Perform {analysis_type} analysis on: {content}"
 ai_result = reason(prompt, options)

 return {
 "content": content,
 "analysis_type": analysis_type,
 "result": ai_result,
 "options_used": options,
 "timestamp": get_current_time()
 }
```

---

## Scope and Context

### Function Scope Inheritance
```dana
# Functions inherit calling context scopes
private:global_config = {"debug": true, "verbose": false}
public:shared_data = {"status": "active"}

def process_with_context(data: list) -> dict:
 # Function can access calling context scopes
 debug_mode = private:global_config["debug"]
 current_status = public:shared_data["status"]

 # Local function scope
 processing_start = get_current_time()

 if debug_mode:
 log(f"Processing {len(data)} items", "debug")

 # Process data
 results = []
 for item in data:
 processed_item = item * 2
 results.append(processed_item)

 # Update shared state
 public:shared_data["last_processed"] = processing_start

 return {
 "results": results,
 "debug_mode": debug_mode,
 "status": current_status,
 "processed_at": processing_start
 }
```

### Function Local Scope
```dana
def isolated_processing(input_data: list) -> dict:
 # Local variables don't affect calling context
 temp_result = []
 processing_step = 1
 error_count = 0

 for item in input_data:
 try:
 processed = complex_operation(item)
 temp_result.append(processed)
 processing_step += 1
 except Exception as e:
 error_count += 1
 log(f"Error processing item {item}: {e}", "error")

 # Return results without polluting calling scope
 return {
 "results": temp_result,
 "total_steps": processing_step - 1,
 "errors": error_count,
 "success_rate": (processing_step - 1 - error_count) / (processing_step - 1)
 }

# Calling function doesn't see temp_result, processing_step, etc.
result = isolated_processing([1, 2, 3, 4, 5])
```

---

## Best Practices

### 1. Always Use Type Hints
```dana
# ✅ Good: Clear function signature
def calculate_discount(price: float, discount_percent: float) -> float:
 return price * (1 - discount_percent / 100)

# ❌ Avoid: Unclear function signature
def calculate_discount(price, discount_percent):
 return price * (1 - discount_percent / 100)
```

### 2. Use Descriptive Function Names
```dana
# ✅ Good: Clear purpose
def validate_user_email(email: str) -> bool:
 return "@" in email and "." in email

def calculate_monthly_payment(principal: float, rate: float, months: int) -> float:
 return principal * (rate / 12) / (1 - (1 + rate / 12) ** -months)

# ❌ Avoid: Unclear purpose
def check(email: str) -> bool:
 return "@" in email and "." in email

def calc(p: float, r: float, m: int) -> float:
 return p * (r / 12) / (1 - (1 + r / 12) ** -m)
```

### 3. Handle Edge Cases
```dana
# ✅ Good: Robust error handling
def safe_divide(a: float, b: float) -> any:
 """Safely divide two numbers."""
 if b == 0:
 log("Division by zero attempted", "warning")
 return None

 if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
 log("Invalid input types for division", "error")
 return None

 return a / b

def process_list_safely(items: list, processor: any) -> list:
 """Process list items with error handling."""
 if not items:
 return []

 results = []
 for i, item in enumerate(items):
 try:
 processed = processor(item)
 results.append(processed)
 except Exception as e:
 log(f"Error processing item {i}: {e}", "error")
 results.append(None)

 return results
```

### 4. Use Appropriate Return Types
```dana
# ✅ Good: Appropriate return types
def find_user_by_id(user_id: int) -> any:
 """Find user by ID, return user dict or None."""
 users = get_all_users()
 for user in users:
 if user["id"] == user_id:
 return user
 return None

def validate_and_process(data: any) -> dict:
 """Validate and process data, return status and result."""
 if not data:
 return {"valid": false, "error": "No data provided", "result": None}

 try:
 processed = process_data(data)
 return {"valid": true, "error": None, "result": processed}
 except Exception as e:
 return {"valid": false, "error": str(e), "result": None}
```

### 5. Document Function Purpose
```dana
# ✅ Good: Well-documented functions
def ai_sentiment_analysis(text: str, model_config: dict = None) -> dict:
 """
 Perform sentiment analysis on text using AI reasoning.

 Args:
 text: The text to analyze
 model_config: Optional AI model configuration

 Returns:
 Dictionary with sentiment, confidence, and details
 """
 if model_config is None:
 model_config = {"temperature": 0.3, "max_tokens": 200}

 prompt = f"Analyze the sentiment of this text: {text}"
 ai_response = reason(prompt, model_config)

 return {
 "text": text,
 "sentiment": ai_response,
 "model_config": model_config,
 "analyzed_at": get_current_time()
 }
```

---

## Examples

### Complete Function Examples

#### Data Processing Pipeline
```dana
def data_processing_pipeline(raw_data: list, config: dict) -> dict:
 """Complete data processing pipeline with type safety."""

 # Validation
 if not raw_data:
 return {"error": "No data provided", "result": None}

 # Configuration with defaults
 clean_config = {
 "remove_nulls": config.get("remove_nulls", true),
 "normalize": config.get("normalize", false),
 "validate": config.get("validate", true)
 }

 # Step 1: Data cleaning
 log("Starting data cleaning", "info")
 cleaned_data = clean_data(raw_data, clean_config)

 # Step 2: Data validation
 if clean_config["validate"]:
 validation_result = validate_data(cleaned_data)
 if not validation_result["valid"]:
 return {
 "error": f"Validation failed: {validation_result['error']}",
 "result": None
 }

 # Step 3: Data transformation
 log("Starting data transformation", "info")
 transformed_data = transform_data(cleaned_data, clean_config)

 # Step 4: Analysis
 log("Starting data analysis", "info")
 analysis_result = analyze_data(transformed_data)

 return {
 "error": None,
 "result": {
 "original_count": len(raw_data),
 "processed_count": len(transformed_data),
 "analysis": analysis_result,
 "config_used": clean_config,
 "processed_at": get_current_time()
 }
 }

# Helper functions
def clean_data(data: list, config: dict) -> list:
 """Clean data according to configuration."""
 cleaned = []
 for item in data:
 if config["remove_nulls"] and item is None:
 continue
 if config["normalize"] and isinstance(item, str):
 item = item.lower().strip()
 cleaned.append(item)
 return cleaned

def validate_data(data: list) -> dict:
 """Validate processed data."""
 if not data:
 return {"valid": false, "error": "Empty dataset"}

 # Check for required fields, data types, etc.
 for i, item in enumerate(data):
 if item is None:
 return {"valid": false, "error": f"Null item at index {i}"}

 return {"valid": true, "error": None}

def transform_data(data: list, config: dict) -> list:
 """Transform data for analysis."""
 # Apply transformations based on config
 transformed = []
 for item in data:
 # Example transformation
 if isinstance(item, str):
 transformed.append({"text": item, "length": len(item)})
 else:
 transformed.append({"value": item, "type": type(item).__name__})
 return transformed

def analyze_data(data: list) -> dict:
 """Analyze transformed data."""
 return {
 "total_items": len(data),
 "item_types": list(set(item.get("type", "text") for item in data)),
 "average_length": sum(item.get("length", 0) for item in data) / len(data)
 }
```

#### AI-Powered Analysis Function
```dana
def ai_powered_analysis(content: str, analysis_type: str,
 context: dict = None) -> dict:
 """Perform comprehensive AI analysis with context."""

 # Default context
 if context is None:
 context = {
 "temperature": 0.5,
 "max_tokens": 1000,
 "include_confidence": true
 }

 # Prepare analysis prompt
 base_prompt = f"Perform {analysis_type} analysis on the following content:"
 full_prompt = f"{base_prompt}\n\nContent: {content}"

 if context.get("include_confidence"):
 full_prompt += "\n\nPlease include confidence scores in your analysis."

 # Log analysis start
 analysis_id = generate_analysis_id()
 log(f"Starting AI analysis {analysis_id}: {analysis_type}", "info")

 # Store analysis state
 private:current_analysis = {
 "id": analysis_id,
 "type": analysis_type,
 "content_length": len(content),
 "start_time": get_current_time()
 }

 # Perform AI reasoning
 try:
 ai_result = reason(full_prompt, {
 "temperature": context["temperature"],
 "max_tokens": context["max_tokens"]
 })

 # Process AI result
 processed_result = process_ai_result(ai_result, analysis_type)

 # Update analysis state
 private:current_analysis["status"] = "completed"
 private:current_analysis["end_time"] = get_current_time()

 # Log completion
 log(f"AI analysis {analysis_id} completed successfully", "info")

 return {
 "success": true,
 "analysis_id": analysis_id,
 "type": analysis_type,
 "result": processed_result,
 "metadata": {
 "content_length": len(content),
 "context_used": context,
 "processing_time": calculate_processing_time(
 private:current_analysis["start_time"],
 private:current_analysis["end_time"]
 )
 }
 }

 except Exception as e:
 # Handle analysis errors
 private:current_analysis["status"] = "failed"
 private:current_analysis["error"] = str(e)

 log(f"AI analysis {analysis_id} failed: {e}", "error")

 return {
 "success": false,
 "analysis_id": analysis_id,
 "error": str(e),
 "metadata": {
 "content_length": len(content),
 "context_used": context
 }
 }

def process_ai_result(ai_result: str, analysis_type: str) -> dict:
 """Process raw AI result based on analysis type."""
 processed = {
 "raw_result": ai_result,
 "analysis_type": analysis_type,
 "processed_at": get_current_time()
 }

 # Type-specific processing
 if analysis_type == "sentiment":
 processed["sentiment"] = extract_sentiment(ai_result)
 elif analysis_type == "summary":
 processed["summary"] = extract_summary(ai_result)
 elif analysis_type == "classification":
 processed["categories"] = extract_categories(ai_result)

 return processed

def generate_analysis_id() -> str:
 """Generate unique analysis ID."""
 import random
 return f"analysis_{random.randint(1000, 9999)}_{get_current_time()}"

def calculate_processing_time(start_time: str, end_time: str) -> float:
 """Calculate processing time in seconds."""
 # Simplified time calculation
 return 1.5 # Placeholder implementation
```

---

## Implementation Details

### Function Registry
```python
# Function lookup hierarchy implementation
class FunctionRegistry:
 def __init__(self):
 self.user_functions = {} # Highest priority
 self.core_functions = {} # Medium priority (protected)
 self.builtin_functions = {} # Lowest priority

 def resolve_function(self, name: str):
 # 1. Check user-defined functions first
 if name in self.user_functions:
 return self.user_functions[name]

 # 2. Check core functions (cannot be overridden)
 if name in self.core_functions:
 return self.core_functions[name]

 # 3. Check built-in functions
 if name in self.builtin_functions:
 return self.builtin_functions[name]

 raise NameError(f"Function '{name}' not found")
```

### Type Checking
```python
# Function parameter type validation
def validate_function_call(function_def, args, kwargs):
 """Validate function call against type hints."""
 for i, (param, arg) in enumerate(zip(function_def.parameters, args)):
 if param.type_hint:
 expected_type = param.type_hint.name
 actual_type = get_dana_type(arg)
 if not is_compatible_type(expected_type, actual_type):
 raise TypeError(
 f"Parameter {param.name} expects {expected_type}, "
 f"got {actual_type}"
 )
```

### Import Resolution
```python
# Module import system
class ImportResolver:
 def resolve_dana_module(self, module_path: str):
 """Resolve Dana module import."""
 file_path = f"{module_path}.na"
 if os.path.exists(file_path):
 return parse_and_execute_dana_file(file_path)
 raise ImportError(f"Dana module '{module_path}' not found")

 def resolve_python_module(self, module_path: str):
 """Resolve Python module import."""
 module_name = module_path.replace(".py", "")
 return importlib.import_module(module_name)
```

---

## See Also

- [Core Functions](core-functions.md) - Essential Dana functions like `reason()`, `log()`, `print()`
- [Built-in Functions](built-in-functions.md) - Pythonic built-in functions with type validation
- [Type System](type-system.md) - Type annotations for function parameters and returns
- [Scoping System](scoping.md) - Variable scopes and context inheritance

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>