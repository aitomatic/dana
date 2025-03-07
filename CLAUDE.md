# DXA (Domain-Expert Agent) Framework

## Build/Test/Lint Commands

```bash
# Install dependencies and develop locally
pip install -e .

# Run all tests
pytest

# Run a specific test file
pytest tests/execution/planning/test_plan_factory.py

# Run a specific test case
pytest tests/execution/planning/test_plan_factory.py::TestPlanFactory::test_create_plan

# Run tests with coverage
pytest --cov=dxa

# Format code
black dxa/

# Type checking
mypy dxa/
```

## Code Style Guidelines

- **Documentation**: Use docstrings with triple double quotes `"""` for classes and functions
- **Imports**: Group imports (stdlib → third-party → local), use absolute imports
- **Types**: Use type hints throughout; import from `typing` module
- **Classes**: PascalCase for classes; inherit from `Loggable` for standardized logging
- **Variables**: snake_case for methods/variables, UPPER_CASE for constants
- **Error Handling**: Use custom exceptions from `dxa.common.exceptions`
- **Testing**: Test classes named `Test{ClassName}`, methods as `test_{descriptive_name}`
- **Logging**: Use the `Loggable` base class for consistent logging patterns

## Project Architecture

- 3-layer execution framework: Workflows → Plans → Reasoning
- Modular resource design with agent capabilities and resources
- Strong typing with factory pattern for component creation