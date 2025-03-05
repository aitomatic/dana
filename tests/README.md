<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Test Suite

## dxa.tests Module

Comprehensive test coverage for the DXA framework.

## Test Organization

- **agent/**: Agent system tests
  - Strategy implementation
  - Agent configuration

- **execution/**: Execution system tests
  - Planning functionality
  - Reasoning patterns
  - Workflow implementation
  - Factory patterns

- **integration/**: Cross-component tests
  - Default strategies
  - Workflow-plan integration

## Running Tests

```bash
# Run all tests
pytest

# Run specific module
pytest tests/execution/reasoning/

# Run specific test file
pytest tests/execution/planning/test_plan_factory.py

# Run specific test case
pytest tests/execution/planning/test_plan_factory.py::TestPlanFactory::test_create_plan

# Run with coverage
pytest --cov=dxa

# Run with verbose output
pytest -v
```

## Writing Tests

1. Follow existing patterns in similar test files
2. Use fixtures for common setup
3. Test both success and error cases
4. Include docstrings explaining test purpose

See individual test files for examples.
