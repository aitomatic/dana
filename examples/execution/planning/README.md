# Planning Examples

This directory contains examples demonstrating the Planning layer (WHAT) of the DXA execution system. The Planning layer is responsible for transforming high-level objectives into concrete execution steps.

## Learning Paths

### Core Concepts [Intermediate]

These examples demonstrate key planning concepts:

- [simple_plan.py](simple_plan.py): Basic planning patterns
  - Creating plans from objectives
  - Plan structure and components
  - Understanding the planning layer

## Key Concepts

### Plan Creation

```python
from dxa.execution import PlanFactory
from dxa.execution.execution_types import Objective

# Create a plan from an objective
objective = Objective("Design a database schema for a library management system")
plan = PlanFactory.create_default_plan(objective)
```

### Plan Structure

A plan consists of:
- START node: Entry point for execution
- Task nodes: Concrete execution steps
- END node: Exit point for execution

### Planning Strategies

```python
from dxa.execution import PlanStrategy

# Different planning strategies
direct_plan = PlanFactory.create_plan(
    objective=objective,
    strategy=PlanStrategy.DIRECT
)

dynamic_plan = PlanFactory.create_plan(
    objective=objective,
    strategy=PlanStrategy.DYNAMIC
)
```

## Related Concepts

- [Workflow Examples](../workflow/): How workflows are transformed into plans
- [Reasoning Examples](../reasoning/): How plan steps are executed

## Next Steps

After exploring these examples, consider:

1. Creating custom planning strategies
2. Understanding plan execution
3. Exploring the relationship between workflows and plans
4. Implementing domain-specific planning patterns 