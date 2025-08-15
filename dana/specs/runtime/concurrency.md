| [← Interpreter](./interpreter.md) | [Core Language →](../core/language.md) |
|---|---|

# Dana Promise System and Concurrency Model

**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 2.0.0  
**Status:** Implemented

## Executive Summary

Dana implements a sophisticated Promise system that enables concurrent-by-default execution through transparent Promise[T] types. The system provides two function completion mechanisms - `deliver` for simple synchronous returns and `return` for concurrent Promise-based execution - while maintaining complete type transparency.

**Key Features:**
- **Transparent Typing**: Promise[T] appears and behaves as type T
- **Dual Completion**: `deliver` (sync) and `return` (concurrent) keywords
- **Automatic Concurrency**: `return` statements create EagerPromise for background execution
- **Zero Syntax Overhead**: No async/await keywords needed

## 1. Core Concepts

### Promise[T] Transparency

Dana's Promise system achieves true transparency through comprehensive operator overloading:

```dana
// Promise[Int] behaves exactly like Int
def compute_value() -> Int:
    return expensive_calculation()  // Returns Promise[Int] that appears as Int

// Usage is completely transparent
result = compute_value()  // Promise[Int]
doubled = result * 2      // Works immediately, returns Promise[Int]
if result > 10:          // Comparison works, blocks if needed
    print(result)        // Automatic resolution when value needed
```

### Dual Completion Mechanisms

#### **`deliver` - Simple Synchronous Return**
Returns a value immediately and synchronously, like traditional return statements in other languages.

```dana
def get_cached_value(key: String) -> String:
    if cache.has(key):
        deliver cache.get(key)  // Immediate synchronous return
    deliver "default"           // No Promise creation, direct value
```

#### **`return` - Concurrent Promise Creation**
Creates an EagerPromise that executes in the background, enabling concurrent execution.

```dana
def fetch_data(url: String) -> Data:
    return http.get(url)  // Creates EagerPromise, executes in background
```

## 2. Architecture

### Promise Type Hierarchy

```
BasePromise (Abstract)
├── EagerPromise  - Starts execution immediately in background thread
└── LazyPromise   - Defers execution until first access (reserved for future use)
```

### Key Components

1. **BasePromise**: Abstract base providing transparent proxy behavior via 40+ magic methods
2. **EagerPromise**: Concurrent execution with ThreadPoolExecutor
3. **Promise Utilities**: Consolidated detection and resolution functions
4. **DanaThreadpool**: Shared thread pool management

### Promise Boundaries

Only specific operations create Promise boundaries:
- Dana function `return` statements
- LLM function calls
- Explicit Promise creation

All other operations remain synchronous:
- Arithmetic and comparisons
- Collection operations
- Control flow statements
- `deliver` statements

## 3. Implementation Details

### Return Statement Processing

When a Dana function uses `return`:

1. The return value expression is wrapped in a computation function
2. An EagerPromise is created with this computation
3. The computation executes immediately in a background thread
4. The Promise is raised as a ReturnException to exit the function

```python
# Simplified implementation in control_flow_utils.py
def execute_return_statement(self, node: ReturnStatement, context: SandboxContext):
    def return_computation():
        return self.parent_executor.execute(node.value, captured_context)
    
    promise_value = EagerPromise.create(return_computation, executor)
    raise ReturnException(promise_value)
```

### Promise Resolution Patterns

**Automatic Resolution in Collections**:
```python
# Collections auto-resolve Promises during construction
[1, promise_of_2, 3]  # Becomes [1, 2, 3] with resolved value
```

**Explicit Resolution**:
```python
# Using consolidated utilities
from dana.core.concurrency import is_promise, resolve_if_promise

value = resolve_if_promise(potentially_promise_value)
```

### Thread Pool Management

Dana uses a shared ThreadPoolExecutor for all EagerPromise execution:
- Default: 4 worker threads
- Singleton pattern for resource efficiency
- Automatic cleanup on process exit

## 4. Usage Patterns

### Common Patterns

**Concurrent I/O Operations**:
```dana
def fetch_user_data(user_id: Int) -> UserData:
    // All three API calls start immediately in parallel
    profile = fetch_profile(user_id)      // return creates Promise
    posts = fetch_posts(user_id)          // return creates Promise  
    friends = fetch_friends(user_id)      // return creates Promise
    
    // Promises resolve when accessed
    deliver UserData(
        profile=profile,    // Blocks here if not ready
        posts=posts,        // Blocks here if not ready
        friends=friends     // Blocks here if not ready
    )
```

**Mixed Sync/Async Operations**:
```dana
def process_data(data: Data) -> Result:
    if data.is_cached():
        deliver data.cached_result  // Synchronous, no Promise
    
    // Only create Promise for expensive operation
    return expensive_computation(data)  // Concurrent execution
```

### Best Practices

1. **Use `deliver` for simple returns**: When returning cached values, constants, or simple computations
2. **Use `return` for I/O or expensive operations**: Enables concurrent execution automatically
3. **Don't worry about Promise types**: The transparent proxy handles all operations
4. **Let collections auto-resolve**: Don't manually resolve Promises in collections

## 5. Performance Characteristics

### Promise Creation Overhead
- EagerPromise: ~1-2ms for thread pool task submission
- Transparent operations: Near-zero overhead until resolution needed
- Memory: Small object overhead + computation closure

### Concurrency Benefits
- Parallel I/O: 60-80% speedup for multiple API calls
- Resource utilization: CPU available during I/O waits
- Scalability: Thread pool prevents resource exhaustion

### Resolution Costs
- First access: Blocks until computation complete
- Subsequent access: Cached result, zero cost
- Failed computations: Exception cached and re-raised

## 6. Error Handling

Promises preserve error semantics transparently:

```dana
def may_fail() -> Int:
    return 1 / 0  // Division by zero in Promise

try:
    value = may_fail()      // No error yet (Promise created)
    result = value + 1      // Error raised here on access
except DivisionByZero:
    print("Caught error")   // Normal error handling works
```

## 7. Future Directions

### Potential Enhancements
- **Smart Promise Creation**: Skip Promises for literal values
- **Promise Batching**: Group related operations
- **Async/Await Support**: Optional explicit control
- **LazyPromise Activation**: For truly deferred computations

### Reserved for Future
- LazyPromise implementation
- Promise cancellation
- Progress monitoring
- Custom execution strategies

## 8. Implementation Status

### Completed
- ✅ BasePromise with full transparent proxy
- ✅ EagerPromise with ThreadPoolExecutor
- ✅ Return statement Promise creation
- ✅ Deliver statement synchronous returns
- ✅ Collection auto-resolution
- ✅ Consolidated Promise utilities
- ✅ REPL Promise display modes

### In Progress
- 🚧 Performance optimizations
- 🚧 Enhanced error messages

### Planned
- 📋 LazyPromise implementation
- 📋 Smart Promise creation
- 📋 Promise debugging tools

## Quick Reference

### When to use `deliver` vs `return`

| Use `deliver` when... | Use `return` when... |
|----------------------|---------------------|
| Returning cached values | Making API/network calls |
| Returning constants | Performing I/O operations |
| Simple computations | CPU-intensive calculations |
| Already have the value | Need concurrent execution |
| Want immediate return | Want background processing |

### Promise Utilities

```python
from dana.core.concurrency import (
    is_promise,           # Check if object is a Promise
    resolve_promise,      # Force Promise resolution
    resolve_if_promise,   # Resolve if Promise, else return as-is
)
```

### Common Patterns

```dana
// Pattern 1: Parallel API calls
def fetch_all_data(id: Int) -> Data:
    a = api_call_1(id)  // return → Promise, starts immediately
    b = api_call_2(id)  // return → Promise, runs in parallel
    c = api_call_3(id)  // return → Promise, runs in parallel
    
    deliver Data(a, b, c)  // Waits for all to complete

// Pattern 2: Conditional concurrency
def smart_fetch(key: String) -> Value:
    if cache.has(key):
        deliver cache.get(key)  // Sync return, no Promise
    return database.query(key)  // Concurrent database call

// Pattern 3: Promise chaining
def process_chain(input: String) -> Result:
    parsed = parse_data(input)      // return → Promise
    validated = validate(parsed)     // Works on Promise transparently
    transformed = transform(validated)  // Chain continues
    deliver transformed              // Final sync return
```

## Summary

Dana's Promise system provides powerful concurrent-by-default execution while maintaining the simplicity of synchronous code. Through transparent typing and dual completion mechanisms, developers can write naturally concurrent code without cognitive overhead. The system is production-ready and forms a core part of Dana's agent-oriented programming model.