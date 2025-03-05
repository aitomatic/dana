# Workflow Examples

This directory contains examples demonstrating workflow creation, configuration, and execution in the DXA framework.

## Learning Paths

### Getting Started [Beginner]

Start with these examples to understand basic workflow concepts:

- [qa_approaches.py](qa_approaches.py): Different approaches to question answering
  - Direct question answering using `agent.ask()`
  - Single-step workflow with WORKFLOW_IS_PLAN strategy
  - Multi-step reasoning with custom workflow creation
  
- [default_workflow.py](default_workflow.py): Default workflow creation
  - Creating a basic workflow
  - Running a workflow with an agent

- [run_default_workflow.py](run_default_workflow.py): Running default workflows
  - Workflow execution process
  - Handling workflow results

### Advanced Patterns [Advanced]

Once comfortable with basic workflows, explore these advanced examples:

- [prosea_workflow.py](prosea_workflow.py): ProSEA framework implementation
  - Problem-Solution-Evaluation-Action pattern
  - Complex reasoning workflows
  
- [complex_research.py](complex_research.py): Multi-step research pattern
  - Sequential task execution
  - Managing complex workflows

### Real-World Applications [Advanced]

See how workflows are applied to real-world problems:

- [system_health.py](system_health.py): System monitoring example
  - Health check workflows
  - Monitoring and alerting patterns

## Key Concepts

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

### Workflow Execution

```python
from dxa.agent import Agent

agent = Agent()
result = agent.run(workflow)
```

### Workflow Strategies

```python
from dxa.execution import WorkflowStrategy

agent = Agent().with_workflow(WorkflowStrategy.DEFAULT)
```

## Related Concepts

- [Planning Examples](../planning/): How workflows are transformed into execution plans
- [Reasoning Examples](../reasoning/): How individual tasks are executed
- [Pipeline Examples](../pipeline/): Continuous execution workflows

## Next Steps

After exploring these examples, consider:

1. Creating custom workflow patterns
2. Implementing conditional workflows
3. Exploring parallel execution
4. Developing domain-specific workflows 