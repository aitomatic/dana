# DANA Language Syntax Cheatsheet

*Concise reference for essential DANA syntax*

---

## Variables & Data Types
```dana
# Basic assignment (auto-scoped to local)
name = "OpenDXA"
count = 42
active = true
data = none

# F-strings
greeting = f"Hello, {name}!"
status = f"Processing {count} items"

# Scoped assignment
private:agent_status = "ready"
public:temperature = 72.5
system:debug_mode = true
```

## Core Functions
```dana
# AI reasoning
analysis = reason("Analyze this data")
summary = reason("Summarize", context=documents, temperature=0.7)

# Resource loading
websearch = use("mcp", url="http://localhost:8880/websearch")
rag = use("rag", doc_paths=["docs/"], enable_print=False)

# State setting
set("system:agent_status", "ready")
```

## Control Flow
```dana
# Conditionals
if condition:
    action()
elif other_condition:
    other_action()
else:
    default_action()

# Loops
while condition:
    process_item()

for item in items:
    process(item)
```

## Operators
```dana
# Comparison: ==, !=, >, <, >=, <=
if score >= 90:
    grade = "A"

# Logical: and, or, not
if user.authenticated and not system:maintenance_mode:
    allow_access()

# Membership: in (note: "not in" is NOT supported)
if "error" in log_message:
    flag_for_review()

# Arithmetic: +, -, *, /, %
total = price + tax
```

## Structs & Methods
```dana
# Struct definition
struct User:
    name: str
    email: str
    age: int

# Instantiation
user = User(name="Alice", email="alice@example.com", age=30)

# Method definition
def greet(user: User) -> str:
    return f"Hello, {user.name}!"

# Method calling (equivalent)
greeting = user.greet()     # Method syntax
greeting = greet(user)      # Function syntax
```

## Built-in Functions
```dana
# Numeric
len([1, 2, 3])              # → 3
sum([1, 2, 3])              # → 6
max([1, 2, 3])              # → 3
min([1, 2, 3])              # → 1
abs(-5)                     # → 5
round(3.14159, 2)           # → 3.14

# Type conversion
int("42")                   # → 42
float("3.14")               # → 3.14
bool(1)                     # → true

# Collections
sorted([3, 1, 2])           # → [1, 2, 3]
list(range(1, 4))           # → [1, 2, 3]
range(5)                    # → [0, 1, 2, 3, 4]
all([true, 1, "yes"])       # → true
any([false, 0, "text"])     # → true
```

## Python Library Imports
```dana
# Standard library modules (add .py extension)
import math.py
import json.py
import os.py as operating_system
import datetime.py
import threading.py
import time.py

# Third-party libraries
import pandas.py as pd
import numpy.py as np
import uvicorn.py

# From-imports (import specific functions/classes)
from math.py import sqrt, pi
from json.py import dumps as json_dumps
from pandas.py import DataFrame

# Usage examples
pi_value = math.pi                      # → 3.141592653589793
sqrt_result = math.sqrt(16)             # → 4.0
json_string = json.dumps({"key": "value"})
current_dir = operating_system.getcwd()

# Data science workflows
df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
subset = df.iloc[0:2]                   # Pandas slicing
array = np.array([1, 2, 3, 4, 5])
mean_val = np.mean(array)               # → 3.0
```

## Object Method Calls
```dana
# MCP services
websearch = use("mcp", url="http://localhost:8880/websearch")
tools = websearch.list_openai_functions()
results = websearch.search("query")

# RAG services
rag = use("rag", doc_paths=["docs/"], enable_print=False)
answer = rag.retrieve("What is DANA?")

# With statements
with use("mcp", url="http://localhost:8080/sse") as mcp:
    functions = mcp.list_openai_functions()

# Python library objects
df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
filtered = df[df["A"] > 1]              # Pandas filtering
first_row = df.iloc[0]                  # Row selection
```

## Output & Logging
```dana
# Print (log() doesn't work in DANA)
print("Hello, world!")
print(f"Result: {result}")
```

## Collections
```dana
# Lists
items = ["a", "b", "c"]
items.append("d")
items[0]                    # First item
items[-1]                   # Last item

# Dictionaries
data = {"name": "Alice", "age": 25}
data["email"] = "alice@example.com"
name = data.get("name", "Unknown")

# Iteration
for item in items:
    process(item)

for key, value in data.items():
    print(f"{key}: {value}")
```

## Scope Reference
| Scope | Syntax | Usage |
|-------|--------|-------|
| **local** | `variable = value` | Default (preferred) |
| **private** | `private:variable = value` | Agent private |
| **public** | `public:variable = value` | World state |
| **system** | `system:variable = value` | System state |

## DANA Limitations (Not Supported)
```dana
# ❌ These Python features don't work in DANA:

# No "not in" operator
# if item not in list:  # ❌ ERROR

# No "is" operator  
# if value is None:     # ❌ ERROR

# No try/except blocks
# try:                  # ❌ ERROR
#     risky_operation()
# except:
#     handle_error()

# No tuple unpacking
# x, y = point          # ❌ ERROR
# for key, val in items: # ❌ ERROR (use .items())

# No inline if/else (ternary operator)
# result = x if condition else y  # ❌ ERROR

# No generator expressions
# sum([x for x in list])          # ❌ ERROR

# No inline comments
# items = [1, 2, 3]  # comment    # ❌ ERROR

# No multi-import from Python modules
# from math.py import sin, cos, tan      # ❌ ERROR
# Must import individually:
# from math.py import sin
# from math.py import cos

# No log() function
# log("message")                  # ❌ ERROR (use print)
```

## Quick Rules
- **✅ Use:** `private:status = "ready"` (colon notation)
- **❌ Avoid:** `private.status = "ready"` (dot notation)
- **✅ Use:** `f"Hello, {name}!"` (f-strings)
- **❌ Avoid:** `"Hello, " + name` (concatenation)
- **✅ Use:** Type hints in functions
- **✅ Use:** Named arguments for structs
- **✅ Use:** `print()` for output (not `log()`)
- **✅ Use:** `struct` instead of `class`
- **✅ Use:** `import math.py` (Python modules need .py)
- **❌ Avoid:** `import math` (for Python modules)
- **✅ Use:** `import dana_module` (Dana modules no extension)
- **✅ Use:** `from math.py import sqrt` (single imports)
- **❌ Avoid:** `from math.py import sin, cos` (multi-import) 