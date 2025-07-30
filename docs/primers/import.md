# Dana Import System Primer

## TL;DR (1 minute read)

```dana
# math_utils.na
def add(a: int, b: int) -> int: return a + b
def multiply(a: int, b: int) -> int: return a * b
def _complex_calc(): return "private"  # Can't be imported

# main.na
import math_utils
from math_utils import add, multiply
from math_utils import _complex_calc  # ❌ Error - actually private!

result = math_utils.add(5, 3)  # 8
product = multiply(4, 7)       # 28

# Package structure (simpler than Python):
# my_package/        # Directory automatically becomes a package
#   utils.na
#   helpers.na
#   sub_package/      # Nested packages work too
#     more_utils.na
```

---

**What it is**: Python's import system, but simpler. If you know Python imports, you already know 90% of Dana imports. The main differences? Dana uses underscore prefix for privacy instead of Python's complex visibility rules, and directories automatically become packages without needing `__init__.na` files.

## Why Should You Care?

If you're coming from Python, you're probably used to this:

```python
# Python way - clean imports
import math
from utils import format_data
from config import DATABASE_URL

# Usage
result = math.sqrt(16)
formatted = format_data(user_data)
```

But you've also dealt with Python's privacy confusion:

```python
# Python privacy - confusing!
class MyClass:
    def public_method(self):  # Public by default
        return self._private_method()  # Private by convention
    
    def _private_method(self):  # Actually still accessible!
        return "secret"
    
    def __really_private(self):  # Name mangling - really private
        return "really secret"

# In Python, this still works (confusing!)
obj = MyClass()
obj._private_method()  # Works! Convention only
obj.__really_private()  # Fails - name mangled
```

**Dana's import system gives you Python's simplicity with better privacy:**

- **Same familiar syntax**: `import`, `from`, `as` - just like Python
- **Clear privacy**: Underscore prefix actually prevents imports (no confusion!)
- **No boilerplate**: No `__init__.na` required, no `public`/`private` keywords
- **Simpler packages**: Directories automatically become packages (optional `__init__.na` for initialization)

## The Big Picture

```dana
# Your modules look just like Python modules
# math_utils.na
def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b

def _complex_calculation():  # Private - can't be imported
    return "complicated math"

# user_utils.na  
def format_name(first: str, last: str) -> str:
    return f"{first} {last}"

def validate_email(email: str) -> bool:
    return _check_email_format(email)  # Uses private helper

def _check_email_format(email: str) -> bool:  # Private - implementation detail
    return "@" in email

# main.na - imports work exactly like Python
from math_utils import add, multiply
from user_utils import format_name, validate_email

result = add(5, 3)  # 8 - just like Python!
name = format_name("John", "Doe")  # "John Doe"
```

## Why You'll Love This (Python Perspective)

- **Zero learning curve**: If you know Python imports, you know Dana imports
- **Actually private**: Underscore prefix prevents imports (unlike Python's convention)
- **Even simpler packages**: No `__init__.na` required - directories are automatically packages
- **Flexible structure**: Nested folders work exactly like Python, with optional initialization
- **Python interop**: Import `.py` modules seamlessly

## How to Use Imports (Python Style)

### Basic Module Import - Exactly Like Python
```dana
import my_module

# Access through module name
result = my_module.my_function()
```

### Import with Alias - Exactly Like Python
```dana
import my_module as mm

# Access through alias
result = mm.my_function()
```

### From Import - Exactly Like Python
```dana
from my_module import my_function

# Use directly
result = my_function()
```

### Multiple Imports - Exactly Like Python
```dana
from my_module import func1, func2, func3

# Use all directly
result1 = func1()
result2 = func2()
result3 = func3()
```

### Import with Aliases - Exactly Like Python
```dana
from my_module import add, multiply as mult, square as sq

# Use with aliases
sum = add(5, 3)
product = mult(4, 7)
squared = sq(6)
```

## Privacy Rules (The Only Difference from Python)

**Dana uses underscore (`_`) prefix for privacy - and it actually works!**

### ✅ Public (Like Python's Public)
```dana
# In my_module.na
def public_function():
    return "Available for import"

PUBLIC_CONSTANT = "Exportable"

struct DataPoint:
    x: float
    y: float
```

### ❌ Private (Unlike Python - Actually Private!)
```dana
# In my_module.na
def _private_helper():
    return "Internal use only"

_INTERNAL_CONFIG = "Hidden"

struct _InternalState:
    secret: str
```

### Import Behavior (Clear Error Messages)
```dana
# ✅ These work - just like Python
from my_module import public_function, PUBLIC_CONSTANT, DataPoint

# ❌ These fail - unlike Python's confusing behavior
from my_module import _private_helper      # Error: names starting with '_' are private
from my_module import _INTERNAL_CONFIG     # Error: names starting with '_' are private
from my_module import _InternalState       # Error: names starting with '_' are private
```

### Internal Usage Still Works (Like Python)
```dana
# Inside my_module.na - private functions can be used internally
def public_api():
    result = _private_helper()  # ✅ Works within the same module
    return f"Result: {result}"
```

## Real-World Examples (Python-Style)

### Building a Math Library (Like Python's math module)
```dana
# math_utils.na
def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b

def square(x: int) -> int:
    return multiply(x, x)

def _complex_formula():  # Private helper - like Python's internal functions
    return "complicated calculation"

# geometry.na
from math_utils import multiply

def circle_area(radius: float) -> float:
    return 3.14159 * multiply(radius, radius)

def rectangle_area(width: float, height: float) -> float:
    return multiply(width, height)

# main.na - just like importing Python modules
from math_utils import add, square
from geometry import circle_area, rectangle_area

sum = add(5, 3)           # 8
squared = square(4)       # 16
circle = circle_area(5.0) # 78.53975
rect = rectangle_area(3.0, 4.0)  # 12.0
```

### Building a Business App (Like Python's standard library)
```dana
# user_utils.na
def format_name(first: str, last: str) -> str:
    return f"{first} {last}"

def validate_email(email: str) -> bool:
    return _check_email_format(email)

def _check_email_format(email: str) -> bool:  # Private implementation
    return "@" in email and "." in email

# payment_utils.na
def process_payment(amount: float, currency: str) -> bool:
    if _validate_amount(amount):  # Private validation
        return _charge_card(amount, currency)  # Private processing
    return false

def _validate_amount(amount: float) -> bool:  # Private helper
    return amount > 0

def _charge_card(amount: float, currency: str) -> bool:  # Private implementation
    return true  # Simplified for example

# main.na - clean imports like Python
from user_utils import format_name, validate_email
from payment_utils import process_payment

user_name = format_name("Alice", "Smith")  # "Alice Smith"
valid_email = validate_email("alice@example.com")  # true
payment_success = process_payment(99.99, "USD")  # true
```

## Package Structure (Simpler than Python Packages)

### The Big Change: Directory Packages (Revolutionary Simplicity)

**Dana automatically treats directories containing `.na` files as packages!** No more `__init__.na` boilerplate.

```dana
# This just works - no setup needed!
from utils.math import add, multiply
from config.settings import DATABASE_URL
```

### Automatic Directory Packages (Even Simpler than Python)
```
your_package/          # ← Automatically a package (no __init__.na needed!)
└── submodule.na       # Your module
```

### Optional Initialization (When You Need It)
```
your_package/
├── __init__.na        # ← Optional - only if you need initialization code
└── submodule.na       # Your module
```

### Example Project (Simpler than Python Project Structure)
```
project/
├── main.na
├── utils/             # ← Automatically a package
│   ├── math.na        # Public: add(), multiply()
│   └── helpers.na     # Public: format(), Private: _validate()
├── config/            # ← Automatically a package
│   └── settings.na    # Public: DATABASE_URL, Private: _SECRET_KEY
└── advanced/          # ← Package with initialization
    ├── __init__.na    # Optional - for package-level setup
    └── algorithms.na  # Advanced algorithms
```

## Advanced Import Patterns (Python-Style)

### Deep Module Import (Like Python's nested imports)
```dana
import dana.frameworks.corral.curate as curate

# Access through alias
recipe = curate.curate_knowledge_recipe(...)
```

### Python Module Import (Seamless Python interop)
```dana
import json.py as json
import pandas.py as pd

# Use Python modules directly - just like Python!
data = json.loads('{"key": "value"}')
df = pd.DataFrame({"a": [1, 2, 3]})
```

### Framework Modules (Like Python's standard library)
```dana
from dana.frameworks.corral import curate, organize
from dana.frameworks.workflow import core, engine as wf_engine
```

## Environment Setup (Like Python's PYTHONPATH)

### Setting DANAPATH (Like Python's PYTHONPATH)
```bash
# Add paths where Dana should look for modules
export DANAPATH="/path/to/your/modules:$DANAPATH"
```

## What Happens When Things Go Wrong (Python-Style Errors)

### Module Not Found (Like Python's ModuleNotFoundError)
```dana
from missing_module import function
# Error: Dana module 'missing_module' not found
```

### Privacy Violation (Clear error messages - unlike Python)
```dana
from my_module import _private_func
# Error: Cannot import name '_private_func': names starting with '_' are private
```

### Import Syntax Error (Helpful debugging)
```dana
from module import *  # Not supported in Dana
# Error: Unexpected token - Dana doesn't support wildcard imports
```

## Pro Tips (Python Best Practices)

### 1. Use Descriptive Names (Python Style)
```dana
# ✅ Good
import data_processor as dp
from math_utils import calculate_distance

# ❌ Avoid
import x as y
```

### 2. Leverage Privacy (Unlike Python - Actually Works!)
```dana
# ✅ Good module design
def public_api():          # Exportable
    return _internal_logic()

def _internal_logic():     # Private - actually private!
    return "result"
```

### 3. Organize Imports (Python Style)
```dana
# ✅ Good grouping
import system_module
import dana.frameworks.corral.curate as curate

from local_utils import helper_function
from config import DATABASE_URL
```

### 4. Keep Modules Focused (Single Responsibility)
```dana
# ✅ Good - focused modules (like Python's standard library)
# math_utils.na - only math functions
# user_utils.na - only user-related functions
# payment_utils.na - only payment functions

# ❌ Avoid - mixed concerns
# utils.na - math, user, payment, email, database, etc.
```

## Performance Wins (Over Python)

- **Fast lookup**: Direct module resolution
- **Clear boundaries**: No confusion about what's public vs private
- **No runtime magic**: Simple underscore prefix rule
- **Zero boilerplate**: No `__init__.na` files needed for basic packages
- **Instant packages**: Directories automatically become packages

## Before vs After (Python Perspective)

### Python's Confusing Privacy
```python
# Python way - confusing!
class MyClass:
    def public_method(self):
        return self._private_method()  # Convention only
    
    def _private_method(self):  # Still accessible!
        return "secret"

obj = MyClass()
obj._private_method()  # Works! Convention only
```

### Dana's Clear Privacy
```dana
# Dana way - actually private!
def public_method():
    return _private_method()  # Works internally

def _private_method():  # Actually private!
    return "secret"

# This would fail:
# from my_module import _private_method  # Error: private!
```

**Bottom line**: Dana's import system is Python's import system, but with actually working privacy and automatic directory packages. If you know Python imports, you already know Dana imports. The key differences? Underscore prefix actually prevents imports instead of just being a convention, and directories automatically become packages without needing `__init__.na` files. 