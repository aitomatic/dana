# Core Concepts in DXA

This guide provides a structured learning path for understanding the core concepts of the DXA framework. These examples build on the Getting Started path and explore the framework's key components in more depth.

## Learning Objectives

By the end of this learning path, you will be able to:
- Understand the three-layer execution model (Workflow, Planning, Reasoning)
- Work with different execution strategies
- Process data through pipelines
- Integrate and use resources

## Examples in this Learning Path

### 1. Workflow Layer (WHY)

Start with these examples to understand the Workflow layer:

- [execution/workflow/run_default_workflow.py](execution/workflow/run_default_workflow.py): Running default workflows
  - Workflow execution process
  - Handling workflow results

### 2. Planning Layer (WHAT)

Next, explore the Planning layer:

- [execution/planning/simple_plan.py](execution/planning/simple_plan.py): Basic planning patterns
  - Creating plans from objectives
  - Plan structure and components
  - Understanding the planning layer

### 3. Reasoning Layer (HOW)

Then, learn about the Reasoning layer:

- [execution/reasoning/simple_reasoning.py](execution/reasoning/simple_reasoning.py): Basic reasoning patterns
  - Reasoning strategies
  - Executing reasoning tasks
  - Understanding the reasoning layer

### 4. Data Pipelines

Explore data processing with pipelines:

- [execution/pipeline/temperature_monitor.py](execution/pipeline/temperature_monitor.py): Data pipeline example
  - Processing streaming data
  - Continuous execution patterns
  - Sensor data analysis

### 5. Resource Integration

Finally, learn about resource integration:

- [resource/llm_resource.py](resource/llm_resource.py): LLM integration
  - Configuring LLM resources
  - Using LLMs in agents
  - Managing LLM interactions

## Suggested Learning Order

1. Start with [execution/workflow/run_default_workflow.py](execution/workflow/run_default_workflow.py) to understand workflow execution
2. Move to [execution/planning/simple_plan.py](execution/planning/simple_plan.py) to learn about planning
3. Explore reasoning with [execution/reasoning/simple_reasoning.py](execution/reasoning/simple_reasoning.py)
4. Learn about data pipelines with [execution/pipeline/temperature_monitor.py](execution/pipeline/temperature_monitor.py)
5. Understand resource integration with [resource/llm_resource.py](resource/llm_resource.py)

## Key Concepts

### Execution Hierarchy

```
Workflow (WHY) → Plan (WHAT) → Reasoning (HOW)
```

### Execution Context

```python
from dxa.execution import ExecutionContext

context = ExecutionContext()
context.set_value("key", "value")
result = context.get_value("key")  # "value"
```

### Signal-Based Communication

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

### Resource Management

```python
from dxa.agent import Agent
from dxa.agent.resource import LLMResource

# Create and configure a resource
llm = LLMResource(
    config={
        "model": "openai:gpt-4",
        "temperature": 0.7
    }
)

# Add to agent
agent = Agent(name="example_agent")
agent.with_llm(llm)
```

## Next Steps

After completing this learning path, you can:

1. Explore the [Advanced Patterns](ADVANCED_PATTERNS.md) learning path
2. Learn about complex workflow patterns
3. Dive into domain-specific applications 