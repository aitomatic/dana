# Dana Language PR

## Description
Implements comprehensive module and import system for Dana, enabling code organization, reusability, and namespace management. This adds native `import` and `export` statements to the Dana language, allowing developers to split code across multiple `.na` files and create reusable libraries.

## Type of Change
- [ ] 🐛 Parser bug fix
- [x] ✨ New language feature
- [ ] 🔧 Interpreter improvement
- [ ] ♻️ AST refactoring
- [ ] 💥 Breaking syntax change

## Dana Components
- [x] **Parser** - Lark grammar, syntax rules (import/export statements)
- [x] **AST** - Node types, validation, transformations (Module, Import, Export nodes)
- [x] **Interpreter** - Execution logic, function registry (module execution context)
- [x] **Sandbox** - Runtime environment, context management (module isolation)
- [x] **Functions** - Built-in functions, core capabilities (module loading functions)

## Language Changes
Adds comprehensive module system with import/export capabilities, module registry, and Python interoperability.

### Syntax Example
```dana
# Before - everything in one file
def calculate_metrics(text: str) -> dict:
    return {"length": len(text), "words": len(text.split())}

text: str = "Sample text"
metrics = calculate_metrics(text)

# After - modular organization
# string_utils.na
export StringMetrics, calculate_metrics

struct StringMetrics:
    length: int
    word_count: int

def calculate_metrics(text: str) -> StringMetrics:
    len = len(text)
    words = len(text.split()) if len > 0 else 0
    return StringMetrics(length=len, word_count=words)

# main.na  
import path/to/string_utils.na
from path/to/string_utils.na import StringMetrics, calculate_metrics

text: str = "Sample text for analysis"
metrics: StringMetrics = calculate_metrics(text)
print(f"Length: {metrics.length}, Words: {metrics.word_count}")
```

## Testing
- [x] Added Dana language tests
- [x] Parser tests pass: `pytest tests/dana/sandbox/parser/`
- [x] Interpreter tests pass: `pytest tests/dana/sandbox/interpreter/`
- [x] Example Dana programs still work
- [x] Edge cases tested (syntax errors, invalid inputs, circular imports)

### Test Commands
```bash
# Run Dana-specific tests
pytest tests/dana/
bin/dana examples/

# Test module-specific functionality
pytest tests/dana/module/
bin/dana examples/dana/na/basic_imports.na
bin/dana examples/dana/na/circular_dependency_test.na
```

## Backward Compatibility
- [x] ✅ Fully backward compatible
- [ ] ⚠️ Minor breaking changes (migration notes below)
- [ ] 💥 Major breaking changes (requires version bump)

This is an additive feature that introduces new `import` and `export` syntax without changing existing language behavior. All existing Dana programs continue to work unchanged.

## Documentation
- [x] Updated language documentation (`docs/design/01_dana_language_specification/modules_and_imports.md`)
- [x] Added/updated examples (module import/export examples)
- [x] Function docstrings updated (ModuleLoader, ModuleRegistry)
- [x] Grammar rules documented (import/export statement grammar)

## Implementation Details

### Core Features Implemented:
- ✅ Basic module loading and execution
- ✅ Module namespace isolation  
- ✅ Basic package support with `__init__.na`
- ✅ Python module integration (`from path/to/module.py import symbol`)
- ✅ Circular dependency detection
- ✅ Module-level exports with `export` statement
- ✅ Import statement parsing (`import module`, `from module import symbol`)
- ✅ Module search path resolution
- ✅ Basic lazy loading
- ✅ Comprehensive error handling (ModuleError, CircularImportError, ModuleNotFoundError)

### Architecture:
- **ModuleRegistry**: Central tracking of modules and dependencies
- **ModuleLoader**: Handles module discovery and loading with search paths
- **Module Types**: Core data structures (ModuleSpec, Module objects)
- **Scope Management**: Module-level scoping with local/private/public/system contexts

### Future Enhancements (Phase 2):
- ⏳ Module reloading support
- ⏳ Dynamic imports
- ⏳ Advanced package features
- ⏳ Hot reloading with state preservation

**Closes #** [module-system-implementation] 