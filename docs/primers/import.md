# Dana Import System Primer

## TL;DR (1 minute read)

```dana
# math_utils.na
def add(a: int, b: int) -> int: return a + b
def multiply(a: int, b: int) -> int: return a * b
def power(x: int, n: int) -> int: return x ** n
def _complex_calc(): return "private"  # Can't be imported

# Export only specific functions for star imports
__exports__ = ["add", "multiply"]

# main.na
import math_utils
from math_utils import add, multiply
from math_utils import *  # Gets add() and multiply() only
from math_utils import _complex_calc  # ❌ Error - actually private!

result = math_utils.add(5, 3)  # 8
product = multiply(4, 7)       # 28

# Python ecosystem - import any Python package!
import pandas as pd
import requests
from datetime import datetime

df = pd.DataFrame({"name": ["Alice"], "age": [25]})
response = requests.get("https://api.example.com")
now = datetime.now()

# Package structure (simpler than Python):
# my_package/        # Directory automatically becomes a package
#   utils.na
#   helpers.na
#   sub_package/      # Nested packages work too
#     more_utils.na
```

---

**What it is**: Python's import system, but better. Dana adds star imports with security controls, `__exports__` for API design, underscore prefix for actual privacy, and directories automatically become packages without initialization files.

## Key Syntax

**Basic Imports**:
```dana
import my_module
import my_module as mm
from my_module import my_function
from my_module import func1, func2, func3
from my_module import add, multiply as mult, square as sq
from my_module import *  # Star import - imports all public functions
```

**Privacy Rules**:
```dana
# ✅ Public (importable)
def public_function(): return "Available"
PUBLIC_CONSTANT = "Exportable"
struct DataPoint: x: float; y: float

# ❌ Private (not importable)
def _private_helper(): return "Internal only"
_INTERNAL_CONFIG = "Hidden"
struct _InternalState: secret: str
```

**Star Imports and Export Control**:
```dana
# my_utils.na
def add(a: int, b: int) -> int: return a + b
def multiply(a: int, b: int) -> int: return a * b
def divide(a: int, b: int) -> int: return a / b
def _internal_calc(): return "private"

# Only export specific functions
__exports__ = ["add", "multiply"]  # Only these will be imported with *

# main.na
from my_utils import *  # Only imports add() and multiply()

result1 = add(5, 3)      # ✅ Works - explicitly exported
result2 = multiply(4, 2) # ✅ Works - explicitly exported
# result3 = divide(10, 2)  # ❌ Error - not in __exports__
# result4 = _internal_calc()  # ❌ Error - private function
```

**Star Import Rules**:
- `from module import *` imports all **public** functions by default
- If `__exports__` is defined, **only** those functions are imported
- Private functions (starting with `_`) are **never** imported
- Variables and constants follow the same rules as functions

## Real-World Examples

### Math Library with Star Imports
```dana
# math_utils.na
def add(a: int, b: int) -> int: return a + b
def multiply(a: int, b: int) -> int: return a * b
def square(x: int) -> int: return multiply(x, x)
def power(x: int, n: int) -> int: return x ** n
def _complex_formula(): return "complicated calculation"
def _internal_cache(): return {}

# Export only the main math functions
__exports__ = ["add", "multiply", "square", "power"]

# geometry.na
from math_utils import multiply
def circle_area(radius: float) -> float: return 3.14159 * multiply(radius, radius)

# main.na - using star import for convenience
from math_utils import *  # Gets: add, multiply, square, power
from geometry import circle_area

sum = add(5, 3)           # 8
product = multiply(4, 7)  # 28
squared = square(4)       # 16
cubed = power(3, 3)      # 27
circle = circle_area(5.0) # 78.53975

# These would cause errors:
# result = _complex_formula()  # ❌ Private function not imported
# cache = _internal_cache()    # ❌ Private function not imported
```

### Business App
```dana
# user_utils.na
def format_name(first: str, last: str) -> str: return f"{first} {last}"
def validate_email(email: str) -> bool: return _check_email_format(email)
def _check_email_format(email: str) -> bool: return "@" in email and "." in email

# payment_utils.na
def process_payment(amount: float, currency: str) -> bool:
    if _validate_amount(amount): return _charge_card(amount, currency)
    return false
def _validate_amount(amount: float) -> bool: return amount > 0
def _charge_card(amount: float, currency: str) -> bool: return true

# main.na
from user_utils import format_name, validate_email
from payment_utils import process_payment

user_name = format_name("Alice", "Smith")  # "Alice Smith"
valid_email = validate_email("alice@example.com")  # true
payment_success = process_payment(99.99, "USD")  # true
```

## Package Structure

**Automatic Directory Packages**:
```
project/
├── main.na
├── utils/             # ← Automatically a package
│   ├── math.na        # Public: add(), multiply()
│   └── helpers.na     # Public: format(), Private: _validate()
├── config/            # ← Automatically a package
│   └── settings.na    # Public: DATABASE_URL, Private: _SECRET_KEY
└── advanced/          # ← Package with algorithms
    └── algorithms.na  # Advanced algorithms
```

**Usage**:
```dana
from utils.math import add, multiply
from config.settings import DATABASE_URL
```

## Advanced Import Patterns

### Deep Module Import
```dana
import dana.frameworks.corral.curate as curate
recipe = curate.curate_knowledge_recipe(...)
```

### Python Module Import

**🚀 Leverage the entire Python ecosystem!** Import any Python package/module - from built-ins like `os` and `json` to popular libraries like `numpy`, `pandas`, `requests`, `flask`, `tensorflow`, and thousands more from PyPI.

**Useful Examples**:
```dana
# Data processing
import pandas as pd
import numpy as np
df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})

# Web requests
import requests
response = requests.get("https://api.example.com/data")

# File operations
import os, json
files = os.listdir(".")
data = json.loads('{"key": "value"}')

# Date/time
from datetime import datetime
now = datetime.now()
```

**Quick Reference**:
```dana
import math                    # Basic import
from math import sqrt, pi      # From import
import math as m               # With alias
from math import sqrt as sq    # From with alias
import my_module.py            # Local Python file
```

**Common Python modules work seamlessly**:
```dana
import os, json, datetime, random
import numpy as np
import pandas as pd

files = os.listdir(".")
data = json.dumps({"key": "value"})
array = np.array([1, 2, 3])
```

**Local Python files**:
```dana
# utils.py
def greet(name): return f"Hello, {name}!"

# main.na
import utils.py
message = utils.greet("World")
```

**Error handling**:
```dana
try:
    import pandas as pd
    df = pd.DataFrame({"a": [1, 2, 3]})
except ImportError:
    print("pandas not available")
```

That's it! Python imports work exactly like Python - no special syntax needed.

### Framework Modules
```dana
from dana.frameworks.corral import curate, organize
from dana.frameworks.workflow import core, engine as wf_engine
```

## Environment Setup and Search Path

**Module Search Path Precedence** (highest to lowest priority):
1. **Current working directory** - `./my_module.na`
2. **Relative paths** - `./utils/helpers.na`
3. **DANA_PATH directories** - Set via environment variable
4. **System stdlib** - Dana's built-in standard library
5. **Python modules** - Available via Python's import system

**Setting DANA_PATH**:
```bash
# Single path
export DANA_PATH="/path/to/your/modules"

# Multiple paths (colon-separated)
export DANA_PATH="/path/to/modules:/another/path:/third/path"

# Add to existing path
export DANA_PATH="/new/path:$DANA_PATH"
```

**Example Directory Structure**:
```
project/
├── main.na              # Current directory (highest priority)
├── local_utils.na       # Local module
├── utils/               # Local package
│   └── helpers.na
├── /home/user/dana_libs/  # In DANA_PATH
│   └── shared_utils.na
└── /usr/local/dana/     # System location
    └── system_utils.na
```

**Import Resolution**:
```dana
import helpers  # Searches:
# 1. ./helpers.na (found - stops here)
# 2. Would check DANA_PATH if not found
# 3. Would check system directories if still not found

from utils import helpers  # Searches:
# 1. ./utils/helpers.na (found - stops here)
```

## Error Handling

**Common Errors**:
```dana
# Module Not Found
from missing_module import function
# Error: Dana module 'missing_module' not found

# Privacy Violation
from my_module import _private_func
# Error: Cannot import name '_private_func': names starting with '_' are private

# Function Not Exported
# my_module.na has: __exports__ = ["add"]
from my_module import multiply  # multiply not in __exports__
# Error: Cannot import name 'multiply': not in module's __exports__ list

# Star Import from Empty Module
from empty_module import *
# Warning: No public functions found for star import

# Conflicting Names
from math_utils import add
from text_utils import add  # Same function name
# Error: Name 'add' already imported - use aliases or explicit imports
```

## Best Practices

### 1. Use Descriptive Names
```dana
# ✅ Good
import data_processor as dp
from math_utils import calculate_distance

# ❌ Avoid
import x as y
```

### 2. Smart Use of Star Imports
```dana
# ✅ Good - use for utility modules with clear exports
from math_utils import *    # When __exports__ is well-defined
from constants import *     # For configuration constants

# ✅ Good - explicit imports for specific needs
from large_module import specific_function, another_function

# ❌ Avoid - star imports without export control
from huge_library import *  # Could import 100+ functions

# ✅ Good - controlled exports in your modules
# my_api.na
def public_function(): pass
def another_public(): pass
def _internal_helper(): pass

__exports__ = ["public_function", "another_public"]  # Clear API
```

### 3. Design Clean Module APIs
```dana
# ✅ Good - thoughtful __exports__
# data_processing.na
def process_csv(file): return _parse_and_clean(file)
def process_json(file): return _validate_and_parse(file)
def validate_data(data): return _run_validation(data)

def _parse_and_clean(file): pass  # Internal implementation
def _validate_and_parse(file): pass  # Internal implementation
def _run_validation(data): pass  # Internal implementation

# Only export the public API
__exports__ = ["process_csv", "process_json", "validate_data"]

# usage.na
from data_processing import *  # Gets clean, focused API
result = process_csv("data.csv")
```

### 4. Leverage Privacy
```dana
# ✅ Good module design
def public_api():          # Exportable
    return _internal_logic()

def _internal_logic():     # Private - actually private!
    return "result"
```

### 5. Organize Imports
```dana
# ✅ Good grouping
import system_module
import dana.frameworks.corral.curate as curate

from local_utils import helper_function
from config import DATABASE_URL
from math_utils import *  # Star imports at the end for clarity
```

### 6. Keep Modules Focused
```dana
# ✅ Good - focused modules
# math_utils.na - only math functions
# user_utils.na - only user-related functions
# payment_utils.na - only payment functions

# ❌ Avoid - mixed concerns
# utils.na - math, user, payment, email, database, etc.
```

## Summary

Dana's import system provides:
- **Python compatibility**: Same syntax as Python imports, plus enhanced features
- **Star imports**: `from module import *` with security controls and export declarations
- **Export control**: `__exports__` variable for fine-grained API control
- **Actual privacy**: Underscore prefix prevents imports (unlike Python's convention)
- **Smart search paths**: Predictable module resolution with DANA_PATH precedence
- **Automatic packages**: Directories become packages without initialization files
- **Python interop**: Import `.py` modules seamlessly
- **Clear errors**: Helpful error messages for import issues

Perfect for: Python developers, modular code organization, building maintainable applications, and creating clean APIs with controlled exports. 