# Phase 1: Basic Syntax Tests

This directory contains comprehensive tests for Dana language basic syntax elements, covering assignments, expressions, and control flow.

## Test Categories

### 1. Basic Assignments and Variables
- **test_basic_assignments.na** - Simple variable assignments and data types
- **test_scoped_assignments.na** - Scoped assignments (private, public, local, system)
- **test_typed_assignments.na** - Typed variable assignments with type annotations
- **test_compound_assignments.na** - Compound assignment operators (+=, -=, *=, /=)
- **test_attribute_assignments.na** - Attribute assignments with dot notation
- **test_index_assignments.na** - Index assignments with list and dictionary indices

### 2. Expressions and Operations
- **test_arithmetic_expressions.na** - Arithmetic operators and expressions
- **test_comparison_expressions.na** - Comparison operators and expressions
- **test_logical_expressions.na** - Logical operators (and, or, not) and expressions

### 3. Control Flow
- **test_control_flow.na** - Control flow statements (if, elif, else, for, while)

## Running the Tests

### Individual Test
```bash
dana test_basic_assignments.na
```

### All Phase 1 Tests
```bash
python run_phase1_tests.py
```

### From Project Root
```bash
cd tests/integration/tests/01_basic_syntax
python run_phase1_tests.py
```

## Test Structure

Each test file follows a consistent structure:
- Header comment with test purpose and category
- Multiple test cases with descriptive comments
- Assertions to verify expected behavior
- Log statements for progress tracking
- Error handling for edge cases

## Expected Coverage

Phase 1 tests cover:

### Basic Assignments
- ✅ Simple assignments: `x = 42`
- ✅ Scoped assignments: `private:x = 42`
- ✅ Typed assignments: `x: int = 42`
- ✅ Compound assignments: `x += 5`
- ✅ Attribute assignments: `obj.value = 10`
- ✅ Index assignments: `list[0] = 10`

### Expressions
- ✅ Arithmetic: `+`, `-`, `*`, `/`, `//`, `%`, `**`
- ✅ Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- ✅ Logical: `and`, `or`, `not`
- ✅ Order of operations and parentheses
- ✅ Mixed type operations
- ✅ Error handling (division by zero, etc.)

### Control Flow
- ✅ If/elif/else statements
- ✅ For loops with various iterables
- ✅ While loops with break/continue
- ✅ Nested control structures
- ✅ Complex conditions
- ✅ Conditional expressions

## Test Results

Tests should pass with:
- ✅ All assertions successful
- ✅ Proper error handling
- ✅ Expected output and behavior
- ✅ No syntax errors
- ✅ No runtime errors

## Integration with CI/CD

These tests are designed to run in CI/CD pipelines to ensure:
- No regressions in basic syntax
- Consistent behavior across environments
- Early detection of breaking changes
- Comprehensive coverage of core language features

## Next Steps

After Phase 1 tests pass, proceed to:
- Phase 2: Advanced Syntax (lambdas, comprehensions, pipelines)
- Phase 3: Built-in Functions
- Phase 4: Type System
- And subsequent phases as defined in the implementation plan 