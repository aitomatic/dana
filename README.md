<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# OpenDXA - Domain-Expert Agent Framework

> A comprehensive framework for easily coding and deploying smart, multi-agent systems with domain expertise, powered by DANA, a Pythonic agentic programming language and secure sandboxed runtime.

## TL;DR

```bash
# Clone and setup
% git clone https://github.com/aitomatic/opendxa.git
% cd opendxa
% source ./SOURCE_ME.sh

# Start the DANA shell, just like Python
% bin/dana
```

That's it! Oh, be sure to add an LLM API key to your environment:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `AITOMATIC_API_KEY`

or put the folllwing in your `.env` file, and `OpenDXA` will pick it up automatically.

```bash
OPENAI_API_KEY=your_api_key
ANTHROPIC_API_KEY=your_api_key
AITOMATIC_API_KEY=your_api_key
```

If you start up a fresh terminal session, you'll need to do this:

```bash
% source bin/source_env.sh
```

## Example DANA Code

```python
# Simple stock research agent in DANA
def stock_research(ticker, question):
    while confidence < 0.8:
      answer = ask("danke.stock.research", ticker=ticker, question=question)

    return answer
```


## Core Components

OpenDXA consists of three primary components:

1. **OpenDXA Framework**
   - Orchestrates DANA and DANKE components
   - Manages agent lifecycle and coordination
   - [Framework Documentation](docs/README.md)

2. **DANA (Domain-Aware NeuroSymbolic Architecture)**
   - A universal program format and runtime for agent reasoning
   - [DANA Documentation](docs/dana/dana.md)
   - [DANA Manifesto](docs/dana/manifesto.md) - Vision and philosophy

3. **DANKE (Domain-Aware NeuroSymbolic Knowledge Engine)**
   - Knowledge management implementing the CORRAL methodology: Collect, Organize, Retrieve, Reason, Act, Learn
   - [DANKE Documentation](docs/danke/README.md)


## Documentation

### Getting Started
- [Installation Guide](docs/getting-started/installation.md)
- [First Agent Tutorial](docs/getting-started/first-agent.md)
- [Examples](examples/README.md)

### Core Concepts
- [Architecture Overview](docs/core-concepts/architecture.md)
- [Agents](docs/core-concepts/agent.md)
- [Capabilities](docs/core-concepts/capabilities.md)
- [Resources](docs/core-concepts/resources.md)
- [Mixins](docs/core-concepts/mixins.md)
- [State Management](docs/core-concepts/state-management.md)

### DANA Language
- [DANA Overview](docs/dana/dana.md)
- [Language Reference](docs/dana/language.md)
- [Sandbox Environment](docs/dana/sandbox.md)

### Advanced Topics
- [Development Roadmap](docs/ROADMAP.md)
- [Key Differentiators](docs/key-differentiators/README.md)
- [Requirements](docs/requirements/README.md)

## Example: DANA Program

```python
# Simple Customer Support Agent in DANA
if public.customer.query.type == "password_reset":
    # Search knowledge-base engine (KE)
    private.ke_result = use("danke.support.password_reset")

    # If no clear answer, escalate
    if private.ke_result.confidence < 0.8:
        private.analysis = reason("Should this be escalated to human support?", 
                                context=[public.customer, private.ke_result])
        if private.analysis == "yes":
            use("tools.support.escalate")
            system.status = "escalated"
            return

    system.response = private.ke_result.answer
```

## Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

This will ensure code quality checks run automatically on commit, including:
- Code formatting with Ruff
- Linting with Ruff (including undefined attributes/methods)
- Basic file checks (trailing whitespace, merge conflicts, etc.)

## Key Features

- **Domain Expertise Integration** - Embed expert knowledge into agent behavior
- **Structured Reasoning** - DANA programs provide clear, auditable execution
- **Declarative + Imperative Architecture** - Clear separation of knowledge and action
- **Extensive Capabilities** - Memory, knowledge management, planning, and more
- **Protocol Federation (NLIP)** - Interoperability between agent standards

## Why OpenDXA?

OpenDXA stands out by enabling truly expert agents grounded in specific domain knowledge:

- **Leverage Existing Knowledge** - Tap into your company's documents, databases, and expertise
- **Embed Deep Domain Expertise** - Create reliable agents that understand your specialized processes
- **Adaptive Knowledge Management** - Manage the full lifecycle as your knowledge evolves
- **True Interoperability** - Seamlessly connect agents and systems based on different standards

## AST Validation

The AST validation system helps ensure that the parser properly transforms Lark parse trees into DANA AST nodes without leaving any Lark Tree nodes in the AST. This is important for maintaining a clean, well-defined AST structure.

Key validation tools:

- **`validate_ast`**: A utility function to check if an AST contains any Lark Tree nodes
- **`StrictDanaParser`**: A variant of the parser that enforces strict AST validation
- **`safe_strip_lark_trees`**: A recursive validation function that detects Tree nodes while avoiding infinite recursion

These tools help maintain a clean separation between the parser's internal implementation and the AST, making it easier to work with the AST in downstream code.

## License

OpenDXA is released under the [MIT License](LICENSE.md).

## Support

For questions or support, please open an issue on the [GitHub repository](https://github.com/aitomatic/opendxa/issues).

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the <a href="LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>