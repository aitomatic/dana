<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Examples

This directory contains examples demonstrating the DXA (Distributed eXecution Architecture) framework.

## Directory Structure

- **learning_paths/**: Examples organized by learning progression
  - **01_getting_started/**: Beginner-friendly examples
  - **02_core_concepts/**: Intermediate examples
  - **03_advanced_patterns/**: Advanced examples
  - **04_real_world_applications/**: Domain-specific examples

- **tutorials/**: Step-by-step tutorials for building complete applications
  - **build_qa_agent/**: Building a question-answering agent
  - **temperature_monitoring/**: Building a temperature monitoring system

## Getting Started

Start with these beginner-friendly examples in the recommended order:

- **learning_paths/01_getting_started/00_hello_dxa.py**: Introduction to DXA and basic concepts
- **learning_paths/01_getting_started/01_simple_qa.py**: Creating a simple question-answering agent
- **learning_paths/01_getting_started/02_default_workflow.py**: Creating a basic workflow
- **learning_paths/01_getting_started/03_qa_approaches.py**: Different approaches to question answering
- **learning_paths/01_getting_started/04_logging_example.py**: DXA logging system

## Core Concepts

Once familiar with the basics, explore these intermediate examples:

- **learning_paths/02_core_concepts/01_run_default_workflow.py**: Workflow execution process
- **learning_paths/02_core_concepts/02_simple_plan.py**: Planning layer concepts
- **learning_paths/02_core_concepts/03_simple_reasoning.py**: Reasoning layer concepts
- **learning_paths/02_core_concepts/04_temperature_monitor.py**: Data pipeline example
- **learning_paths/02_core_concepts/05_llm_resource.py**: LLM integration

## Advanced Patterns

For more sophisticated patterns and workflows:

- **learning_paths/03_advanced_patterns/01_prosea_workflow.py**: ProSEA framework implementation
- **learning_paths/03_advanced_patterns/02_complex_research.py**: Multi-step research pattern
- **learning_paths/03_advanced_patterns/03_system_health.py**: System monitoring example
- **learning_paths/03_advanced_patterns/04_mcp_agent_demo.py**: MCP integration

## Real-World Applications

Domain-specific examples:

- **learning_paths/04_real_world_applications/01_rie_monitoring.py**: Semiconductor manufacturing use case
- **learning_paths/04_real_world_applications/02_system_health.py**: System monitoring example
- **learning_paths/04_real_world_applications/03_temperature_monitor.py**: Data pipeline example

## Quick Reference

### Agent Creation & Configuration

```python
from dxa.agent import Agent
from dxa.agent.resource import LLMResource
from dxa.execution import ReasoningStrategy

agent = Agent(name="example_agent")\
    .with_reasoning(ReasoningStrategy.DEFAULT)\
    .with_llm(LLMResource())\
    .with_capabilities({...})
```

### Task Execution

```python
# Synchronous execution
result = agent.run(workflow)

# Asynchronous execution
async with agent:
    result = await agent.async_run(workflow)
```

### Workflow Creation

```python
from dxa.execution import WorkflowFactory

# Create a sequential workflow
workflow = WorkflowFactory.create_sequential_workflow(
    objective="Research topic X",
    commands=["Step 1", "Step 2", "Step 3"]
)

# Create a minimal workflow
workflow = WorkflowFactory.create_minimal_workflow("Simple task")
```

## Running Examples

Each example can be run directly:

```bash
python examples/learning_paths/01_getting_started/01_simple_qa.py
```
