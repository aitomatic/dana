# EagerPromise Transparency Guide

## Overview

EagerPromise is designed to be transparent - it should behave like its resolved value in most operations. However, there are important limitations and edge cases that developers should be aware of.

## What Works (Transparent Operations)

### ✅ **Equality and Comparison**
```python
# All these work correctly
assert result.result == 42           # Value equality
assert result.result != 43           # Inequality
assert result.result > 40            # Greater than
assert result.result < 50            # Less than
assert result.result >= 42           # Greater than or equal
assert result.result <= 42           # Less than or equal
```

### ✅ **Arithmetic Operations**
```python
# All arithmetic operations trigger transparency
assert result.result + 5 == 15       # Addition
assert result.result - 3 == 7        # Subtraction
assert result.result * 2 == 20       # Multiplication
assert result.result / 2 == 5.0      # Division
assert result.result ** 2 == 100     # Exponentiation
assert result.result % 3 == 1        # Modulo
```

### ✅ **Attribute and Method Access**
```python
# Method calls work transparently
assert result.result.upper() == "HELLO WORLD"  # String methods
assert result.result.strip().upper() == "HELLO WORLD"  # Method chaining
assert result.result["name"] == "Alice"        # Dictionary access
assert result.result[2] == 3                   # List indexing
assert len(result.result) == 5                 # Length
assert 3 in result.result                      # Containment
```

### ✅ **Boolean Operations**
```python
# Boolean operations work
assert bool(result.result)            # Boolean conversion
assert result.result and True         # AND operation
assert result.result or False         # OR operation
assert not (not result.result)        # NOT operation
```

### ✅ **Function Calls**
```python
# EagerPromise can be passed to functions
def test_function(x):
    return x * 2

value = some_function()  # Returns EagerPromise
result = test_function(value)  # Receives resolved value
assert result == 84
```

## What Doesn't Work (Transparency Limitations)

### ❌ **Identity Comparisons (`is`)**
```python
# These FAIL - identity doesn't work
assert result.result is True          # ❌ Fails
assert result.result is None          # ❌ Fails
assert result.result is [1, 2, 3]     # ❌ Fails

# Use equality instead
assert result.result == True          # ✅ Works
assert result.result == None          # ✅ Works
assert result.result == [1, 2, 3]     # ✅ Works
```

### ❌ **Type Checking (`isinstance`)**
```python
# These FAIL - type checking doesn't work
assert isinstance(result.result, str)  # ❌ Fails
assert isinstance(result.result, int)  # ❌ Fails

# Use string representation instead
assert "test string" in str(result.result)  # ✅ Works
```

### ❌ **Built-in Functions**
```python
# These FAIL - built-ins don't trigger transparency
assert int(result.result) == 10       # ❌ TypeError
assert float(result.result) == 10.5   # ❌ TypeError
assert abs(result.result) == 10.5     # ❌ TypeError
assert round(result.result) == 10     # ❌ TypeError

# Use arithmetic operations instead
assert result.result + 0 == 10.5      # ✅ Works
assert result.result * 1 == 10.5      # ✅ Works
```

### ❌ **String Conversion (`str()`)**
```python
# This shows the wrapper, not the value
assert str(result.result) == "hello world"  # ❌ Fails
# Actual: "EagerPromise['hello world']"

# Use string containment instead
assert "hello world" in str(result.result)  # ✅ Works
```

## Best Practices

### 1. **Use Equality, Not Identity**
```python
# ❌ Don't do this
if result.result is True:
    pass

# ✅ Do this instead
if result.result == True:
    pass
```

### 2. **Avoid Type Checking**
```python
# ❌ Don't do this
if isinstance(result.result, str):
    pass

# ✅ Do this instead
if "expected_value" in str(result.result):
    pass
```

### 3. **Use Arithmetic for Numeric Operations**
```python
# ❌ Don't do this
value = int(result.result)

# ✅ Do this instead
value = result.result + 0  # Triggers transparency
value = int(value)         # Now safe to convert
```

### 4. **Test for Specific Values**
```python
# ❌ Don't do this
assert str(result.result) == "expected"

# ✅ Do this instead
assert "expected" in str(result.result)
# Or better yet, use direct equality
assert result.result == "expected"
```

## Why These Limitations Exist

### **Identity Comparisons (`is`)**
- `is` checks object identity, not value
- `EagerPromise[True]` and `True` are different objects
- This is by design - promises are wrappers

### **Type Checking (`isinstance`)**
- `isinstance()` checks the wrapper type, not the resolved value
- Would require special handling in Python's type system
- Not practical to implement

### **Built-in Functions**
- Functions like `int()`, `float()`, `abs()` don't know about EagerPromise
- Would require monkey-patching all built-ins
- Arithmetic operations provide a workaround

### **String Conversion**
- `str()` shows the wrapper to avoid deadlocks
- Calling `_ensure_resolved()` in `__str__` could cause infinite recursion
- String containment provides a safe alternative

## Testing EagerPromise Transparency

We have a comprehensive test suite at `tests/unit/concurrency/test_eager_promise_transparency.py` that covers:

- Basic value transparency
- String, boolean, list, dict transparency
- Arithmetic operations
- Function calls and nesting
- Complex object operations
- Edge cases and limitations

Run the tests to verify transparency behavior:
```bash
python -m pytest tests/unit/concurrency/test_eager_promise_transparency.py -v
```

## Summary

EagerPromise provides excellent transparency for most operations, especially:
- **Equality and comparisons** ✅
- **Arithmetic operations** ✅
- **Method calls and attribute access** ✅
- **Boolean operations** ✅
- **Function parameters** ✅

The main limitations are:
- **Identity comparisons** (`is`) ❌
- **Type checking** (`isinstance`) ❌
- **Built-in functions** (`int()`, `float()`, etc.) ❌
- **String conversion** (`str()`) ❌

These limitations are by design and have practical workarounds. The transparency works well for the most common use cases while avoiding potential deadlocks and complexity. 