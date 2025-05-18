<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)


# Planning in OpenDXA

## Overview

Planning in OpenDXA enables agents to decompose complex objectives into manageable tasks, allocate resources effectively, and manage dependencies between tasks. Using DANA programs, planning combines strategic thinking with tactical execution to achieve goals efficiently.

## Core Concepts

### 1. Planning Components
- Task Decomposition
  - Goal analysis
  - Task breakdown
  - Dependency mapping
  - Resource allocation
- Strategy Development
  - Approach selection
  - Risk assessment
  - Contingency planning
  - Optimization criteria
- Execution Planning
  - Task sequencing
  - Resource scheduling
  - Timeline management
  - Progress tracking

### 2. Planning Operations
- Goal analysis
- Task decomposition
- Resource allocation
- Dependency management
- Strategy selection

## Architecture

The planning system in OpenDXA is implemented as a series of DANA programs that perform specific planning functions:

1. **Goal Analysis Layer**: Analyzes objectives and breaks them down into manageable components
2. **Task Decomposition Layer**: Creates specific tasks from goal components
3. **Resource Allocation Layer**: Assigns resources to tasks based on availability and requirements
4. **Dependency Management Layer**: Establishes relationships between tasks
5. **Strategy Planning Layer**: Develops overall execution approach and contingency plans

## Implementation

### 1. Basic Planning with DANA
```python
from opendxa.dana import run
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Define DANA planning program
planning_program = """
# Initialize planning state
agent.objective = "Analyze customer data"
temp.resources = world.available_resources
temp.tasks = []

# Break down the objective
temp.subtasks = reason("Break down the objective '{agent.objective}' into 3-5 subtasks")

# For each subtask, create a task definition
for subtask in temp.subtasks:
    temp.task = {
        "name": subtask,
        "resources": [],
        "dependencies": [],
        "estimated_time": reason("Estimate time needed for task: {subtask}")
    }
    temp.tasks.append(temp.task)

# Analyze dependencies between tasks
temp.dependency_analysis = reason("Identify dependencies between these tasks: {temp.tasks}")

# Update tasks with dependency information
for task_info in temp.dependency_analysis:
    for task in temp.tasks:
        if task["name"] == task_info["task"]:
            task["dependencies"] = task_info["depends_on"]

# Store the final plan
agent.plan = temp.tasks
"""

# Create context with initial state
context = SandboxContext(
    agent={"name": "planning_agent"},
    world={"available_resources": ["database", "analytics_tool", "visualization_library"]},
    temp={}
)

# Execute planning program
result = run(planning_program, context)
```

### 2. Resource Allocation
```python
# DANA program for resource allocation
resource_allocation_program = """
# Initialize resource state
temp.tasks = agent.plan
temp.resources = world.available_resources
temp.allocated_resources = {}

# Analyze resource requirements
for task in temp.tasks:
    temp.requirements = reason("What resources are needed for task: {task['name']}?")
    temp.resource_match = []
    
    # Match requirements to available resources
    for req in temp.requirements:
        for res in temp.resources:
            if req in res:
                temp.resource_match.append(res)
                break
    
    # Allocate resources to task
    temp.allocated_resources[task["name"]] = temp.resource_match

# Update plan with resource allocation
for task in temp.tasks:
    task["resources"] = temp.allocated_resources[task["name"]]

# Store updated plan
agent.plan = temp.tasks
"""
```

### 3. Execution Scheduling
```python
# DANA program for execution scheduling
scheduling_program = """
# Initialize scheduling state
temp.tasks = agent.plan
temp.schedule = []
temp.completed = []
temp.pending = [task["name"] for task in temp.tasks]

# Schedule tasks based on dependencies
while len(temp.pending) > 0:
    temp.schedulable = []
    
    # Find tasks with no pending dependencies
    for task_name in temp.pending:
        temp.task = next(task for task in temp.tasks if task["name"] == task_name)
        temp.dependencies_met = True
        
        for dependency in temp.task["dependencies"]:
            if dependency not in temp.completed:
                temp.dependencies_met = False
                break
        
        if temp.dependencies_met:
            temp.schedulable.append(task_name)
    
    # Schedule tasks and update tracking
    for task_name in temp.schedulable:
        temp.schedule.append(task_name)
        temp.completed.append(task_name)
        temp.pending.remove(task_name)

# Store execution schedule
agent.execution_schedule = temp.schedule
"""
```

## Key Differentiators

1. **DANA-Powered Planning**
   - Programmatic planning logic
   - Integrated reasoning capabilities
   - Dynamic plan adaptation
   - Context-aware planning

2. **Strategic Task Management**
   - Goal-oriented decomposition
   - Resource optimization
   - Dependency management
   - Execution sequencing

3. **Adaptive Planning**
   - Dynamic replanning
   - Resource reallocation
   - Strategy adjustment
   - Contingency handling

## Best Practices

1. **Goal Analysis**
   - Establish clear objectives
   - Define measurable outcomes
   - Set realistic expectations
   - Maintain proper scoping

2. **Task Decomposition**
   - Create logical breakdowns
   - Identify clear dependencies
   - Maintain proper granularity
   - Align tasks with resources

3. **Resource Management**
   - Allocate efficiently
   - Schedule appropriately
   - Plan for contingencies
   - Monitor performance

## Common Patterns

1. **Basic Planning**
   ```python
   # DANA program for basic planning
   planning_program = """
   # Define objective
   agent.objective = "Process customer data"
   
   # Break down into tasks
   temp.tasks = reason("Break down the objective '{agent.objective}' into specific tasks")
   
   # Identify dependencies
   temp.dependencies = reason("Identify dependencies between these tasks: {temp.tasks}")
   
   # Create structured plan
   agent.plan = []
   for task in temp.tasks:
       temp.task_deps = [d for d in temp.dependencies if d["task"] == task]
       temp.deps = temp.task_deps[0]["depends_on"] if temp.task_deps else []
       
       agent.plan.append({
           "name": task,
           "dependencies": temp.deps
       })
   """
   ```

2. **Resource Allocation**
   ```python
   # DANA program for resource allocation
   resource_program = """
   # Get resources and tasks
   temp.resources = world.available_resources
   temp.tasks = agent.plan
   
   # Allocate resources to tasks
   for task in temp.tasks:
       task["resources"] = reason("Allocate resources from {temp.resources} to task: {task['name']}")
   
   # Update plan
   agent.plan = temp.tasks
   """
   ```

3. **Plan Execution Monitoring**
   ```python
   # DANA program for execution monitoring
   monitoring_program = """
   # Initialize tracking
   temp.tasks = agent.plan
   temp.completed = world.completed_tasks
   temp.in_progress = world.in_progress_tasks
   
   # Update status
   for task in temp.tasks:
       if task["name"] in temp.completed:
           task["status"] = "completed"
       elif task["name"] in temp.in_progress:
           task["status"] = "in_progress"
       else:
           task["status"] = "pending"
   
   # Check for next tasks
   temp.next_tasks = []
   for task in temp.tasks:
       if task["status"] == "pending":
           temp.dependencies_met = True
           for dep in task["dependencies"]:
               temp.dep_task = next(t for t in temp.tasks if t["name"] == dep)
               if temp.dep_task["status"] != "completed":
                   temp.dependencies_met = False
                   break
           
           if temp.dependencies_met:
               temp.next_tasks.append(task["name"])
   
   # Store next tasks
   agent.next_tasks = temp.next_tasks
   """
   ```

## Planning Examples

1. **Data Analysis Planning**
   - Data collection tasks
   - Processing step organization
   - Analysis sequencing
   - Results generation planning

2. **Process Automation Planning**
   - Task sequence determination
   - Resource requirement analysis
   - Dependency identification
   - Execution schedule creation

3. **Decision Making Planning**
   - Option generation planning
   - Analysis criteria definition
   - Evaluation process structuring
   - Implementation step organization

## Next Steps

- Learn about [Reasoning](./reasoning.md)
- Understand [Execution Flow](../core-concepts/execution-flow.md)

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>