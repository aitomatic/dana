# Functional Tests

This directory contains Dana language tests (`.na` files) that test the language features directly.

## Structure

- **`language/`** - Core language features
  - Syntax and semantics
  - Control flow (if/else, loops)
  - Functions and function composition
  - Variable assignments and scope
  - Error handling
  - Method chaining
  - Type coercion
  - Imports and modules

- **`stdlib/`** - Standard library features
  - Poet framework integration
  - Built-in functions
  - Standard library modules
  - Utility functions

- **`agent/`** - Agent language features
  - Reasoning capabilities
  - Agent keywords and syntax
  - Agent interactions
  - Agent state management

- **`integration/`** - Cross-feature integration
  - Data structures and management
  - Financial services scenarios
  - Complex workflows
  - End-to-end scenarios

## Running Functional Tests

```bash
# Run all .na files
find tests/functional -name "*.na" -exec dana {} \;

# Run specific category
find tests/functional/language -name "*.na" -exec dana {} \;
find tests/functional/stdlib -name "*.na" -exec dana {} \;

# Run specific file
dana tests/functional/language/test_simple.na
```

## Test Guidelines

1. **Clarity**: Use clear, descriptive file names
2. **Comments**: Include comments explaining test purpose
3. **Coverage**: Test both success and failure cases
4. **Isolation**: Each test should be self-contained
5. **Realistic**: Use realistic examples and scenarios

## Example Test Structure

```dana
# Test basic variable assignment
x = 42
assert x == 42

# Test function definition and call
def add(a, b):
    return a + b

result = add(5, 3)
assert result == 8

# Test error handling
try:
    result = 1 / 0
except:
    print("Division by zero caught")
```

## Integration with Python Tests

Some functional tests may have corresponding Python test files that:
- Set up test environments
- Provide test fixtures
- Validate test results
- Handle test execution

These Python files should be placed in the corresponding `tests/unit/` directory. 