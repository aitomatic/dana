# Dana Import System - Primer

This primer covers Dana's import system, including basic imports, privacy rules, and package structure.

## Quick Start

### Basic Module Import
```dana
import my_module
import utils.math as math
```

### Import Specific Items
```dana
from my_module import my_function
from my_module import func1, func2, func3
from my_module import add, multiply as mult
```

### Submodule Import
```dana
import dana.frameworks.corral.curate
from dana.frameworks.corral import curate, organize
```

## Privacy Rules

**Dana uses underscore (`_`) prefix for privacy - simple and intuitive!**

### ✅ Public (Automatically Exportable)
```dana
# In my_module.na
def public_function():
    return "Available for import"

PUBLIC_CONSTANT = "Exportable"

struct DataPoint:
    x: float
    y: float
```

### ❌ Private (Not Exportable)
```dana
# In my_module.na
def _private_helper():
    return "Internal use only"

_INTERNAL_CONFIG = "Hidden"

struct _InternalState:
    secret: str
```

### Import Behavior
```dana
# ✅ These work
from my_module import public_function, PUBLIC_CONSTANT, DataPoint

# ❌ These fail with clear error messages
from my_module import _private_helper      # Error: names starting with '_' are private
from my_module import _INTERNAL_CONFIG     # Error: names starting with '_' are private
from my_module import _InternalState       # Error: names starting with '_' are private
```

### Internal Usage Still Works
```dana
# Inside my_module.na - private functions can be used internally
def public_api():
    result = _private_helper()  # ✅ Works within the same module
    return f"Result: {result}"
```

## Import Patterns

### 1. Basic Module Import
```dana
import math_utils

# Access through module
result = math_utils.add(5, 3)
```

### 2. Import with Alias
```dana
import math_utils as math

# Access through alias
result = math.add(5, 3)
```

### 3. From Import (Single)
```dana
from math_utils import add

# Use directly
result = add(5, 3)
```

### 4. From Import (Multiple)
```dana
from math_utils import add, multiply, square

# Use all directly
sum_result = add(5, 3)
product = multiply(4, 7)
squared = square(6)
```

### 5. From Import with Aliases
```dana
from math_utils import add, multiply as mult, square as sq

# Use with aliases
result = add(5, 3)
product = mult(4, 7)
squared = sq(6)
```

### 6. Deep Module Import
```dana
import dana.frameworks.corral.curate as curate

# Access through alias
recipe = curate.curate_knowledge_recipe(...)
```

### 7. Python Module Import
```dana
import json.py as json
import pandas.py as pd

# Use Python modules
data = json.loads('{"key": "value"}')
df = pd.DataFrame({"a": [1, 2, 3]})
```

## Package Structure

### Required Structure
```
your_package/
├── __init__.na        # ← REQUIRED for packages
└── submodule.na       # Your module
```

### Example Project
```
project/
├── main.na
├── utils/
│   ├── __init__.na    # Required
│   ├── math.na        # Public: add(), multiply()
│   └── helpers.na     # Public: format(), Private: _validate()
└── config/
    ├── __init__.na    # Required
    └── settings.na    # Public: DATABASE_URL, Private: _SECRET_KEY
```

## Environment Setup

### Setting DANAPATH
```bash
# Add paths where Dana should look for modules
export DANAPATH="/path/to/your/modules:$DANAPATH"
```

## Common Patterns

### Framework Modules
```dana
from dana.frameworks.corral import curate, organize
from dana.frameworks.workflow import core, engine as wf_engine
```

### Utility Modules
```dana
from utils import format_data, validate_input
from config import DATABASE_URL, API_KEY
# Note: _secret_config won't be importable (private)
```

### Mixed Imports
```dana
import utils
from utils import format_data
from config import get_settings as settings

result = utils.process(format_data(data))
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

def _internal_logic():     # Private - implementation detail
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

## Troubleshooting

### Module Not Found
**Error:** `Dana module 'my_module' not found`

**Solutions:**
1. Check file exists: `ls my_module.na`
2. Verify DANAPATH: `echo $DANAPATH`
3. Ensure `__init__.na` exists for packages

### Privacy Violation
**Error:** `Cannot import name '_private_func': names starting with '_' are private`

**Solution:** Only import public names (no underscore prefix)

### Import Syntax Error
**Error:** `Unexpected token`

**Solution:** Use correct syntax:
```dana
# ✅ Correct
from module import func1, func2
from module import func1 as f1, func2

# ❌ Incorrect  
from module import *
```

## Summary

Dana's import system provides:
- ✅ **Intuitive privacy** with underscore convention
- ✅ **Zero boilerplate** - everything public by default
- ✅ **Clean APIs** - hide implementation details
- ✅ **Deep imports** - unlimited nesting depth
- ✅ **Multiple import styles** - basic, from, aliased, comma-separated
- ✅ **Python interop** - import `.py` modules seamlessly

**Key Features:**
1. **Underscore privacy** - `_` prefix makes items private
2. **Package structure** - `__init__.na` required for packages  
3. **DANAPATH** - controls module search paths
4. **Clear error messages** - helpful debugging information 