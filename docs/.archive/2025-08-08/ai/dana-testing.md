# Dana Testing Guidelines

**Recommended Approach**: Use universal Python test runners with `.na` test files for comprehensive Dana language testing.

## 🎯 Overview

Dana testing follows a **universal test runner pattern** that automatically discovers and executes `.na` test files. This approach minimizes boilerplate while ensuring consistent test execution across the codebase.

## 📁 Test Organization Structure

The following shows **examples** of how tests are organized. You can create additional categories as needed for your specific testing requirements:

```
tests/
├── functional/
│   ├── agent/
│   │   ├── test_na_agent.py          # Universal runner for agent tests
│   │   ├── test_reason.na            # Actual Dana test file
│   │   └── test_planning.na          # Another Dana test file
│   ├── language/
│   │   ├── test_na_language_features.py  # Universal runner for language tests
│   │   ├── test_functions.na         # Dana test file
│   │   └── test_control_flow.na      # Dana test file
│   └── stdlib/
│       ├── test_na_stdlib.py         # Universal runner for stdlib tests
│       └── test_math.na              # Dana test file
├── unit/
│   └── frameworks/
│       ├── test_na_frameworks.py     # Universal runner for framework tests
│       └── test_poet.na              # Dana test file
└── regression/
    └── syntax_limitations/
        ├── test_na_syntax_limitations.py  # Universal runner
        └── test_edge_cases.na        # Dana test file
```

**Note**: These are examples of existing categories. You can create new categories and subdirectories as needed for your specific testing requirements.

## 🔧 Universal Test Runner Pattern

### Standard Test Runner Template

Every test category should have a universal runner following this pattern. This file enables pytest to discover and run the `.na` test files:

```python
import pytest
from tests.conftest import run_dana_test_file

@pytest.mark.dana
def test_dana_files(dana_test_file):
    """Universal test that runs any Dana (.na) test file in [category]."""
    run_dana_test_file(dana_test_file)
```

**Purpose**: The runner file makes `.na` tests discoverable by pytest. Without this file, pytest cannot find or execute the `.na` test files.

**Naming Convention**: Use the pattern `test_na_<category_designation>.py` to ensure unique names that pytest can distinguish:
- `test_na_agent.py` for agent tests
- `test_na_language_features.py` for language feature tests
- `test_na_stdlib.py` for standard library tests
- `test_na_frameworks.py` for framework tests

### How It Works

1. **Pytest Discovery**: The runner file enables pytest to discover `.na` test files in the directory
2. **Automatic Discovery**: `pytest_generate_tests()` in `conftest.py` finds all `test_*.na` files when the runner is present
3. **Test Generation**: Creates individual pytest tests for each `.na` file
4. **Execution**: `run_dana_test_file()` executes each `.na` file in a fresh sandbox
5. **Validation**: Asserts successful execution and handles cleanup

**Key Point**: The runner file is the bridge that allows pytest to find and execute `.na` files. Without it, pytest will not run your `.na` tests.

## 📝 Creating Dana Test Files

### Basic Test Structure

```dana
# test_basic_functionality.na
result = some_function("test_input")
# Test passes if execution succeeds without errors
```

### Assertion-Based Tests

```dana
# test_with_assertions.na
value = calculate_something(5)
assert value == 25, "Expected 25, got " + str(value)
```

### Error Testing

```dana
# test_error_handling.na
try:
    invalid_operation()
    assert false, "Should have raised an error"
except:
    # Test passes if error is caught
    pass
```

### Integration Tests

```dana
# test_integration.na
# Test multiple components working together
data = load_data("test.csv")
processed = process_data(data)
result = save_results(processed)
assert result.success == true
```

## 🎯 Test Categories and Naming

The following are **examples** of existing test categories. You can create additional categories based on your specific needs:

### Functional Tests (`tests/functional/`)
- **Agent Tests**: `tests/functional/agent/test_*.na`
- **Language Features**: `tests/functional/language/test_*.na`
- **Standard Library**: `tests/functional/stdlib/test_*.na`
- **Integration**: `tests/functional/integration/test_*.na`
- **Your Category**: `tests/functional/your_category/test_*.na`

### Unit Tests (`tests/unit/`)
- **Core Components**: `tests/unit/core/test_*.na`
- **Frameworks**: `tests/unit/frameworks/test_*.na`
- **API Components**: `tests/unit/api/test_*.na`
- **Your Category**: `tests/unit/your_category/test_*.na`

### Regression Tests (`tests/regression/`)
- **Syntax Issues**: `tests/regression/syntax_limitations/test_*.na`
- **Performance**: `tests/regression/performance/test_*.na`
- **Edge Cases**: `tests/regression/edge_cases/test_*.na`
- **Your Category**: `tests/regression/your_category/test_*.na`

### Creating New Categories

To create a new test category:

1. **Create the directory structure**:
   ```bash
   mkdir -p tests/functional/your_new_category
   ```

2. **Create the universal runner** (required for pytest to discover `.na` files):
   ```python
   # tests/functional/your_new_category/test_na_your_category.py
   import pytest
   from tests.conftest import run_dana_test_file

   @pytest.mark.dana
   def test_dana_files(dana_test_file):
       """Universal test that runs any Dana (.na) test file in your_new_category."""
       run_dana_test_file(dana_test_file)
   ```
   
   **Important**: 
   - This runner file is essential - pytest will not discover or run `.na` files without it
   - Use a unique name following the pattern `test_na_<category_designation>.py` to avoid pytest conflicts

3. **Add your `.na` test files**:
   ```bash
   touch tests/functional/your_new_category/test_example.na
   ```

## 🚀 Running Tests

### Run All Dana Tests
```bash
pytest tests/ -m dana -v
```

### Run Specific Category
```bash
pytest tests/functional/agent/ -v
pytest tests/functional/language/ -v
```

### Run Individual Test File
```bash
pytest tests/functional/agent/test_na_agent.py::test_dana_files[test_reason] -v
```

### Run with LLM Support
```bash
pytest tests/ -m dana --run-llm -v
```

## 📋 Best Practices

### Test File Naming
- Use descriptive names: `test_user_authentication.na`
- Group related tests: `test_math_operations.na`
- Use consistent prefixes: `test_*.na`

### Runner File Naming
- **Use unique names**: `test_na_<category_designation>.py` to avoid pytest conflicts
- **Be descriptive**: Choose names that clearly identify the test category
- **Follow conventions**: Use lowercase with underscores for readability
- **Examples**:
  - `test_na_agent.py` for agent functionality tests
  - `test_na_language_core.py` for core language features
  - `test_na_integration_api.py` for API integration tests

### Test Content
- **Keep tests focused**: One concept per test file
- **Use clear assertions**: Make expected behavior explicit
- **Test edge cases**: Include boundary conditions
- **Test error scenarios**: Verify proper error handling
- **Use realistic data**: Test with production-like inputs

### Test Organization
- **Group by functionality**: Related tests in same directory
- **Use subdirectories**: For complex feature areas
- **Mirror code structure**: Test organization follows code organization

### Test Isolation
- **Fresh sandbox**: Each test runs in isolated environment
- **Clean state**: No shared state between tests
- **Resource cleanup**: Automatic cleanup after each test

## 🔍 Debugging Tests

### Verbose Output
```bash
pytest tests/ -m dana -v -s
```

### Specific Test Debugging
```bash
pytest tests/functional/agent/test_na_agent.py::test_dana_files[test_reason] -v -s --log-cli-level=DEBUG
```

### Manual Test Execution
```python
from dana.core.lang.dana_sandbox import DanaSandbox

sandbox = DanaSandbox()
try:
    result = sandbox.run_file("path/to/test.na")
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")
finally:
    sandbox._cleanup()
```

## ⚠️ Common Pitfalls

### ❌ Avoid These Patterns
- **Complex setup in .na files**: Keep tests simple and focused
- **Shared state between tests**: Each test should be independent
- **Long-running tests**: Keep execution time reasonable
- **External dependencies**: Mock external services when possible
- **Hardcoded paths**: Use relative paths and test data
- **Duplicate runner names**: Avoid using the same runner file name across different directories
- **Generic runner names**: Don't use names like `test_na_tests.py` that don't identify the category

### ✅ Recommended Patterns
- **Simple, focused tests**: One concept per test file
- **Clear assertions**: Explicit success/failure conditions
- **Descriptive names**: Self-documenting test names
- **Error testing**: Include both success and failure scenarios
- **Realistic scenarios**: Test with production-like data

## 🔄 Test Maintenance

### Adding New Tests
1. Create `.na` file in appropriate test directory
2. Ensure universal runner exists for that category
3. Run tests to verify discovery and execution
4. Add to CI/CD pipeline if needed

### Updating Existing Tests
1. Modify `.na` file directly
2. Run tests to verify changes
3. Update documentation if test behavior changes
4. Consider impact on other tests

### Test Review Process
- **Code review**: Include test changes in PR reviews
- **Test coverage**: Ensure new features have corresponding tests
- **Test quality**: Verify tests are meaningful and maintainable
- **Performance**: Monitor test execution time

## 📊 Test Metrics and Quality

### Coverage Goals
- **Functional coverage**: All public APIs tested
- **Error coverage**: All error paths tested
- **Integration coverage**: Component interactions tested
- **Regression coverage**: Known issues prevented

### Quality Indicators
- **Test pass rate**: 100% pass rate required
- **Execution time**: Reasonable test suite duration
- **Maintainability**: Easy to understand and modify
- **Reliability**: Consistent results across environments

## 🎯 Summary

The universal test runner pattern provides:
- **Pytest Integration**: Enables pytest to discover and run `.na` test files
- **Minimal boilerplate**: Just create `.na` files and a simple runner
- **Automatic discovery**: No manual test registration required
- **Consistent execution**: Standardized test environment across all tests
- **Easy maintenance**: Simple to add and modify tests
- **Comprehensive coverage**: Systematic testing approach

**Core Benefit**: The runner file is the essential bridge that makes `.na` files discoverable and executable by pytest. Without it, your `.na` tests won't be run by the test suite.

This approach makes Dana testing accessible and maintainable while ensuring high-quality, reliable test coverage across the codebase. 