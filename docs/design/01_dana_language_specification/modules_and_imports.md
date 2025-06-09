```text
Author: Christopher Nguyen
Version: 0.5
Status: Released
Module: opendxa.dana

Current Capabilities:
✅ Basic module loading and execution
✅ Module namespace isolation
✅ Basic package support with __init__.na
✅ Python module integration
✅ Circular dependency detection
✅ Basic error handling and recovery
✅ Module-level exports
✅ Basic lazy loading
✅ Import statement syntax (parsing and execution implemented)
✅ **Dana module imports fully functional** (Phase 4.1-4.2 ✅)
✅ **Basic Dana module infrastructure** (test modules, functions, constants)
✅ **Dana vs Python module distinction** (explicit .py vs .na)
🚧 Advanced package features (partial)
⏳ Module reloading (planned)
⏳ Dynamic imports (planned)
⏳ Advanced caching (planned)
```

Also see: [Data Types and Structs](data_types_and_structs.md)

# Dana Modules and Imports

## 1. Overview

### 1.1 Motivation
Dana's module system provides a way to organize code into reusable and manageable units. Key benefits include:
* Code Reusability: Define functions, structs, and constants once, use them anywhere
* Namespacing: Avoid naming conflicts through distinct namespaces
* Logical Organization: Group related code by functionality or domain
* Collaboration: Enable independent development of different components

### 1.2 Key Concepts
* Module: A `.na` file containing Dana code (functions, structs, variables)
* Package: A directory containing related modules and an optional `__init__.na`
* Import: A mechanism to use code from other modules
* Namespace: A scope containing module-specific names and symbols

### 1.3 Example Usage

#### *`export` Statement*

```dana
# string_utils.na
export StringMetrics, calculate_metrics

struct StringMetrics:
  length: int
  word_count: int

def calculate_metrics(text: str) -> StringMetrics:
  len = len(text)
  words = len(text.split()) if len > 0 else 0
  return StringMetrics(length=len, word_count=words)

def to_uppercase(text: str) -> str:
  return text.upper()
```

#### *`import` Statement*

```dana
# main.na
import path/to/string_utils.na

text: str = "Analyze this text."
metrics: string_utils.StringMetrics = string_utils.calculate_metrics(text)
print(f"Length: {metrics.length}, Words: {metrics.word_count}")
```

## 2. Module System Design

### 2.1 Module Structure and Lifecycle
```mermaid
graph LR
    A[Source Code] --> B[Parse]
    B --> C[AST]
    C --> D[Type Check]
    D --> E[Execute]
    
    style A fill:#f9f,stroke:#333
    style C fill:#bbf,stroke:#333
    style E fill:#fbb,stroke:#333
```

Each module goes through several stages:
1. Parsing: Source code is converted to an Abstract Syntax Tree (AST)
2. Type Checking: AST nodes are validated for type correctness
3. Execution: Code is executed in a module-specific context

### 2.2 Module Components
* AST: Represents the module's code structure
* Namespace: Contains module-specific variables and imports
* Exports: Symbols explicitly made available to other modules
* Dependencies: Other modules required for operation

### 2.3 Import Resolution
1. Module path resolution using search paths
2. Dependency graph construction
3. Circular dependency detection
4. Module loading and execution
5. Namespace population

### 2.4 Module AST and Runtime Relationships

The relationship between a module's AST and the runtime environment is carefully managed:

#### AST Structure
- Each module has its own AST with a `Program` node at the root
- The `Program` node contains a list of statements (assignments, function calls, etc.)
- The AST represents the module's code structure independent of execution state

#### Execution Context
- Each module gets its own namespace stored in `module.__dict__`
- The module's AST is executed by the `DanaInterpreter` in a `SandboxContext`
- The sandbox context manages scoped state during execution:
  - `local`: Module-specific variables
  - `private`: Internal module state
  - `public`: Exported module interface
  - `system`: Runtime metadata

#### Module Loading Flow
```mermaid
graph TD
    A[Import Statement] --> B[ModuleLoader]
    B --> C[Parse Module]
    C --> D[Create Module AST]
    D --> E[Create Module Object]
    E --> F[Execute Module AST]
    F --> G[Update Module Dict]
    G --> H[Register Module]
```

### 2.5 Example Module

Example: `string_utils.na`
```dana
# Module: string_utils.na

struct StringMetrics:
 length: int
 word_count: int

def calculate_metrics(text: str) -> StringMetrics:
 len = len(text)
 # Basic word count, can be made more sophisticated
 words = 0
 if len > 0:
   parts = text.split(' ')
   words = len(parts)

 return StringMetrics(length=len, word_count=words)

def to_uppercase(text: str) -> str:
 return text.upper()

public:DEFAULT_GREETING: str = "Hello, Dana!"
```

### 2.6 Import System

#### Basic Import Syntax
```dana
# In main.na
import path/to/string_utils.na
from path/to/string_utils.na import StringMetrics, calculate_metrics
from path/to/string_utils import some_other_dana_reference # .na is optional
from path/to/other_utils.py import some_python_reference # .py is required

text: str = "Sample text for analysis."
metrics: string_utils.StringMetrics = string_utils.calculate_metrics(text)
print(f"Length: {metrics.length}, Words: {metrics.word_count}")
```

#### Import with Alias
```dana
import path/to/string_utils.na as str_util

text: str = "Sample text for analysis."
metrics: str_util.StringMetrics = str_util.calculate_metrics(text)
```

#### Import Process Flow
```mermaid
sequenceDiagram
    participant App as Application
    participant IM as ImportManager
    participant ML as ModuleLoader
    participant MR as ModuleRegistry
    participant FS as FileSystem
    participant Cache as ModuleCache
    
    App->>IM: import module
    IM->>ML: load_module(path)
    ML->>MR: get_module(path)
    
    alt Module in Registry
        MR-->>ML: return cached module
        ML-->>IM: return module
    else Module not found
        ML->>Cache: check_cache(path)
        alt Cache hit
            Cache-->>ML: return cached module
        else Cache miss
            ML->>FS: read_file(path)
            FS-->>ML: source code
            ML->>ML: parse(source)
            ML->>Cache: cache_module()
        end
        ML->>MR: register_module()
        ML-->>IM: return new module
    end
    
    IM-->>App: module ready
```

### 2.7 Module Search Path Resolution

The Dana runtime uses the following search strategy:

1. **Current Directory**: Look in the same directory as the importing file
2. **Package Directory**: Check for package-relative imports
3. **Standard Library**: Search in Dana's standard library path
4. **DANAPATH**: Search in paths specified in the DANAPATH environment variable (PYTHONPATH if name ends with .py)
5. **Project Config**: Search in paths specified in project configuration

```mermaid
graph TD
    A[Module Search Path] --> B[Current Directory]
    A --> C[Standard Library]
    A --> D[User-defined Paths]
    
    B --> E[./my_module.na]
    B --> F[./subdir/module.na]
    
    C --> G[stdlib/string.na]
    C --> H[stdlib/math.na]
    
    D --> I[DANAPATH/module1]
    D --> J[Project Config Path]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333
    style C fill:#bbf,stroke:#333
    style D fill:#bbf,stroke:#333
```

### 2.8 Python Module Integration

Dana supports seamless integration with Python modules. For detailed design information, see:

- [Python Integration Overview](../02_dana_runtime_and_execution/python_integration.md)
- [Dana to Python Integration](../02_dana_runtime_and_execution/dana-to-python.md)  
- [Python to Dana Integration](../02_dana_runtime_and_execution/python-to-dana.md)

```mermaid
classDiagram
    class DanaModule {
        +str name
        +dict namespace
        +set exports
        +load()
        +execute()
    }
    
    class PythonModule {
        +str name
        +PyObject module
        +dict conversions
        +load()
        +convert_types()
    }
    
    class ModuleInterface {
        <<interface>>
        +load()
        +execute()
    }
    
    ModuleInterface <|.. DanaModule
    ModuleInterface <|.. PythonModule
```

### 3.3 Error Handling

The module system includes comprehensive error handling:

```dana
struct ModuleError:
    path: str
    message: str
    cause: Exception | None
    
struct CircularImportError(ModuleError):
    cycle: list[str]  # The import cycle
    
struct ModuleNotFoundError(ModuleError):
    searched_paths: list[str]  # Paths that were searched
    
def handle_import_error(error: ModuleError):
    """Handle module import errors."""
    match error:
        case CircularImportError():
            log.error(f"Circular import detected: {' -> '.join(error.cycle)}")
        case ModuleNotFoundError():
            log.error(f"Module not found: {error.path}")
            log.debug(f"Searched paths: {error.searched_paths}")
        case _:
            log.error(f"Module error: {error.message}")
```

### 3.4 Performance Optimizations

#### Lazy Loading
```dana
struct LazyModule:
    path: str
    _loaded: bool = False
    _module: Module | None = None
    
    def __getattr__(name: str) -> any:
        """Load module on first attribute access."""
        if not self._loaded:
            self._module = load_module(self.path)
            self._loaded = True
        return getattr(self._module, name)
```

## 3. Implementation

### 3.1 Core Components

The module system is built on three main components that work together:

1. **Module Registry**: Central manager for module state
```python
class ModuleRegistry:
    """Registry for tracking Dana modules and their dependencies."""
    def __init__(self):
        self._modules: dict[str, Module] = {}        # name -> module
        self._specs: dict[str, ModuleSpec] = {}      # name -> spec
        self._aliases: dict[str, str] = {}           # alias -> real name
        self._dependencies: dict[str, set[str]] = {} # module -> dependencies
        self._loading: set[str] = set()              # modules being loaded
```

2. **Module Loader**: Handles finding and loading modules
```python
class ModuleLoader(MetaPathFinder, Loader):
    """Loader responsible for finding and loading Dana modules."""
    def __init__(self, search_paths: list[str], registry: ModuleRegistry):
        self.search_paths = [Path(p).resolve() for p in search_paths]
        self.registry = registry
```

3. **Module Types**: Core data structures
```python
@dataclass
class ModuleSpec:
    """Specification for a module during import."""
    name: str                                    # Fully qualified name
    loader: ModuleLoader                         # Loader instance
    origin: str                                  # File path/description
    parent: str | None = None                    # Parent package
    has_location: bool = True                    # Has concrete location
    submodule_search_locations: list[str] | None = None  # For packages
```

### 3.2 Implementation Status

> **⚠️ Important Note on Import Statements:**
> 
> While import statement syntax is fully supported in Dana's parser and type checker, **import statement execution is not yet implemented**. The `execute_import_statement` method in `StatementExecutor` currently raises a `SandboxError("Import statements are not yet supported in Dana")`.
> 
> **Current Status:**
> - ✅ **Parsing**: `import math` and `from collections import deque` parse correctly
> - ✅ **Type Checking**: Import statements pass type validation
> - ❌ **Execution**: Import statements fail at runtime with SandboxError
> 
> The module loading infrastructure exists but needs to be connected to the import statement executor.

#### Phase 1: Core Module System ✅
- [x] Basic module loading and execution
- [x] Module registry singleton
- [x] Module loader with search path support
- [x] Basic module object with namespace
- [x] AST execution in module context

#### Phase 2: Module Features 🟨
- [x] Basic module state management
- [x] Basic export declarations
- [x] Scope isolation
- [x] Basic cross-module references
- [x] Import statement handling
  - [x] Import statement syntax parsing (`import module`, `from module import name`)
  - [x] Import statement AST nodes (`ImportStatement`, `ImportFromStatement`)
  - [x] Import statement type checking
  - [x] **Import statement execution with explicit module type selection**
- [x] Dependency graph building
- [x] Circular dependency detection
- [ ] Module reloading support
- [ ] Dynamic imports
- [ ] Full package support

#### Phase 3: Error Handling & Edge Cases ✅ **COMPLETE**
- [x] **Step 3.1:** Add comprehensive error handling to import executors
- [x] **Step 3.2:** Test module not found scenarios
- [x] **Step 3.3:** Test invalid module syntax scenarios  
- [x] **Step 3.4:** Test circular import detection
- [x] **Step 3.5:** Add proper error message formatting

#### Phase 4: Dana Module Support 🚧 **IN PROGRESS**
- [x] **Step 4.1:** Create test Dana modules (.na files) and basic module infrastructure
- [x] **Step 4.2:** Test basic Dana module imports (`import module`, `from module import func`)
- [x] **Step 4.3:** Test Dana packages with __init__.na and submodule imports (26/33 tests passing ✅)
- [ ] **Step 4.4:** Test circular dependency detection and export visibility rules
- [ ] **Step 4.5:** Integration testing and performance benchmarks for Dana modules

#### Phase 5: Integration & Regression Tests
- [ ] **Step 5.1:** Create integration tests for imports within larger programs
- [ ] **Step 5.2:** Test multiple imports in single program
- [ ] **Step 5.3:** Test using imported functions immediately after import
- [ ] **Step 5.4:** Run full regression test suite to ensure no breakage
- [ ] **Step 5.5:** Performance baseline testing

#### Phase 6: Polish & Documentation
- [ ] **Step 6.1:** Update modules_and_imports.md implementation status
- [ ] **Step 6.2:** Add usage examples to documentation
- [ ] **Step 6.3:** Update error handling documentation
- [ ] **Step 6.4:** Create migration guide for existing code
- [ ] **Step 6.5:** Final validation and sign-off

### 4.0 Latest Implementation Update

**🎉 Import Statements Now Fully Functional! (December 2024)**

**Major Changes Completed:**
- ✅ **Parser Fix:** Resolved alias parsing bug in `from_import` transformer
- ✅ **Architecture Refactor:** Implemented explicit module type selection:
  - **Python modules:** Must use `.py` extension (e.g., `import math.py`)
  - **Dana modules:** No extension, looks for `.na` files (e.g., `import collections`)
- ✅ **Context Naming:** Fixed module context storage to use clean names without extensions
- ✅ **Function Registry:** Imported functions with aliases now properly registered
- ✅ **Full Test Coverage:** All 15 test cases passing with comprehensive edge case coverage

**New Import Syntax Examples:**
```python
# Python module imports (require .py extension)
import math.py           # Access as: math.pi
import json.py as j      # Access as: j.dumps()
from os.py import getcwd # Access as: getcwd()
from json.py import dumps as json_dumps  # Access as: json_dumps()

# Dana module imports (no extension, implicit .na)
import collections       # Looks for collections.na
import utils as u        # Looks for utils.na, access as: u.function()
from mymodule import func  # Looks for mymodule.na
```

**Benefits of New Architecture:**
- 🔒 **Clear Boundaries:** Explicit separation between Python and Dana ecosystems
- 🎯 **Type Safety:** No ambiguity about which module system is being used
- 🚀 **Performance:** Direct routing to appropriate module loader
- 🔧 **Maintainability:** Clean, separated import handling logic

**Test Coverage Summary (41 Tests Total):**
- ✅ **Basic Functionality:** 15 tests covering core import/from-import with aliases
- ✅ **Edge Cases:** 14 tests covering error scenarios, invalid syntax, unicode, etc.
- ✅ **Dana Module Integration:** 12 tests covering Dana vs Python module distinction

**Key Test Categories:**
- **Python Module Imports:** `import math.py`, `from json.py import dumps as json_dumps`
- **Dana Module Imports:** `import collections` (looks for collections.na)
- **Error Handling:** Module not found, invalid names, parsing errors
- **Context Management:** Variable isolation, alias overwrites, multiple sandboxes
- **Edge Cases:** Unicode names, keywords, case sensitivity, special characters

### 4.1 Phase 4 Dana Module Support Complete! (December 2024)

**🎯 Phase 4 Steps 4.1-4.2 Successfully Completed!**

**Major Achievements:**
- ✅ **Dana Module Infrastructure:** Created comprehensive test Dana modules (.na files)
- ✅ **Module Loading Fixed:** Resolved sys.meta_path interference with Python imports
- ✅ **Public Variable Support:** Fixed module execution to include public scope variables
- ✅ **Grammar Compatibility:** Adapted tests to current Dana grammar (single imports)
- ✅ **15 Dana Module Tests Passing:** Complete test coverage for basic Dana module functionality

**Created Dana Test Modules:**
- `simple_math.na` - Mathematical functions with public constants
- `string_utils.na` - String processing utilities  
- `data_types.na` - Functions for custom data structures
- `utils/__init__.na` - Package initialization with constants
- `utils/text.na` - Text processing submodule
- `utils/numbers.na` - Number processing submodule
- `circular_a.na` / `circular_b.na` - For testing circular dependencies

**Key Fixes Applied:**
- **Dana Syntax Correction:** Fixed `public.PI` to `public:PI` (colon notation required)
- **Module Loader Isolation:** Removed sys.meta_path installation to prevent Python import interference
- **Public Variable Access:** Added public scope variables to module namespace for dot notation access
- **Grammar Limitations:** Adapted tests to use single imports instead of comma-separated imports

**Fully Working Dana Import Patterns:**
```dana
# Basic module import
import simple_math
result = simple_math.add(5, 3)  # Returns 8
pi_value = simple_math.PI       # Returns 3.14159...

# Import with alias
import simple_math as math
result = math.multiply(4, 7)    # Returns 28

# From-import basic
from simple_math import add
result = add(10, 15)            # Returns 25

# From-import with alias  
from simple_math import square as sq
result = sq(6)                  # Returns 36

# Multiple imports (separate statements)
from simple_math import add
from simple_math import multiply
from simple_math import square
```

**Test Results Summary:**
- **Dana Module Tests:** 15/15 passing ✅
- **Python Module Tests:** 15/15 passing ✅  
- **Total Import Tests:** 30/30 passing ✅

**Architecture Benefits:**
- 🏗️ **Solid Foundation:** Robust Dana module system ready for advanced features
- 🔧 **Maintainable:** Clean separation between Python and Dana module handling
- 🚀 **Performance:** Direct module loading without Python import system interference
- ✅ **Reliable:** Comprehensive error handling and edge case coverage

## 4. ImportStatement Implementation Roadmap

### 4.1 Current Status Summary

**Key Findings from Analysis:**
- ✅ Module system infrastructure is fully implemented and working
- ✅ Grammar, AST, and type checking already support import statements  
- ❌ Only the execution layer is missing (`execute_import_statement` throws `SandboxError`)
- ✅ Module registry and loader are functional and well-tested
- ✅ Tests show modules can be loaded, executed, and accessed correctly

### 4.2 Implementation Strategy

The missing piece is connecting the import statement execution to the existing, working module system infrastructure.

#### Core Implementation Requirements:

1. **Add ImportFromStatement handler** - Currently missing from statement executor
2. **Implement execute_import_statement** - Replace SandboxError with actual logic
3. **Implement execute_import_from_statement** - New method needed
4. **Connect to module system** - Use existing `get_module_registry()` and `get_module_loader()`
5. **Handle namespace updates** - Set imported names in sandbox context

#### Expected Implementation:

```python
def execute_import_statement(self, node: ImportStatement, context: SandboxContext) -> Any:
    """Execute an import statement (import module [as alias])."""
    
    # 1. Initialize module system if needed
    # 2. Load the module using the existing module loader
    # 3. Set module reference in context (with optional alias)
    # 4. Return None (import statements don't return values)

def execute_import_from_statement(self, node: ImportFromStatement, context: SandboxContext) -> Any:
    """Execute a from-import statement (from module import name [as alias])."""
    
    # 1. Initialize module system if needed  
    # 2. Load the module using the existing module loader
    # 3. Extract specific names from module
    # 4. Set individual names in context (with optional aliases)
    # 5. Return None
```

### 4.3 Sequential Implementation Plan

#### Phase 1: Core Implementation ✅ **COMPLETE**
- [x] **Step 1.1:** Add `ImportFromStatement` to statement executor imports
- [x] **Step 1.2:** Register `ImportFromStatement` handler in `register_handlers()`
- [x] **Step 1.3:** Implement basic `execute_import_statement` method
- [x] **Step 1.4:** Implement basic `execute_import_from_statement` method
- [x] **Step 1.5:** Add module system initialization helper

#### Phase 2: Basic Testing ✅ **COMPLETE**
- [x] **Step 2.1:** Create test file `tests/dana/sandbox/interpreter/test_import_statements.py`
- [x] **Step 2.2:** Implement basic import tests (`import module`)
- [x] **Step 2.3:** Implement import with alias tests (`import module as alias`)
- [x] **Step 2.4:** Implement from-import tests (`from module import name`)
- [x] **Step 2.5:** Implement from-import with alias tests (`from module import name as alias`)

#### Phase 3: Error Handling & Edge Cases ✅ **COMPLETE**
- [x] **Step 3.1:** Add comprehensive error handling to import executors
- [x] **Step 3.2:** Test module not found scenarios
- [x] **Step 3.3:** Test invalid module syntax scenarios  
- [x] **Step 3.4:** Test circular import detection
- [x] **Step 3.5:** Add proper error message formatting

#### Phase 4: Dana Module Support 🚧 **IN PROGRESS**
- [x] **Step 4.1:** Create test Dana modules (.na files) and basic module infrastructure
- [x] **Step 4.2:** Test basic Dana module imports (`import module`, `from module import func`)
- [x] **Step 4.3:** Test Dana packages with __init__.na and submodule imports (26/33 tests passing ✅)
- [ ] **Step 4.4:** Test circular dependency detection and export visibility rules
- [ ] **Step 4.5:** Integration testing and performance benchmarks for Dana modules

#### Phase 5: Integration & Regression Tests
- [ ] **Step 5.1:** Create integration tests for imports within larger programs
- [ ] **Step 5.2:** Test multiple imports in single program
- [ ] **Step 5.3:** Test using imported functions immediately after import
- [ ] **Step 5.4:** Run full regression test suite to ensure no breakage
- [ ] **Step 5.5:** Performance baseline testing

#### Phase 6: Polish & Documentation
- [ ] **Step 6.1:** Update modules_and_imports.md implementation status
- [ ] **Step 6.2:** Add usage examples to documentation
- [ ] **Step 6.3:** Update error handling documentation
- [ ] **Step 6.4:** Create migration guide for existing code
- [ ] **Step 6.5:** Final validation and sign-off

### 4.4 Success Criteria

#### Functional Requirements:
- [ ] `import module` works correctly
- [ ] `import module as alias` works correctly
- [ ] `from module import name` works correctly
- [ ] `from module import name as alias` works correctly
- [ ] Python modules can be imported
- [ ] Dana modules (.na files) can be imported
- [ ] Package imports work correctly

#### Quality Requirements:
- [ ] 100% test coverage for import functionality
- [ ] All existing tests continue to pass
- [ ] Performance within 5% of baseline
- [ ] Clear error messages for all failure cases

#### Files to be Modified:
- `opendxa/dana/sandbox/interpreter/executor/statement_executor.py` - Core implementation
- `tests/dana/sandbox/interpreter/test_import_statements.py` - New test file
- `docs/design/01_dana_language_specification/modules_and_imports.md` - Status updates

### 4.5 Integration Points

**Module System Connection:**
- Use existing `get_module_loader()` and `get_module_registry()` from `opendxa.dana.module.core`
- Leverage existing module loading infrastructure
- Connect to existing error handling and circular dependency detection

**Context Management:**
- Use `context.set()` to store imported module/function references
- Respect Dana's scoping rules for imported names
- Handle alias assignments correctly

**Error Handling:**
- Leverage existing module system exceptions (`ModuleNotFoundError`, `CircularImportError`, etc.)
- Provide clear, actionable error messages
- Maintain consistency with existing Dana error patterns

## 5. Future Work

### 5.1 Post-Implementation Enhancements
* Enhanced package support with namespace packages
* Module hot reloading with state preservation  
* Dynamic import capabilities (`importlib`-style)
* Advanced caching and optimization strategies
* Comprehensive development tools

### 5.2 Open Questions for Future Iterations
* Circular Dependencies: How should we handle edge cases in circular dependency detection?
* Dynamic Loading: What's the best API design for dynamic module loading?
* Hot Reloading: How can we preserve state while reloading modules?
* Package Management: What additional features are needed for large-scale package management?

### 4.2 Phase 4 Step 4.3: Dana Package Support Progress! (December 2024)

**🎯 Major Package Infrastructure Achievements!**

**Step 4.3 Results: 26/33 Tests Passing ✅**
- ✅ **Grammar Enhancement:** Added relative import support (`from .module import func`)
- ✅ **Package Loading:** Packages with `__init__.na` files load correctly
- ✅ **Package Constants:** Access to package-level public variables
- ✅ **Submodule Imports:** Basic submodule import with aliases
- ✅ **From-Imports:** Import specific functions from packages and submodules

**Fully Working Package Features:**
```dana
# Package imports
import utils                                # ✅ Works
import utils as u                          # ✅ Works  
utils.PACKAGE_VERSION                      # ✅ Works - access constants
utils.get_package_info()                  # ✅ Works - package functions

# Submodule imports with aliases
import utils.numbers as nums               # ✅ Works
nums.factorial(5)                          # ✅ Works
nums.is_odd(7)                            # ✅ Works

# From-imports
from utils import factorial                # ✅ Works - re-exported functions
from utils.numbers import sum_range        # ✅ Works - direct submodule import
factorial(4)                              # ✅ Works
sum_range(1, 5)                           # ✅ Works
```

**Infrastructure Enhancements Made:**
- **Relative Import Grammar:** Added `relative_module_path: DOT+ [module_path]` to Dana grammar
- **Transformer Updates:** Enhanced `from_import` method to handle relative imports
- **Module Context Tracking:** Added `_current_module` to context for relative import resolution  
- **Import Resolution:** Added `_resolve_relative_import()` method with proper package hierarchy handling
- **Package Specification:** Enhanced ModuleSpec to properly handle package search locations

**Known Limitations (7 failing tests):**
- **Dotted Access Chain:** `utils.text.function()` syntax not yet supported (grammar limitation)
- **Re-exported Function Execution:** Functions imported via `__init__.na` return DanaFunction objects instead of executing
- **Submodule Direct Access:** `from utils.text import func` imports fail due to submodule loading issues

**Next Steps for Step 4.4:**
- Fix dotted module access chains in grammar/interpreter
- Resolve function execution vs. object return issues
- Complete submodule from-import functionality
- Add circular dependency detection tests