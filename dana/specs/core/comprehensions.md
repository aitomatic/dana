# Comprehensions Design Document

**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 1.0.0  
**Status:** Implementation

## Problem Statement

Dana currently lacks support for comprehensions, which are a powerful and Pythonic way to create collections from iterables. Users need to write verbose loops to transform and filter data, making code less readable and more error-prone. The current limitation forces users to use traditional for-loops for data transformation tasks that could be expressed more concisely with comprehensions.

**Current Limitations:**
- No list comprehensions: `[x*2 for x in numbers if x > 0]`
- No set comprehensions: `{x*2 for x in numbers if x > 0}`
- No dict comprehensions: `{k: v*2 for k, v in data.items() if v > 0}`
- Users must write verbose loops for data transformation

## Goals

- Provide Pythonic comprehension syntax for creating collections
- Support list, set, and dict comprehensions with conditional filtering
- Maintain consistency with Dana's existing syntax and scoping rules
- Enable concise data transformation and filtering operations
- Follow KISS/YAGNI principles for minimal viable implementation

## Non-Goals

- Nested comprehensions (multiple `for` clauses)
- Multiple conditions (chained `if` statements)
- Generator expressions (lazy evaluation)
- Complex comprehension patterns beyond basic transformation and filtering
- Performance optimizations beyond basic iteration

## Proposed Solution

Comprehensions provide a concise way to create collections by applying expressions to iterable items with optional filtering. The implementation follows the same pattern as Python comprehensions while respecting Dana's scoping and type system.

### Syntax

```dana
# List comprehensions
[expression for item in iterable if condition]

# Set comprehensions  
{expression for item in iterable if condition}

# Dict comprehensions
{key_expression: value_expression for item in iterable if condition}
```

### Semantics

1. **Iteration**: For each item in the iterable, bind it to the target variable
2. **Conditional Filtering**: If a condition is provided, skip items where the condition evaluates to false
3. **Expression Evaluation**: Evaluate the expression(s) in the context of the current item
4. **Collection Building**: Add the result to the appropriate collection type

**Scoping Rules:**
- The target variable (`item`) is scoped to the comprehension iteration
- Variables from outer scopes remain accessible
- The condition and expression can reference both the target variable and outer scope variables

**Type System:**
- List comprehensions return `list` type
- Set comprehensions return `set` type  
- Dict comprehensions return `dict` type
- Type checking validates that the iterable is iterable and expressions are valid

### Implementation Considerations

- **Grammar Extensions**: Extend existing collection grammar rules to support comprehensions
- **AST Nodes**: Create dedicated AST nodes for each comprehension type
- **Executor Integration**: Integrate with existing expression execution framework
- **Type Checking**: Extend type checker to validate comprehension types
- **Backward Compatibility**: No breaking changes to existing collection literals

## Examples

### Basic Usage

```dana
# List comprehension - double each number
numbers = [1, 2, 3, 4, 5]
doubled = [x * 2 for x in numbers]
# Result: [2, 4, 6, 8, 10]

# Set comprehension - unique squares
squares = {x ** 2 for x in numbers}
# Result: {1, 4, 9, 16, 25}

# Dict comprehension - number to string mapping
number_map = {x: str(x) for x in numbers}
# Result: {1: "1", 2: "2", 3: "3", 4: "4", 5: "5"}
```

### Conditional Filtering

```dana
# List comprehension with condition - even numbers only
even_doubled = [x * 2 for x in numbers if x % 2 == 0]
# Result: [4, 8]

# Set comprehension with condition - positive numbers only
positive_squares = {x ** 2 for x in numbers if x > 0}
# Result: {1, 4, 9, 16, 25}

# Dict comprehension with condition - filter by value
data = {"a": 1, "b": 2, "c": 3, "d": 4}
filtered = {k: v * 2 for k, v in data.items() if v > 2}
# Result: {"c": 6, "d": 8}
```

### Advanced Usage

```dana
# Using scoped variables
private:numbers = [1, 2, 3, 4, 5]
private:doubled = [x * 2 for x in private:numbers if x > 2]
# Result: [6, 8, 10]

# Nested data access
data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
names = [item["name"] for item in data if item["age"] > 25]
# Result: ["Alice"]

# Lambda integration
double = lambda x -> x * 2
doubled = [private:double(x) for x in numbers]
# Result: [2, 4, 6, 8, 10]
```

## Alternatives Considered

- **Generator Expressions**: Rejected for initial implementation due to complexity and KISS principles
- **Multiple For Clauses**: Rejected as out of scope for MVP
- **Chained Conditions**: Rejected to keep syntax simple and avoid precedence issues
- **Custom Syntax**: Rejected in favor of Python-compatible syntax for familiarity

## Implementation Plan

### Phase 1: List Comprehensions ✅
- [x] Grammar extension for list comprehensions
- [x] AST node for ListComprehension
- [x] Parser transformer for list comprehensions
- [x] Executor for list comprehension evaluation
- [x] Type checker for list comprehensions
- [x] Comprehensive testing

### Phase 2: Set Comprehensions
- [ ] Grammar extension for set comprehensions
- [ ] AST node for SetComprehension
- [ ] Parser transformer for set comprehensions
- [ ] Executor for set comprehension evaluation
- [ ] Type checker for set comprehensions
- [ ] Comprehensive testing

### Phase 3: Dict Comprehensions
- [ ] Grammar extension for dict comprehensions
- [ ] AST node for DictComprehension
- [ ] Parser transformer for dict comprehensions
- [ ] Executor for dict comprehension evaluation
- [ ] Type checker for dict comprehensions
- [ ] Comprehensive testing

## Testing Strategy

- **Unit Tests**: Test each component (parser, transformer, executor, type checker) in isolation
- **Integration Tests**: Test complete comprehension evaluation end-to-end
- **Edge Cases**: Empty iterables, all items filtered out, type errors
- **Performance Tests**: Large iterables to ensure reasonable performance
- **Compatibility Tests**: Ensure comprehensions work with existing Dana features

## Dependencies

- **Lark Parser**: For grammar parsing and AST generation
- **Existing AST Infrastructure**: Reuse existing Expression and Location types
- **Executor Framework**: Integrate with existing expression execution system
- **Type System**: Extend existing DanaType system for comprehension types

## References

- **Python Comprehensions**: [PEP 202](https://peps.python.org/pep-0202/) - List Comprehensions
- **Dana Grammar**: `dana/core/lang/parser/dana_grammar.lark`
- **Dana AST**: `dana/core/lang/ast/__init__.py`
- **Dana Executor**: `dana/core/lang/interpreter/executor/expression_executor.py`

## Status

- [x] Design approved
- [x] List comprehensions implementation complete
- [ ] Set comprehensions implementation started
- [ ] Dict comprehensions implementation started
- [ ] Documentation complete
- [ ] Released 