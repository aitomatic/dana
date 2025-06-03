[Project Overview](../README.md) | [Main Documentation](../docs/README.md)

# OpenDXA Examples

This directory contains examples demonstrating different aspects of the OpenDXA framework.

## Directory Structure

```text
examples/
├── getting_started/      # Basic examples for new users
├── core_concepts/        # Examples of core DXA features
├── advanced_topics/      # Complex patterns and integrations
└── real_world_applications/  # Real-world use cases
```

## Getting Started

The `getting_started/` directory contains basic examples that demonstrate fundamental OpenDXA concepts:

1. `01_introduction_to_dxa.ipynb` - Introduction to OpenDXA
2. `02_simple_plans.ipynb` - Creating and running basic plans
3. `03_agent_configuration.ipynb` - Configuring agents with different settings

## Core Concepts

The `core_concepts/` directory contains examples that demonstrate core OpenDXA features:

1. `01_planning_layer.ipynb` - Understanding the planning layer
2. `02_reasoning_layer.ipynb` - Understanding the reasoning layer
3. `03_execution_context.ipynb` - Managing execution context and resources
4. `04_capabilities.ipynb` - Working with agent capabilities
5. `05_resources.ipynb` - Managing and using resources
6. `06_tool_calling.ipynb` - Making resource methods callable
7. `07_mcp_resource.ipynb` - Working with MCP resources
8. `08_smart_resource_selection.ipynb` - Smart resource selection strategies

## Advanced Topics

The `advanced_topics/` directory contains complex examples and patterns:

1. `01_custom_agents.ipynb` - Creating custom agents
2. `02_advanced_planning.ipynb` - Advanced planning strategies
3. `03_advanced_reasoning.ipynb` - Advanced reasoning strategies

## Real-World Applications

The `real_world_applications/` directory contains examples of OpenDXA in real-world scenarios:

1. `01_semiconductor_manufacturing.ipynb` - Semiconductor manufacturing applications
2. `02_general_manufacturing.ipynb` - General manufacturing applications
3. `03_financial_applications.ipynb` - Financial applications

## Prerequisites

Before running any examples:

1. Install OpenDXA and its dependencies:

   ```bash
   pip install -e .
   ```

2. Set up your environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. Configure logging (optional):

   ```python
   from opendxa.common import DXA_LOGGER
   DXA_LOGGER.configure(
       level=DXA_LOGGER.DEBUG,
       console=True,
       log_data=True
   )
   ```

## Running Examples

Each example can be run directly with Python:

```bash
# Run a specific example
python examples/getting_started/01_introduction_to_dxa.py

# Run all examples in a directory
python -m pytest examples/getting_started/
```

## Learning Path

1. Start with the getting_started examples to understand basic concepts
2. Move to core_concepts to learn about DXA's 2-layer architecture
3. Explore advanced_topics for complex patterns
4. Study real_world_applications for practical use cases

## Troubleshooting

Common issues and solutions:

1. **LLM Connection Issues**
   - Verify your API key is set correctly in .env
   - Check your network connection
   - Ensure you have sufficient API credits

2. **Planning Layer Issues**
   - Check the plan structure is valid
   - Verify all required steps are present
   - Ensure proper resource selection
   - Validate planning strategy configuration

3. **Reasoning Layer Issues**
   - Verify reasoning strategy is properly configured
   - Check resource availability
   - Ensure proper execution context
   - Validate reasoning results

4. **Context Management**
   - Verify execution context is properly initialized
   - Check resource availability
   - Ensure proper cleanup
   - Validate resource configuration

## Contributing

When adding new examples:

1. Follow the existing directory structure
2. Include clear documentation
3. Add proper error handling
4. Include prerequisites and dependencies
5. Add cross-references to related examples
6. Update this README with new example information

---
<!-- AI Assistants: documentation markdowns should have this logo at the bottom -->
---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
