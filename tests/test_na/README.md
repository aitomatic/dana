# Test Runners for test_na Directory

This directory contains comprehensive test runners for the Dana language syntax tests located in the `01_basic_syntax/` and `02_advanced_syntax/` subdirectories.

## Test Runners

### 1. `test_na_basic_syntax.py`
Runs all basic syntax tests from `01_basic_syntax/` directory.

**Usage:**
```bash
# Run all basic syntax tests
python -m pytest test_na_basic_syntax.py -v

# Run with pytest markers
python -m pytest test_na_basic_syntax.py -m na_file -v
```

**Tests covered:**
- Basic assignments and variables
- Data types and literals
- Arithmetic and comparison operators
- Control flow
- Collections and indexing

### 2. `test_na_advanced_syntax.py`
Runs all advanced syntax tests from `02_advanced_syntax/` directory.

**Usage:**
```bash
# Run all advanced syntax tests
python -m pytest test_na_advanced_syntax.py -v

# Run with pytest markers
python -m pytest test_na_advanced_syntax.py -m na_file -v
```

**Tests covered:**
- Lambda functions and closures
- Pipelines (basic and named)
- Comprehensions (list, dict, set, nested)
- Conditional expressions
- Placeholder expressions

### 3. `test_na_comprehensive.py`
Runs all tests from both basic and advanced syntax directories.

**Usage:**
```bash
# Run all tests
python -m pytest test_na_comprehensive.py -v

# Run only the file count test
python -m pytest test_na_comprehensive.py::test_na_file_count -v

# Run with pytest markers
python -m pytest test_na_comprehensive.py -m na_file -v
```

### 4. `run_tests.py`
A simple command-line test runner that can be used directly.

**Usage:**
```bash
# Run all tests
python run_tests.py

# Run only basic syntax tests
python run_tests.py basic

# Run only advanced syntax tests
python run_tests.py advanced

# Run a specific test file
python run_tests.py test_basic_assignments.na
```

## Test Structure

### Basic Syntax Tests (12 files)
Located in `01_basic_syntax/`:
- `test_arithmetic_expressions.na` - Arithmetic operators and precedence
- `test_attribute_assignments.na` - Object attribute assignments
- `test_basic_assignments.na` - Simple variable assignments
- `test_collections_indexing.na` - List, dict, set, tuple operations
- `test_comparison_expressions.na` - Comparison and membership operators
- `test_compound_assignments.na` - +=, -=, *=, /= operators
- `test_control_flow.na` - if/elif/else, for, while loops
- `test_data_types_literals.na` - All literal types and data structures
- `test_index_assignments.na` - Array and dictionary indexing
- `test_logical_expressions.na` - and, or, not operators
- `test_scoped_assignments.na` - private:, public:, local: assignments
- `test_typed_assignments.na` - Type annotations and typed assignments

### Advanced Syntax Tests (13 files)
Located in `02_advanced_syntax/`:
- `test_basic_lambdas.na` - Simple lambda function definitions
- `test_basic_pipelines.na` - Basic pipeline operations
- `test_conditional_expressions.na` - Ternary operators and conditionals
- `test_dict_comprehensions.na` - Dictionary comprehensions
- `test_lambda_closures.na` - Lambda functions with closures
- `test_lambda_complex.na` - Complex lambda expressions
- `test_lambda_parameters.na` - Lambda functions with parameters
- `test_lambda_with_structs.na` - Lambda functions with structs
- `test_list_comprehensions.na` - List comprehensions
- `test_named_pipelines.na` - Named pipeline operations
- `test_nested_comprehensions.na` - Nested comprehension expressions
- `test_placeholder_expressions.na` - Placeholder and wildcard expressions
- `test_set_comprehensions.na` - Set comprehensions

## Configuration

### Environment Variables
- `DANA_SKIP_NA_LLM_TESTS=true` - Skip tests that use `reason()` function

### Type Checking
Most tests run with type checking disabled (`do_type_check=False`) to focus on syntax validation rather than type validation. This allows testing of syntax features that may not yet have full type support.

### Error Handling
The test runners handle expected errors gracefully:
- Division by zero errors (arithmetic tests)
- Index out of range errors (collection tests)
- Callable errors (lambda tests)
- Key errors (dictionary tests)

## Running Tests

### From the test_na directory:
```bash
cd tests/test_na

# Run all tests with pytest
python -m pytest test_na_comprehensive.py -v

# Run basic syntax only
python -m pytest test_na_basic_syntax.py -v

# Run advanced syntax only
python -m pytest test_na_advanced_syntax.py -v

# Use the simple runner
python run_tests.py
```

### From the project root:
```bash
# Run all test_na tests
python -m pytest tests/test_na/test_na_comprehensive.py -v

# Run specific category
python -m pytest tests/test_na/test_na_basic_syntax.py -v
python -m pytest tests/test_na/test_na_advanced_syntax.py -v
```

## Expected Results

- **Basic Syntax Tests**: 12/12 should pass (or handle expected errors)
- **Advanced Syntax Tests**: 13/13 should pass (or handle expected errors)
- **Total Tests**: 25/25 should pass (or handle expected errors)

Some tests may have intentional syntax errors or features that are not yet fully implemented in the Dana language parser/interpreter. These are expected and help identify areas for future development.

## Test Isolation

Each test runs with:
- Cleared `StructTypeRegistry`
- Cleared `MethodRegistry`
- Fresh `SandboxContext`
- Mock LLM resources when needed

This ensures that tests don't interfere with each other and can run independently.
