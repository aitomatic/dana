# Dana Libraries

This directory contains the organized library structure for Dana, with core library functions.

## Structure

```
dana/libs/
├── corelib/           # Core library functions (preloaded at startup)
│   ├── __init__.py
│   ├── register_corelib_functions.py
│   ├── py/            # Python function files
│   │   ├── __init__.py
│   │   ├── math_functions.py
│   │   ├── text_functions.py
│   │   ├── reason_function.py
│   │   ├── llm_function.py
│   │   ├── log_function.py
│   │   ├── print_function.py
│   │   ├── agent_function.py
│   │   └── ... (other function files)
│   ├── na/            # Dana (.na) module files
│   │   └── __init__.py
│   └── README.md
├── initlib/           # Initialization and startup utilities
│   ├── __init__.py
│   ├── dana_load_dotenv.py
│   └── README.md
└── stdlib/            # Standard library (for future use)
    ├── __init__.py
    └── README.md
```

## Rationalized Library Loading System

Dana uses a rationalized library loading system that provides clear separation of concerns and optimal startup performance:

### 1. Initialization Library (`initlib/`)

**Purpose**: Conduct startup activities during Dana initialization.

**Activities**:
- **Environment Loading**: Load `.env` files following Dana's search hierarchy
- **Configuration Setup**: Initialize and cache configuration systems
- **Module System**: Set up Dana's module system with default search paths
- **Logging**: Configure logging system with default settings
- **Core Library Preloading**: Preload core library functions for immediate availability

**Execution**: Runs automatically when `import dana` is called (imports `dana.libs.initlib`)

**Performance**: Uses phased approach to balance startup speed with functionality

### 2. Core Library (`corelib/`)

**Purpose**: Provide all fundamental functions that are essential to the Dana language.

**Loading Strategy**: **Preloaded during startup** for immediate availability.

**Structure**:
- **`py/`**: Python function files (preloaded at startup)
- **`na/`**: Dana (.na) module files (for future use)

**Functions**:
- **Math Functions**: `sum_range`, `is_odd`, `is_even`, `factorial`
- **Text Functions**: `capitalize_words`, `title_case`
- **AI/LLM Functions**: `reason`, `llm`, `set_model`, `context_aware_reason`
- **Logging Functions**: `log`, `print`, `log_level`
- **Agent Functions**: `agent`
- **Utility Functions**: `str`, `cast`, `use`, `noop`
- **Framework Functions**: `poet`, `feedback`

**Implementation**:
- Functions are preloaded during `initlib` startup
- Stored in a temporary registry and made available to all `DanaInterpreter` instances
- Fallback to normal registration if preloading fails

### 3. Standard Library (`stdlib/`)

**Purpose**: Reserved for future standard library functions.

**Loading Strategy**: **Future use** - currently empty.

## Startup Sequence

```
1. Import dana → triggers dana.libs.initlib import
2. initlib startup activities:
   - Load environment variables
   - Initialize configuration
   - Set up module system
   - Configure logging
   - Preload corelib functions
3. DanaInterpreter creation:
   - Load preloaded corelib functions
   - Ready for execution
```

## Function Registration Order

1. **Core Library Functions** (preloaded - highest priority)
2. **Pythonic Built-in Functions** (lowest priority)

This registration order ensures that core library functions take precedence over built-in functions.

## Performance Benefits

### Startup Performance
- **Core Library**: Preloaded during startup for immediate availability
- **Test Mode**: Skips heavy initialization for faster test execution

### Runtime Performance
- **Core Functions**: Always available without import overhead
- **Module Resolution**: Efficient search through DANA_PATH

## Usage

### Core Library Functions

Core library functions are automatically available without imports:

```dana
# Math functions are globally available
result = sum_range(1, 10)
is_odd(7)
factorial(5)

# AI/LLM functions are globally available
answer = reason("What is 2 + 2?")
llm("Hello", "gpt-4")

# Logging functions are globally available
log("Hello, world!")
print("Output")
```

## Adding New Functions

### To Core Library

1. **Python Functions**: Create a new Python file in `dana/libs/corelib/py/`
2. **Dana Modules**: Create a new .na file in `dana/libs/corelib/na/`
3. Define functions with names ending in `_function`
4. Functions are automatically preloaded during startup

## Migration from Old Structure

The library functions have been moved from:
- `dana/libs/stdlib/core/` → `dana/libs/corelib/py/`
- All functions are now preloaded at startup

All import paths have been updated to reflect the new organization.

## Testing

The rationalized library loading system is tested in `tests/functional/library_loading/test_rationalized_library_loading.py`:

- Startup activities verification
- Core library preloading tests
- Performance benchmarks
- Fallback loading mechanisms
- Test mode behavior 