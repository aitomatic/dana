# Dana Module Registry Specification

## Overview

This document specifies WHAT the Dana module registry should support and how it should behave. This is the definitive specification for Dana's module management and path resolution capabilities.

## Core Abstract Concepts

The Dana module registry is built on fundamental concepts for module management and path resolution:

### **1. Module Path**
A specification of which module to locate, supporting:

#### **Absolute Module Paths**
- **Dana modules**: `module`, `module.submodule`
- **Python modules**: `module.py`, `module.submodule.py`

#### **Pure Dotted Relative Paths**
- **Current directory**: `.` (Dana), `..py` (Python)
- **Parent directory**: `..` (Dana), `...py` (Python)
- **Grandparent directory**: `...` (Dana), `....py` (Python)
- **Higher levels**: `....`, `.....`, etc.

#### **Relative Dotted Paths**
- **Sibling modules**: `.sibling`, `.sibling.py`
- **Parent level modules**: `..outer_relative`, `..outer_relative.py`
- **Complex relative paths**: `..outer_relative.sibling`
- **Mixed language paths**: `..outer_relative.py.sibling`

## Module Path Resolution

The Module Path concept is the foundation of all module location in Dana. It specifies exactly which module to locate through a combination of absolute/relative positioning and language targeting.

### **Absolute Module Paths**
Absolute paths start from the root of the module search path and specify the complete path to the target module.

#### **Dana Module Paths**
- **Simple module**: `module` → `module.na`
- **Submodule**: `module.submodule` → `module/submodule.na`
- **Deep submodule**: `module.submodule.subsubmodule` → `module/submodule/subsubmodule.na`

#### **Python Module Paths**
- **Simple module**: `module.py` → `module.py`
- **Submodule**: `module.submodule.py` → `module/submodule.py`
- **Deep submodule**: `module.submodule.subsubmodule.py` → `module/submodule/subsubmodule.py`

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
5. **Module Detection**: Directories with initialization files are treated as modules

## Module Path Resolution Rules

The module registry resolves module paths to file system paths using these rules:

### **Path Resolution Logic**
1. **Language Detection**: `.py` suffix indicates Python module, no suffix indicates Dana module
2. **Directory Navigation**: Each `.` represents one level up in the directory hierarchy
3. **Path Construction**: Relative paths are resolved from the current module's directory
4. **File Extension**: Dana modules use `.na` extension, Python modules use `.py` extension
5. **Module Detection**: Directories with initialization files are treated as modules

## Test Modules

This specification includes concrete test modules in the `.spec/` directory that demonstrate what should work:

- **`basic_module.na`** - Basic module for testing absolute path resolution
- **`regular_module/`** - Regular module with initialization file and submodules
- **`namespace_module/`** - Namespace module without initialization file
- **`mixed_module/`** - Mixed module with both Dana and Python modules
- **`circular_module/`** - Module with allowable circular references
- **`python_module.py`** - Python module for testing cross-language path resolution
- **`python_module/`** - Python module with submodules for testing cross-language path resolution

## Module Types

### Regular Modules
- **Definition**: Directories containing initialization files
- **Behavior**: Execute initialization file when module is loaded
- **Submodules**: Available as attributes on module object

### Namespace Modules
- **Definition**: Directories without initialization files
- **Behavior**: Submodules discovered and made available directly
- **Lazy Loading**: Submodules loaded on-demand

### Mixed Modules
- **Definition**: Modules containing both Dana and Python files
- **Behavior**: Handle both `.na` and `.py` files appropriately

## Lazy Loading

### Submodule Lazy Loading
- **Trigger**: Module submodules loaded on-demand when first accessed
- **Behavior**: Submodules are discovered and made available when needed
- **Resolution**: Automatically resolve submodules when accessed

## Error Handling

### Module Not Found
- **Error**: Module not found in search paths
- **Causes**: Invalid module name, module not in search paths

### Path Resolution Errors
- **Error**: Invalid module path
- **Causes**: Malformed module paths, invalid relative path syntax

### Lazy Loading Errors
- **Error**: Submodule not accessible
- **Causes**: Submodule failed to load, module not fully initialized

## Success Criteria

The module registry meets the specification when:

1. **Path Resolution**: All module paths resolve to correct file system paths
2. **Cross-Language Support**: Seamless Dana-Python module path resolution
3. **Error Handling**: Clear, helpful error messages for all failure cases
4. **Lazy Loading**: Lazy loading works without circular reference issues
5. **Module Detection**: Correctly identifies regular, namespace, and mixed modules
