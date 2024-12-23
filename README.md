<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA - Domain-Expert Agent Framework

## Top-level module

DXA is a framework for building and deploying intelligent agents powered by Large Language Models (LLMs). At its core are Workflows that define what agents can do - from simple Q&A to complex research patterns. These agents combine workflows with cognitive abilities, domain expertise, and external resources to solve complex problems.

Through a composable architecture, DXA enables both rapid deployment of standard workflows and full customization when needed, guided by the principle that simple things should be easy and complex things should be possible.

## Documentation Map

The DXA framework documentation is organized by component:

### Framework Core

- [Framework Overview](dxa/README.md) - `dxa` - System architecture and design
- [Common Utilities](dxa/common/README.md) - `dxa.common` - Shared functionality and tools

### Components

The DXA agent framework is built around Workflows executed by composable agents:

- A `Workflow` (via `dxa.core.workflow`) defines what agents can do
- An `Agent` (via `dxa.agent`) executes workflows by:
  - Using `Reasoning` (via `dxa.core.reasoning`) for decision-making
  - Accessing `Resources` (via `dxa.core.resource`) for external tools
  - Interacting through `I/O` (via `dxa.core.io`) with its environment
  - Leveraging `Capabilities` (via `dxa.core.capability`) like memory and expertise

These components are designed to be modular and extensible, allowing agents to be configured with different combinations of capabilities, reasoning patterns, and resources to suit specific needs.

Component documentation:

- [Workflow System](dxa/core/workflow/README.md) - `dxa.core.workflow` - Workflow patterns
- [Agent System](dxa/agent/README.md) - `dxa.agent` - Agent implementation and runtime
- [Agent Capabilities](dxa/core/capability/README.md) - `dxa.core.capability` - Agent abilities
- [Planning System](dxa/core/planning/README.md) - `dxa.core.planning` - Planner
- [Reasoning System](dxa/core/reasoning/README.md) - `dxa.core.reasoning` - Reasoner
- [Resource System](dxa/core/resource/README.md) - `dxa.core.resource` - External tool integration
- [I/O System](dxa/core/io/README.md) - `dxa.core.io` - Environment interaction

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
   from dxa.core.agent import Agent
   from dxa.core.workflow import create_research_workflow

   # Simple Q&A
   answer = Agent().ask("What is quantum computing?")

   # Using research workflow
   workflow = create_research_workflow()
   agent = Agent(resources={"llm": LLMResource()})
   result = agent.execute(workflow)

   # Custom workflow with resources
   agent = Agent(resources={
       "llm": LLMResource(model="gpt-4"),
       "search": SearchResource()
   })
   result = agent.execute(workflow)

   # Template with customization
   agent = AgentFactory.from_template("researcher")\
      .with_reasoning("cot")\
      .with_resources({"llm": LLMResource(model="gpt-4")})
   result = await agent.run("Research quantum computing")

   # Quick start with full customization 
   agent = AgentFactory.quick("assistant")\
      .with_reasoning("cot")\
      .with_resources({"llm": LLMResource(model="gpt-4")})
   result = await agent.run("Help with this task")
   ```

## Strategic Framework Selection Matrix

DXA provides distinct advantages in several key areas when compared to other agent frameworks:

| Use Case | DXA | LangChain | AutoGPT | BabyAGI |
|----------|-----|-----------|----------|----------|
| **Quick Start** | ✨ Template-based initialization | Direct chain construction | Command interface | Simple task queue |
| **Simple Tasks** | ✨ Pre-configured templates | Chain composition | Command sequences | Task scheduling |
| **Complex Tasks** | ✨ Full cognitive architecture | Multiple chains | Command sequences | Task recursion |
| **Domain Expertise** | ✨ Built-in expertise system | Tool integration | Command-based tools | Task-based tools |
| **Autonomous Operation** | ✨ Structured autonomy | Chain automation | Free-form commands | Task loops |
| **Growth Path** | ✨ Seamless capability expansion | Chain rebuilding | New commands | New tasks |

✨ = Optimal choice for category

### Framework Selection Guide

| Need | Best Choice | Why |
|------|-------------|-----|
| Fast Start | DXA/LangChain | Equivalent simplicity with better growth |
| Simple Tasks | DXA/LangChain | Standard patterns with full power available |
| Complex Systems | DXA | Superior architecture and capabilities |
| Expert Systems | DXA | Native expertise and knowledge integration |
| Autonomous Agents | DXA/AutoGPT | Structured autonomy with better control |

### Implementation Complexity

| Framework | Initial | Growth | Maintenance |
|-----------|---------|--------|-------------|
| DXA | Low | Linear | Low |
| LangChain | Low | Step Function | Medium |
| AutoGPT | Low | Limited | High |
| BabyAGI | Low | Limited | Medium |

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
