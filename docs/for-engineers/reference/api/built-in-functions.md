<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md) | [For Engineers](../README.md) | [Reference](README.md) | [API Reference](README.md)

# Built-in Functions API Reference

Dana provides a comprehensive set of Pythonic built-in functions that are automatically available in all Dana code. These functions provide familiar Python-like functionality while maintaining Dana's security and type safety principles.

## Table of Contents
- [Overview](#overview)
- [Numeric Functions](#numeric-functions)
- [Type Conversion Functions](#type-conversion-functions)
- [Collection Functions](#collection-functions)
- [Logic Functions](#logic-functions)
- [Range and Iteration](#range-and-iteration)
- [Function Lookup Precedence](#function-lookup-precedence)
- [Type Safety and Validation](#type-safety-and-validation)
- [Security Model](#security-model)
- [Implementation Status](#implementation-status)

---

## Overview

### Key Features
- **15+ Built-in Functions**: Including `len()`, `sum()`, `max()`, `min()`, `abs()`, `round()`, type conversion functions, and collection utilities
- **Dynamic Function Factory**: Central dispatch approach for efficient management and extensibility
- **Multi-Layered Security**: Explicit blocking of dangerous functions with detailed security rationales
- **Type Safety**: Comprehensive type validation with clear error messages
- **Function Lookup Precedence**: User functions → Core functions → Built-in functions

### Quick Reference

| Category | Functions | Example |
|----------|-----------|---------|
| **Numeric** | `len()`, `sum()`, `max()`, `min()`, `abs()`, `round()` | `sum([1, 2, 3])` → `6` |
| **Type Conversion** | `int()`, `float()`, `bool()` | `int("42")` → `42` |
| **Collections** | `sorted()`, `reversed()`, `enumerate()`, `list()` | `sorted([3, 1, 2])` → `[1, 2, 3]` |
| **Logic** | `all()`, `any()` | `all([true, 1, "yes"])` → `true` |
| **Range** | `range()` | `range(1, 4)` → `[1, 2, 3]` |

---

## Numeric Functions

### `len(obj: any) -> int` {#len}

Returns the length of sequences and collections.

**Parameters:**
- `obj: any` - The object to measure (must be `list`, `dict`, `str`, or `tuple`)

**Returns:** `int` - The number of items in the object

**Examples:**
```dana
# Lists
numbers: list = [1, 2, 3, 4, 5]
count: int = len(numbers)  # Returns 5

# Strings
name: str = "Dana"
name_length: int = len(name)  # Returns 4

# Dictionaries
user_data: dict = {"name": "Alice", "age": 25, "role": "engineer"}
field_count: int = len(user_data)  # Returns 3

# Tuples
coordinates: tuple = (10, 20, 30)
dimension_count: int = len(coordinates)  # Returns 3

# Empty collections
empty_list: list = []
empty_count: int = len(empty_list)  # Returns 0
```

**Type Validation:** Accepts `list`, `dict`, `str`, `tuple`

### `sum(iterable: list) -> any` {#sum}

Returns the sum of a sequence of numbers.

**Parameters:**
- `iterable: list` - A list or tuple of numeric values

**Returns:** `any` - The sum of all values (type depends on input types)

**Examples:**
```dana
# Integer lists
numbers: list = [1, 2, 3, 4, 5]
total: int = sum(numbers)  # Returns 15

# Float lists
prices: list = [10.99, 25.50, 8.75]
total_price: float = sum(prices)  # Returns 45.24

# Mixed numeric types
mixed: list = [1, 2.5, 3, 4.7]
mixed_sum: float = sum(mixed)  # Returns 11.2

# Empty list
empty: list = []
zero: int = sum(empty)  # Returns 0

# Tuples work too
tuple_data: tuple = (10, 20, 30)
tuple_sum: int = sum(tuple_data)  # Returns 60
```

**Type Validation:** Accepts `list`, `tuple` containing numeric values

### `max(*args: any) -> any` {#max}

Returns the largest item in an iterable.

**Parameters:**
- `*args: any` - A list or tuple of comparable values

**Returns:** `any` - The maximum value from the input

**Examples:**
```dana
# Integer lists
scores: list = [85, 92, 78, 96, 88]
highest_score: int = max(scores)  # Returns 96

# Float lists
temperatures: list = [98.6, 99.1, 97.8, 100.2]
max_temp: float = max(temperatures)  # Returns 100.2

# Mixed numeric types
mixed: list = [1, 2.5, 3, 4.7]
maximum: float = max(mixed)  # Returns 4.7

# Single element
single: list = [42]
only_value: int = max(single)  # Returns 42

# Negative numbers
negatives: list = [-5, -2, -8, -1]
least_negative: int = max(negatives)  # Returns -1
```

**Type Validation:** Accepts `list`, `tuple` containing comparable values

### `min(*args: any) -> any` {#min}

Returns the smallest item in an iterable.

**Parameters:**
- `*args: any` - A list or tuple of comparable values

**Returns:** `any` - The minimum value from the input

**Examples:**
```dana
# Integer lists
scores: list = [85, 92, 78, 96, 88]
lowest_score: int = min(scores)  # Returns 78

# Float lists
temperatures: list = [98.6, 99.1, 97.8, 100.2]
min_temp: float = min(temperatures)  # Returns 97.8

# Mixed numeric types
mixed: list = [1, 2.5, 3, 4.7]
minimum: int = min(mixed)  # Returns 1

# Negative numbers
negatives: list = [-5, -2, -8, -1]
most_negative: int = min(negatives)  # Returns -8
```

**Type Validation:** Accepts `list`, `tuple` containing comparable values

### `abs(x: any) -> any` {#abs}

Returns the absolute value of a number.

**Parameters:**
- `x: any` - A numeric value (`int` or `float`)

**Returns:** `any` - The absolute value (same type as input)

**Examples:**
```dana
# Positive numbers (unchanged)
positive_int: int = abs(5)  # Returns 5
positive_float: float = abs(3.14)  # Returns 3.14

# Negative numbers (made positive)
negative_int: int = abs(-5)  # Returns 5
negative_float: float = abs(-3.14)  # Returns 3.14

# Zero
zero_int: int = abs(0)  # Returns 0
zero_float: float = abs(0.0)  # Returns 0.0

# Use in calculations
distance: float = abs(point_a - point_b)
error_magnitude: float = abs(expected - actual)
```

**Type Validation:** Accepts `int`, `float`

### `round(x: float, digits: int = 0) -> any` {#round}

Rounds a number to a given precision.

**Parameters:**
- `x: float` - The number to round
- `digits: int` - Number of decimal places (default: 0)

**Returns:** `any` - The rounded number

**Examples:**
```dana
# Basic rounding (to nearest integer)
pi: float = 3.14159
rounded_pi: int = round(pi)  # Returns 3

# Rounding to decimal places
precise_pi: float = round(pi, 2)  # Returns 3.14
very_precise: float = round(pi, 4)  # Returns 3.1416

# Rounding with integers
int_value: int = 42
rounded_int: int = round(int_value)  # Returns 42

# Negative numbers
negative: float = -3.7
rounded_negative: int = round(negative)  # Returns -4

# Banker's rounding (Python's default)
half_value: float = 3.5
banker_round: int = round(half_value)  # Returns 4
```

**Type Validation:** Accepts `float`, `int`

---

## Type Conversion Functions

### `int(x: any) -> int` {#int}

Converts a value to an integer.

**Parameters:**
- `x: any` - Value to convert (`str`, `float`, or `bool`)

**Returns:** `int` - The integer representation

**Examples:**
```dana
# String to integer
number_string: str = "42"
number_int: int = int(number_string)  # Returns 42

# Float to integer (truncates decimal)
decimal: float = 3.14159
truncated: int = int(decimal)  # Returns 3

# Boolean to integer
true_value: bool = true
false_value: bool = false
true_int: int = int(true_value)   # Returns 1
false_int: int = int(false_value) # Returns 0

# Negative numbers
negative_string: str = "-25"
negative_int: int = int(negative_string)  # Returns -25
```

**Type Validation:** Accepts `str`, `float`, `bool`

### `float(x: any) -> float` {#float}

Converts a value to a floating-point number.

**Parameters:**
- `x: any` - Value to convert (`str`, `int`, or `bool`)

**Returns:** `float` - The floating-point representation

**Examples:**
```dana
# String to float
decimal_string: str = "3.14159"
decimal_float: float = float(decimal_string)  # Returns 3.14159

# Integer to float
whole_number: int = 42
float_number: float = float(whole_number)  # Returns 42.0

# Boolean to float
true_value: bool = true
false_value: bool = false
true_float: float = float(true_value)   # Returns 1.0
false_float: float = float(false_value) # Returns 0.0

# Scientific notation
scientific: str = "1.23e-4"
scientific_float: float = float(scientific)  # Returns 0.000123
```

**Type Validation:** Accepts `str`, `int`, `bool`

### `bool(x: any) -> bool` {#bool}

Converts a value to a boolean.

**Parameters:**
- `x: any` - Value to convert (`str`, `int`, `float`, `list`, or `dict`)

**Returns:** `bool` - The boolean representation

**Examples:**
```dana
# Numbers to boolean
zero_int: int = 0
nonzero_int: int = 42
zero_bool: bool = bool(zero_int)     # Returns false
nonzero_bool: bool = bool(nonzero_int) # Returns true

# Strings to boolean
empty_string: str = ""
nonempty_string: str = "hello"
empty_bool: bool = bool(empty_string)     # Returns false
nonempty_bool: bool = bool(nonempty_string) # Returns true

# Collections to boolean
empty_list: list = []
nonempty_list: list = [1, 2, 3]
empty_dict: dict = {}
nonempty_dict: dict = {"key": "value"}

empty_list_bool: bool = bool(empty_list)     # Returns false
nonempty_list_bool: bool = bool(nonempty_list) # Returns true
empty_dict_bool: bool = bool(empty_dict)     # Returns false
nonempty_dict_bool: bool = bool(nonempty_dict) # Returns true
```

**Type Validation:** Accepts `str`, `int`, `float`, `list`, `dict`

---

## Collection Functions

### `sorted(iterable: list) -> list` {#sorted}

Returns a new sorted list from an iterable.

**Parameters:**
- `iterable: list` - A list or tuple to sort

**Returns:** `list` - A new sorted list

**Examples:**
```dana
# Sort numbers
numbers: list = [3, 1, 4, 1, 5, 9, 2, 6]
sorted_numbers: list = sorted(numbers)  # Returns [1, 1, 2, 3, 4, 5, 6, 9]

# Sort strings (alphabetical)
names: list = ["Charlie", "Alice", "Bob", "Diana"]
sorted_names: list = sorted(names)  # Returns ["Alice", "Bob", "Charlie", "Diana"]

# Sort mixed numbers
mixed: list = [3.14, 1, 2.5, 4]
sorted_mixed: list = sorted(mixed)  # Returns [1, 2.5, 3.14, 4]

# Original list unchanged
original: list = [3, 1, 2]
new_sorted: list = sorted(original)
# original is still [3, 1, 2]
# new_sorted is [1, 2, 3]
```

**Type Validation:** Accepts `list`, `tuple`

### `reversed(iterable: list) -> list` {#reversed}

Returns a new list with elements in reverse order.

**Parameters:**
- `iterable: list` - A list, tuple, or string to reverse

**Returns:** `list` - A new list with reversed elements

**Examples:**
```dana
# Reverse a list
numbers: list = [1, 2, 3, 4, 5]
reversed_numbers: list = reversed(numbers)  # Returns [5, 4, 3, 2, 1]

# Reverse a string (returns list of characters)
word: str = "hello"
reversed_chars: list = reversed(word)  # Returns ["o", "l", "l", "e", "h"]

# Reverse a tuple
coordinates: tuple = (10, 20, 30)
reversed_coords: list = reversed(coordinates)  # Returns [30, 20, 10]

# Original unchanged
original: list = [1, 2, 3]
new_reversed: list = reversed(original)
# original is still [1, 2, 3]
# new_reversed is [3, 2, 1]
```

**Type Validation:** Accepts `list`, `tuple`, `str`

### `enumerate(iterable: list) -> list` {#enumerate}

Returns a list of [index, value] pairs.

**Parameters:**
- `iterable: list` - A list, tuple, or string to enumerate

**Returns:** `list` - A list of [index, value] pairs

**Examples:**
```dana
# Enumerate a list
fruits: list = ["apple", "banana", "cherry"]
enumerated: list = enumerate(fruits)
# Returns [[0, "apple"], [1, "banana"], [2, "cherry"]]

# Enumerate a string
word: str = "abc"
char_indices: list = enumerate(word)
# Returns [[0, "a"], [1, "b"], [2, "c"]]

# Use in loops (conceptual - actual loop syntax may vary)
scores: list = [85, 92, 78]
indexed_scores: list = enumerate(scores)
# Returns [[0, 85], [1, 92], [2, 78]]

# Empty collections
empty: list = []
empty_enum: list = enumerate(empty)  # Returns []
```

**Type Validation:** Accepts `list`, `tuple`, `str`

### `list(iterable: any) -> list` {#list}

Converts an iterable to a list.

**Parameters:**
- `iterable: any` - An iterable object (tuple, string, range, etc.)

**Returns:** `list` - A new list containing the elements

**Examples:**
```dana
# Convert tuple to list
coordinates: tuple = (10, 20, 30)
coord_list: list = list(coordinates)  # Returns [10, 20, 30]

# Convert string to list of characters
word: str = "hello"
char_list: list = list(word)  # Returns ["h", "e", "l", "l", "o"]

# Convert range to list
number_range: list = range(5)
numbers: list = list(number_range)  # Returns [0, 1, 2, 3, 4]

# Copy a list (creates new list)
original: list = [1, 2, 3]
copy: list = list(original)  # Returns [1, 2, 3] (new list)
```

**Type Validation:** Accepts `list`, `tuple`, `str`, `range`, iterators

---

## Logic Functions

### `all(iterable: list) -> bool` {#all}

Returns `true` if all elements in the iterable are truthy.

**Parameters:**
- `iterable: list` - A list or tuple of values to check

**Returns:** `bool` - `true` if all elements are truthy, `false` otherwise

**Examples:**
```dana
# All truthy values
all_true: list = [true, 1, "yes", [1, 2]]
result: bool = all(all_true)  # Returns true

# Contains falsy value
mixed: list = [true, 1, "", "yes"]  # Empty string is falsy
result: bool = all(mixed)  # Returns false

# All falsy values
all_false: list = [false, 0, "", []]
result: bool = all(all_false)  # Returns false

# Empty list (special case)
empty: list = []
result: bool = all(empty)  # Returns true (vacuous truth)

# Numeric values
numbers: list = [1, 2, 3, 4, 5]  # All non-zero
result: bool = all(numbers)  # Returns true

numbers_with_zero: list = [1, 2, 0, 4, 5]  # Contains zero
result: bool = all(numbers_with_zero)  # Returns false
```

**Type Validation:** Accepts `list`, `tuple`

### `any(iterable: list) -> bool` {#any}

Returns `true` if any element in the iterable is truthy.

**Parameters:**
- `iterable: list` - A list or tuple of values to check

**Returns:** `bool` - `true` if any element is truthy, `false` otherwise

**Examples:**
```dana
# Contains truthy values
mixed: list = [false, 0, "", "yes"]  # "yes" is truthy
result: bool = any(mixed)  # Returns true

# All falsy values
all_false: list = [false, 0, "", []]
result: bool = any(all_false)  # Returns false

# All truthy values
all_true: list = [true, 1, "yes", [1, 2]]
result: bool = any(all_true)  # Returns true

# Empty list (special case)
empty: list = []
result: bool = any(empty)  # Returns false

# Single truthy element
single_true: list = [false, false, true, false]
result: bool = any(single_true)  # Returns true
```

**Type Validation:** Accepts `list`, `tuple`

---

## Range and Iteration

### `range(start: int, stop: int = None, step: int = 1) -> list` {#range}

Generates a list of numbers in a specified range.

**Parameters:**
- `start: int` - Starting number (or stop if only one argument)
- `stop: int` - Ending number (exclusive, optional)
- `step: int` - Step size (default: 1, optional)

**Returns:** `list` - A list of integers in the specified range

**Examples:**
```dana
# Single argument (0 to n-1)
numbers: list = range(5)  # Returns [0, 1, 2, 3, 4]

# Two arguments (start to stop-1)
numbers: list = range(2, 7)  # Returns [2, 3, 4, 5, 6]

# Three arguments (start, stop, step)
evens: list = range(0, 10, 2)  # Returns [0, 2, 4, 6, 8]
odds: list = range(1, 10, 2)   # Returns [1, 3, 5, 7, 9]

# Negative step (countdown)
countdown: list = range(10, 0, -1)  # Returns [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

# Empty ranges
empty: list = range(0)     # Returns []
empty2: list = range(5, 2) # Returns [] (start >= stop with positive step)

# Use with other functions
indices: list = range(len([10, 20, 30]))  # Returns [0, 1, 2]
```

**Type Validation:** Accepts `int` parameters

---

## Function Lookup Precedence

Dana follows a clear precedence order when resolving function calls:

1. **User-defined functions** (highest priority) - Functions defined in the current Dana file
2. **Core functions** (medium priority) - Essential Dana functions like `reason()`, `log()`, `print()`
3. **Built-in functions** (lowest priority) - Pythonic built-ins documented above

This ensures that:
- User code can override any built-in function if needed
- Core Dana functions maintain their essential behavior
- Built-in functions provide familiar Python-like functionality

**Example:**
```dana
# User-defined function overrides built-in
def len(obj):
    return "custom length function"

# This calls the user-defined function, not the built-in
result = len([1, 2, 3])  # Returns "custom length function"

# Core functions like reason() cannot be overridden for security
analysis = reason("What should I do?")  # Always calls core function

# Built-ins are available when not overridden
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)  # Calls built-in sum() function
```

---

## Type Safety and Validation

All built-in functions include comprehensive type validation:

### Validation Features
- **Strict type checking** - Functions only accept specified types
- **Clear error messages** - Helpful feedback when types don't match
- **Runtime validation** - Types are checked at function call time
- **Multiple signatures** - Some functions accept multiple valid type combinations

### Error Examples
```dana
# Type validation errors
len(42)           # TypeError: Invalid arguments for 'len'
sum("not a list") # TypeError: Invalid arguments for 'sum'
int([1, 2, 3])    # TypeError: Invalid arguments for 'int'

# Valid type combinations
len([1, 2, 3])    # ✅ Valid: list
len("hello")      # ✅ Valid: string
len({"a": 1})     # ✅ Valid: dict

sum([1, 2, 3])    # ✅ Valid: list of numbers
sum((1, 2, 3))    # ✅ Valid: tuple of numbers

int("42")         # ✅ Valid: string
int(3.14)         # ✅ Valid: float
int(true)         # ✅ Valid: boolean
```

---

## Security Model

### Security Architecture
- **25+ Blocked Functions**: Dangerous functions like `eval()`, `exec()`, `open()`, `globals()` are explicitly blocked
- **Threat Mitigation**: Protection against arbitrary code execution, file system access, memory manipulation, and introspection abuse
- **Sandboxed Execution**: All functions execute within Dana's secure sandbox environment
- **Security Reporting**: Comprehensive reporting of function restrictions and security measures

### Blocked Functions (Security)
The following Python built-ins are **explicitly blocked** for security:

| Category | Blocked Functions | Reason |
|----------|------------------|---------|
| **Code Execution** | `eval()`, `exec()`, `compile()` | Arbitrary code execution |
| **File System** | `open()`, `input()` | File system access |
| **Introspection** | `globals()`, `locals()`, `vars()`, `dir()` | Memory/scope inspection |
| **System Access** | `breakpoint()`, `help()` | System interaction |

### Safe Alternatives
Instead of blocked functions, use Dana's secure alternatives:

```dana
# ❌ Blocked: eval("1 + 2")
# ✅ Safe: Use Dana expressions directly
result = 1 + 2

# ❌ Blocked: open("file.txt")
# ✅ Safe: Use Dana's secure file operations (when available)

# ❌ Blocked: globals()
# ✅ Safe: Use Dana's scoping system
public:shared_data = {"key": "value"}
```

---

## Implementation Status

| Function | Type Signature | Status | Notes |
|----------|---------------|--------|-------|
| `len()` | `(obj: any) -> int` | ✅ Complete | Supports list, dict, str, tuple |
| `sum()` | `(iterable: list) -> any` | ✅ Complete | Supports list, tuple of numbers |
| `max()` | `(*args: any) -> any` | ✅ Complete | Supports list, tuple of comparable values |
| `min()` | `(*args: any) -> any` | ✅ Complete | Supports list, tuple of comparable values |
| `abs()` | `(x: any) -> any` | ✅ Complete | Supports int, float |
| `round()` | `(x: float, digits: int = 0) -> any` | ✅ Complete | Supports float, int with optional precision |
| `int()` | `(x: any) -> int` | ✅ Complete | Converts str, float, bool to int |
| `float()` | `(x: any) -> float` | ✅ Complete | Converts str, int, bool to float |
| `bool()` | `(x: any) -> bool` | ✅ Complete | Converts various types to bool |
| `sorted()` | `(iterable: list) -> list` | ✅ Complete | Supports list, tuple |
| `reversed()` | `(iterable: list) -> list` | ✅ Complete | Supports list, tuple, str |
| `enumerate()` | `(iterable: list) -> list` | ✅ Complete | Supports list, tuple, str |
| `list()` | `(iterable: any) -> list` | ✅ Complete | Converts iterables to list |
| `all()` | `(iterable: list) -> bool` | ✅ Complete | Supports list, tuple |
| `any()` | `(iterable: list) -> bool` | ✅ Complete | Supports list, tuple |
| `range()` | `(start: int, stop: int = None, step: int = 1) -> list` | ✅ Complete | Multiple signature support |

**📖 For detailed implementation and security analysis, see: [Pythonic Built-in Functions](../../../../.ai-only/pythonic-builtins.md)**

---

## See Also

- **[Core Functions](core-functions.md)** - Essential Dana functions like `reason()`, `log()`, `print()`
- **[Type System](type-system.md)** - Complete type system documentation
- **[Function Calling](function-calling.md)** - Function calling and import system
- **[Scoping System](scoping.md)** - Variable scopes and security model

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 