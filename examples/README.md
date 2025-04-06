<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# OpenDXA Examples

This directory contains examples demonstrating different aspects of the OpenDXA framework.

## Directory Structure

```text
examples/
├── getting_started/      # Basic examples for new users
├── core_concepts/        # Examples of core DXA features
├── advanced/            # Complex patterns and integrations
├── learning_paths/      # Tutorial examples
├── workflow/           # Workflow-specific examples
└── tutorials/          # Detailed tutorials
```

## Getting Started

The `getting_started/` directory contains basic examples that demonstrate fundamental OpenDXA concepts:

1. `01_hello_dxa.py` - Basic agent creation and usage
2. `02_simple_workflow.py` - Creating and running a basic workflow
3. `03_qa_approaches.py` - Different question-answering patterns

## Core Concepts

The `core_concepts/` directory contains examples that demonstrate core OpenDXA features:

1. `01_workflow_planning.py` - Workflow and planning layer interaction
2. `02_workflow_planning_reasoning.py` - Understanding the three-layer architecture
3. `03_execution_context.py` - Managing execution context and resources

## Advanced

The `advanced/` directory contains complex examples and patterns:

1. `01_custom_executors.py` - Creating custom executors
2. `02_complex_workflows.py` - Complex workflow patterns
3. `03_integration.py` - Integration with external systems

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
python examples/getting_started/01_hello_dxa.py

# Run all examples in a directory
python -m pytest examples/getting_started/
```

## Learning Path

1. Start with the getting_started examples to understand basic concepts
2. Move to core_concepts to learn about DXA's architecture
3. Explore advanced examples for complex use cases
4. Follow learning_paths for structured tutorials

## Troubleshooting

Common issues and solutions:

1. **LLM Connection Issues**
   - Verify your API key is set correctly in .env
   - Check your network connection
   - Ensure you have sufficient API credits

2. **Workflow Execution Errors**
   - Check the workflow structure is valid
   - Verify all required nodes are present
   - Ensure proper edge connections
   - Check execution context setup

3. **Context Management**
   - Verify execution context is properly initialized
   - Check resource availability
   - Ensure proper cleanup
   - Validate LLM resource configuration

## Contributing

When adding new examples:

1. Follow the existing directory structure
2. Include clear documentation
3. Add proper error handling
4. Include prerequisites and dependencies
5. Add cross-references to related examples
6. Update this README with new example information
