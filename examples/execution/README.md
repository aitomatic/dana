# Execution System Examples

This directory contains examples demonstrating the DXA execution system, which is organized into three hierarchical layers:

1. **Workflow Layer (WHY)**: High-level objectives and task sequences
2. **Planning Layer (WHAT)**: Concrete execution steps
3. **Reasoning Layer (HOW)**: Detailed implementation of individual tasks

## Subdirectories

- [workflow/](workflow/): Workflow creation, configuration, and execution examples
- [planning/](planning/): Planning system examples
- [reasoning/](reasoning/): Reasoning pattern examples
- [pipeline/](pipeline/): Data pipeline and continuous execution examples

## Learning Paths

### Getting Started [Beginner]

Start with these examples to understand basic execution concepts:

- [workflow/qa_approaches.py](workflow/qa_approaches.py): Different approaches to question answering
- [workflow/default_workflow.py](workflow/default_workflow.py): Default workflow creation
- [planning/simple_plan.py](planning/simple_plan.py): Basic planning patterns

### Core Concepts [Intermediate]

Once familiar with the basics, explore these examples to understand key execution concepts:

- [workflow/run_default_workflow.py](workflow/run_default_workflow.py): Running default workflows
- [reasoning/simple_reasoning.py](reasoning/simple_reasoning.py): Basic reasoning patterns
- [pipeline/temperature_monitor.py](pipeline/temperature_monitor.py): Data pipeline example

### Advanced Patterns [Advanced]

These examples demonstrate sophisticated patterns and complex workflows:

- [workflow/prosea_workflow.py](workflow/prosea_workflow.py): ProSEA framework implementation
- [workflow/complex_research.py](workflow/complex_research.py): Multi-step research pattern
- [workflow/system_health.py](workflow/system_health.py): System monitoring example

## Key Concepts

### Execution Hierarchy

```
Workflow (WHY) → Plan (WHAT) → Reasoning (HOW)
```

### Execution Context

The execution context maintains state across the execution hierarchy:

```python
from dxa.execution import ExecutionContext

context = ExecutionContext()
context.set_value("key", "value")
result = context.get_value("key")  # "value"
```

### Signal-Based Communication

Execution components communicate using signals:

```python
from dxa.execution import ExecutionSignal, ExecutionSignalType

# Create a signal
signal = ExecutionSignal(
    type=ExecutionSignalType.DATA_RESULT,
    content={"result": "Some result data"}
)

# Process a signal
if signal.type == ExecutionSignalType.DATA_RESULT:
    result = signal.content.get("result")
```

## Next Steps

After exploring these examples, consider:

1. Creating custom workflow patterns
2. Implementing conditional workflows
3. Exploring parallel execution
4. Developing domain-specific workflows 