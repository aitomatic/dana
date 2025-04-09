# OpenDXA (Domain-Expert Agent) Framework

> **Note:** This codebase is actively evolving. Some documentation may not reflect the latest changes.

## Setup and Installation

```bash
# Initial setup (creates virtual environment and installs dependencies)
source ./RUN_ME.sh

# Subsequent activations after initial setup
source ./VENV.sh
```

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
pytest --cov=opendxa

# Format code
black opendxa/

# Type checking
mypy opendxa/

# Linting
ruff check opendxa/
```

## Dependencies

- **Core LLM Libraries**: OpenAI, Anthropic, Azure, Google, Groq, HuggingFace, Ollama
- **Additional Libraries**: matplotlib, pandas, pytest, PyYAML, seaborn, structlog, websockets
- **MCP Support**: Model Context Protocol for standardized interface to external resources

## Code Style Guidelines

- **Documentation**: Use docstrings with triple double quotes `"""` for classes and functions
- **Imports**: Group imports (stdlib → third-party → local), use absolute imports
- **Types**: Use type hints throughout; import from `typing` module
- **Classes**: PascalCase for classes; inherit from `Loggable` for standardized logging
- **Variables**: snake_case for methods/variables, UPPER_CASE for constants
- **Error Handling**: Use custom exceptions from `opendxa.common.exceptions`
- **Testing**: Test classes named `Test{ClassName}`, methods as `test_{descriptive_name}`
- **Logging**: Use the `Loggable` base class for consistent logging patterns

## Project Architecture

- 3-layer execution framework: Workflows → Plans → Reasoning
- Modular resource design with agent capabilities and resources
- Strong typing with factory pattern for component creation
- Built-in support for Model Context Protocol (MCP) integration