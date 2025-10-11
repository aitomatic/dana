# Dana System Libraries

**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 1.0.0  
**Status:** Implementation Complete

## Overview

Dana implements a sophisticated **3-tier rationalized loading system** that provides zero-friction access to essential functions while maintaining modularity for advanced features. The system eliminates import overhead for core functionality while enabling explicit control over specialized modules.

## 3-Tier Library Architecture

### Tier 1: Initialization Library (`initlib/`)
**Purpose**: Bootstrap Dana environment during startup  
**Loading**: Automatic on `import dana`  
**Location**: `dana/libs/initlib/`

**Responsibilities**:
- Environment variable loading (.env files)
- Configuration system initialization
- Module system setup with default search paths
- Logging system configuration
- **Core library preloading** (Phase 3)

### Tier 2: Core Library (`corelib/`)
**Purpose**: Essential functions available globally  
**Loading**: Preloaded during startup  
**Location**: `dana/libs/corelib/`

**Structure**:
```
dana/libs/corelib/
├── py/           # Python function files (preloaded)
│   ├── py_math.py
│   ├── py_reason.py
│   ├── py_llm.py
│   └── ...
├── na/           # Dana module files
│   ├── __init__.na
│   ├── core.na
│   └── na_agent.na
└── register_corelib_functions.py
```

**Functions**: 20+ essential functions including `sum_range`, `is_odd`, `reason`, `llm`, `print`, `log`, `agent`, etc.

### Tier 3: Standard Library (`stdlib/`)
**Purpose**: Extended functionality requiring explicit imports  
**Loading**: On-demand via import statements  
**Location**: `dana/libs/stdlib/`

## Startup Sequence

### Phase 1: Essential Environment Setup
```python
# Automatic on import dana
import dana.libs.initlib as _dana_initlib
```

**Activities**:
- Load `.env` files following Dana's search hierarchy
- Initialize `ConfigLoader` (singleton pattern)
- Set `DANA_CONFIG` environment variable

### Phase 2: Core System Initialization (Conditional)
**Skipped in test mode** (`DANA_TEST_MODE=1`) for performance

**Activities**:
- Initialize Dana module system with default search paths
- Configure logging with default settings
- Set up module resolution infrastructure

### Phase 3: Core Library Preloading
```python
def _preload_corelib_functions():
    # Create temporary registry
    temp_registry = FunctionRegistry()
    
    # Register all core library functions
    register_corelib_functions(temp_registry)
    
    # Store for later use by DanaInterpreter
    registry_module._preloaded_corelib_functions = temp_registry._functions.copy()
```

**Benefits**:
- Zero runtime overhead for core functions
- Immediate availability without imports
- Consistent performance across all interpreter instances

### Phase 4: Standard Library Path Setup
**Activities**:
- Ensure stdlib is in `DANA_PATH` for on-demand loading
- Configure module search paths for future imports

## Module Resolution Process

### Search Path Hierarchy
1. **Current directory** (`Path.cwd()`)
2. **./dana directory** (`Path.cwd() / "dana"`)
3. **Core library** (`dana/libs/corelib`)
4. **Standard library** (`dana/libs/stdlib`)
5. **DANAPATH environment variable** (colon-separated)

### File Discovery Strategy
```python
def _find_module_file(self, module_name: str) -> Path | None:
    for search_path in self.search_paths:
        # 1. Direct .na file
        module_file = search_path / f"{module_name}.na"
        if module_file.exists():
            return module_file
            
        # 2. Legacy package/__init__.na
        init_file = search_path / module_name / "__init__.na"
        if init_file.exists():
            return init_file
            
        # 3. Directory package (modern)
        package_dir = search_path / module_name
        if package_dir.is_dir() and self._is_dana_package_directory(package_dir):
            return package_dir
```

### Package Structure Support
**Legacy Packages** (with `__init__.na`):
```
my_package/
├── __init__.na
├── utils.na
└── helpers.na
```

**Modern Packages** (directory-based):
```
my_package/
├── utils.na
├── helpers.na
└── sub_package/
    ├── more_utils.na
    └── config.na
```

## Function Registration System

### Core Library Function Registration

#### Python Functions (`py/` directory)
```python
def _register_python_functions(py_dir, registry):
    # Scan py/ directory for modules
    # Use __all__ convention to register functions
    # Remove 'py_' prefix for Dana registration
    # Register with SYSTEM namespace and trusted_for_context=True
```

**Process**:
1. Import Python modules from `py/` directory
2. Extract functions using `__all__` convention
3. Remove `py_` prefix for Dana naming
4. Register with `SYSTEM` namespace and `trusted_for_context=True`

#### Dana Functions (`na/` directory)
**Two-step process**:

**Step 1: Module Loading**
```python
def _load_init_module(init_file, registry):
    # Initialize module system with corelib paths
    initialize_module_system([corelib_dir])
    
    # Execute __init__.na to import all modules
    interpreter = DanaInterpreter()
    context = SandboxContext()
    interpreter._eval(init_content, context)
    
    # Store context for function wrappers
    registry._init_context = context
```

**Step 2: Function Wrapper Creation**
```python
def _register_dana_functions_from_init(registry):
    # Get context from loaded __init__.na
    context = getattr(registry, "_init_context", None)
    
    # Define functions to register (hardcoded mapping)
    module_functions = {
        "core": ["add_one", "add_two", "add_three", "add_four"]
    }
    
    # Create Python wrappers for Dana functions
    for module_name, func_names in module_functions.items():
        module_obj = context.get_scope("local")[module_name]
        
        for func_name in func_names:
            # Create wrapper that calls imported function
            wrapper_func = create_wrapper(module_obj, func_name)
            
            # Register as PythonFunction with trusted_for_context=True
            registry.register(
                name=func_name,
                func=PythonFunction(wrapper_func, trusted_for_context=True),
                namespace=RuntimeScopes.SYSTEM,
                func_type=FunctionType.PYTHON,
                overwrite=True,
                trusted_for_context=True
            )
```

### Runtime Function Loading
```python
def _load_preloaded_corelib_functions(self):
    # Check if preloaded functions are available
    if hasattr(registry_module, "_preloaded_corelib_functions"):
        preloaded_functions = registry_module._preloaded_corelib_functions
        
        # Merge into this registry
        for namespace, functions in preloaded_functions.items():
            if namespace not in self._functions:
                self._functions[namespace] = {}
            self._functions[namespace].update(functions)
```

## Module Import Process

### Import Statement Execution
```python
def _execute_dana_import(self, module_name: str, context_name: str, context: SandboxContext):
    # 1. Ensure module system initialized
    self._ensure_module_system_initialized()
    
    # 2. Handle relative imports
    absolute_module_name = self._resolve_relative_import(module_name, context)
    
    # 3. Get module loader and find spec
    loader = get_module_loader()
    spec = loader.find_spec(absolute_module_name)
    
    # 4. Create and execute module
    module = loader.create_module(spec)
    loader.exec_module(module)
    
    # 5. Set module in context
    context.set_in_scope(context_name, module, scope="local")
```

### Module Execution
```python
def exec_module(self, module: Module):
    # 1. Read source file
    source = origin_path.read_text()
    
    # 2. Parse with DanaParser
    parser = ParserCache.get_parser("dana")
    ast = parser.parse(source)
    
    # 3. Execute with DanaInterpreter
    interpreter = DanaInterpreter()
    context = SandboxContext()
    context._interpreter = interpreter
    context._current_module = module.__name__
    
    # 4. Execute AST and populate module
    interpreter._eval(ast, context)
    module.__dict__.update(context.get_scope("local"))
```

## Performance Optimizations

### Caching Strategy
- **Module Cache**: 150 modules cached for reuse
- **Namespace Cache**: 100 namespaces cached
- **Function Registry**: Preloaded functions shared across interpreters

### Test Mode Optimization
- **Skipped Initialization**: Heavy setup deferred when `DANA_TEST_MODE=1`
- **Faster Startup**: Core library preloading bypassed for tests
- **Reduced Overhead**: Minimal initialization for test performance

### Memory Management
- **Weak References**: Module instances use weak references for cleanup
- **Shared Resources**: Core library functions shared across all interpreters
- **Lazy Loading**: Standard library loaded only when imported

## Privacy and Security

### Privacy Rules
- **Underscore Prefix**: Names starting with `_` are private
- **Import Enforcement**: Private names cannot be imported
- **Scope Boundaries**: Respect public/private/system scope separation

### Security Features
- **Sandbox Context**: All module execution in isolated contexts
- **Trusted Functions**: Core library functions marked as `trusted_for_context=True`
- **Scope Validation**: Access control based on function metadata

## Error Handling

### Graceful Degradation
- **Preloading Failures**: Log warnings but don't fail startup
- **Module Not Found**: Clear error messages with search path information
- **Import Errors**: Detailed error context with available alternatives

### Error Recovery
- **Fallback Loading**: Core library functions loaded normally if preloading fails
- **Partial Registration**: Continue with available functions if some fail
- **Context Preservation**: Maintain execution context even with errors

## Integration Points

### Function Registry Integration
- **Unified Interface**: All functions (core, imported, built-in) through single registry
- **Namespace Support**: Consistent namespace handling across all function types
- **Type Detection**: Automatic detection of Dana vs Python functions

### Interpreter Integration
- **Automatic Loading**: Core functions available in all interpreter instances
- **Context Injection**: Proper context passing for all function types
- **Performance**: Zero overhead for core function access

### Module System Integration
- **Search Path Management**: Consistent path resolution across all import types
- **Package Support**: Both legacy and modern package structures
- **Caching**: Shared caching for improved performance

---

**Implementation Status**: Complete and production-ready  
**Performance**: Optimized for zero-friction core function access  
**Extensibility**: Modular design supports future enhancements 