<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../README.md) | [Main Documentation](../docs/README.md)

# OpenDXA Test Suite

## opendxa.tests Module

Comprehensive test coverage for the OpenDXA framework.

## Test Organization

- **agent/**: Agent system tests
  - Agent configuration

- **execution/**: Execution system tests
  - Workflow implementation
  - Factory patterns

- **integration/**: Cross-component tests
  - Default strategies
  - Workflow integration

## Test Categories

The test suite is organized into two main categories to optimize CI performance:

### Fast Tests (CI)
- **Purpose**: Quick regression testing for CI/CD pipelines
- **Characteristics**: Unit tests, simple integration tests, fast execution
- **Runtime**: ~55 seconds
- **Count**: ~486 tests
- **Usage**: Default for CI, local development

### Deep Tests (Local)
- **Purpose**: Comprehensive testing for local development
- **Characteristics**: Large test files (>300 lines), integration tests, comprehensive scenarios
- **Runtime**: ~23 seconds
- **Count**: ~79 tests
- **Usage**: Local development, thorough validation

## Running Tests

### Default (Fast Tests Only)
```bash
# Run fast tests (excludes deep and live tests)
pytest

# Explicit fast tests only
pytest -m "not live and not deep"
```

### All Tests (Local Development)
```bash
# Run all tests except live tests
pytest -m "not live"

# Run only deep tests
pytest -m "deep"

# Run all tests including live tests (requires external services)
pytest -m ""
```

### Specific Test Categories
```bash
# Run specific module
pytest tests/execution/

# Run specific test file
pytest tests/execution/test_pipeline.py

# Run specific test case
pytest tests/execution/test_pipeline.py::TestPipeline::test_placeholder

# Run with coverage
pytest --cov=opendxa

# Run with verbose output
pytest -v
```

## Test Markers

- `fast`: Quick regression tests suitable for CI
- `deep`: Comprehensive/integration tests for local development
- `live`: Tests requiring external services (LLM, APIs)
- `unit`: Pure unit tests
- `na_file`: Tests that execute .na files

## CI/CD Integration

OpenDXA uses a parallelized testing strategy to optimize CI/CD performance:
- **Parallel CI Runtime**: ~6-8 minutes (all fast tests across 6 jobs)
- **Sequential CI Runtime**: ~15-20 minutes (single job)
- **Full Suite**: ~78 seconds (all tests including deep)
- **Deep Tests**: ~23 seconds (comprehensive tests)

For detailed information about the parallel testing strategy, see [CI/CD Testing Strategy](../docs/for-contributors/development/ci-cd-testing.md).

## Managing Test Categories

Use the categorization script to analyze and update test categories:

```bash
# Analyze current test categorization
python scripts/categorize_tests.py --dry-run

# Apply suggested categorizations
python scripts/categorize_tests.py --apply
```

The script automatically identifies tests that should be marked as "deep" based on:
- File size (>300 lines)
- Class names containing: integration, comprehensive, advanced, scenario, etc.
- Test method names suggesting complex scenarios
- Files with many test methods (>15 per class)

## Writing Tests

1. Follow existing patterns in similar test files
2. Use fixtures for common setup
3. Test both success and error cases
4. Include docstrings explaining test purpose
5. Mark comprehensive tests with `@pytest.mark.deep`
6. Keep fast tests focused and lightweight

### Example Test Structure

```python
import pytest
from opendxa.common.exceptions import SandboxError

class TestBasicFunctionality:
    """Fast regression tests for basic functionality."""
    
    def test_simple_case(self):
        """Test simple case that should run quickly."""
        # Fast, focused test
        pass

@pytest.mark.deep
class TestComprehensiveFunctionality:
    """Comprehensive tests for complex scenarios."""
    
    def test_integration_scenario(self):
        """Test complex integration scenario."""
        # More comprehensive test
        pass
```

See individual test files for examples.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
