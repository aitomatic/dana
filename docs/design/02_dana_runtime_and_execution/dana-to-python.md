# Dana → Python Integration: Same-Process Design

**Status**: Current ("same-process") Design  
**Module**: `opendxa.dana.python`

## Problem Statement

In order for Dana users to enjoy the full benefits of the Python ecosystem, Dana code needs to call Python functions and libraries. We want to do this securely, but we want to avoid the over-engineering pitfalls identified in our Python-to-Dana implementation while maintaining a clean, secure, and maintainable design.

### Core Challenges
1. **Simplicity vs. Power**: Provide a simple interface while enabling real use cases
2. **Type Mapping**: Map Python types to Dana types cleanly
3. **Resource Management**: Handle Python resources properly
4. **Error Handling**: Propagate Python errors to Dana meaningfully

## Design Goals

1. **Simple Developer Experience**: Make calling Python from Dana feel natural
2. **Type Safety**: Clear and predictable type conversions
3. **Resource Management**: Explicit and clean resource handling
4. **Error Handling**: Meaningful error propagation
5. **Future Compatibility**: Design allows for future process isolation

## Non-Goals

1. ❌ General-purpose Python import system
2. ❌ Complete type safety guarantees
3. ❌ Process isolation in initial implementation (but design must support it)

## Core Design

**Goal**: Enable Dana scripts to call Python *today* with zero IPC overhead, while ensuring every call site is ready for a hardened out-of-process sandbox tomorrow.

## Directional Design Choice

Dana↔Python integration is intentionally split into two separate designs:

1. **Dana → Python** (this document)
   - Dana code calling Python functions
   - Managing Python objects from Dana
   - Future sandboxing of Python execution

2. **Python → Dana** ([python-to-dana.md](python-to-dana.md))
   - Python code calling Dana functions
   - Dana runtime embedding in Python
   - Dana sandbox security model

This separation exists because:
- Different security models (Dana sandbox vs. Python process)
- Different trust boundaries (Dana trusts Python runtime vs. Python isolated from Dana)
- Different use cases (Dana using Python libraries vs. Python embedding Dana)
- Different implementation needs (transport layer vs. sandbox protocol)

## 1. Core Runtime Abstractions

| Runtime Object | Contents | Usage Pattern |
|---------------|----------|----------------|
| **`PythonFunction`** | - FQN string (e.g. `"geom.area"`)  <br> - Pointer to real Python `callable` | `__call__(*args)` delegates to **`_transport.call_fn(fqn, args)`** |
| **`PythonClass`** | - FQN string (e.g. `"geom.Rect"`) <br> - Pointer to real Python `type` | `__call__(*ctor_args)` → `obj = _transport.create(fqn, ctor_args)` → returns wrapped `PythonObject` |
| **`PythonObject`** | - FQN of its class <br> - `_id = id(real_instance)` (handle) | - `__getattr__(name)` returns closure that forwards to `_transport.call_method(fqn, _id, name, args)` <br> - `close()` / `__del__` → `_transport.destroy(_id)` |

All public behavior (function calls, method calls, destruction) funnels through **one pluggable transport**.

## 2. Transport Abstraction

This API is frozen and must not change:

```python
class Transport:
    def call_fn(fqn: str, args: tuple) -> Any: ...
    def create(cls_fqn: str, args: tuple) -> int:   # returns obj-id
    def call_method(cls_fqn: str, obj_id: int,
                   name: str, args: tuple) -> Any: ...
    def destroy(obj_id: int) -> None: ...
```

*All Dana-generated stubs—present and future—**must** use this interface only.*

## 3. InProcTransport Implementation

Current implementation that ships today:

- Maintains two tables:
  - `functions[fqn] → callable`
  - `classes[fqn] → type`
- `create()`: 
  1. Instantiates the class
  2. Stores `OBJECTS[obj_id] = instance`
  3. Returns `id(instance)`
- `call_method()`: Looks up `OBJECTS[obj_id]` and invokes `getattr(inst, name)(*args)`
- `destroy()`: Pops the `obj_id` from the map

Result: Everything runs in a single CPython interpreter with no serialization cost.

## 4. Stub Generation

Build-time code generation process:

1. Probe imported symbols using `inspect.isfunction / isclass`
2. Generate Dana wrappers that instantiate **`PythonFunction`** or **`PythonClass`**
3. Wrapper bodies never touch real Python objects directly—only the transport

Example generated wrapper:

```dana
def area(a: float, b: float) -> float:
    result = __py_transport.call_fn("geom.area", [a, b])
    return result.asFloat()
```

## 5. Future Sandbox Migration

> **Security Note**: While Dana's sandbox primarily exists to contain potentially malicious Dana code from harming the host system, when Dana calls Python code, we need additional security considerations. The sandbox in this direction is about isolating the Python execution environment to protect against potentially malicious Python packages or code that Dana might try to use.

To move out-of-process:

1. **Drop-in `RpcTransport`**
   - Converts same `call_fn/create/...` calls into JSON/MsgPack messages
   - Sends over socket/vsock/gRPC stream

2. **Hardened Worker**
   - Runs in separate process/container/µ-VM
   - Implements reciprocal dispatcher (`call_fn`, `create`, `call_method`, `destroy`)
   - Maintains real object instances

3. **Config Switch**
   - Change `PythonFunction/Class/Object` to import `RpcTransport` instead of `InProcTransport`
   - Dana source, stubs, and public runtime classes remain untouched

## 6. Migration Safety Rules

| Rule | Future Impact |
|------|--------------|
| All wrappers **must** use `Transport` API (no direct calls) | Enables transport swapping without stub edits |
| Store only **FQN + opaque `obj_id`** in `PythonObject` | Works with both raw pointers and remote handles |
| Keep `PythonFunction`, `PythonClass`, `PythonObject` signatures **stable** | Preserves binary compatibility with compiled stubs |
| Never expose transport implementation to user code | Prevents reliance on in-process shortcuts |

## 7. Future Sandbox Implementation

Key components to add later:

1. **RpcTransport**
   - JSON/MsgPack ↔ socket conversion
   - Handle serialization/deserialization

2. **Worker Hardening**
   - UID drop
   - `prctl(PR_SET_NO_NEW_PRIVS)`
   - seccomp filters
   - chroot jail
   - Resource limits

3. **Optional Worker Pool**
   - Worker management
   - `(worker_id, obj_id)` handle pairs
   - Load balancing

Because every call site already goes through the transport layer, **no change is required in Dana scripts or the public runtime objects** when enabling the sandbox.

## Implementation Plan

### Phase 1: Core Transport Layer
- [ ] Implement `Transport` base class with core interface
  - [ ] Function call handling (`call_fn`)
  - [ ] Object creation (`create`)
  - [ ] Method calls (`call_method`)
  - [ ] Object cleanup (`destroy`)
- [ ] Create `InProcTransport` implementation
  - [ ] Object lifecycle management
  - [ ] Method delegation
  - [ ] Error propagation
- [ ] Add comprehensive tests
  - [ ] Function call tests
  - [ ] Object lifecycle tests
  - [ ] Error handling tests
  - [ ] Resource cleanup tests

### Phase 2: Type System
- [ ] Implement type conversion layer
  - [ ] Basic type mappings
  - [ ] Complex type handling
  - [ ] Custom type converters
- [ ] Add type validation system
  - [ ] Input validation
  - [ ] Output validation
  - [ ] Error reporting
- [ ] Create type system tests
  - [ ] Basic type conversion tests
  - [ ] Complex type tests
  - [ ] Error case tests
  - [ ] Performance benchmarks

### Phase 3: Runtime Objects
- [ ] Implement `PythonFunction` wrapper
  - [ ] FQN-based function lookup
  - [ ] Argument type conversion
  - [ ] Error handling and propagation
- [ ] Implement `PythonClass` wrapper
  - [ ] Constructor handling
  - [ ] Instance creation via transport
  - [ ] Method resolution
- [ ] Implement `PythonObject` wrapper
  - [ ] Method delegation
  - [ ] Attribute access
  - [ ] Resource cleanup
- [ ] Add runtime object tests
  - [ ] Function wrapping tests
  - [ ] Class instantiation tests
  - [ ] Method call tests
  - [ ] Cleanup behavior tests

### Phase 4: Integration and Testing
- [ ] Integrate with Dana runtime
  - [ ] Import statement handling
  - [ ] Symbol resolution
  - [ ] Error reporting
- [ ] Add context management
  - [ ] Scope handling
  - [ ] State persistence
  - [ ] Resource lifecycle
- [ ] Create integration tests
  - [ ] End-to-end workflow tests
  - [ ] Error propagation tests
  - [ ] Resource cleanup tests
  - [ ] Performance benchmarks

### Phase 5: Developer Experience
- [ ] Add debugging support
  - [ ] Stack trace integration
  - [ ] Variable inspection
  - [ ] Breakpoint handling
- [ ] Improve error messages
  - [ ] Clear error contexts
  - [ ] Helpful suggestions
  - [ ] Stack trace formatting
- [ ] Create developer documentation
  - [ ] API reference
  - [ ] Usage examples
  - [ ] Best practices
  - [ ] Troubleshooting guide

### Phase 6: Error Handling
- [ ] Implement error translation system
  - [ ] Python-to-Dana error mapping
  - [ ] Stack trace preservation
  - [ ] Context enrichment
- [ ] Add error recovery mechanisms
  - [ ] Automatic retry logic
  - [ ] Fallback strategies
  - [ ] Resource cleanup
- [ ] Create error handling tests
  - [ ] Error translation tests
  - [ ] Recovery tests
  - [ ] Cleanup verification
  - [ ] Integration tests

### Phase 7: Performance Optimization
- [ ] Implement caching system
  - [ ] Function lookup caching
  - [ ] Type conversion caching
  - [ ] Object handle caching
- [ ] Add performance monitoring
  - [ ] Call latency tracking
  - [ ] Memory usage monitoring
  - [ ] Resource utilization
- [ ] Create optimization tests
  - [ ] Cache effectiveness tests
  - [ ] Memory usage tests
  - [ ] Load tests
  - [ ] Benchmark suite

### Phase 8: Security Hardening
- [ ] Implement sandbox isolation
  - [ ] Process separation
  - [ ] Resource limits
  - [ ] Security boundaries
- [ ] Add security monitoring
  - [ ] Access logging
  - [ ] Resource tracking
  - [ ] Violation detection
- [ ] Create security tests
  - [ ] Isolation tests
  - [ ] Resource limit tests
  - [ ] Security boundary tests
  - [ ] Penetration tests

## Design Review

### ✓ Goal: Simple Developer Experience
- [x] Natural import syntax
  ```dana
  from numpy import array, mean
  data = array([1, 2, 3, 4])  # Auto-scoped to local
  ```
- [x] Method calls look like regular Dana code
- [x] No explicit transport handling needed
- [x] Resources managed automatically
- [x] Errors propagated naturally

### ✓ Goal: Type Safety
- [x] Compile-time type checking via generated stubs
  ```dana
  def area(a: float, b: float) -> float:
      result = __py_transport.call_fn("geom.area", [a, b])
      return result.asFloat()
  ```
- [x] FQN-based symbol resolution
- [x] Explicit type conversions in stubs
- [x] No implicit coercion
- [x] Clear type boundaries

### ✓ Goal: Resource Management
- [x] Explicit object lifecycle
  ```python
  def destroy(obj_id: int) -> None:
      OBJECTS.pop(obj_id, None)  # Guaranteed cleanup
  ```
- [x] Automatic cleanup via `__del__`
- [x] Handle-based tracking
- [x] No resource leaks
- [x] Clear ownership model

### ✓ Goal: Error Handling
- [x] Transport layer error translation
- [x] Python exceptions → Dana errors
- [x] Stack traces preserved
- [x] Clear error propagation
- [x] Predictable failure modes

### ✓ Goal: Future Compatibility
- [x] Transport abstraction ready for IPC
- [x] Handle-based design works cross-process
- [x] No in-process assumptions in API
- [x] Clean sandbox migration path
- [x] Pluggable transport layer

### ✓ Non-Goal: General Import System
- [x] Simple FQN-based imports only
  ```python
  functions[fqn] → callable
  classes[fqn] → type
  ```
- [x] No complex module hierarchy
- [x] Direct symbol imports only
- [x] Avoids Python import machinery
- [x] Clear import limitations

### ✓ Non-Goal: Complete Type Safety
- [x] Focuses on common type mappings
- [x] Accepts some runtime checks where needed
- [x] Documents type limitations clearly
- [x] Pragmatic safety vs. complexity balance
- [x] No false guarantees

### ✓ Non-Goal: Initial Process Isolation
- [x] Starts with efficient in-process calls
  ```python
  # Today: Direct calls
  def call_method(cls_fqn, obj_id, name, args):
      return getattr(OBJECTS[obj_id], name)(*args)
  ```
- [x] But design ready for future isolation
  ```python
  # Tomorrow: Same API, different transport
  def call_method(cls_fqn, obj_id, name, args):
      return rpc_client.invoke("call_method", 
                             cls_fqn, obj_id, name, args)
  ```
- [x] No premature complexity
- [x] Clear upgrade path
- [x] Zero-cost abstractions

### Key Design Decisions

✓ **Abstraction Layer**
- [x] Transport interface hides details
- [x] Runtime objects protect internals
- [x] Generated stubs provide safety
- [x] Handle-based design enables sandboxing

✓ **Migration Strategy**
- [x] Start simple with direct calls
- [x] Preserve API compatibility
- [x] Enable gradual hardening
- [x] No user code changes needed

✓ **Security Architecture**
- [x] Security through API design
- [x] No exposed Python internals
- [x] Clear trust boundaries
- [x] Ready for future hardening

### Summary

The design successfully:
- ✓ Achieves all primary goals
- ✓ Respects stated non-goals
- ✓ Provides clear migration paths
- ✓ Maintains simplicity while enabling power

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 