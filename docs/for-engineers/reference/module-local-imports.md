# Module-Local Imports in Dana

## Overview

Dana now supports **module-local imports**, making it easier and more intuitive to import modules within the same directory or project. This feature automatically includes the directory of the importing module in the search path, allowing direct imports of sibling modules without relative import syntax.

## Key Features

1. **Automatic Directory Inclusion**: The directory containing the current module is automatically included in the module search path
2. **Sibling Imports**: Import modules in the same directory directly by name
3. **Directory Packages**: Directories containing `.na` files automatically become packages (no `__init__.na` required)
4. **Context-Aware**: Each module maintains its own import context based on its location
5. **Backward Compatible**: Existing import mechanisms continue to work as before

## Basic Usage

### Directory Packages (No `__init__.na` Required)

Dana automatically treats directories containing `.na` files as packages:

```
math_library/          # Automatically a package
├── basic.na           # Contains add(), subtract()
├── advanced.na        # Contains calculus(), statistics()
└── constants.na       # Contains PI, E, etc.
```

Import from directory packages directly:

```dana
# main.na
from math_library.basic import add, subtract
from math_library.advanced import calculus
from math_library.constants import PI

result = add(5, 3)
area = PI * radius * radius
```

### Sibling Module Imports

Given this directory structure:
```
project/
├── math_utils.na
├── string_utils.na
└── main.na
```

In `main.na`, you can import sibling modules directly:

```dana
# main.na
import math_utils
import string_utils

result = math_utils.add(5, 3)
text = string_utils.capitalize("hello")
```

### From Imports

You can also use from-imports with sibling modules:

```dana
# main.na
from math_utils import add, multiply
from string_utils import capitalize, reverse

result = add(10, 20)
reversed = reverse("hello")
```

## Import Precedence

When Dana looks for a module, it searches in this order:

1. **Module's directory** (NEW) - The directory containing the importing module
2. **Current working directory** - Where the Dana command was run
3. **Standard paths** - Directories in DANAPATH environment variable

This means local modules take precedence over system-wide modules with the same name.

## Examples

### Example 1: Simple Project

```
calculator/
├── operations.na
├── constants.na
└── calculator.na
```

`operations.na`:
```dana
import constants  # Imports ./constants.na

def circle_area(radius: float) -> float:
    return constants.PI * radius * radius
```

`calculator.na`:
```dana
import operations  # Imports ./operations.na

area = operations.circle_area(5.0)
print(f"Area: {area}")
```

### Example 2: Nested Modules (Directory Packages)

```
app/
├── utils/             # Automatically a package (no __init__.na needed)
│   ├── text.na
│   └── numbers.na
├── models.na
└── main.na
```

In `main.na`:
```dana
import models          # Imports ./models.na
import utils.text      # Imports ./utils/text.na
import utils.numbers   # Imports ./utils/numbers.na
```

### Example 3: Module Chains

When module A imports module B, and module B imports module C, each import is resolved relative to the importing module's directory:

```
project/
├── moduleA.na
├── moduleB.na
└── moduleC.na
```

`moduleC.na`:
```dana
value = 42
```

`moduleB.na`:
```dana
import moduleC  # Finds ./moduleC.na
multiplier = 2
```

`moduleA.na`:
```dana
import moduleB  # Finds ./moduleB.na
result = moduleB.moduleC.value * moduleB.multiplier
```

## Benefits

1. **Simplicity**: No need to remember relative import syntax (`.`, `..`, etc.)
2. **Portability**: Move directories without changing import statements
3. **Intuitive**: Works the way developers expect - local files are easily accessible
4. **Isolation**: Different projects can have modules with the same names without conflicts

## Comparison with Python

| Feature | Python | Dana |
|---------|--------|------|
| Current directory in path | Only for main script | Yes, for all modules |
| Relative imports | Requires `.` syntax | Direct import works |
| Package requirement | Needs `__init__.py` | No `__init__.na` needed |
| Directory packages | Not supported | Automatic |
| Import syntax | `from . import sibling` | `import sibling` |

## Best Practices

1. **Use direct imports for siblings**: Instead of complex relative paths, just use the module name
2. **Organize related modules together**: Keep modules that import each other in the same directory
3. **Use directories for organization**: Directories automatically become packages - no `__init__.na` needed
4. **Add `__init__.na` only when needed**: For package-level initialization, imports, or exports
5. **Avoid naming conflicts**: Be mindful of module names that might conflict with standard library modules

## Configuration

### Environment Variables

- **DANAPATH**: Additional directories to search for modules (similar to Python's PYTHONPATH)
  ```bash
  export DANAPATH=/path/to/modules:/another/path
  ```

### Programmatic Configuration

When initializing the module system programmatically:

```python
from dana.core.runtime.modules.core import initialize_module_system

# Add custom search paths
initialize_module_system([
    "/path/to/custom/modules",
    "/another/module/directory"
])
```

## Troubleshooting

### Module Not Found

If a sibling module is not found:
1. Ensure the file has a `.na` extension
2. Check that the module name matches the filename (without extension)
3. Verify there are no syntax errors in the module
4. For packages, ensure the directory contains `.na` files (directories are automatically packages)

### Import Conflicts

If the wrong module is imported:
1. Check for naming conflicts with modules in DANAPATH
2. Use explicit package paths for disambiguation
3. Consider renaming local modules to avoid conflicts

## Implementation Details

The module-local import feature works by:

1. When a module imports another module, Dana checks the importing module's directory first
2. The module loader maintains context about which module is doing the importing
3. Each module's directory is temporarily added to the search path during its imports
4. This ensures modules can find their siblings while maintaining isolation between projects

This feature is implemented in:
- `dana/core/runtime/modules/core/loader.py` - Module finding logic
- `dana/core/lang/interpreter/executor/statement/import_handler.py` - Import execution
- `dana/core/lang/dana_sandbox.py` - Main script directory handling