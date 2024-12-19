<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA - Domain-Expert Agent Framework

DXA is a framework for building and deploying intelligent agents powered by Large Language Models (LLMs). These agents combine cognitive abilities, domain expertise, and external resources to solve complex problems.

## Documentation Map

The DXA framework documentation is organized by component:

### Framework Core

- [Framework Overview](dxa/README.md) - `dxa` - System architecture and design
- [Common Utilities](dxa/common/README.md) - `dxa.common` - Shared functionality and tools

### Components

The DXA agent framework is built around a composable agent architecture:

- An `Agent` (via `dxa.agent`) is the central entity that:
  - Has `Capabilities` (via `dxa.core.capability`) like memory, learning, and expertise
  - Uses `Reasoning` (via `dxa.core.reasoning`) for decision-making and planning
  - Accesses `Resources` (via `dxa.core.resource`) for external tools and services, including domain experts
  - Interacts through `I/O` (via `dxa.core.io`) with its environment

These components are designed to be modular and extensible, allowing agents to be configured with different combinations of capabilities, reasoning patterns, and resources to suit specific needs.

Component documentation:

- [Agent System](dxa/agent/README.md) - `dxa.agent` - Agent implementation and runtime
- [Reasoning System](dxa/core/reasoning/README.md) - `dxa.core.reasoning` - Decision-making patterns
- [Resource System](dxa/core/resource/README.md) - `dxa.core.resource` - External tool integration
- [I/O System](dxa/core/io/README.md) - `dxa.core.io` - Environment interaction
- [Capability System](dxa/core/capability/README.md) - `dxa.core.capability` - Agent abilities

### Development

- [Examples](examples/README.md) - `examples` - Implementation examples and patterns
- [Tests](tests/README.md) - `tests` - Test suite and coverage
- [API Documentation](docs/README.md) - `docs` - API reference and guides

Each component's README provides:

- Detailed architecture
- Usage examples
- Interface documentation
- Best practices

## Quick Start

1. Prerequisites:
   - Python 3.x
   - bash shell (Unix) or Git Bash (Windows)

2. Installation:

   ```bash
   git clone <repository-url>
   cd dxa-prototype
   bash setup_env.sh
   source venv/bin/activate  # Windows: source venv/Scripts/activate
   ```

3. Basic Usage:

   ```python
   from dxa import get_agent_factory

   # Quick start with factory

   factory = get_agent_factory()
   agent = factory.create_quick("assistant")
   result = await agent.run("Help with this task")
   ```

Or use templates for common patterns

   ```python
   agent = factory.create_from_template("researcher", "research_assistant")
   result = await agent.run("Research quantum computing")
   ```

Full configuration available when needed

   ```python
   agent = Agent("assistant")\
      .with_reasoning("cot")\
      .with_resources({"llm": LLMResource(model="gpt-4")})
   ```

## Project Structure

```text
dxa/                    # Project root
├── dxa/                # Main package
│   ├── agent/          # Agent implementation
│   └── core/           # Core components
│       ├── io/         # I/O handlers
│       ├── reasoning/  # Reasoning patterns
│       └── resource/   # External resources
│
├── examples/           # Usage examples
│   ├── basic/          # Basic usage examples
│   └── advanced/       # Advanced patterns
│
├── tests/              # Test suite
│   ├── agent/          # Agent tests
│   └── core/           # Core component tests
│       ├── io/         # I/O handlers
│       ├── reasoning/  # Reasoning patterns
│       └── resource/   # External resources
│
└── docs/               # Documentation
    ├── api/            # API reference
    └── guides/         # User guides
```

## Contributing

DXA is proprietary software developed by Aitomatic, Inc. Contributions are limited to authorized Aitomatic employees and contractors. If you're an authorized contributor:

1. Please ensure you have signed the necessary Confidentiality and IP agreements
2. Follow the internal development guidelines
3. Submit your changes through the company's approved development workflow
4. Contact the project maintainers for access to the internal Contributing Guide

For external users or organizations interested in collaborating with Aitomatic on DXA development, please contact our business development team.

## License

This software is proprietary and confidential. Copyright © 2024 Aitomatic, Inc. All rights reserved.

Unauthorized copying, transfer, or reproduction of this software, via any medium, is strictly prohibited. This software is protected by copyright law and international treaties.
