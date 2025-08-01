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

**What it is**: Python's import system, but simpler. Dana uses underscore prefix for privacy (actually works!) and directories automatically become packages without initialization files.

## Key Syntax

**Basic Imports**:
```dana
import my_module
import my_module as mm
from my_module import my_function
from my_module import func1, func2, func3
from my_module import add, multiply as mult, square as sq
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

## Real-World Examples

### Math Library
```dana
# math_utils.na
def add(a: int, b: int) -> int: return a + b
def multiply(a: int, b: int) -> int: return a * b
def square(x: int) -> int: return multiply(x, x)
def _complex_formula(): return "complicated calculation"

# geometry.na
from math_utils import multiply
def circle_area(radius: float) -> float: return 3.14159 * multiply(radius, radius)

# main.na
from math_utils import add, square
from geometry import circle_area

sum = add(5, 3)           # 8
squared = square(4)       # 16
circle = circle_area(5.0) # 78.53975
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
```dana
import json.py as json
import pandas.py as pd

data = json.loads('{"key": "value"}')
df = pd.DataFrame({"a": [1, 2, 3]})
```

### Framework Modules
```dana
from dana.frameworks.corral import curate, organize
from dana.frameworks.workflow import core, engine as wf_engine
```

## Environment Setup

**Setting DANAPATH**:
```bash
export DANAPATH="/path/to/your/modules:$DANAPATH"
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

# Import Syntax Error
from module import *  # Not supported in Dana
# Error: Unexpected token - Dana doesn't support wildcard imports
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

### 2. Leverage Privacy
```dana
# ✅ Good module design
def public_api():          # Exportable
    return _internal_logic()

def _internal_logic():     # Private - actually private!
    return "result"
```

### 3. Organize Imports
```dana
# ✅ Good grouping
import system_module
import dana.frameworks.corral.curate as curate

from local_utils import helper_function
from config import DATABASE_URL
```

### 4. Keep Modules Focused
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
- **Python compatibility**: Same syntax as Python imports
- **Actual privacy**: Underscore prefix prevents imports (unlike Python's convention)
- **Automatic packages**: Directories become packages without initialization files
- **Python interop**: Import `.py` modules seamlessly
- **Clear errors**: Helpful error messages for import issues

Perfect for: Python developers, modular code organization, and building maintainable applications. 