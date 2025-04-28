<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# OpenDXA - Domain-Expert Agent Framework Documentation

This document provides a detailed overview of the OpenDXA framework's architecture, core concepts, features, and design philosophy. For a quick start and installation instructions, please refer to the main [README.md](../../README.md).

## Core Concepts

OpenDXA is built around two fundamental aspects:

1. **Declarative Aspect**
   - Defines what the agent knows
   - Manages knowledge and resources
   - Handles domain expertise
   - Provides structured access to knowledge

2. **Imperative Aspect**
   - Implements planning and reasoning
   - Executes tasks using available knowledge
   - Manages state and context
   - Coordinates multi-agent interactions

For detailed architecture information, see [Architecture Documentation](details/architecture.md).

## Key Features

- **Domain Expertise Integration** - Embed expert knowledge into agent behavior
- **Adaptive Knowledge Management** - Support for knowledge lifecycle including evolution and versioning
- **Declarative + Imperative Architecture** - Clear separation of knowledge and action for robust design
- **Agent Learning & Adaptability** - Mechanisms for agents to improve over time
- **Protocol Federation (NLIP)** - Interoperability between different agent communication standards
- **Progressive Complexity** - Start simple, scale to complex tasks
- **Composable Architecture** - Mix and match capabilities as needed
- **Built-in Best Practices** - Pre-configured templates for common patterns
- **Full Customization** - Complete control when needed

## Key Differentiators

### Business/Strategic Differentiators
1. **Declarative-Imperative Architecture**: Clear separation between what agents know and how they act
2. **Knowledge Management**: Built-in support for structured knowledge management and evolution
3. **Domain Expertise Integration**: Specifically designed to embed domain expertise into agents

### Engineering Approaches
1. **Progressive Complexity**: Start with simple implementations and progressively add complexity
2. **Composable Architecture**: Mix and match components as needed for highly customized agents
3. **Clean Separation of Concerns**: Maintain clear boundaries between description and execution layers

For detailed framework comparisons, see [Framework Comparison](details/comparison.md).

## Documentation Map

- **Architecture**
  - [Architecture Overview](details/architecture.md) - Core concepts and design
  - [Interaction Patterns](details/interaction_patterns.md) - Agent communication and workflows
  - [Framework Comparison](details/comparison.md) - Comparison with other frameworks

- **Agent System**
  - [Agent Core](../opendxa/agent/README.md) - Factory and runtime
  - [Capabilities](../opendxa/agent/capability/README.md) - Cognitive abilities
  - [Resources](../opendxa/agent/resource/README.md) - Tools and services
  - [IO System](../opendxa/agent/io/README.md) - Environmental interaction
  - [State System](../opendxa/agent/state/README.md) - Execution state management

- **Execution System**
  - [Workflow](../opendxa/execution/workflow/README.md) - Process definition
  - [Planning](../opendxa/execution/planning/README.md) - Strategic planning
  - [Reasoning](../opendxa/execution/reasoning/README.md) - Tactical execution
  - [Pipeline](../opendxa/execution/pipeline/README.md) - Execution orchestration

- **Utilities**
  - [Logging](details/logging.md) - Logging configuration and usage

- [Examples](../../examples/README.md) - Usage patterns and tutorials

## Contributing

DXA is proprietary software developed by Aitomatic, Inc. Contributions are limited to authorized Aitomatic employees and contractors. If you're an authorized contributor:

1. Please ensure you have signed the necessary Confidentiality and IP agreements
2. Follow the internal development guidelines
3. Submit your changes through the company's approved development workflow
4. Contact the project maintainers for access to the Contributing Guide

For external users or organizations interested in collaborating with Aitomatic on DXA development, please contact our business development team.

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE.md) file for details.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
