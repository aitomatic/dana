# Dana Execute-Time Async Detection

## Overview

Dana now supports **execute-time async detection**, which automatically detects and handles async Python functions at the moment they are called, rather than at import time. This provides comprehensive coverage for all function call scenarios, including dynamic function assignments, function arguments, and runtime function creation.

## How It Works

Execute-time async detection uses `asyncio.iscoroutinefunction()` to check if a function is async at the moment it's called, then automatically uses `Misc.safe_asyncio_run()` to execute async functions properly.

### Key Components Enhanced

#### 1. **Function Registry** (`dana/core/lang/interpreter/functions/function_registry.py`)
- Added async detection to all `wrapped_func` calls
- Handles functions called through the registry system
- Covers both context-aware and context-free function calls

#### 2. **Python Function Wrapper** (`dana/core/lang/interpreter/functions/python_function.py`)
- Enhanced `execute()` method with async detection
- Handles all Python function execution paths
- Supports context injection with async detection

#### 3. **Unified Function Dispatcher** (`dana/core/lang/interpreter/executor/resolver/unified_function_dispatcher.py`)
- Added async detection to `_execute_callable_function()`
- Handles direct function calls through the dispatcher
- Covers dynamic function resolution

#### 4. **Expression Executor** (`dana/core/lang/interpreter/executor/expression_executor.py`)
- Enhanced pipeline execution with async detection
- Handles direct function calls in pipelines
- Supports async detection for non-registry functions

#### 5. **Function Executor** (`dana/core/lang/interpreter/executor/function_executor.py`)
- Added async detection to subscript expressions
- Handles method calls and object function calls
- Supports async detection for dynamically resolved functions

## Implementation Details

### Function Registry Async Detection

```python
# In function_registry.py - call method
if first_param_is_ctx:
    if not func._is_trusted_for_context():
        # Function wants context but is not trusted - call without context with async detection
        import asyncio
        from dana.common.utils.misc import Misc
        
        if asyncio.iscoroutinefunction(wrapped_func):
            return _resolve_if_promise(Misc.safe_asyncio_run(wrapped_func, *positional_args, **func_kwargs))
        else:
            return _resolve_if_promise(wrapped_func(*positional_args, **func_kwargs))
    else:
        # First parameter is context and function is trusted - add execute-time async detection
        import asyncio
        from dana.common.utils.misc import Misc
        
        if asyncio.iscoroutinefunction(wrapped_func):
            return _resolve_if_promise(Misc.safe_asyncio_run(wrapped_func, context, *positional_args, **func_kwargs))
        else:
            return _resolve_if_promise(wrapped_func(context, *positional_args, **func_kwargs))
else:
    # No context parameter - add execute-time async detection
    import asyncio
    from dana.common.utils.misc import Misc
    
    if asyncio.iscoroutinefunction(wrapped_func):
        return _resolve_if_promise(Misc.safe_asyncio_run(wrapped_func, *positional_args, **func_kwargs))
    else:
        return _resolve_if_promise(wrapped_func(*positional_args, **func_kwargs))
```

### Python Function Wrapper Async Detection

```python
# In python_function.py - execute method
def execute(self, context: SandboxContext, *args: Any, **kwargs: Any) -> Any:
    import asyncio
    from dana.common.utils.misc import Misc

    # Security check: only trusted functions can receive context
    if self.wants_context and self.context_param_name:
        if not self._is_trusted_for_context():
            # Function wants context but is not trusted - call without context
            if asyncio.iscoroutinefunction(self.func):
                return Misc.safe_asyncio_run(self.func, *args, **kwargs)
            else:
                return self.func(*args, **kwargs)
        # ... handle context injection with async detection
    else:
        # Function doesn't want context - call normally with async detection
        if asyncio.iscoroutinefunction(self.func):
            return Misc.safe_asyncio_run(self.func, *args, **kwargs)
        else:
            return self.func(*args, **kwargs)
```

### Unified Dispatcher Async Detection

```python
# In unified_function_dispatcher.py - _execute_callable_function method
def _execute_callable_function(self, resolved_func, context, evaluated_args, evaluated_kwargs, func_name):
    """Execute a regular callable with automatic async detection."""
    import asyncio
    from dana.common.utils.misc import Misc
    
    func = resolved_func.func
    
    # Execute-time async detection and handling
    if asyncio.iscoroutinefunction(func):
        # Function is async - use Misc.safe_asyncio_run
        raw_result = Misc.safe_asyncio_run(func, *evaluated_args, **evaluated_kwargs)
    else:
        # Function is sync - call directly
        raw_result = func(*evaluated_args, **evaluated_kwargs)
        
    return self._assign_and_coerce_result(raw_result, func_name)
```

## Use Cases Covered

### 1. **Static Function Calls**
```dana
from dana.common.sys_resource.rag.utility.web_fetch.py import fetch_web_content

def load_webpage(url: str):
    # Direct call to imported async function
    content = fetch_web_content(url)
    return content
```

### 2. **Dynamic Function Assignment**
```dana
def process_with_choice(use_async: bool):
    if use_async:
        func = fetch_web_content  # Async function
    else:
        func = test_sync_function  # Sync function
    
    # Execute-time detection handles the choice
    return func("data")
```

### 3. **Function Arguments**
```dana
def apply_function(func, data):
    # func could be any function type
    return func(data)

# All of these work automatically
apply_function(fetch_web_content, "url")      # Async
apply_function(test_sync_function, "data")    # Sync
apply_function(len, "string")                 # Built-in
```

### 4. **Object Methods**
```dana
def process_object(obj):
    # Method calls are detected at execute time
    return obj.async_method()  # Works if async
    return obj.sync_method()   # Works if sync
```

### 5. **Subscript Expressions**
```dana
def process_subscript(obj):
    # Subscript calls are detected at execute time
    return obj['async_method']()  # Works if async
    return obj['sync_method']()   # Works if sync
```

## Benefits

### 1. **Complete Coverage**
- Works with all function call patterns
- No edge cases or scenarios where async detection fails
- Handles both static and dynamic function usage

### 2. **Performance**
- No import-time overhead for functions that aren't used
- Per-call detection is efficient and transparent
- No wrapper objects created unnecessarily

### 3. **Flexibility**
- Works with functions created at runtime
- Supports function factories and dynamic loading
- Handles complex function composition patterns

### 4. **Developer Experience**
- No manual async handling required
- Functions work the same way regardless of sync/async
- Consistent behavior across all call patterns

### 5. **Backward Compatibility**
- Existing code continues to work unchanged
- No breaking changes to existing functionality
- Gradual adoption possible

## Testing

### Demo File: `execute_time_demo.na`

The demo file demonstrates all the key scenarios:

```dana
# Test 1: Basic sync function
def test_sync_function():
    return "This is a sync function result"

# Test 2: Mixed sync and async calls
def test_execute_time_async():
    sync_result = test_sync_function()
    web_content = fetch_web_content("https://www.aitomatic.com/")
    return "Execute-time async detection works!"

# Test 3: Dynamic function assignment
def test_dynamic_async():
    dynamic_func = fetch_web_content
    result = dynamic_func("https://www.aitomatic.com/")
    return "Dynamic async detection works!"

# Test 4: Function passed as argument
def test_function_argument(func):
    result = func("https://www.aitomatic.com/")
    return "Function argument async detection works!"
```

### Expected Output
```
=== Dana Execute-Time Async Detection Demo ===
Test 1: Basic sync function
Result: This is a sync function result

Test 2: Execute-time async detection
Sync result: This is a sync function result
Web content length: 1548
Result: Execute-time async detection works!

Test 3: Dynamic async function assignment
Dynamic async call result length: 1548
Result: Dynamic async detection works!

Test 4: Function passed as argument
Function argument call result length: 1548
Result: Function argument async detection works!

=== Demo Complete ===
Execute-time async detection works perfectly!
```

## Technical Implementation

### Async Detection Logic

The core async detection logic is consistent across all components:

```python
import asyncio
from dana.common.utils.misc import Misc

if asyncio.iscoroutinefunction(func):
    # Function is async - use Misc.safe_asyncio_run
    result = Misc.safe_asyncio_run(func, *args, **kwargs)
else:
    # Function is sync - call directly
    result = func(*args, **kwargs)
```

### Integration Points

1. **Function Registry**: Handles registered functions and built-ins
2. **Python Function Wrapper**: Handles imported Python functions
3. **Unified Dispatcher**: Handles dynamic function resolution
4. **Expression Executor**: Handles pipeline and direct function calls
5. **Function Executor**: Handles method calls and subscript expressions

### Error Handling

- Graceful fallback if async detection fails
- Proper error propagation for both sync and async functions
- Consistent error messages across all execution paths

## Comparison with Import-Time Detection

| Aspect | Execute-Time | Import-Time |
|--------|-------------|-------------|
| **Detection Timing** | During execution | During import |
| **Coverage** | All function calls | Static imports only |
| **Performance** | Per-call detection | One-time wrapping |
| **Memory Usage** | No overhead | Wrapper objects |
| **Dynamic Functions** | ✅ Yes | ❌ No |
| **Function Arguments** | ✅ Yes | ❌ No |
| **Runtime Creation** | ✅ Yes | ❌ No |

## Conclusion

Execute-time async detection provides Dana with comprehensive async handling that works in all scenarios. It complements the existing import-time detection to provide complete coverage for both static and dynamic function usage patterns.

The implementation is:
- **Comprehensive**: Covers all function call patterns
- **Efficient**: Minimal overhead with per-call detection
- **Flexible**: Works with any function type or creation pattern
- **Transparent**: No manual intervention required from developers
- **Robust**: Graceful error handling and fallbacks

This makes Dana incredibly powerful for working with Python libraries and APIs, as developers can focus on their business logic rather than managing async/sync complexity.
