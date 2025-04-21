<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>
<!-- markdownlint-enable MD033 -->

# OpenDXA Documentation

This directory contains the official documentation for OpenDXA (Domain-Expert Agent), an intelligent agent architecture designed for complex domain-specific tasks.

## Architecture Overview

OpenDXA is built on a two-layer architecture that breaks down high-level objectives into executable actions through a What-How paradigm:

1. **Planning Layer (WHAT)**
   - Decomposes strategic plans into tactical actions
   - Handles task decomposition and sequencing
   - Manages high-level decision making

2. **Reasoning Layer (HOW)**
   - Executes actions using standardized reasoning patterns
   - Handles tactical decision making
   - Manages resource allocation and execution

## Documentation Structure

### Getting Started
- [Introduction to OpenDXA](examples/01_getting_started/01_introduction_to_dxa.ipynb)
- [Simple Plans](examples/01_getting_started/02_simple_plans.ipynb)
- [Agent Configuration](examples/01_getting_started/03_agent_configuration.ipynb)

### Core Concepts
- [Planning Layer](examples/02_core_concepts/01_planning_layer.ipynb)
- [Reasoning Layer](examples/02_core_concepts/02_reasoning_layer.ipynb)
- [Execution Context](examples/02_core_concepts/03_execution_context.ipynb)
- [Capabilities](examples/02_core_concepts/04_capabilities.ipynb)
- [Resources](examples/02_core_concepts/05_resources.ipynb)
- [Tool Calling](examples/02_core_concepts/06_tool_calling.ipynb)
- [MCP Resource](examples/02_core_concepts/07_mcp_resource.ipynb)
- [Smart Resource Selection](examples/02_core_concepts/08_smart_resource_selection.ipynb)

### Advanced Topics
- [Custom Agents](examples/03_advanced_topics/01_custom_agents.ipynb)
- [Advanced Planning](examples/03_advanced_topics/02_advanced_planning.ipynb)
- [Advanced Reasoning](examples/03_advanced_topics/03_advanced_reasoning.ipynb)

### Real-World Applications
- [Semiconductor Manufacturing](examples/04_real_world_applications/01_semiconductor_manufacturing.ipynb)
- [General Manufacturing](examples/04_real_world_applications/02_general_manufacturing.ipynb)
- [Financial Applications](examples/04_real_world_applications/03_financial_applications.ipynb)

## Key Components

### Agent System
- **Agent Factory & Runtime**: Creates and manages agent instances
- **Capabilities**: Cognitive abilities for task execution
- **Resources**: Tools and services used by agents
- **IO System**: Handles environmental interaction
- **State System**: Manages execution state

### Execution System
- **Planning**: Strategic decomposition
- **Reasoning**: Tactical execution
- **Pipeline**: Execution flow management

## Requirements

- Python 3.8 or higher
- OpenDXA package installed
- Understanding of basic AI/ML concepts
- Familiarity with Python programming

## Contributing

We welcome contributions to the documentation! Please follow these guidelines:

1. Ensure all examples are up-to-date with the latest OpenDXA version
2. Include clear explanations and comments in code examples
3. Follow the existing documentation structure
4. Test all examples before submitting
5. Update the README.md if adding new sections

## License

Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.

---

<p align="center">
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
