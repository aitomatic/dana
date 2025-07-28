# Design Document: Struct Methods with Explicit Receiver Syntax

Author: AI Assistant
Version: 1.0
Date: 2025-01-28
Status: Design Phase
Implementation Tracker: struct_methods-implementation.md

## Problem Statement

**Brief Description**: Dana currently uses implicit struct method resolution where methods are looked up dynamically. This creates performance issues and lack of compile-time validation.

- Current situation: Methods are resolved at runtime by searching for functions with matching names
- Pain points: 
  - O(n) performance for method lookup in scopes
  - No compile-time validation of method existence
  - Ambiguity when multiple functions could match
  - Complex transformation logic for method calls
- Impact: Slower execution, runtime errors, harder to debug
- Background: Following Go's philosophy of explicit receiver functions

## Goals

**Brief Description**: Implement explicit receiver syntax for struct methods with compile-time validation.

- Replace implicit method resolution with explicit receiver syntax
- Enable compile-time validation of method existence
- Support union types for polymorphic methods (e.g., `Point | Circle`)
- Achieve O(1) method resolution performance
- Maintain backward compatibility during transition

## Non-Goals

**Brief Description**: What we explicitly won't do in this implementation.

- NOT implementing inheritance or class hierarchies
- NOT adding method visibility modifiers (public/private)
- NOT supporting method overloading by parameter types
- NOT implementing interfaces or traits
- NOT changing how structs store data

## Proposed Solution

**Brief Description**: Go-inspired explicit receiver syntax using union types for polymorphic dispatch.

- Explicit receiver syntax: `def (receiver: Type) method_name(args) -> ReturnType:`
- Union type support: `def (shape: Point | Circle) area() -> float:`
- Compile-time registration of methods with their receiver types
- Direct method dispatch without scope searching
- **KISS/YAGNI Analysis**: Simple receiver syntax covers 95% of use cases without complex type systems

## Proposed Design

**Brief Description**: Four-phase implementation with strict quality gates.

### System Architecture Diagram

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Parser/Grammar    │────▶│ Method Registry  │────▶│ Runtime Dispatch │
│                     │     │                  │     │                 │
│ def (p: Point)     │     │ Point.translate  │     │ instance.method │
│   translate(...)    │     │ Circle.area      │     │ -> direct call  │
└─────────────────────┘     └──────────────────┘     └─────────────────┘
           │                         │                         │
           ▼                         ▼                         ▼
    ┌─────────────┐         ┌──────────────┐         ┌──────────────┐
    │ AST Nodes   │         │ Struct Type  │         │ Method Call  │
    │ MethodDef   │         │ Registry     │         │ Executor     │
    └─────────────┘         └──────────────┘         └──────────────┘
```

### Component Details

#### 1. Grammar and Parser (Phase 1)

**Why this component exists**: Parse explicit receiver syntax and create AST nodes.

**Key design decisions**:
- New grammar rule: `method_def: "def" "(" param ")" NAME "(" [params] ")" ["->" type] ":" suite`
- Receiver must be first parameter with type annotation
- Union types supported: `Point | Circle | Rectangle`
- **Alternatives rejected**: Method syntax inside struct blocks - violates Go philosophy

**Implementation**:
```dana
# New syntax examples
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

def (shape: Circle | Rectangle) area() -> float:
    if isinstance(shape, Circle):
        return 3.14 * shape.radius ** 2
    else:
        return shape.width * shape.height
```

#### 2. Method Registry (Phase 2)

**Why this component exists**: Store method-to-struct mappings for O(1) lookup.

**Key design decisions**:
- Registry maps `(struct_type, method_name) -> DanaFunction`
- Support for union types expanded at registration
- Compile-time validation during registration
- **Alternatives rejected**: Runtime method resolution - too slow

**Data structure**:
```python
class MethodRegistry:
    _methods: dict[tuple[str, str], DanaFunction] = {}  # (type_name, method_name) -> function
    
    def register_method(self, receiver_types: list[str], method_name: str, function: DanaFunction):
        for type_name in receiver_types:
            key = (type_name, method_name)
            if key in self._methods:
                raise DanaError(f"Method {method_name} already defined for {type_name}")
            self._methods[key] = function
```

#### 3. Runtime Dispatch (Phase 3)

**Why this component exists**: Execute method calls with direct dispatch.

**Key design decisions**:
- Direct lookup: `method = registry.get_method(instance.struct_type.name, method_name)`
- No scope searching required
- Error if method not found at runtime
- **Alternatives rejected**: Dynamic dispatch with inheritance - too complex

#### 4. Cleanup and Migration (Phase 4)

**Why this component exists**: Remove old implicit resolution code safely.

**Key design decisions**:
- Deprecation warnings for implicit method calls
- Migration guide for existing code
- Remove transformation logic after transition period

### Data Flow Diagram

```
Method Definition Flow:
Parser ──▶ AST (MethodDef) ──▶ Method Registry ──▶ Stored Function

Method Call Flow:
instance.method() ──▶ Get Struct Type ──▶ Registry Lookup ──▶ Direct Call
```

## Proposed Implementation

**Brief Description**: Four-phase implementation plan with quality gates.

### Phase 1: Grammar and Parser (1-2 weeks)
1. Update `dana_grammar.lark` with method definition syntax
2. Create `MethodDef` AST node
3. Update transformer to handle method definitions
4. Parse receiver types including unions

**Quality Gates**:
- ✅ Grammar parses all test cases
- ✅ AST correctly represents methods
- ✅ Union types parsed correctly

### Phase 2: Method Registration (1-2 weeks)
1. Create `MethodRegistry` class
2. Integrate with `StructTypeRegistry`
3. Register methods at definition time
4. Validate receiver types exist

**Quality Gates**:
- ✅ Methods registered correctly
- ✅ Duplicate detection works
- ✅ Union types expanded properly

### Phase 3: Runtime Execution (1-2 weeks)
1. Update method call executor
2. Implement direct dispatch
3. Error handling for missing methods
4. Remove scope-based lookup

**Quality Gates**:
- ✅ All method calls work
- ✅ Performance improved
- ✅ Error messages clear

### Phase 4: Cleanup and Optimization (1-2 weeks)
1. Remove old transformation code
2. Optimize method lookup
3. Add deprecation warnings
4. Update documentation

**Quality Gates**:
- ✅ No regressions
- ✅ Code simplified
- ✅ Documentation complete

### Testing Strategy

**Test Categories**:
1. **Functional Tests** (`tests/functional/language/test_na_struct_methods.py`):
   - Basic method definitions
   - Union type receivers
   - Method calls and chaining
   - Error cases

2. **Unit Tests** (`tests/unit/core/test_na_struct_methods_core.py`):
   - Parser tests
   - Registry tests
   - Executor tests

3. **Regression Tests** (`tests/regression/struct_methods/`):
   - Ensure existing code works
   - Performance benchmarks

### Performance Considerations

- **Current**: O(n) scope search for each method call
- **New**: O(1) direct registry lookup
- **Memory**: Small overhead for method registry (~100 bytes per method)
- **Benchmark**: 10x faster method resolution expected

### Error Handling

1. **Parse Time**:
   - Invalid receiver syntax
   - Missing type annotations
   - Duplicate method definitions

2. **Runtime**:
   - Method not found
   - Invalid receiver instance
   - Type mismatches

### Security Considerations

- No new security concerns
- Methods have same access as functions
- No dynamic code execution

## Migration Guide

### For Users
```dana
# Old implicit style
def translate(point: Point, dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)

# New explicit style  
def (point: Point) translate(dx: int, dy: int) -> Point:
    return Point(x=point.x + dx, y=point.y + dy)
```

### Compatibility
- Phase 1-3: Both styles work
- Phase 4: Deprecation warnings
- Future: Remove implicit style

## Success Metrics

1. **Performance**: 10x faster method resolution
2. **Reliability**: Zero runtime method-not-found errors
3. **Adoption**: 90% of struct methods migrated
4. **Quality**: 100% test coverage, zero regressions