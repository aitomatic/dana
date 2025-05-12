# Function Parameters in DANA

## Overview

In DANA, function parameters are automatically added to the local scope when a function is called. This behavior is similar to Python's function parameter handling, making it intuitive for Python developers.

## Parameter Types

DANA supports two types of function parameters:

1. **Named Parameters**
   ```dana
   function_name(param1=value1, param2=value2)
   ```
   These parameters are added to the local scope with their exact names:
   ```dana
   local.param1 = value1
   local.param2 = value2
   ```

2. **Positional Parameters**
   ```dana
   function_name(value1, value2)
   ```
   These parameters are added to the local scope with sequential names:
   ```dana
   local.arg0 = value1
   local.arg1 = value2
   ```

## Parameter Access

Function parameters can be accessed in two ways:

1. **Direct Local Scope Access**
   ```dana
   def my_function(ctx, args):
       x = ctx.get("local.x")  # Named parameter
       first_arg = ctx.get("local.arg0")  # First positional parameter
   ```

2. **Args Dictionary Access** (for backward compatibility)
   ```dana
   def my_function(ctx, args):
       x = args.get("x")  # Named parameter
       first_arg = args.get("__positional_0")  # First positional parameter
   ```

## Scope Rules

- Function parameters are always added to the local scope
- Local scope variables are isolated to the current function call
- Parameters do not leak to global scopes (private/public/system)
- Local scope variables do not inherit from parent contexts

## Example

```dana
# Function definition
def process_data(ctx, args):
    # Access named parameters
    input_data = ctx.get("local.data")
    threshold = ctx.get("local.threshold")
    
    # Access positional parameters
    first_arg = ctx.get("local.arg0")
    second_arg = ctx.get("local.arg1")
    
    # Process the data
    result = input_data * threshold
    return result

# Function call with named parameters
result = process_data(data=10, threshold=2)

# Function call with positional parameters
result = process_data(10, 2)

# Function call with mixed parameters
result = process_data(10, threshold=2)
```

## Best Practices

1. Use named parameters for clarity when calling functions with multiple parameters
2. Use positional parameters for simple functions with obvious parameter order
3. Access parameters through the local scope for better readability
4. Keep the args dictionary access for backward compatibility only
5. Document parameter names and types in function metadata

## Implementation Details

The function parameter handling is implemented in the `evaluate_function_call` method of the `ExpressionEvaluator` class. When a function is called:

1. A new runtime context is created with the base context
2. Named parameters are added to the local scope with their exact names
3. Positional parameters are added to the local scope as `local.arg0`, `local.arg1`, etc.
4. The function is called with both the context and the original args dictionary

This implementation ensures that:
- Parameters are easily accessible in the local scope
- Function calls remain backward compatible
- Parameter modifications are isolated to the function call
- Global scope variables remain unchanged 