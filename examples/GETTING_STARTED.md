# Getting Started with DXA

This guide provides a structured learning path for beginners to the DXA framework. Follow these examples in sequence to build a solid foundation.

## Learning Objectives

By the end of this learning path, you will be able to:
- Understand the basic concepts of the DXA framework
- Create and run simple workflows
- Configure logging and basic utilities
- Execute question-answering tasks

## Examples in this Learning Path

### 1. Basic Logging and Utilities

Start with these examples to understand the foundational utilities:

- [basic/loggable_example.py](basic/loggable_example.py): Using the Loggable base class
  - Basic logging configuration
  - Structured logging patterns
  
- [basic/logging_example.py](basic/logging_example.py): DXA logging system
  - Configuring loggers
  - Log levels and formatting

### 2. Simple Workflow Creation

Next, learn how to create basic workflows:

- [execution/workflow/default_workflow.py](execution/workflow/default_workflow.py): Default workflow creation
  - Creating a basic workflow
  - Running a workflow with an agent
  
- [execution/workflow/run_default_workflow.py](execution/workflow/run_default_workflow.py): Running default workflows
  - Workflow execution process
  - Handling workflow results

### 3. Question Answering

Finally, explore different approaches to question answering:

- [execution/workflow/qa_approaches.py](execution/workflow/qa_approaches.py): Different approaches to question answering
  - Direct question answering using `agent.ask()`
  - Single-step workflow with WORKFLOW_IS_PLAN strategy
  - Multi-step reasoning with custom workflow creation

## Suggested Learning Order

1. Start with [basic/loggable_example.py](basic/loggable_example.py) to understand logging
2. Move to [execution/workflow/default_workflow.py](execution/workflow/default_workflow.py) to create your first workflow
3. Learn how to run workflows with [execution/workflow/run_default_workflow.py](execution/workflow/run_default_workflow.py)
4. Explore different QA approaches with [execution/workflow/qa_approaches.py](execution/workflow/qa_approaches.py)

## Key Concepts

### Agent Creation

```python
from dxa.agent import Agent
from dxa.agent.resource import LLMResource

agent = Agent(name="example_agent")\
    .with_llm(LLMResource())\
    .with_capabilities({...})
```

### Workflow Creation

```python
from dxa.execution import WorkflowFactory

# Create a minimal workflow
workflow = WorkflowFactory.create_minimal_workflow("Answer this question")

# Create a default workflow
workflow = WorkflowFactory.create_default_workflow(
    objective="Design a database schema",
    agent_role="Database Designer"
)
```

### Workflow Execution

```python
# Synchronous execution
result = agent.run(workflow)

# Asynchronous execution
async with agent:
    result = await agent.async_run(workflow)
```

## Next Steps

After completing this learning path, you can:

1. Explore the [Core Concepts](CORE_CONCEPTS.md) learning path
2. Dive deeper into planning and reasoning layers
3. Learn about resource integration and management 