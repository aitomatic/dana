# Dana Importing System Specification

## Overview

This document specifies WHAT the Dana importing system should support and how it should behave. This is the definitive specification for Dana's importing capabilities.

## Test Modules

This specification includes concrete test modules in the `.spec/` directory that demonstrate what should work:

- **`basic_module.na`** - Basic module for testing absolute imports
- **`regular_package/`** - Regular package with `__init__.na` and submodules
- **`namespace_package/`** - Namespace package without `__init__.na`
- **`mixed_package/`** - Mixed package with both Dana and Python modules
- **`circular_package/`** - Package with allowable circular imports
Each test module contains specific objects and functions that should be importable according to the patterns described below.

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

## Core Import Patterns

### 1. **Module Resolution**

#### Absolute Imports
- **Pattern**: `import module`, `import package.submodule`
- **Behavior**: Resolve module names to file paths in search paths
- **Support**: Both Dana (`.na`) and Python (`.py`) modules
- **Examples**:
  ```dana
  import os
  import sys
  import basic_module
  import regular_package
  import regular_package.submodule1
  import namespace_package.module1
  import mixed_package.dana_module
  import mixed_package.python_module
  ```

#### Relative Imports
- **Pattern**: `from . import submodule`, `from ..parent import sibling`
- **Behavior**: Resolve relative to current module's package context
- **Requirements**: Current module must have `__package__` attribute
- **Examples**:
  ```dana
  from . import sibling_module
  from .. import parent_module
  from ..parent import sibling
  from .subpackage import module
  ```

#### Cross-Language Imports
- **Pattern**: Dana modules importing Python modules and vice versa
- **Behavior**: Seamless interoperability between Dana and Python
- **Examples**:
  ```dana
  import os.py          # Dana importing Python
  import mymodule.py    # Dana importing Python
  ```

### 2. **Package Types**

#### Regular Packages
- **Definition**: Directories containing `__init__.na` or `__init__.py`
- **Behavior**: Execute `__init__` file when package is imported
- **Submodules**: Available as attributes on package object
- **Examples**:
  ```
  mypackage/
  ├── __init__.na
  ├── module1.na
  └── subpackage/
      ├── __init__.na
      └── module2.na
  ```

#### Namespace Packages
- **Definition**: Directories without `__init__.na` or `__init__.py`
- **Behavior**: Submodules discovered and made available directly
- **Lazy Loading**: Critical for efficient handling of large namespace packages
- **Examples**:
  ```
  namespace_pkg/
  ├── module1.na
  ├── module2.na
  └── subpackage/
      └── module3.na
  ```

#### Mixed Packages
- **Definition**: Packages containing both Dana and Python modules
- **Behavior**: Handle both `.na` and `.py` files appropriately
- **Examples**:
  ```
  mixed_pkg/
  ├── __init__.na
  ├── dana_module.na
  └── python_module.py
  ```

### 3. **Import Operations**

#### Basic Imports
- **Pattern**: `import module`
- **Behavior**: Load module and bind to local name
- **Aliasing**: `import module as alias`
- **Examples**:
  ```dana
  import os
  import sys as system
  import mypackage.mymodule
  ```

#### From Imports
- **Pattern**: `from module import name`
- **Behavior**: Import specific names from module
- **Aliasing**: `from module import name as alias`
- **Multiple**: `from module import name1, name2, name3`
- **Examples**:
  ```dana
  from os import path
  from sys import argv as args
  from basic_module import I_AM
  from regular_package import submodule1, submodule2
  from regular_package.submodule1 import I_AM
  from namespace_package.module1 import I_AM
  from mixed_package.dana_module import I_AM
  from mixed_package.python_module import I_AM_PY
  ```

#### Star Imports
- **Pattern**: `from module import *`
- **Behavior**: Import all public names from module
- **Privacy**: Respect `__exports__` if defined, exclude private names (starting with `_`)
- **Examples**:
  ```dana
  from basic_module import *
  from regular_package.submodule1 import *
  from namespace_package.module1 import *
  from mixed_package.dana_module import *
  ```

### 4. **Lazy Loading Strategy**

#### Submodule Lazy Loading
- **Trigger**: Package submodules loaded on-demand when first accessed
- **Implementation**: Lazy loader functions stored as attributes
- **Resolution**: Automatically resolve lazy loaders when accessed
- **Benefits**: Prevents circular import issues, improves performance

#### Lazy Loader Behavior
- **Identification**: Lazy loaders have `__NAME__ == "__LAZY_MODULE_LOADER__"`
- **Resolution**: Call lazy loader to get actual module
- **Fallback**: Graceful handling when lazy loader fails
- **Caching**: Resolved modules cached for subsequent access

### 5. **Circular Import Handling**

#### Allowable Patterns
- **Submodule Cross-References**: Modules within same package can reference each other
- **Parent-Child References**: Child modules can reference parent package
- **Sibling References**: Sibling modules can reference each other
- **Examples**:
  ```dana
  # pkg/__init__.na
  from . import module_a
  from . import module_b

  # pkg/module_a.na
  from . import module_b  # OK: sibling reference

  # pkg/module_b.na
  from . import module_a  # OK: sibling reference
  ```

#### Prohibited Patterns
- **Direct Circular Dependencies**: Module A imports Module B, Module B imports Module A
- **Infinite Recursion**: Patterns that would cause infinite loading loops
- **Examples**:
  ```dana
  # BAD: Direct circular dependency
  # module_a.na
  import module_b

  # module_b.na
  import module_a  # This should be detected and prevented
  ```

#### Graceful Degradation
- **Partial Loading**: Allow partially initialized modules when circular imports detected
- **Lazy Resolution**: Defer loading until dependencies are resolved
- **Clear Errors**: Distinguish between allowable and prohibited circular patterns

### 6. **Module Lifecycle**

#### Discovery Phase
- **Search Paths**: Search in `sys.path` and custom search paths
- **File Types**: Look for `.na` files first, then `.py` files
- **Package Detection**: Identify packages by `__init__.na` or `__init__.py` presence
- **Namespace Detection**: Identify namespace packages by absence of `__init__` files

#### Loading Phase
- **Module Creation**: Create module object with proper metadata
- **Execution**: Execute module code in isolated namespace
- **Submodule Setup**: Create lazy loaders for package submodules
- **Registration**: Register module in global registry

#### Caching Phase
- **Module Storage**: Store loaded modules for reuse
- **Dependency Tracking**: Track module dependencies for circular import detection
- **State Management**: Track loading states (loading, loaded, failed)

#### Cleanup Phase
- **Module Unloading**: Handle module unloading and garbage collection
- **Cache Management**: Manage module cache size and cleanup
- **Dependency Cleanup**: Clean up dependency tracking when modules unloaded

## Error Handling

### Module Not Found
- **Error**: `ModuleNotFoundError: No module named 'module_name'`
- **Causes**: Module not found in search paths, invalid module name
- **Recovery**: Check search paths, verify module name spelling

### Import Errors
- **Error**: `ImportError: cannot import name 'name' from 'module'`
- **Causes**: Name not found in module, privacy violations, circular imports
- **Recovery**: Check module contents, verify name spelling, resolve circular dependencies

### Circular Import Errors
- **Error**: `CircularImportError: circular import detected`
- **Causes**: Prohibited circular import patterns
- **Recovery**: Restructure imports to avoid circular dependencies

### Lazy Loading Errors
- **Error**: `AttributeError: module has no attribute 'name'`
- **Causes**: Lazy loader failed to resolve, module not fully loaded
- **Recovery**: Ensure module is fully loaded before accessing attributes

## Performance Requirements

### Loading Performance
- **Module Discovery**: O(log n) where n is number of modules in search paths
- **Lazy Loading**: O(1) for subsequent access to lazy-loaded modules
- **Circular Import Detection**: O(1) for simple cases, O(n) for complex dependency graphs

### Memory Usage
- **Module Caching**: Configurable cache size with LRU eviction
- **Lazy Loaders**: Minimal memory overhead for lazy loader functions
- **Dependency Tracking**: Efficient storage of dependency relationships

### Scalability
- **Large Packages**: Efficient handling of packages with many submodules
- **Deep Nesting**: Support for deeply nested package structures
- **Namespace Packages**: Efficient discovery and loading of namespace packages

## Compatibility Requirements

### Python Compatibility
- **Import Semantics**: Dana imports should behave like Python imports
- **Error Messages**: Similar error messages and handling
- **Module Objects**: Compatible module object structure
- **Package Behavior**: Similar package loading and submodule access

### Backward Compatibility
- **Existing APIs**: Maintain existing import-related APIs
- **Module Structure**: Preserve existing module object structure
- **Import Syntax**: Support existing Dana import syntax
- **Error Handling**: Maintain existing error handling behavior

## Success Criteria

The importing system meets the specification when:

1. **All Smoke Tests Pass**: `tests/importing/test-imports.na` executes without errors
2. **Python Compatibility**: Dana imports behave like Python imports
3. **Performance**: No significant performance regression compared to current system
4. **Error Handling**: Clear, helpful error messages for all failure cases
5. **Lazy Loading**: Efficient lazy loading without circular import issues
6. **Circular Import Tolerance**: Allow legitimate circular imports that Python permits
7. **Cross-Language Support**: Seamless Dana-Python module interoperability

## Test Coverage

The specification must be validated through comprehensive testing:

### Unit Tests
- Individual import patterns
- Error handling scenarios
- Lazy loading behavior
- Circular import detection

### Integration Tests
- Complex package structures
- Cross-language imports
- Performance benchmarks
- Memory usage tests

### Smoke Tests
- Original failing tests
- Real-world import scenarios
- Edge cases and error conditions
- Compatibility with existing code

This specification defines the complete behavior that the Dana importing system must support to be considered successful.

## Testing the Specification

To verify that the importing system meets this specification, test the following patterns:

1. **Basic module imports**:
   ```dana
   import basic_module
   print(basic_module.I_AM)  # Should print: 'basic_module'
   ```

2. **Package imports**:
   ```dana
   import regular_package
   print(regular_package.I_AM)  # Should print: 'regular_package'
   print(regular_package.submodule1.I_AM)  # Should print: 'regular_package.submodule1'
   ```

3. **From imports**:
   ```dana
   from basic_module import I_AM
   print(I_AM)  # Should print: 'basic_module'
   ```

4. **Namespace package imports**:
   ```dana
   import namespace_package.module1
   print(namespace_package.module1.I_AM)  # Should print: 'namespace_package.module1'
   ```

5. **Mixed package imports**:
   ```dana
   import mixed_package.dana_module
   import mixed_package.python_module
   print(mixed_package.dana_module.I_AM)  # Should print: 'mixed_package.dana_module'
   print(mixed_package.python_module.I_AM_PY)  # Should print: 'mixed_package.python_module'
   ```

6. **Circular package imports**:
   ```dana
   import circular_package.module_a
   import circular_package.module_b
   print(circular_package.module_a.I_AM)  # Should print: 'circular_package.module_a'
   print(circular_package.module_b.I_AM)  # Should print: 'circular_package.module_b'
   ```

The importing system is successful when all these patterns work correctly without errors.
