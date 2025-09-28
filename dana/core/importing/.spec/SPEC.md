# Dana Importing System Specification

## Overview

This document specifies WHAT the Dana importing system should support and how it should behave. This is the definitive specification for Dana's importing capabilities.

## Core Abstract Concepts

The Dana importing system is built on three fundamental abstract concepts:

### **1. Module Path**
A specification of which module to import, supporting:

#### **Absolute Module Paths**
- **Dana modules**: `module`, `package.submodule`
- **Python modules**: `module.py`, `package.submodule.py`

#### **Pure Dotted Relative Paths**
- **Current directory**: `.` (Dana), `..py` (Python)
- **Parent directory**: `..` (Dana), `...py` (Python)
- **Grandparent directory**: `...` (Dana), `....py` (Python)
- **Higher levels**: `....`, `.....`, etc.

#### **Relative Dotted Paths**
- **Sibling modules**: `.a_fellow_submodule`, `.a_fellow_submodule.py`
- **Parent level modules**: `..a_parent_level_submodule`, `..a_parent_level_submodule.py`
- **Complex relative paths**: `..a_parent_level_submodule.a_fellow_submodule_of_another_parent`
- **Mixed language paths**: `..a_parent_level_submodule.py.a_fellow_submodule`

### **2. Object Spec**
A specification of what to import from a module:
- **Single object**: `object`
- **Multiple objects**: `obj1, obj2, obj3`
- **Module**: `module` (imports the module itself)
- **All objects**: `*` (star import, requires `__all__` attribute)

### **3. Alias**
Optional name rebinding for imported items:
- **No alias**: Use original name
- **With alias**: `as alias` for name rebinding

## Module Path Specification

The Module Path concept is the foundation of all importing in Dana. It specifies exactly which module to import through a combination of absolute/relative positioning and language targeting.

### **Absolute Module Paths**
Absolute paths start from the root of the module search path and specify the complete path to the target module.

#### **Dana Module Paths**
- **Simple module**: `module` → `module.na`
- **Package submodule**: `package.submodule` → `package/submodule.na`
- **Deep package**: `package.subpackage.submodule` → `package/subpackage/submodule.na`

#### **Python Module Paths**
- **Simple module**: `module.py` → `module.py`
- **Package submodule**: `package.submodule.py` → `package/submodule.py`
- **Deep package**: `package.subpackage.submodule.py` → `package/subpackage/submodule.py`

### **Pure Dotted Relative Paths**
Pure dotted paths use only dots to navigate the directory hierarchy, with optional language suffix.

#### **Current Directory Navigation**
- **Dana current**: `.` → Current directory (Dana)
- **Python current**: `..py` → Current directory (Python)

#### **Parent Directory Navigation**
- **Dana parent**: `..` → Parent directory (Dana)
- **Python parent**: `...py` → Parent directory (Python)

#### **Higher Level Navigation**
- **Dana grandparent**: `...` → Grandparent directory (Dana)
- **Python grandparent**: `....py` → Grandparent directory (Python)
- **Dana great-grandparent**: `....` → Great-grandparent directory (Dana)
- **Python great-grandparent**: `....py` → Great-grandparent directory (Python)

### **Relative Dotted Paths**
Relative dotted paths combine directory navigation with specific module names.

#### **Sibling Module Paths**
- **Dana sibling**: `.a_fellow_submodule` → `./a_fellow_submodule.na`
- **Python sibling**: `.a_fellow_submodule.py` → `./a_fellow_submodule.py`

#### **Parent Level Module Paths**
- **Dana parent level**: `..a_parent_level_submodule` → `../a_parent_level_submodule.na`
- **Python parent level**: `..a_parent_level_submodule.py` → `../a_parent_level_submodule.py`

#### **Complex Relative Paths**
- **Multi-level Dana**: `..a_parent_level_submodule.a_fellow_submodule_of_another_parent` → `../a_parent_level_submodule/a_fellow_submodule_of_another_parent.na`
- **Multi-level Python**: `..a_parent_level_submodule.py.a_fellow_submodule_of_another_parent.py` → `../a_parent_level_submodule.py/a_fellow_submodule_of_another_parent.py`

#### **Mixed Language Paths**
- **Dana parent, Python child**: `..a_parent_level_submodule.py.a_fellow_submodule` → `../a_parent_level_submodule.py/a_fellow_submodule.na`
- **Python parent, Dana child**: `..a_parent_level_submodule.a_fellow_submodule.py` → `../a_parent_level_submodule/a_fellow_submodule.py`

### **Module Path Resolution Rules**
1. **Language Detection**: `.py` suffix indicates Python module, no suffix indicates Dana module
2. **Directory Navigation**: Each `.` represents one level up in the directory hierarchy
3. **Path Construction**: Relative paths are resolved from the current module's directory
4. **File Extension**: Dana modules use `.na` extension, Python modules use `.py` extension
5. **Package Detection**: Directories with `__init__.na` or `__init__.py` are treated as packages

## Fundamental Import Syntax

The Dana importing system supports exactly two fundamental syntax patterns:

### **Pattern 1: Module Import**
```
import [module_path] [as alias]
```

### **Pattern 2: Object Import**
```
from [module_path] import [object_spec] [as alias]
```

## Import Pattern Combinations

All import patterns are combinations of these 2 syntax patterns with the 3 core concepts:

### **Module Import Patterns**
- `import module` - Basic module import
- `import module as alias` - Aliased module import
- `import package.submodule` - Package import
- `import module.py` - Python module import

### **Object Import Patterns**
- `from module import object` - Single object import
- `from module import object as alias` - Aliased object import
- `from module import obj1, obj2, obj3` - Multiple object import
- `from module import obj1, obj2 as alias2, obj3` - Mixed aliasing
- `from package import module` - Module import from package
- `from module import *` - Star import (requires `__all__` attribute)

### **Relative Import Patterns**
- `from . import module` - Same package import
- `from .. import module` - Parent package import
- `from .module import object` - Relative object import

### **Python Import Patterns**
- `import module.py` - Python module import
- `from module.py import object` - Python object import
- `import package.py.submodule` - Python package import

## Test Modules

This specification includes concrete test modules in the `.spec/` directory that demonstrate what should work:

- **`basic_module.na`** - Basic module for testing absolute imports
- **`regular_package/`** - Regular package with `__init__.na` and submodules
- **`namespace_package/`** - Namespace package without `__init__.na`
- **`mixed_package/`** - Mixed package with both Dana and Python modules
- **`circular_package/`** - Package with allowable circular imports
- **`python_module.py`** - Python module for testing cross-language imports
- **`python_package/`** - Python package with submodules for testing cross-language imports

Each test module contains specific objects that should be importable according to the patterns described below.

## Importable Objects

### Basic Module (`basic_module.na`)
- **Variables**: `I_AM`

### Regular Package (`regular_package/`)
- **Package variables**: `I_AM`
- **Submodules**: `submodule1`, `submodule2`
- **From submodule1**: `I_AM`
- **From submodule2**: `I_AM`

### Namespace Package (`namespace_package/`)
- **Module1**: `I_AM`
- **Module2**: `I_AM`

### Mixed Package (`mixed_package/`)
- **Dana module**: `I_AM`
- **Python module**: `I_AM_PY`

### Circular Package (`circular_package/`)
- **Package variables**: `I_AM`
- **Module A**: `I_AM`
- **Module B**: `I_AM`

### Python Module (`python_module.py`)
- **Variables**: `I_AM_PY`

### Python Package (`python_package/`)
- **Package variables**: `I_AM_PY`
- **Submodule**: `I_AM_PY`
- **Nested package**: `I_AM_PY`
- **Deep module**: `I_AM_PY`

## Python Importing Requirements

### Key Principles
1. **`.py` Suffix Required**: All Python imports must use `.py` suffix
2. **Equivalent Treatment**: Python modules treated as equivalent to Dana modules
3. **Full Pattern Support**: All import patterns (absolute, relative, from, star) work with Python
4. **Package Support**: Python packages work identically to Dana packages
5. **Cross-Language Seamless**: No special handling needed beyond the `.py` suffix

### Import Syntax Rules
- **Basic imports**: `import module.py`
- **From imports**: `from module.py import name`
- **Package imports**: `import package.py`, `import package.submodule.py`
- **Relative imports**: `from .module.py import name`, `from ..package.py import name`
- **Star imports**: `from module.py import *`

### Examples
```dana
# Standard library imports
import os.py
import sys.py
from os.py import path
from sys.py import argv

# Third-party imports
import pandas.py
import numpy.py
from pandas.py import DataFrame, read_csv
from numpy.py import array, zeros

# Local Python module imports
import my_py_module.py
from my_py_module.py import my_function, MyClass

# Python package imports
import my_py_package.py
from my_py_package.py import submodule
from my_py_package.py.submodule import my_function

# Relative Python imports
from .sibling_py_module.py import sibling_function
from ..parent_py_package.py import parent_function
from ..parent_py_package.py.child_py_module import child_function
```

## Fundamental Import Patterns

### 1. **Module Imports**

#### Basic Module Import
- **Pattern**: `import module`
- **Behavior**: Load module and bind to local name
- **Examples**:
  ```dana
  import basic_module
  import python_module.py
  ```

#### Aliased Module Import
- **Pattern**: `import module as alias`
- **Behavior**: Load module and bind to alias name
- **Examples**:
  ```dana
  import basic_module as bm
  import python_module.py as pm
  ```

#### Package Import
- **Pattern**: `import package.submodule`
- **Behavior**: Load submodule from package
- **Examples**:
  ```dana
  import regular_package.submodule1
  import python_package.py.submodule
  ```

### 2. **Object Imports**

#### Single Object Import
- **Pattern**: `from module import object`
- **Behavior**: Import specific object into current namespace
- **Examples**:
  ```dana
  from basic_module import I_AM
  from python_module.py import I_AM_PY
  ```

#### Aliased Object Import
- **Pattern**: `from module import object as alias`
- **Behavior**: Import object with alias name
- **Examples**:
  ```dana
  from basic_module import I_AM as name
  from python_module.py import I_AM_PY as py_name
  ```

#### Multiple Object Import
- **Pattern**: `from module import obj1, obj2, obj3`
- **Behavior**: Import multiple objects from same module
- **Examples**:
  ```dana
  from basic_module import I_AM
  from python_module.py import I_AM_PY
  ```

#### Mixed Aliasing Import
- **Pattern**: `from module import obj1, obj2 as alias2, obj3`
- **Behavior**: Import multiple objects with some aliased
- **Examples**:
  ```dana
  from basic_module import I_AM
  from python_module.py import I_AM_PY
  ```

### 3. **Relative Imports**

#### Same Package Import
- **Pattern**: `from . import module`
- **Behavior**: Import from same package
- **Examples**:
  ```dana
  from . import sibling_module
  from . import sibling_py_module.py
  ```

#### Parent Package Import
- **Pattern**: `from .. import module`
- **Behavior**: Import from parent package
- **Examples**:
  ```dana
  from .. import parent_module
  from .. import parent_py_module.py
  ```

#### Relative Object Import
- **Pattern**: `from .module import object`
- **Behavior**: Import object from sibling module
- **Examples**:
  ```dana
  from .sibling_module import I_AM
  from .sibling_py_module.py import I_AM_PY
  ```

### 4. **Star Imports**

#### Star Import
- **Pattern**: `from module import *`
- **Behavior**: Import all public names from module
- **Examples**:
  ```dana
  from basic_module import *
  from python_module.py import *
  ```

### 5. **Module Resolution**

#### Absolute Module Resolution
- **Pattern**: `import module`
- **Behavior**: Resolve module names to file paths in search paths
- **Support**: Both Dana (`.na`) and Python (`.py`) modules

#### Package Module Resolution
- **Pattern**: `import package.submodule`
- **Behavior**: Resolve submodule within package
- **Support**: Both Dana and Python packages

#### Python Module Resolution
- **Pattern**: `import module.py`
- **Behavior**: Resolve Python modules with `.py` suffix
- **Requirement**: `.py` suffix required for Python modules

### 6. **Package Types**

#### Regular Packages
- **Definition**: Directories containing `__init__.na` or `__init__.py`
- **Behavior**: Execute `__init__` file when package is imported
- **Submodules**: Available as attributes on package object

#### Namespace Packages
- **Definition**: Directories without `__init__.na` or `__init__.py`
- **Behavior**: Submodules discovered and made available directly
- **Lazy Loading**: Submodules loaded on-demand

#### Mixed Packages
- **Definition**: Packages containing both Dana and Python modules
- **Behavior**: Handle both `.na` and `.py` files appropriately

### 7. **Lazy Loading**

#### Submodule Lazy Loading
- **Trigger**: Package submodules loaded on-demand when first accessed
- **Implementation**: Lazy loader functions stored as attributes
- **Resolution**: Automatically resolve lazy loaders when accessed

#### Lazy Loader Behavior
- **Identification**: Lazy loaders have `__NAME__ == "__LAZY_MODULE_LOADER__"`
- **Resolution**: Call lazy loader to get actual module
- **Caching**: Resolved modules cached for subsequent access

### 8. **Circular Import Handling**

#### Allowable Patterns
- **Submodule Cross-References**: Modules within same package can reference each other
- **Parent-Child References**: Child modules can reference parent package
- **Sibling References**: Sibling modules can reference each other

#### Prohibited Patterns
- **Direct Circular Dependencies**: Module A imports Module B, Module B imports Module A
- **Infinite Recursion**: Patterns that would cause infinite loading loops

#### Graceful Degradation
- **Partial Loading**: Allow partially initialized modules when circular imports detected
- **Lazy Resolution**: Defer loading until dependencies are resolved
- **Clear Errors**: Distinguish between allowable and prohibited circular patterns

## Error Handling

### Module Not Found
- **Error**: `ModuleNotFoundError: No module named 'module_name'`
- **Causes**: Module not found in search paths, invalid module name

### Import Errors
- **Error**: `ImportError: cannot import name 'name' from 'module'`
- **Causes**: Name not found in module, privacy violations, circular imports

### Circular Import Errors
- **Error**: `CircularImportError: circular import detected`
- **Causes**: Prohibited circular import patterns

### Lazy Loading Errors
- **Error**: `AttributeError: module has no attribute 'name'`
- **Causes**: Lazy loader failed to resolve, module not fully loaded


## Success Criteria

The importing system meets the specification when:

1. **All Smoke Tests Pass**: `tests/importing/test-imports.na` executes without errors
2. **Python Compatibility**: Dana imports behave like Python imports
3. **Error Handling**: Clear, helpful error messages for all failure cases
4. **Lazy Loading**: Lazy loading works without circular import issues
5. **Circular Import Tolerance**: Allow legitimate circular imports that Python permits
6. **Cross-Language Support**: Seamless Dana-Python module interoperability

## Testing the Specification

To verify that the importing system meets this specification, test the following fundamental patterns:

### Basic Patterns
1. **Module Import**: `import basic_module`
2. **Aliased Module Import**: `import basic_module as bm`
3. **Object Import**: `from basic_module import I_AM`
4. **Aliased Object Import**: `from basic_module import I_AM as name`
5. **Multiple Object Import**: `from basic_module import I_AM`
6. **Mixed Aliasing Import**: `from basic_module import I_AM`

### Package Patterns
7. **Package Import**: `import regular_package.submodule1`
8. **Package Object Import**: `from regular_package import I_AM`
9. **Submodule Object Import**: `from regular_package.submodule1 import I_AM`

### Relative Patterns
10. **Same Package Import**: `from . import sibling_module`
11. **Parent Package Import**: `from .. import parent_module`
12. **Relative Object Import**: `from .sibling_module import I_AM`

### Python Patterns
13. **Python Module Import**: `import python_module.py`
14. **Python Object Import**: `from python_module.py import I_AM_PY`
15. **Python Aliased Import**: `from python_module.py import I_AM_PY as py_name`

### Star Import Pattern
16. **Star Import**: `from basic_module import *`

The importing system is successful when all these fundamental patterns work correctly without errors.
