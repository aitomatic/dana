# OpenDXA (Domain-Expert Agent) Framework

> **Note:** This codebase is actively evolving. Some documentation may not reflect the latest changes.

## Setup and Installation

```bash
# Initial setup (creates virtual environment and installs dependencies)
source ./SOURCE_ME.sh

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
- DANA language for implementing agent reasoning and knowledge representation

## DANA Language

The Domain-Aware NeuroSymbolic Architecture (DANA) is a key component of OpenDXA:

- **Language Features**: Strongly typed DSL with variables, conditionals, loops, and functions
- **Runtime System**: Scoped execution context with standardized memory spaces
- **LLM Integration**: Via `reason()` statements and transcoding capabilities
- **File Extensions**: Use `.na` extension for DANA files
- **State Management**: Explicit memory spaces (`agent`, `world`, `temp`, `execution`)

## Directory Structure

```
opendxa/               # Main package
├── agent/             # Agent implementation
│   ├── capability/    # Agent capabilities (memory, expertise)
│   ├── resource/      # External resource integration
├── common/            # Shared utilities
│   ├── capability/    # Base capability system
│   ├── resource/      # Base resource system
│   └── utils/         # Utility functions
├── dana/              # DANA language implementation
│   ├── io/            # DANA I/O handlers
│   ├── language/      # DANA language parser and types
│   ├── runtime/       # DANA runtime and interpreter
│   └── transcoder/    # DANA transcoding capabilities
├── danke/             # DANA Knowledge Engine
└── __init__.py        # Package initialization
```

## Documentation Resources

- **docs/**: Comprehensive documentation by topic
- **examples/**: Usage examples and tutorials
- **LLMS.md**: AI coder guide with detailed project information
- **README.md**: Project overview and quick start guide

## Common Tasks

### Working with DANA

```python
from dana import run, compile_nl
from dana.runtime.context import RuntimeContext

# Create runtime context
ctx = RuntimeContext(agent={}, world={}, temp={})

# Run DANA code
dana_code = """
temp.result = reason("What is the meaning of life?")
log.info("The meaning of life is {temp.result}")
"""
run(dana_code, ctx)

# Compile natural language to DANA
nl_prompt = "If temperature is over 100, alert operations"
dana_code = compile_nl(nl_prompt)
```

### Creating a Custom Agent

```python
from opendxa.agent.agent import Agent
from opendxa.agent.agent_config import AgentConfig

# Create agent configuration
config = AgentConfig(
    id="my_agent",
    name="My Custom Agent",
    description="A custom agent for specific tasks"
)

# Initialize agent
agent = Agent(config)

# Add capabilities and resources
agent.add_capability(...)
agent.add_resource(...)
```