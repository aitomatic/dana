# Dana Comprehensions Primer

**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 0.9.0  
**Status:** Implementation

## Problem Statement

Dana currently lacks list, set, and dictionary comprehensions, which are powerful and expressive ways to create collections from existing data. Users need concise, readable syntax for transforming and filtering data without verbose loops.

## Goals

- Provide Python-like comprehension syntax for creating lists, sets, and dictionaries
- Support filtering with conditional expressions
- Enable nested comprehensions for complex transformations
- Maintain Dana's scoping and type safety principles

## Non-Goals

- Complex generator expressions (deferred to future)
- Async comprehensions (not needed in Dana's model)
- Custom comprehension protocols (keep it simple)

## Proposed Solution

**Note:** Dana's comprehension syntax is largely compatible with Python, except for dictionary comprehensions which require parentheses around key-value pairs: `{(k: v) for ...}` instead of Python's `{k: v for ...}`.

### List Comprehensions

```dana
# Basic list comprehension
numbers = [1, 2, 3, 4, 5]
squares = [x * x for x in numbers]

# With filtering
even_squares = [x * x for x in numbers if x % 2 == 0]

# Nested comprehension
matrix = [[1, 2], [3, 4], [5, 6]]
flattened = [x for row in matrix for x in row]
```

### Set Comprehensions

```dana
# Basic set comprehension
words = ["hello", "world", "hello", "dana"]
unique_lengths = {len(word) for word in words}

# With filtering
long_words = {word for word in words if len(word) > 4}
```

### Dictionary Comprehensions

```dana
# Basic dict comprehension
numbers = [1, 2, 3, 4, 5]
squares_dict = {(x: x * x) for x in numbers}

# With filtering
even_squares_dict = {(x: x * x) for x in numbers if x % 2 == 0}

# From existing dict
original = {"a": 1, "b": 2, "c": 3}
doubled = {(k: v * 2) for k, v in original.items()}
```

**Note:** Dana uses parentheses around key-value pairs `{(k: v) for ...}` to distinguish dictionary comprehensions from set comprehensions, unlike Python's `{k: v for ...}` syntax.

## Syntax Specification

### Grammar Rules

```
comprehension ::= "[" expression "for" target_list "in" expression ["if" expression] "]"
                | "{" expression "for" target_list "in" expression ["if" expression] "}"
                | "{" "(" expression ":" expression ")" "for" target_list "in" expression ["if" expression] "}"
```

### Scoping Rules

- Variables in the target_list are scoped to the comprehension
- Variables from outer scope are accessible
- Comprehension variables don't leak to outer scope
- Follows Dana's existing scoping rules

### Type Safety

- List comprehensions produce lists
- Set comprehensions produce sets
- Dict comprehensions produce dictionaries
- Type checking applies to expressions within comprehensions

## Implementation Examples

### Basic Usage

```dana
# Transform numbers
numbers = [1, 2, 3, 4, 5]
doubled = [x * 2 for x in numbers]
# Result: [2, 4, 6, 8, 10]

# Filter and transform
positive = [x for x in numbers if x > 0]
# Result: [1, 2, 3, 4, 5]
```

### Advanced Usage

```dana
# Nested data transformation
users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]

# Extract names
names = [user["name"] for user in users]

# Filter by age and extract names
adult_names = [user["name"] for user in users if user["age"] >= 30]

# Create lookup dict
age_lookup = {(user["name"]: user["age"]) for user in users}
```

## Error Handling

```dana
# Safe access with comprehensions
data = [{"value": 1}, {}, {"value": 3}]

# Handle missing keys gracefully
values = [item.get("value", 0) for item in data]
# Result: [1, 0, 3]
```

## Performance Considerations

- Comprehensions are generally more efficient than equivalent loops
- Memory usage scales with input size
- Consider generator expressions for large datasets (future feature)
- Lazy evaluation not supported (Dana is eager by design)

## Migration from Loops

### Before (with loops)
```dana
numbers = [1, 2, 3, 4, 5]
squares = []
for x in numbers:
    if x % 2 == 0:
        squares.append(x * x)
```

### After (with comprehension)
```dana
numbers = [1, 2, 3, 4, 5]
squares = [x * x for x in numbers if x % 2 == 0]
```

## Testing Strategy

### Unit Tests
- Basic comprehension syntax
- Filtering with conditions
- Nested comprehensions
- Type safety validation
- Scoping rules verification

### Integration Tests
- Comprehension with Dana's type system
- Integration with existing collection operations
- Performance benchmarks vs loops

## Future Enhancements

- Generator expressions for lazy evaluation
- Async comprehensions (if async is added)
- Custom comprehension protocols
- Comprehension optimization passes 