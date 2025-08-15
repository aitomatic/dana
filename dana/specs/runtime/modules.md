# Dana Module System Specification

**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 1.0.0  
**Status:** Implementation-based specification

## Overview

The Dana module system provides a comprehensive module loading and management infrastructure that supports both Dana (`.na`) and Python (`.py`) modules. The system implements Python's import protocols while maintaining Dana-specific features like export statements and privacy rules.

## Core Architecture

### Module System Components

The module system consists of four primary components located in `dana/core/runtime/modules/core/`:

1. **ModuleLoader** (`loader.py`) - Finds and loads modules
2. **ModuleRegistry** (`registry.py`) - Tracks loaded modules and dependencies  
3. **Module Types** (`types.py`) - Core data structures
4. **Import Handler** (`dana/core/lang/interpreter/executor/statement/import_handler.py`) - Executes import statements

### Initialization

```python
# dana/core/runtime/modules/core/__init__.py:21-51
def initialize_module_system(search_paths: list[str] | None = None) -> None:
    # Default search paths:
    # 1. Current directory
    # 2. ./dana directory  
    # 3. dana/libs/corelib
    # 4. dana/libs/stdlib
    # 5. DANAPATH environment variable paths
```

## Module Types and Data Structures

### ModuleSpec
```python
# dana/core/runtime/modules/core/types.py:20-44
@dataclass
class ModuleSpec:
    name: str                                    # Fully qualified module name
    loader: "ModuleLoader"                       # Loader instance
    origin: str | None                          # File path or description
    cache: dict[str, Any]                       # Cache data
    parent: str | None = None                   # Parent package name
    has_location: bool = True                   # Has concrete file location
    submodule_search_locations: list[str] | None = None  # For packages
```

### Module Class
```python
# dana/core/runtime/modules/core/types.py:67-136
class Module:
    __name__: str           # Module name
    __file__: str | None    # File path
    __package__: str        # Package name
    __spec__: ModuleSpec    # Module specification
    __path__: list[str]     # Package search paths
    __exports__: set[str]   # Exported symbols
    __doc__: str           # Documentation
```

### ModuleType Enumeration
```python
# dana/core/runtime/modules/core/types.py:139-145
class ModuleType:
    DANA = "dana"          # Native Dana modules (.na)
    PYTHON = "python"      # Python modules (.py)
    GENERATED = "gen"      # Generated modules
    HYBRID = "hybrid"      # Mixed Dana/Python modules
```

## Module Loading Process

### 1. Module Discovery (`ModuleLoader.find_spec`)

The loader searches for modules in the following order:

```python
# dana/core/runtime/modules/core/loader.py:279-311
# Search hierarchy:
# 1. Importing module's directory (for relative imports)
# 2. Parent package's submodule_search_locations
# 3. Regular search paths:
#    - Current directory
#    - ./dana directory
#    - Core library (dana/libs/corelib)
#    - Standard library (dana/libs/stdlib)
#    - DANAPATH environment variable paths
```

### 2. Package Detection

Dana supports three package types:

```python
# dana/core/runtime/modules/core/loader.py:552-637
def _find_module_file(self, module_name: str) -> Path | None:
    # 1. Direct .na file
    module_file = search_path / f"{module_name}.na"
    
    # 2. Legacy package with __init__.na
    init_file = search_path / module_name / "__init__.na"
    
    # 3. Directory package (modern)
    package_dir = search_path / module_name
    if package_dir.is_dir() and self._is_dana_package_directory(package_dir):
        return package_dir
```

A directory is considered a Dana package if it contains:
- At least one `.na` file, OR
- At least one subdirectory that is also a Dana package

### 3. Module Creation (`ModuleLoader.create_module`)

```python
# dana/core/runtime/modules/core/loader.py:353-399
def create_module(self, spec: PyModuleSpec) -> Module | None:
    module = Module(__name__=spec.name, __file__=spec.origin)
    
    # Set package attributes for different types:
    if spec.origin.endswith("__init__.na"):
        module.__path__ = [str(origin_path.parent)]
        module.__package__ = spec.name
    elif origin_path.is_dir():
        module.__path__ = [str(origin_path)]
        module.__package__ = spec.name
    elif "." in spec.name:
        module.__package__ = spec.name.rsplit(".", 1)[0]
```

### 4. Module Execution (`ModuleLoader.exec_module`)

```python
# dana/core/runtime/modules/core/loader.py:401-507
def exec_module(self, module: Module) -> None:
    # 1. Directory packages - no code to execute
    if origin_path.is_dir():
        return
    
    # 2. Parse source code with DanaParser
    ast = parser.parse(source)
    
    # 3. Execute with DanaInterpreter in SandboxContext
    interpreter = DanaInterpreter()
    context = SandboxContext()
    context._current_module = module.__name__
    interpreter._execute(ast, context)
    
    # 4. Update module namespace
    module.__dict__.update(context.get_scope("local"))
    module.__dict__.update(context.get_scope("public"))
    
    # 5. Handle exports
    if hasattr(context, "_exports"):
        module.__exports__ = context._exports
    else:
        # Auto-export non-underscore names
        module.__exports__ = {name for name in all_vars 
                             if not name.startswith("_")}
```

## Import Statement Execution

### Import Handler Architecture

```python
# dana/core/lang/interpreter/executor/statement/import_handler.py:38-54
class ImportHandler(Loggable):
    MODULE_CACHE_SIZE = 150      # Cached modules
    NAMESPACE_CACHE_SIZE = 100   # Cached namespaces
    
    def __init__(self):
        self._module_cache = {}
        self._namespace_cache = {}
```

### Import Statement Types

#### 1. Simple Import
```python
# import module_name
# import module_name as alias
def execute_import_statement(self, node: ImportStatement, context: SandboxContext):
    if module_name.endswith(".py"):
        # Python module import
        self._execute_python_import(module_name, context_name, context)
    else:
        # Dana module import
        self._execute_dana_import(module_name, context_name, context)
```

#### 2. From Import
```python
# from module_name import name1, name2
# from module_name import name as alias
def execute_import_from_statement(self, node: ImportFromStatement, context: SandboxContext):
    # Load module and extract specific names
    # Enforce privacy rules and export restrictions
```

### Relative Import Resolution

```python
# dana/core/lang/interpreter/executor/statement/import_handler.py:350-410
def _resolve_relative_import(self, module_name: str, context: SandboxContext) -> str:
    if module_name.startswith("."):
        # Count leading dots for parent traversal
        level = len(module_name) - len(module_name.lstrip("."))
        
        # Get current package from context
        current_package = getattr(context, "_current_package", "")
        
        # Navigate up package hierarchy
        parts = current_package.split(".")
        if level > len(parts):
            raise ImportError("Attempted relative import beyond top-level package")
```

## Module Registry

### Singleton Pattern
```python
# dana/core/runtime/modules/core/registry.py:17-35
class ModuleRegistry:
    def __new__(cls) -> "ModuleRegistry":
        # Global singleton instance
        global _REGISTRY
        if _REGISTRY is None:
            _REGISTRY = super().__new__(cls)
        return _REGISTRY
```

### Registry Operations
```python
# dana/core/runtime/modules/core/registry.py
_modules: dict[str, Module]           # name -> module
_specs: dict[str, ModuleSpec]         # name -> spec  
_aliases: dict[str, str]              # alias -> real name
_dependencies: dict[str, set[str]]   # module -> dependencies
_loading: set[str]                    # modules being loaded
```

### Circular Dependency Detection
```python
# dana/core/runtime/modules/core/registry.py:166-180
def start_loading(self, name: str) -> None:
    if name in self._loading:
        raise CircularImportError(f"Circular import detected: {name}")
    self._loading.add(name)

def finish_loading(self, name: str) -> None:
    self._loading.discard(name)
```

## Export and Privacy System

### Export Statement
```python
# dana/core/lang/interpreter/executor/statement/agent_handler.py:169-198
def execute_export_statement(self, node: ExportStatement, context: SandboxContext):
    # Add name to context._exports set
    if not hasattr(context, "_exports"):
        context._exports = set()
    context._exports.add(node.name)
```

### Privacy Rules

1. **Underscore Convention**: Names starting with `_` are private
2. **Export Enforcement**: Only exported names can be imported
3. **Default Behavior**: All non-underscore names are auto-exported

```python
# dana/core/lang/interpreter/executor/statement/import_handler.py:327-335
# Enforce underscore privacy
if name.startswith("_"):
    raise SandboxError(f"Cannot import '{name}': names starting with '_' are private")

# Respect __exports__ if available
if hasattr(module, "__exports__") and name not in module.__exports__:
    raise SandboxError(f"Cannot import '{name}': not in module exports")
```

## Caching Strategy

### Module Cache
- **Size**: 150 modules maximum
- **Key Format**: `"dana:{module_name}"` or `"py:{module_name}"`
- **Scope**: Per ImportHandler instance

### Namespace Cache
- **Size**: 100 namespaces maximum
- **Purpose**: Cache parent namespace objects for submodule access

### Performance Optimizations
```python
# dana/core/lang/interpreter/executor/statement/import_handler.py:170-179
# Check cache first
cache_key = f"dana:{absolute_module_name}"
if cache_key in self._module_cache:
    module = self._module_cache[cache_key]
    context.set_in_scope(context_name, module, scope="local")
    return
```

## Python Module Integration

### Python Module Import
```python
# dana/core/lang/interpreter/executor/statement/import_handler.py:123-155
def _execute_python_import(self, module_name: str, context_name: str, context: SandboxContext):
    # Strip .py extension
    import_name = module_name[:-3] if module_name.endswith(".py") else module_name
    
    # Use standard importlib
    module = importlib.import_module(import_name)
    
    # Set in context
    context.set(f"local:{context_name}", module)
```

### Python Standard Library Filtering
The loader explicitly filters out Python standard library modules to avoid conflicts:

```python
# dana/core/runtime/modules/core/loader.py:79-211
# Extensive list of Python standard library modules to skip:
if fullname.split(".")[0] in {
    "collections", "sys", "os", "json", "math", "datetime",
    "traceback", "importlib", "threading", "logging", ...
}:
    return None  # Let Python handle it
```

## Module Function Context

### Function Registration
```python
# dana/core/runtime/modules/core/loader.py:509-549
def _setup_module_function_context(self, module: Module, interpreter: DanaInterpreter, context: SandboxContext):
    # Find all DanaFunction objects in module
    for name, obj in module.__dict__.items():
        if isinstance(obj, DanaFunction):
            # Register in interpreter's function registry
            interpreter.function_registry.register(
                name=func_name,
                func=func_obj,
                namespace="local",
                func_type=FunctionType.DANA,
                metadata=metadata,
                overwrite=True
            )
```

## Error Handling

### Module Errors
```python
# dana/core/runtime/modules/core/errors.py
class ModuleError(Exception): pass
class ModuleNotFoundError(ModuleError): pass
class CircularImportError(ModuleError): pass
class ImportError(ModuleError): pass
class SyntaxError(ModuleError): pass
```

### Error Recovery
- Preloading failures log warnings but don't fail startup
- Module not found provides clear error messages with search paths
- Import errors include detailed context and available alternatives

## Special Features

### 1. Hybrid Module/Package Support
A single `.na` file can serve as both a module and a package:
```
module.na          # The module file
module/            # Directory with same name
└── submodule.na   # Submodule
```

### 2. Directory Package Auto-detection
Directories containing `.na` files are automatically treated as packages without requiring `__init__.na`.

### 3. Import Hook Isolation
The module loader does NOT install itself in `sys.meta_path` to avoid interfering with Python imports. It's called directly by Dana's import statement executor.

### 4. Context-Aware Module Execution
Modules are executed with proper context including:
- `_current_module`: The module being executed
- `_current_package`: The parent package for relative imports
- `_interpreter`: Reference to the interpreter instance

## Integration Points

### With Function Registry
- Imported functions are automatically registered
- Module functions have access to interpreter's function registry
- Recursive calls within modules are properly supported

### With Sandbox Context
- All module execution happens in isolated SandboxContext
- Public variables are merged into global public scope
- System variables (for agents) are preserved with `system:` prefix

### With Parser System
- Uses ParserCache for efficient AST parsing
- Proper error handling with line numbers and source context
- Support for Dana's extended syntax features

---

**Implementation Status**: Production-ready with comprehensive test coverage  
**Performance**: Optimized with multi-level caching and lazy loading  
**Compatibility**: Full support for Dana and Python module integration