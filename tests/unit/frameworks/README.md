# POET Decorator Test Suite Organization

## Overview

This directory contains comprehensive tests for the POET (Programmable Open-Ended Task) decorator system. The test suite is organized to verify both Python and Dana language integration.

## Test Structure

### Core Test Files

#### 1. **Python Decorator Tests**
- `test_poet_decorator_python.py` - Basic Python decorator functionality
- `test_poet_decorator_unit.py` - Unit tests for decorator components

#### 2. **Dana Integration Tests**
- `test_poet_decorator_dana.py` - Dana `.na` file execution tests
- `test_poet_decorator_integration.py` - End-to-end integration tests

#### 3. **Test Data Files**
- `fixtures/` - Dana `.na` test files
- `helpers.py` - Common test utilities

### Obsolete Files (To Be Cleaned)

The following files contain old implementation references and need updating:
- `test_poet_decorator.py` - Contains old metadata assumptions
- `test_poet_decorator.na` - Uses deprecated syntax
- `test_decorator.py` - References removed POETMetadata class
- `test_poet_registry.py` - Contains commented-out tests

## Test Categories

### 1. Basic Decorator Functionality
- Decorator application and wrapping
- Function metadata preservation
- Context handling and interpreter injection

### 2. Dana Language Integration
- `.na` file execution with POET decorators
- Parameter mapping to Dana function scopes
- Error handling and execution flow

### 3. Advanced Features
- Decorator chaining and composition
- Retry logic and timeout handling
- Domain-specific configurations

### 4. Error Cases and Edge Cases
- Missing interpreter contexts
- Invalid parameter combinations
- Function execution failures

## Known Issues

### Interpreter Context Issue
**Status**: ✅ FIXED
- **Problem**: POET decorated Dana functions failed with "No interpreter available in context"
- **Solution**: Enhanced context handling to preserve interpreter references

### Dana Control Flow Issue
**Status**: ❌ PENDING (Separate Dana Core Issue)
- **Problem**: Functions with if/else statements stop program execution
- **Impact**: Affects both POET and regular Dana functions
- **Workaround**: Use functions without control flow for testing

## Running Tests

```bash
# Run all POET tests
uv run pytest tests/dana/poet/ -v

# Run specific test categories
uv run pytest tests/dana/poet/test_poet_decorator_python.py -v
uv run pytest tests/dana/poet/test_poet_decorator_dana.py -v

# Run with debugging output
DXA_LOG_LEVEL=DEBUG uv run pytest tests/dana/poet/ -v -s
```

## Test Organization Goals

1. **Clear Separation**: Python vs Dana tests
2. **Comprehensive Coverage**: All decorator features
3. **Maintainable**: Easy to update as features change
4. **Fast Execution**: Efficient test suite for CI/CD
5. **Clear Documentation**: Each test clearly describes what it verifies 