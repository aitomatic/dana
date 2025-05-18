<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)

# DANA Function Calls: User Guide

This guide explains how to use and create functions in DANA, from the most common and simple (defining and calling DANA functions in the same file) to more advanced topics like importing modules and integrating Python code. Each section starts with examples, followed by explanations.

---

## 1. Defining and Calling DANA Functions (Same Module)

**Example:**
```dana
func double(x):
    return x * 2

result = double(5)
```
- Define functions using the `func` keyword.
- Call them directly in your DANA code.
- This is the most common and simplest use case.

---

## 2. Importing and Using DANA Functions from Other Modules

**With alias:**
```dana
import "my_utils.na" as util
result = util.double(10)
```
**Without alias:**
```dana
import "my_utils.na"
result = double(10)
```
- Use `import` to bring in functions from other DANA files.
- Use `as` to avoid name collisions or for clarity.

---

## 3. Importing and Using Python Functions

**With alias:**
```dana
import "my_python_module.py" as py
sum = py.add(1, 2)
product = py.multiply(3, 4)
```
**Without alias:**
```dana
import "my_python_module.py"
sum = add(1, 2)
product = multiply(3, 4)
```
- DANA infers the type of import from the file extension (`.py` for Python, `.na` for DANA).
- All functions from the Python module are available as `py.function_name` (with alias) or globally (without alias).

---

## 4. DANA-aware Python Functions

**Python (my_python_module.py):**
```python
def reason(context, prompt):
    return f"You asked: {prompt}"
```
**DANA:**
```dana
import "my_python_module.py"
answer = reason("What is the capital of France?")
```
- Python functions that accept the DANA context as their first argument can access public variables and, if permitted, private, local, or system variables.

---

## 5. Variable Passing

### 5.1 What Variables Are Passed Automatically?
**Example:**
```dana
x = 10
y = 20
timezone = "UTC"

result = py.add(x, 5)
# py.add receives x and 5, but not y unless explicitly passed
```
- All public variables are automatically available to every function call.
- Only allowlisted system variables (e.g., timezone) are available by default. Others require explicit opt-in.
- Private/local variables are not passed unless you explicitly allow them.

### 5.2 Explicitly Passing Variables
**Example:**
```dana
result = py.add(x, y, __with_private__=["token"], __with_local__=["temp"], __with_system__=["timezone"])
```
This passes `x`, `y`, all public variables, and the specified private, local, and system variables to `py.add`.

---

## 6. Security & Best Practices
**Example:**
```dana
# Safe: only public variables
result = py.add(x, y)

# Explicitly passing sensitive data (use with care)
result = py.add(x, y, __with_private__=["secret"])
```
- Only public variables are passed by default.
- Pass private, local, or sensitive system variables only when needed.
- Review function documentation to understand what context it may access.

---

## 7. Advanced: Import Syntax and Best Practices
- Use `as` for larger projects or when importing multiple modules to avoid naming conflicts and for clarity.
- Omit `as` for simple scripts or when you want all functions globally available and are sure there are no conflicts.

**Summary Table:**

| Import Syntax                        | DANA Call Style         | Namespace/Prefix | Collision Risk | Use Case                        |
|--------------------------------------|-------------------------|------------------|---------------|----------------------------------|
| `import "foo.py" as bar`             | `bar.func(...)`         | Yes              | Low           | Many modules, avoid collisions   |
| `import "foo.py"`                    | `func(...)`             | No (global)      | Higher        | Simple scripts, few modules      |
| `import "foo.na" as bar`             | `bar.func(...)`         | Yes              | Low           | Many modules, avoid collisions   |
| `import "foo.na"`                    | `func(...)`             | No (global)      | Higher        | Simple scripts, few modules      |

---

## 8. Future Features
- In the future, DANA will support automatic mapping of context variables to function arguments using Predict-and-ErrorCorrect (P&E) magic. For now, be explicit for maximum control and security.

---

## 9. More Information
For more details, see the [design-guide.md](./design-guide.md) document.

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>