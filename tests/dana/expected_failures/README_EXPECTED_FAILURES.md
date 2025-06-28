# Dana Expected Failures Test Battery

## Overview

This directory contains a comprehensive battery of tests documenting Dana language features that seem natural from a Python/programming perspective but are not currently supported. These tests serve as:

1. **Documentation** of current language limitations
2. **Feature requests** for potential future enhancements  
3. **Workaround guides** for developers encountering these limitations
4. **Design considerations** for language evolution

## Test Philosophy

These tests are marked as **expected failures** (`pytest.xfail`) which means:
- ✅ They **PASS** the test suite (don't break CI/CD)
- 📋 They **DOCUMENT** limitations systematically
- 🔧 They **PROVIDE** workarounds for each limitation
- 🚀 They **SUGGEST** potential future enhancements

## Directory Structure

```
tests/dana/expected_failures/
├── syntax_limitations/           # Language syntax features
├── operator_limitations/         # Operator and expression features  
├── function_limitations/         # Function and callable features
├── data_structure_limitations/   # Collection and data type features
└── README_EXPECTED_FAILURES.md  # This documentation
```

## Test Categories

### 1. Syntax Limitations (`syntax_limitations/`)

Documents syntax features that would be natural but aren't supported:

**Compound Assignment Operators:**
- `+=`, `*=`, `-=`, `/=` operators
- String and list concatenation assignment
- Workaround: Use explicit assignment (`x = x + y`)

**Conditional Expressions:**
- Ternary operator: `result = "yes" if condition else "no"`
- Nested conditionals
- Workaround: Use if-else statements

**Advanced String Operations:**
- `%` formatting: `"Hello %s" % name`
- String multiplication: `"abc" * 3`
- Method chaining issues
- Workaround: Use f-strings and separate method calls

**Assignment Patterns:**
- Tuple unpacking: `a, b, c = (1, 2, 3)`
- Starred expressions: `first, *middle, last = items`
- Chained assignment: `a = b = c = 42`
- Slice assignment: `items[1:3] = [10, 20]`

**Advanced Control Flow:**
- Walrus operator: `if (n := len(items)) > 5:`
- Match/case statements
- Workaround: Use traditional control structures

**Function Features:**
- Keyword-only arguments: `def func(a, *, b, c):`
- Positional-only arguments: `def func(a, b, /, c):`
- Complex type annotations

### 2. Operator Limitations (`operator_limitations/`)

Documents operator features that would be useful but aren't supported:

**Membership Operators:**
- `not in` operator (known limitation)
- `is not` operator
- Workaround: Use `not (x in y)` and `not (x is y)`

**Arithmetic Operators:**
- Floor division: `//`
- Matrix multiplication: `@`
- Unary operators on custom types
- Workaround: Use explicit functions

**Bitwise Operators:**
- `&`, `|`, `^`, `<<`, `>>` operators
- Conflict with pipe operator (`|`)
- Workaround: Use bit manipulation functions

**Operator Overloading:**
- `__add__`, `__eq__`, `__lt__` methods on structs
- Custom operator behavior
- Workaround: Use explicit methods

**Precedence Issues:**
- Complex expressions mixing pipes and arithmetic
- Mixed logical/arithmetic operator chains
- Workaround: Use parentheses for clarity

### 3. Function Limitations (`function_limitations/`)

Documents advanced function features that aren't supported:

**Higher-Order Functions:**
- Function assignment variables (sometimes return `None`)
- Function composition patterns
- Partial function application
- Workaround: Use direct function calls

**Advanced Parameters:**
- `*args` and `**kwargs`
- Mixed parameter types
- Workaround: Use explicit parameters

**Decorators:**
- Custom decorators: `@decorator`
- Parameterized decorators: `@decorator(arg)`
- Multiple decorators
- Workaround: Use explicit function wrapping

**Closures and Scope:**
- `nonlocal` keyword
- Nested function scope issues
- `global` keyword limitations
- Workaround: Use class-based state management

**Lambda Functions:**
- `lambda` expressions
- Lambda in higher-order functions
- Workaround: Use named functions

**Function Introspection:**
- `__name__`, `__doc__` attributes
- `inspect` module functionality
- Workaround: Use explicit documentation

**Recursion Limitations:**
- Deep recursion limits
- Mutual recursion issues
- Tail recursion optimization
- Workaround: Use iterative approaches

### 4. Data Structure Limitations (`data_structure_limitations/`)

Documents advanced data structure features that aren't supported:

**List Comprehensions:**
- `[x*2 for x in items]`
- Conditional comprehensions
- Nested comprehensions
- Dictionary/set comprehensions
- Workaround: Use explicit loops

**Collection Methods:**
- List methods: `.append()`, `.extend()`, `.pop()`, `.remove()`
- Dictionary methods: `.get()`, `.update()`, `.pop()`, `.setdefault()`
- String methods: `.join()`, `.startswith()`, `.find()`
- Workaround: Use manual operations or built-in functions

**Advanced Operations:**
- Set operations and literals: `{1, 2, 3}`
- Dictionary merge operator: `dict1 | dict2`
- Extended slicing: `items[::2]`, `items[::-1]`
- Workaround: Use explicit operations

**Type Operations:**
- `isinstance()` function
- Complex type conversions
- Runtime type annotation access
- Workaround: Use duck typing and explicit checks

## Running Expected Failure Tests

### Run All Expected Failure Tests
```bash
# Run all expected failure tests
uv run pytest tests/dana/expected_failures/ -v

# Run specific category
uv run pytest tests/dana/expected_failures/syntax_limitations/ -v
```

### Run Individual Documentation Files
```bash
# Run Dana files directly to see documentation
uv run python -m opendxa.dana.exec.dana tests/dana/expected_failures/syntax_limitations/test_expected_syntax_failures.na

# Run all documentation files
find tests/dana/expected_failures -name "*.na" -exec uv run python -m opendxa.dana.exec.dana {} \;
```

### Expected Output
- **Pytest**: Shows `XFAIL` (expected failure) status ✅
- **Direct execution**: Shows detailed documentation with workarounds 📋

## Test Design Principles

### 1. Documentation-First Approach
- Each limitation is clearly documented with examples
- Reasons for limitations are explained
- Workarounds are provided for every limitation
- Future considerations are noted

### 2. Non-Breaking Design
- Tests use `pytest.xfail()` to mark as expected failures
- Tests don't cause syntax errors (use string documentation)
- Tests pass the CI/CD pipeline
- Tests provide valuable information without breaking builds

### 3. Comprehensive Coverage
- **80+ documented limitations** across 4 categories
- **Real-world scenarios** that developers might encounter
- **Practical workarounds** for each limitation
- **Future enhancement suggestions** for language evolution

### 4. Maintainable Structure
- Each category has its own directory and test file
- Consistent documentation format across all tests
- Easy to add new limitations as they're discovered
- Clear separation between different types of limitations

## Usage Guidelines

### For Developers
1. **Check expected failures** before reporting bugs
2. **Use provided workarounds** for known limitations
3. **Contribute new limitations** as they're discovered
4. **Reference in documentation** when explaining Dana limitations

### For Language Designers
1. **Review for enhancement priorities** based on developer needs
2. **Use as regression tests** when implementing new features
3. **Reference design decisions** documented in limitations
4. **Track implementation progress** by converting XFAIL to working features

### For Contributors
1. **Add new limitations** following the documentation format
2. **Update workarounds** as better solutions are found
3. **Test thoroughly** to ensure non-breaking behavior
4. **Document clearly** with examples and rationale

## Integration with Main Test Suite

The expected failure tests integrate seamlessly with the main Dana test suite:

```bash
# Run all Dana tests including expected failures
uv run pytest tests/dana/ -v

# Expected failures show as XFAIL and don't break the build
# Regular tests show as PASSED/FAILED as normal
```

## Metrics and Status

- **📊 Total Documented Limitations**: 80+
- **🔧 Categories Covered**: 4 (syntax, operators, functions, data structures)
- **💡 Workarounds Provided**: 100% coverage
- **🚀 Future Enhancements Suggested**: All limitations
- **✅ Test Suite Integration**: Non-breaking XFAIL design
- **📋 Documentation Quality**: Comprehensive with examples

## Future Enhancements

As Dana evolves, expected failures can be converted to regular tests:

1. **Implement feature** in Dana language
2. **Convert XFAIL test** to regular test
3. **Update documentation** to reflect new capability
4. **Add regression tests** to prevent future breakage

This creates a clear roadmap for language enhancement based on documented developer needs.

---

**Note**: This test battery complements the main integrated test suite and provides valuable documentation for both current limitations and future language evolution. 