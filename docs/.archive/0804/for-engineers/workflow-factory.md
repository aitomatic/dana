# Workflow Factory

The `WorkflowFactory` provides a comprehensive system for creating executable `WorkflowInstance` objects from textual workflow definitions, with a focus on YAML format support.

## Overview

The factory system consists of several key components:

- **`WorkflowFactory`**: Main entry point for creating workflows
- **`YAMLWorkflowParser`**: Parses YAML text into structured definitions
- **`WorkflowDefinition`**: Intermediate representation of workflow structure
- **`WorkflowStep`**: Individual step definition with execution details

## Key Features

### 1. YAML Parsing
- Extracts YAML content from code blocks
- Validates workflow structure
- Handles nested workflow definitions

### 2. Structured Step Information
- **`steps_info`**: Complete step data for LLM execution
  - Step names, actions, objectives
  - Parameters and conditions
  - Next step and error handling
- **`workflow_metadata`**: Context information for execution
  - Workflow name and description
  - Total step count and FSM configuration

### 3. Execution-Ready Instances
- **Step status tracking**: `step_step_1`, `step_step_2`, etc.
- **Result storage**: Centralized result container
- **Original YAML preservation**: For debugging and reference
- **FSM integration**: State machine for execution control

## Usage

### Basic Workflow Creation

```python
from dana.core.workflow.factory import WorkflowFactory

factory = WorkflowFactory()

yaml_text = """
workflow:
  name: "ResearchWorkflow"
  description: "A research workflow with multiple phases"
  steps:
    - step: 1
      name: "Research Phase"
      action: "research_topic"
      objective: "Gather comprehensive information about the topic"
      parameters:
        topic: "AI safety"
        sources: ["papers", "blogs", "videos"]
    - step: 2
      name: "Analysis Phase"
      action: "analyze_data"
      objective: "Analyze the gathered information systematically"
      parameters:
        method: "systematic_review"
"""

workflow = factory.create_from_yaml(yaml_text)
```

### Accessing Step Information

```python
# Get structured step information for LLM execution
step_info = workflow.steps_info["step_1"]
print(f"Step: {step_info['name']}")
print(f"Action: {step_info['action']}")
print(f"Objective: {step_info['objective']}")
print(f"Parameters: {step_info['parameters']}")

# Get workflow metadata
metadata = workflow.workflow_metadata
print(f"Workflow: {metadata['name']}")
print(f"Description: {metadata['description']}")
print(f"Total Steps: {metadata['total_steps']}")
```

### Step Execution Simulation

```python
# Simulate LLM prompt construction
current_step_id = "step_1"
current_step_info = workflow.steps_info[current_step_id]

llm_prompt = f"""
Execute the following workflow step:

Step: {current_step_info['name']}
Action: {current_step_info['action']}
Objective: {current_step_info['objective']}
Parameters: {current_step_info['parameters']}

Please execute this step and provide the results.
"""

# Update step status and store results
workflow.step_step_1 = "completed"
workflow.result["step_1"] = {
    "status": "completed",
    "data_collected": 150,
    "sources_accessed": ["database", "api"]
}
```

## YAML Format

### Basic Structure

```yaml
workflow:
  name: "WorkflowName"
  description: "Workflow description"
  steps:
    - step: 1
      name: "Step Name"
      action: "action_name"
      objective: "Step objective"
      parameters:
        key: "value"
        list_param: ["item1", "item2"]
    - step: 2
      name: "Next Step"
      action: "next_action"
      objective: "Next objective"
      parameters:
        method: "systematic"
```

### Advanced Features

#### FSM Configuration

```yaml
workflow:
  name: "AdvancedWorkflow"
  fsm_config:
    type: "linear"
    states: ["start", "process", "validate", "complete"]
  steps:
    - step: 1
      name: "Process"
      action: "process_data"
      next_step: "step_2"
    - step: 2
      name: "Validate"
      action: "validate_results"
      conditions:
        success: "step_3"
        failure: "step_1"
```

#### Error Handling

```yaml
workflow:
  name: "RobustWorkflow"
  steps:
    - step: 1
      name: "Risky Operation"
      action: "risky_action"
      error_step: "step_error"
    - step: "error"
      name: "Error Recovery"
      action: "recover_from_error"
```

## Integration with Agent System

The `WorkflowFactory` is integrated into the agent solving system:

```python
# In agent.solve() -> _complete_plan()
elif plan_type == PlanType.TYPE_WORKFLOW:
    if solution:
        try:
            from dana.core.workflow.factory import WorkflowFactory
            factory = WorkflowFactory()
            workflow_instance = factory.create_from_yaml(solution)
            return workflow_instance
        except Exception as e:
            # Fallback to simple workflow dict
            return {"type": PlanType.TYPE_WORKFLOW.value, "content": solution}
```

## Execution Engine Integration

The enhanced `WorkflowInstance` provides all necessary information for LLM-based execution:

### Required Information for Execution

1. **Step Objectives**: What each step aims to accomplish
2. **Step Actions**: What action to perform
3. **Step Parameters**: Context and configuration for execution
4. **Workflow Context**: Overall workflow metadata
5. **Status Tracking**: Current execution state
6. **Result Storage**: Outcomes from each step

### Execution Flow

1. **Initialize**: Create `WorkflowInstance` from YAML
2. **Iterate**: For each step in the workflow:
   - Extract step information from `steps_info`
   - Construct LLM prompt with objective and parameters
   - Execute step using LLM
   - Update step status and store results
3. **Complete**: Return final workflow results

## Error Handling

### Validation Errors

```python
try:
    workflow = factory.create_from_yaml(invalid_yaml)
except ValueError as e:
    print(f"Invalid workflow: {e}")
```

### Execution Errors

```python
# Step execution can handle errors
workflow.step_step_1 = "error"
workflow.result["step_1"] = {
    "status": "error",
    "error": "Failed to collect data",
    "retry_count": 3
}
```

## Best Practices

### 1. Clear Step Objectives
- Write specific, measurable objectives
- Include success criteria when possible

### 2. Comprehensive Parameters
- Provide all necessary context
- Use structured data formats

### 3. Error Handling
- Define error steps for critical operations
- Include retry logic in parameters

### 4. Documentation
- Use descriptive step names
- Include workflow descriptions

### 5. Testing
- Validate workflows before execution
- Test with sample data

## Future Enhancements

- **JSON Support**: Additional format support
- **Mermaid Integration**: Visual workflow representation
- **Advanced FSM**: Complex state machine configurations
- **Workflow Templates**: Reusable workflow patterns
- **Execution Monitoring**: Real-time execution tracking
