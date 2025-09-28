# Module Resolver Design

## Overview
The Module Resolver is responsible for resolving module paths to actual file system paths and determining the appropriate loader for each module type.

## Core Components

### 1. ModulePath Class
Represents a parsed module path with all its components:
- **path_type**: absolute, relative, pure_dotted
- **language**: dana, python
- **segments**: list of path segments
- **dots**: number of parent directory navigations
- **suffix**: .py for Python, None for Dana

### 2. ModuleResolver Class
Main resolver that handles:
- **Path parsing**: Convert string paths to ModulePath objects
- **Path resolution**: Convert ModulePath to file system paths
- **Language detection**: Determine if module is Dana or Python
- **Loader selection**: Choose appropriate loader for module type

### 3. Path Resolution Strategy
1. **Parse module path** into components
2. **Determine language** from suffix
3. **Resolve relative paths** from current module location
4. **Search in module search paths** for absolute paths
5. **Return file path and loader type**

## Module Path Types

### Absolute Paths
- `module` → `module.na` (Dana)
- `module.py` → `module.py` (Python)
- `module.submodule` → `module/submodule.na` (Dana)
- `module.submodule.py` → `module/submodule.py` (Python)

### Pure Dotted Relative Paths
- `.` → Current directory (Dana)
- `.py` → Current directory (Python)
- `..` → Parent directory (Dana)
- `..py` → Parent directory (Python)
- `...` → Grandparent directory (Dana)
- `...py` → Grandparent directory (Python)

### Relative Dotted Paths
- `.sibling` → `./sibling.na` (Dana)
- `.sibling.py` → `./sibling.py` (Python)
- `..parent_module` → `../parent_module.na` (Dana)
- `..parent_module.py` → `../parent_module.py` (Python)

## Error Handling
- **ModuleNotFoundError**: When module cannot be found
- **InvalidPathError**: When path syntax is invalid
- **LanguageMismatchError**: When language detection fails

## Testing Strategy
- Test each path type with various combinations
- Test error conditions
- Test edge cases (empty paths, invalid syntax)
- Test with both Dana and Python modules
- Test relative path resolution from different starting points
