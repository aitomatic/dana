<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../README.md) | [Main Documentation](../docs/README.md)

# Dana Test Suite

This directory contains the comprehensive test suite for the Dana language and runtime system.

## Test Organization

The test suite is organized into four main categories:

### 1. Unit Tests (`tests/unit/`)
Python-based unit tests for individual modules and components.

- **`core/`** - Tests for `dana/core/` modules (language, runtime, repl, stdlib)
- **`agent/`** - Tests for `dana/agent/` modules (agent system, capabilities)
- **`api/`** - Tests for `dana/api/` modules (server, client)
- **`frameworks/`** - Tests for `dana/frameworks/` modules (knows, poet, agent frameworks)
- **`integrations/`** - Tests for `dana/integrations/` modules (vscode, mcp, python)
- **`common/`** - Tests for `dana/common/` modules (shared utilities)
- **`contrib/`** - Tests for `dana/contrib/` modules (community contributions)

### 2. Functional Tests (`tests/functional/`)
Dana language tests (`.na` files) that test the language features directly.

- **`language/`** - Core language features (syntax, semantics, control flow)
- **`stdlib/`** - Standard library features (poet, built-in functions)
- **`agent/`** - Agent language features (reasoning, agent keywords)
- **`integration/`** - Cross-feature integration tests and scenarios

### 3. Integration Tests (`tests/integration/`)
Python-based integration tests that test multiple components working together.

- **`end_to_end/`** - Full system integration tests
- **`api/`** - API integration tests
- **`frameworks/`** - Framework integration tests

### 4. Regression Tests (`tests/regression/`)
Tests for known issues, expected failures, and regression prevention.

- **`known_issues/`** - Tests for known bugs and limitations
- **`expected_failures/`** - Tests that are expected to fail (syntax limitations, etc.)

## Running Tests

### All Tests
```bash
python -m pytest tests/
```

### Unit Tests Only
```bash
python -m pytest tests/unit/
```

### Functional Tests Only
```bash
python -m pytest tests/functional/
```

### Integration Tests Only
```bash
python -m pytest tests/integration/
```

### Specific Module Tests
```bash
python -m pytest tests/unit/core/
python -m pytest tests/functional/language/
```

### Dana Language Tests
```bash
# Run all .na files
find tests/functional -name "*.na" -exec dana {} \;

# Run specific .na file
dana tests/functional/language/test_simple.na
```

## Test Categories

### Unit Tests
- **Purpose**: Test individual functions, classes, and modules in isolation
- **Language**: Python
- **Scope**: Single module or component
- **Speed**: Fast execution

### Functional Tests
- **Purpose**: Test Dana language features and behavior
- **Language**: Dana (`.na` files)
- **Scope**: Language features, syntax, semantics
- **Speed**: Medium execution (requires Dana interpreter)

### Integration Tests
- **Purpose**: Test multiple components working together
- **Language**: Python
- **Scope**: End-to-end workflows, API interactions
- **Speed**: Slower execution (involves multiple components)

### Regression Tests
- **Purpose**: Prevent regressions and test known limitations
- **Language**: Python and Dana
- **Scope**: Known issues, edge cases, failure modes
- **Speed**: Variable

## Test Naming Conventions

### Python Tests
- `test_*.py` - Test files
- `test_*` - Test functions
- `Test*` - Test classes

### Dana Tests
- `test_*.na` - Test files
- Descriptive names that indicate what feature is being tested

## Adding New Tests

### Unit Tests
1. Create test file in appropriate `tests/unit/` subdirectory
2. Follow pytest conventions
3. Use descriptive test names
4. Include docstrings explaining test purpose

### Functional Tests
1. Create `.na` file in appropriate `tests/functional/` subdirectory
2. Use clear, descriptive names
3. Include comments explaining test purpose
4. Test both success and failure cases

### Integration Tests
1. Create test file in appropriate `tests/integration/` subdirectory
2. Test realistic workflows
3. Include setup and teardown as needed
4. Test error conditions and edge cases

## Test Configuration

- `pytest.ini` - Pytest configuration
- `conftest.py` - Shared fixtures and configuration
- `tests/conftest.py` - Test-specific fixtures

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Main branch commits
- Release tags

## Coverage

Test coverage is tracked and reported for:
- Line coverage
- Branch coverage
- Function coverage

Run coverage report:
```bash
python -m pytest --cov=dana tests/
```

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
