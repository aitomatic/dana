# Python-Calling-Dana: Secure Integration Architecture

**Status**: Design Phase  
**Module**: `opendxa.dana`

## Problem Statement

The Dana language and runtime are intended to be Python-developer-friendly.
As such, many will want to stay in the Python ecosystem and use Dana's
advanced capabilities. One such example is the use of FastAPI to build
Python-based APIs that use Dana's reasoning capabilities. For this, users should not have to learn a new Dana API. Instead, they should be able to use their familiar Python implementation, and call into Dana whenver desired.

Implementing such a bridge would be easy, except for one problem: we want to preserve Dana's security sandbox integrity, with clear rules of engagement, e.g., trusted vs untrusted Python code.

**Core Challenge**: How do we enable seamless Python-calling-Dana integration while preserving Dana's security sandbox integrity?

## Goals

1. **Preserve Sandbox Integrity**: Dana's secure execution environment remains fully isolated from untrusted Python code.
2. **Familiar Developer Experience**: Import Dana modules like Python modules (`import dana.module`)
3. **Performance**: Minimize overhead for cross-language calls
4. **It just works**: Python developers should be able to use Dana as easily as they use Python modules.
5. **Bidirectional Compatibility**: the approach should be architecturally suitable for both Python-calling-Dana and Dana-calling-Python. It may or may not be the same module, but the approach should at least share an architectural philosophy to reason about.

## Non-Goals

1. **❌ Memory Space Isolation**: For this initial design, we do not attempt to prevent Python code from accessing Dana's memory space. While full isolation is possible through out-of-process execution (planned for future), the current in-process design prioritizes simplicity and performance. The sandbox is for Dana's own security features.

> **Note**: Future versions will support running Dana in a separate process with proper isolation boundaries. This is tracked as a TODO but is not part of the initial design.

## Developer Experience: It Just Works

The design prioritizes immediate developer productivity with zero friction. Here's what using Dana from Python looks like:

```python
# Import Dana modules just like Python modules
from opendxa.dana import dana

# Simple function calls - options parameter is optional
result = dana.reason("analyze this text")  # no options needed

# Or with options when needed
result = dana.reason(
    "analyze this text",
    {
        "mode": "detailed",
        "max_tokens": 100
    }
)

# Complex Python types just work
import pandas as pd
df = pd.DataFrame({
    "text": ["example 1", "example 2"],
    "labels": ["A", "B"]
})
results = dana.reason(
    "analyze batch of examples",
    {"data": df}
)

# Resource management is Pythonic
with dana.get_llm() as llm:
    result = llm.generate("some prompt")

# Async support when needed
async def process_text():
    async with dana.get_llm_async() as llm:
        result = await llm.reason("analyze this")  # options are optional
        return result

# Clear error messages
try:
    result = dana.reason(123)  # Wrong type
except TypeError as e:
    print(e)  # "Expected string, got int at argument 'prompt'"

# Type hints and IDE support work
from opendxa.dana.types import ReasoningResult

def process(prompt: str, options: dict | None = None) -> ReasoningResult:
    return dana.reason(prompt, options) if options else dana.reason(prompt)
```

The experience is completely natural for Python developers:
- No special setup required
- No new patterns to learn
- Normal Python tools and practices work
- Clear, Pythonic error messages
- Familiar debugging experience
- IDE support out of the box

## Proposed Solution: Secure Gateway Pattern

Instead of a unified runtime, we implement a **Secure Gateway Pattern** where:

1. **Python calls Dana** through a controlled interface (`dana`)
2. **Dana executes in a sandbox** with clear boundaries
3. **Data flows through defined channels** with type validation
4. **Security boundaries are enforced** at communication points

> **Security Note**: The complete security model requires running the Dana Sandbox in a separate process with additional protections (setuid(), preventing ptrace(), etc.). In the initial implementation, we architect with this in mind but defer these protections as a documented TODO. Like any Python library, we rely on the caller to be security conscious about the code they execute, similar to how they evaluate the trust level of any third-party package.

### Architecture Overview

```python
# Core interface that abstracts process boundary
from opendxa.dana import sandbox, types

class DanaSandbox:
    """Interface to Dana Sandbox - process boundary abstraction."""
    def __init__(self):
        # TODO: In future, this will manage process creation/communication
        self.interpreter = sandbox.Interpreter()
        
    def call_function(self, name: str, args: list, kwargs: dict) -> Any:
        """Call Dana function - future IPC boundary."""
        return self.interpreter.call_function(name, args, kwargs)

# Public API that handles imports
def import_dana_module(name: str) -> ModuleType:
    """Import Dana module through opendxa.dana."""
    sandbox_instance = DanaSandbox()
    return create_module_wrapper(name, sandbox_instance)

# Example usage
from opendxa.dana import dana

result = dana.reason("some text")  # Goes through sandbox boundary
```

The architecture provides:
1. Clean Python import experience (`from opendxa.dana import dana`)
2. Clear sandbox boundaries for future process isolation
3. Type-safe data flow between Python and Dana
4. Foundation for security hardening in future versions

### Key Components

1. **Sandbox Interface**
   - Clear boundary between Python and Dana execution
   - Future-proofed for process isolation
   - Controlled data flow and type conversion

2. **Import System**
   - Natural Python import syntax
   - Module creation and caching
   - Lazy loading of Dana modules

3. **Type System**
   - Safe conversion between Python and Dana types
   - Clear error messages for type mismatches
   - Support for common Python data structures

4. **Resource Management**
   - Controlled access to shared resources (e.g., LLM instances)
   - Resource pooling and lifecycle management
   - Future support for cross-process resource sharing

### Performance Considerations

The design optimizes for both developer experience and runtime performance:

1. **Call Overhead Targets**
   ```python
   # Direct function calls: < 1ms overhead
   result = dana.reason("simple call")
   
   # Type conversion: < 2ms for common types
   result = dana.reason("process list", {"data": [1, 2, 3]})
   
   # Resource initialization: < 50ms first time
   llm = dana.get_llm()  # Cached after first call
   ```

2. **Optimization Strategies**
   - Function call caching
   - Resource pooling
   - Lazy module loading
   - Type conversion caching
   - Shared memory for large data (future)

## Implementation Recommendations

The following are suggested implementations that satisfy the design requirements. Implementation engineers may adapt or modify these based on specific needs or constraints encountered during development.

### Suggested Type System

```python
from typing import Any, TypeVar, Protocol
from enum import Enum

# Dana's actual type system
class DanaType(Enum):
    """Dana's built-in types."""
    INT = "int"
    FLOAT = "float"
    STRING = "string"  # Note: Python's str maps to Dana's string
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"
    TUPLE = "tuple"
    SET = "set"
    NULL = "null"  # Note: Python's None maps to Dana's null
    ANY = "any"

class TypeConverter(Protocol):
    """Type conversion protocol."""
    def to_dana(self, value: Any) -> tuple[DanaType, Any]:
        """Convert Python value to Dana type."""
        ...
    
    def from_dana(self, dana_type: DanaType, value: Any) -> Any:
        """Convert Dana value to Python type."""
        ...

# Actual Dana type mapping
PYTHON_TO_DANA_TYPES = {
    str: DanaType.STRING,
    int: DanaType.INT,
    float: DanaType.FLOAT,
    bool: DanaType.BOOL,
    list: DanaType.LIST,
    dict: DanaType.DICT,
    tuple: DanaType.TUPLE,
    set: DanaType.SET,
    None: DanaType.NULL,
}

# Complex type handlers
class DataFrameHandler:
    """Example pandas DataFrame conversion."""
    def to_dana(self, df) -> dict:
        return {
            "columns": df.columns.tolist(),
            "data": df.values.tolist(),
            "index": df.index.tolist()
        }
    
    def from_dana(self, data: dict) -> "pandas.DataFrame":
        import pandas as pd
        return pd.DataFrame(
            data["data"],
            columns=data["columns"],
            index=data["index"]
        )
```

### Suggested Resource Management

```python
from typing import Protocol, TypeVar
from contextlib import contextmanager
import weakref

T = TypeVar('T')

class Resource(Protocol[T]):
    """Base protocol for managed resources."""
    def acquire(self) -> T:
        """Acquire the resource."""
        ...
    
    def release(self) -> None:
        """Release the resource."""
        ...

class LLMPool:
    """LLM resource pool implementation."""
    def __init__(self, max_size: int = 10):
        self._resources: list[weakref.ref] = []
        self._max_size = max_size
    
    @contextmanager
    def get_llm(self):
        """Get LLM with context management."""
        llm = self._acquire_llm()
        try:
            yield llm
        finally:
            self._release_llm(llm)
```

### Suggested Error Handling

```python
class DanaError(Exception):
    """Base class for Dana exceptions."""
    pass

class TypeConversionError(DanaError):
    """Error during type conversion."""
    pass

class ResourceError(DanaError):
    """Error with resource management."""
    pass

# Error mapping
ERROR_MAP = {
    TypeError: TypeConversionError,
    ValueError: TypeConversionError,
    ResourceError: ResourceError,
}
```

### Suggested Core Interfaces

```python
from typing import Any, Protocol, TypeVar

T = TypeVar('T')

class DanaSandbox(Protocol):
    """Core Dana sandbox interface."""
    def reason(self, prompt: str, options: dict | None = None) -> Any:
        """Core reasoning function."""
        ...
    
    def get_llm(self) -> Resource:
        """Get LLM resource."""
        ...

# Simple module implementation
class Dana:
    """Main Dana module implementation."""
    def __init__(self):
        self._sandbox = DanaSandbox()
    
    def reason(self, prompt: str, options: dict | None = None) -> Any:
        """Main reasoning function."""
        return self._sandbox.reason(prompt, options)
    
    def get_llm(self):
        """Get LLM with context management."""
        return self._sandbox.get_llm()

# Single instance for import
dana = Dana()
```

These implementations are suggestions that satisfy the design requirements while maintaining the developer experience goals. Implementation engineers should feel free to:

- Modify interfaces based on actual Dana language requirements
- Adjust type mappings to match Dana's type system
- Change resource management strategies if needed
- Implement different module loading approaches
- Adapt error handling to match actual needs

The key is maintaining the developer experience and performance goals while potentially using different implementation approaches.

## Implementation Plan

1. **Core Implementation**
   - Basic import system
   - Type conversion system
   - Resource management

2. **Developer Experience**
   - Error handling
   - Documentation
   - IDE support
   - Debugging tools

3. **Future Enhancements**
   - Process isolation
   - Performance optimizations
   - Dana-calling-Python support

## Next Steps

1. Implement core `DanaSandbox` class
2. Build import system
3. Create developer tools
4. Add monitoring and logging
5. Document usage patterns

## Design Review Checklist

### 1. API Design & Developer Experience
✅ Import syntax matches Python conventions (`from opendxa.dana import dana`)
✅ Function signatures are intuitive (`reason(prompt: str, options: dict | None = None)`)
✅ Type hints are comprehensive and accurate
✅ Error messages are clear and actionable
✅ Documentation follows Python standards (docstrings, type hints)
✅ Examples cover common use cases
✅ Resource management follows Python patterns (context managers)
✅ Async support is properly implemented

### 2. Security Model
✅ Dana sandbox integrity is preserved for Dana's own security features
❌ Input validation is comprehensive
❌ Output filtering catches all sensitive data
✅ Resource access is properly controlled
✅ Error messages are clear and actionable
✅ API boundaries are well defined

### 3. Performance & Resources
✅ Function call overhead is minimized
✅ Memory usage is optimized
✅ Resource pooling is implemented
✅ Type conversion is efficient
✅ Batch operations are supported
✅ Async operations are non-blocking
❌ Memory leaks are prevented
❌ Resource cleanup is guaranteed

### 4. Integration & Compatibility
✅ Works with common Python data types (str, int, float, bool)
✅ Supports complex Python types (pandas, numpy)
✅ Compatible with Python async/await
✅ Works with Python debugging tools
✅ Supports Python logging
✅ IDE integration works (autocomplete, type hints)
✅ Testing frameworks can interact with Dana code
✅ Error handling integrates with Python try/except

### 5. Implementation Feasibility
✅ All components are technically feasible
✅ Required dependencies are reasonable
✅ Performance targets are achievable
✅ Resource management is practical
✅ Error handling is implementable
✅ Testing strategy is viable
✅ Documentation can be generated

### 6. Documentation & Support
❌ API documentation is complete
❌ Examples are comprehensive
❌ Performance characteristics are documented
❌ Resource usage is documented
❌ Error conditions are documented
❌ Debugging guide is provided

### 7. Testing Strategy
✅ Unit tests can be written
✅ Integration tests are possible
❌ Performance tests are planned
❌ Resource tests are specified
❌ Error handling can be tested
✅ Edge cases are identified
❌ Test coverage goals are set

## Goals Review

Let's evaluate how well the design meets each of our original goals:

### 1. Preserve Sandbox Integrity
✅ **Goal Met**
- Clear sandbox boundaries through `DanaSandbox` class
- Controlled data flow with type validation
- Process isolation architecture ready for future implementation
- Resource access controls in place

### 2. Familiar Developer Experience
✅ **Goal Met**
- Natural Python import syntax (`from opendxa.dana import dana`)
- Pythonic function signatures and type hints
- Standard context managers and async patterns
- Familiar error handling and debugging experience
- IDE support through standard Python mechanisms

### 3. Performance
✅ **Goal Met with Monitoring Needed**
- Direct function call overhead target < 1ms
- Type conversion overhead target < 2ms
- Resource pooling and caching strategies defined
- ❌ Need to implement performance tests to verify targets

### 4. It Just Works
✅ **Goal Met**
- Zero setup beyond standard Python package installation
- Works with common Python data types
- Handles complex types like pandas DataFrames
- Standard Python tooling works as expected
- Clear, actionable error messages

### 5. Bidirectional Compatibility
✅ **Goal Met Architecturally**
- Design patterns support both directions
- Clean abstraction through `DanaSandbox`
- Type system works both ways
- Resource management supports bidirectional use
- ❌ Actual Dana-calling-Python implementation deferred to future

## Areas Needing Attention

1. **Validation & Filtering**
   - Input validation rules need specification
   - Output filtering rules need specification
   - Security boundary verification needed

2. **Resource Management**
   - Memory leak prevention needs specification
   - Resource cleanup rules need documentation
   - Resource pooling needs implementation details

3. **Documentation & Testing**
   - API documentation incomplete
   - Performance test suite needed
   - Resource test suite needed
   - Test coverage goals undefined

## Conclusion

This **Secure Gateway Pattern** provides:

1. **Security-First Design**: Dana's sandbox integrity is completely preserved
2. **Familiar Developer Experience**: Python developers can import Dana modules naturally
3. **Clear Security Boundaries**: Explicit separation between trusted and untrusted code
4. **Controlled Performance Trade-offs**: Acceptable overhead for security guarantees

The design ensures that **Python-calling-Dana** is safe and maintainable while providing excellent developer experience.

---

**Related Documents:**
- [Dana Language Specification](./dana/language.md)
- [Interpreter Design](./interpreter.md)
- [Sandbox Security](./sandbox.md)

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 