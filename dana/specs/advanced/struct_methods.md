**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 1.0.0  
**Status:** Implementation


# Struct Methods Design - Dana Core Language Enhancement

## Overview

This directory contains the design documents for implementing **explicit receiver syntax with union type support** for struct methods in Dana. This enhancement replaces the current implicit struct method resolution with a Go-inspired explicit receiver syntax.

## Problem Statement

Currently, Dana uses implicit struct method resolution where `some_struct.some_func()` is transformed into `some_func(some_struct, ...)` at runtime. This approach has several limitations:

1. **Inefficient Lookup**: Searches multiple scopes (registry, local, private, public, system)
2. **No Compile-Time Validation**: Errors only discovered at runtime
3. **Limited Expressiveness**: Can't easily express methods that work with multiple struct types
4. **Complex Transformation Logic**: Hidden syntactic sugar makes debugging difficult

## Proposed Solution

Replace implicit method resolution with **explicit receiver syntax**:

```dana
# Current (implicit): Runtime transformation
def translate(point: Point, dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

# Proposed (explicit): Compile-time resolution
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

# With union type support
def (shape: Point | Circle | Rectangle) area() -> float:
    if isinstance(shape, Point):
        return 0.0
    elif isinstance(shape, Circle):
        return 3.14159 * shape.radius * shape.radius
    elif isinstance(shape, Rectangle):
        return shape.width * shape.height
```

## Key Benefits

1. **Compile-Time Validation**: Method existence and type compatibility checked at parse time
2. **Direct Method Resolution**: O(1) lookup from method table, no scope searching
3. **Union Type Support**: Methods can operate on multiple struct types
4. **Clear Intent**: Explicit declaration of which structs a method operates on
5. **Better Performance**: No runtime transformation or scope searching
6. **Simpler Architecture**: One way to define and resolve methods

## Design Documents

- **[01_requirements.md](01_requirements.md)** - Problem statement, use cases, and success criteria
- **[02_syntax_design.md](02_syntax_design.md)** - Detailed syntax specification and grammar changes
- **[03_implementation_plan.md](03_implementation_plan.md)** - 3D methodology implementation plan

## Architecture Impact

### Files to Modify
- `dana/core/lang/parser/` - Add receiver syntax parsing
- `dana/core/lang/ast/` - Add receiver AST nodes
- `dana/core/lang/interpreter/executor/` - Remove implicit transformation logic
- `dana/core/lang/interpreter/struct_system.py` - Add explicit method registration

### Files to Remove/Simplify
- Implicit method transformation logic in `function_executor.py`
- Scope searching for method calls in `expression_executor.py`
- Complex method resolution in `function_resolver.py`

## Migration Strategy

Since we're not maintaining backward compatibility:
1. Remove all implicit method resolution code
2. Implement explicit receiver syntax
3. Update all examples and documentation
4. Provide migration tools for any existing code

## Success Criteria

1. **Compile-Time Errors**: Method existence validated at parse time
2. **Union Type Support**: Methods can operate on multiple struct types
3. **Performance**: O(1) method resolution
4. **Expressiveness**: Clear, readable method declarations
5. **Consistency**: Single, predictable method resolution strategy 