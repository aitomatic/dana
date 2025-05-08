# OpenDXA (Domain-Expert Agent) Framework

> **Note:** This codebase is actively evolving. Some documentation may not reflect the latest changes.

## DANA Language

The OpenDXA framework includes DANA (Domain-Aware NeuroSymbolic Architecture), a domain-specific language for agent reasoning.

### DANA Parser

The DANA language parser uses a grammar-based implementation with the Lark parsing library. This provides:

- Robust error reporting with detailed error messages
- Extensibility through the formal grammar definition
- Better support for language evolution and new features

To use the parser, you need to install the Lark parser:
```bash
pip install lark-parser
```

### Environment Variables

The DANA language parser supports the following environment variables:

| Variable | Description | Default | Values |
|----------|-------------|---------|--------|
| `DANA_TYPE_CHECK` | Enables or disables type checking during parsing | On | `0`, `1`, `true`, `false`, `yes`, `no`, `y`, `n` |

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
pytest tests/execution/planning/test_plan_factory.py::test_specific_case
```

## Key Features

- **State Management**: Explicit memory spaces (`agent`, `world`, `temp`, `execution`)
- **Grammar-based Parser**: Robust parsing using the Lark library

### DANA Parser

The DANA parser uses the Lark parsing library to provide robust parsing capabilities. The parser is configured through environment variables:

```bash
# Disable type checking
export DANA_TYPE_CHECK=0

# Run your code
python your_script.py
```

You can also control type checking programmatically:

```python
from opendxa.dana.language import parse

# Parse without type checking
result = parse(code, type_check=False)
```

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
