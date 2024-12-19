<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Core System

## dxa.core Module

The DXA Core system provides the foundational building blocks for creating intelligent agents. It implements a layered architecture that separates strategic planning from tactical execution, while providing essential capabilities and resources. This separation of concerns allows agents to maintain high-level objectives while efficiently executing individual steps and adapting to new information.

## System Overview

At its heart, DXA Core implements a cognitive architecture inspired by human decision-making:

- **Planning** handles strategic decisions and goal management
- **Reasoning** implements different thinking patterns for execution
- **Capabilities** provide cognitive abilities like memory and expertise
- **Resources** manage concrete tools and services
- **IO** handles all external interactions

These components work together to create agents that can understand objectives, form plans, execute actions, learn from experience, and interact with their environment. The system is designed to make simple tasks easy while enabling complex behaviors through composition.

The system is built around a core LLM that powers both planning and reasoning layers:

- Planning and Reasoning share the agent's LLM
- Capabilities and Resources can access it when needed
- IO remains LLM-independent for flexibility

## Core Modules

### [Planning](planning/README.md)

Strategic layer that manages objectives and generates plans. Implements different planning patterns from simple direct planning to complex hierarchical and dynamic planning strategies.

### [Reasoning](reasoning/README.md)

Tactical layer that executes plans using various cognitive patterns. Includes direct reasoning, chain-of-thought, OODA loops, and DANA (Domain-Aware Neural-Symbolic Analysis).

### [Capability](capability/README.md)

Core cognitive abilities like memory and domain expertise. Built on top of resources but provides higher-level, cognitively-aligned interfaces.

### [Resource](resource/README.md)

Concrete tools and services that agents can use, from LLM interactions to human-in-the-loop operations. Provides the foundation for capabilities.

### [IO](io/README.md)

Input/Output systems for all external interactions. Handles everything from simple console I/O to complex multi-modal interactions.

## Integration

These core modules are primarily used by the [Agent System](../agent/README.md), which provides the main interface for creating and using DXA agents. The agent system composes these components to create coherent, capable agents:

```python
agent = Agent("assistant")\
    .with_planning("hierarchical")\       # Strategic layer
    .with_reasoning("cot")\               # Tactical layer
    .with_capability("memory")\           # Cognitive abilities
    .with_resource("llm")\                # Concrete tools
    .with_io("interactive")               # External interaction
```

## Directory Structure

```python
dxa/core/
├── planning/           # Strategic planning
├── reasoning/          # Tactical execution
├── capability/         # Cognitive abilities
├── resource/           # Tools and services
└── io/                 # External interaction
```

## Development

When developing new components:

1. Choose the appropriate layer (planning, reasoning, etc.)
2. Follow the established patterns in that module
3. Maintain separation of concerns
4. Consider integration points
5. Document thoroughly

## Testing

Each module has its own test suite under `tests/core/`. Run tests with:

```bash
pytest tests/core/
```

## See Also

- [Agent Documentation](../agent/README.md) - Main interface for using DXA
- [Examples](../../examples/README.md) - Example agent implementations
- [API Reference](../../docs/api/README.md) - Detailed API documentation

---

<p align="center">
Copyright © 2024 Aitomatic, Inc. All rights reserved.
</p>

<p align="center">
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
