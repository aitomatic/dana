| [← Python Integration Overview](./python_integration.md) | [Python-to-Dana →](./python-to-dana.md) |
|---|---|

# Design Document: Dana-to-Python Integration

```text
Author: Christopher Nguyen
Version: 0.1
Status: Design Phase
Module: opendxa.dana.python
```

## Problem Statement

In order for Dana users to enjoy the full benefits of the Python ecosystem, Dana code needs to call Python functions and libraries. We want to do this securely, but we want to avoid the over-engineering pitfalls identified in our Python-to-Dana implementation while maintaining a clean, secure, and maintainable design.

### Core Challenges
1. **Simplicity vs. Power**: Provide a simple interface while enabling real use cases
2. **Type Mapping**: Map Python types to Dana types cleanly
3. **Resource Management**: Handle Python resources properly
4. **Error Handling**: Propagate Python errors to Dana meaningfully

## Goals

1. **Simple Developer Experience**: Make calling Python from Dana feel natural
2. **Type Safety**: Clear and predictable type conversions
3. **Resource Management**: Explicit and clean resource handling
4. **Error Handling**: Meaningful error propagation
5. **Future Compatibility**: Design allows for future process isolation

## Non-Goals

1. ❌ General-purpose Python import system
2. ❌ Complete type safety guarantees
3. ❌ Process isolation in initial implementation (but design must support it)

## Proposed Solution

**Goal**: Enable Dana scripts to call Python *today* with zero IPC overhead, while ensuring every call site is ready for a hardened out-of-process sandbox tomorrow.

### Directional Design Choice

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

## Proposed Design

### Example Code

```dana
from a.b.c.d.py import SomeClass

some_object = SomeClass()     # some_object is a PythonObject, which is effectively of `Any` Python type
x = some_object.some_property # x is a PythonObject
y = some_object.some_method() # y is a PythonObject

some_object.close()           # either evaluates to a PythonObject, or None
```

```dana
import pandas as pd

df = pd.read_csv("data.csv") # df is a PythonObject, which is effectively of `Any` Python type
mean_values = df.groupby("column_name").mean()
```

### Core Runtime Abstractions

| Runtime Object | Contents | Usage Pattern |
|---------------|----------|----------------|
| **`PythonFunction`** | - FQN string (e.g. `"geom.area"`)  <br> - Pointer to real Python `callable` | `__call__(*args)` delegates to **`_transport.call_fn(fqn, args)`** |
| **`PythonClass`** | - FQN string (e.g. `"geom.Rect"`) <br> - Pointer to real Python `type` | `__call__(*ctor_args)` → `obj = _transport.create(fqn, ctor_args)` → returns wrapped `PythonObject` |
| **`PythonObject`** | - FQN of its class <br> - `_id = id(real_instance)` (handle) | - `__getattr__(name)` returns closure that forwards to `_transport.call_method(fqn, _id, name, args)` <br> - `close()` / `__del__` → `_transport.destroy(_id)` |

All public behavior (function calls, method calls, destruction) funnels through **one pluggable transport**.

### Transport Abstraction

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

### InProcTransport Implementation

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

### Stub Generation

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

### Future Sandbox Migration

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

### Migration Safety Rules

| Rule | Future Impact |
|------|--------------|
| All wrappers **must** use `Transport` API (no direct calls) | Enables transport swapping without stub edits |
| Store only **FQN + opaque `obj_id`** in `PythonObject` | Works with both raw pointers and remote handles |
| Keep `PythonFunction`, `PythonClass`, `PythonObject` signatures **stable** | Preserves binary compatibility with compiled stubs |
| Never expose transport implementation to user code | Prevents reliance on in-process shortcuts |

### Future Sandbox Implementation

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

## Design Review Checklist

- [ ] Security review completed
  - [ ] Transport layer security verified
  - [ ] Object lifecycle validated
  - [ ] Resource management checked
- [ ] Performance impact assessed
  - [ ] Call overhead measured
  - [ ] Memory usage optimized
  - [ ] Resource cleanup verified
- [ ] Developer experience validated
  - [ ] API usability confirmed
  - [ ] Error messages clear
  - [ ] Documentation complete
- [ ] Future compatibility confirmed
  - [ ] Transport abstraction solid
  - [ ] Migration path clear
  - [ ] Sandbox ready
- [ ] Testing strategy defined
  - [ ] Unit tests planned
  - [ ] Integration tests designed
  - [ ] Performance benchmarks ready

## Implementation Phases

### Phase 1: Core Transport Layer
- [ ] Implement Transport base class
- [ ] Create InProcTransport
- [ ] Add core tests

### Phase 2: Type System
- [ ] Build type conversion
- [ ] Add validation
- [ ] Create type tests

### Phase 3: Runtime Objects
- [ ] Implement PythonFunction
- [ ] Implement PythonClass
- [ ] Implement PythonObject

### Phase 4: Integration & Testing
- [ ] Dana runtime integration
- [ ] Context management
- [ ] Integration tests

### Phase 5: Developer Experience
- [ ] Add debugging support
- [ ] Improve error messages
- [ ] Create documentation

### Phase 6: Error Handling
- [ ] Error translation
- [ ] Recovery mechanisms
- [ ] Error tests

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 