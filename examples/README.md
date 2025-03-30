<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Examples

This directory contains examples demonstrating different aspects of the DXA framework.

## Directory Structure

```
examples/
├── getting_started/      # Basic examples for new users
├── core_concepts/        # Examples of core DXA features
└── advanced/            # Complex patterns and integrations
```

## Getting Started

The `getting_started/` directory contains basic examples that demonstrate fundamental DXA concepts:

1. `01_hello_dxa.py` - Basic agent creation and usage
2. `02_simple_workflow.py` - Creating and running a basic workflow
3. `03_qa_approaches.py` - Different question-answering patterns

## Core Concepts

The `core_concepts/` directory contains examples that demonstrate core DXA features:

1. `01_workflow_planning.py` - Workflow and planning layer interaction
2. `02_reasoning_layer.py` - Understanding the reasoning layer
3. `03_execution_context.py` - Managing execution context and resources

## Advanced

The `advanced/` directory contains complex examples and patterns:

1. `01_custom_executors.py` - Creating custom executors
2. `02_complex_workflows.py` - Complex workflow patterns
3. `03_integration.py` - Integration with external systems

## Prerequisites

Before running any examples:

1. Install DXA and its dependencies:
   ```bash
   pip install -e .
   ```

2. Set up your environment variables:
   ```bash
   export OPENAI_API_KEY=your_api_key
   ```

3. (Optional) Configure logging:
   ```python
   from dxa.common.utils.logging import DXA_LOGGER
   DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG)
   ```

## Running Examples

Each example can be run directly with Python:

```bash
python examples/getting_started/01_hello_dxa.py
```

## Learning Path

1. Start with the getting_started examples to understand basic concepts
2. Move to core_concepts to learn about DXA's architecture
3. Explore advanced examples for complex use cases

## Troubleshooting

Common issues and solutions:

1. **LLM Connection Issues**
   - Verify your API key is set correctly
   - Check your network connection
   - Ensure you have sufficient API credits

2. **Workflow Execution Errors**
   - Check the workflow structure is valid
   - Verify all required nodes are present
   - Ensure proper edge connections

3. **Context Management**
   - Verify execution context is properly initialized
   - Check resource availability
   - Ensure proper cleanup

## Contributing

When adding new examples:

1. Follow the existing directory structure
2. Include clear documentation
3. Add proper error handling
4. Include prerequisites and dependencies
5. Add cross-references to related examples
