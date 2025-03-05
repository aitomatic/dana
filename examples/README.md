<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Examples

## Overview

This directory contains examples demonstrating the DXA (Distributed eXecution Architecture) framework. 
Examples are organized by learning path to help you navigate from basic concepts to advanced applications.

Each example includes:
- Detailed documentation explaining its purpose and key concepts
- Complete runnable code
- Comments explaining important implementation details

## Directory Organization

The examples are organized in two complementary ways:

### 1. Module-Based Organization (Original)

Examples are organized by module type:
- [basic/](basic/): Basic utilities and logging
- [execution/](execution/): Execution system examples (workflow, planning, reasoning, pipeline)
- [resource/](resource/): Resource management examples
- [fab-roca/](fab-roca/): Domain-specific examples

### 2. Learning Path-Based Organization (New)

Examples are also organized by learning progression:
- [learning_paths/01_getting_started/](learning_paths/01_getting_started/): Beginner-friendly examples
- [learning_paths/02_core_concepts/](learning_paths/02_core_concepts/): Intermediate examples
- [learning_paths/03_advanced_patterns/](learning_paths/03_advanced_patterns/): Advanced examples
- [learning_paths/04_real_world_applications/](learning_paths/04_real_world_applications/): Domain-specific examples

### 3. End-to-End Tutorials

Step-by-step tutorials for building complete applications:
- [tutorials/build_qa_agent/](tutorials/build_qa_agent/): Building a question-answering agent
- [tutorials/temperature_monitoring/](tutorials/temperature_monitoring/): Building a temperature monitoring system

## Learning Paths

### 1. Getting Started [Beginner]

Start here if you're new to DXA. These examples introduce fundamental concepts and simple workflows.

- **[execution/workflow/qa_approaches.py](execution/workflow/qa_approaches.py)**: Different approaches to question answering
  - Direct question answering using `agent.ask()`
  - Single-step workflow with WORKFLOW_IS_PLAN strategy
  - Multi-step reasoning with custom workflow creation
  
- **[basic/loggable_example.py](basic/loggable_example.py)**: Using the Loggable base class
  - Basic logging configuration
  - Structured logging patterns
  
- **[execution/workflow/default_workflow.py](execution/workflow/default_workflow.py)**: Default workflow creation
  - Creating a basic workflow
  - Running a workflow with an agent

### 2. Core Concepts [Intermediate]

Once familiar with the basics, these examples demonstrate key DXA concepts in more detail.

#### Workflow Patterns

- **[execution/workflow/run_default_workflow.py](execution/workflow/run_default_workflow.py)**: Running default workflows
  - Workflow execution process
  - Handling workflow results

#### Planning Strategies

- **[execution/planning/simple_plan.py](execution/planning/simple_plan.py)**: Basic planning patterns
  - Creating plans from objectives
  - Plan structure and components

#### Reasoning Approaches

- **[execution/reasoning/simple_reasoning.py](execution/reasoning/simple_reasoning.py)**: Basic reasoning patterns
  - Reasoning strategies
  - Executing reasoning tasks

#### Resource Integration

- **[resource/llm_resource.py](resource/llm_resource.py)**: LLM integration
  - Configuring LLM resources
  - Using LLMs in agents

### 3. Advanced Patterns [Advanced]

These examples demonstrate sophisticated patterns and complex workflows.

- **[execution/workflow/prosea_workflow.py](execution/workflow/prosea_workflow.py)**: ProSEA framework implementation
  - Problem-Solution-Evaluation-Action pattern
  - Complex reasoning workflows
  
- **[execution/workflow/complex_research.py](execution/workflow/complex_research.py)**: Multi-step research pattern
  - Sequential task execution
  - Managing complex workflows
  
- **[execution/pipeline/temperature_monitor.py](execution/pipeline/temperature_monitor.py)**: Data pipeline example
  - Processing streaming data
  - Continuous execution patterns

### 4. Real-World Applications [Advanced]

Domain-specific examples showing DXA in practical applications.

- **[execution/workflow/system_health.py](execution/workflow/system_health.py)**: System monitoring example
  - Health check workflows
  - Monitoring and alerting patterns
  
- **[fab-roca/rie_monitoring.py](fab-roca/rie_monitoring.py)**: Semiconductor manufacturing use case
  - Domain-specific workflows
  - Integration with external systems
  
- **[resource/mcp/mcp_agent_demo.py](resource/mcp/mcp_agent_demo.py)**: MCP integration
  - Using the Model Control Plane
  - Advanced resource configuration

## Concept Reference

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

### Resource Management

```python
agent.with_llm(LLMResource(config={"model": "openai:gpt-4"}))
agent.with_resources({
    "custom": CustomResource()
})
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

## Directory Structure

- **basic/**: Fundamental utilities
  - Logging utilities
  - Loggable class usage
  
- **execution/**: Execution system examples
  - **workflow/**: Workflow definition and execution
  - **planning/**: Planning system usage
  - **reasoning/**: Reasoning patterns
  - **pipeline/**: Data pipeline examples
  
- **resource/**: Resource system examples
  - LLM integration
  - MCP resource examples
  
- **fab-roca/**: Domain-specific examples
  - Semiconductor manufacturing use case
  - RIE monitoring example

## Running Examples

Each example can be run directly:

```bash
python examples/execution/workflow/qa_approaches.py
```

See individual examples for detailed documentation and usage instructions.
