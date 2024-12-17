<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Reasoning System

The DXA reasoning system implements a two-layer architecture that separates strategic planning from tactical execution. This separation allows the system to maintain high-level objectives and adapt plans while efficiently executing individual steps.

## Design Philosophy

1. Simple things should be simple, complex things should be possible
   - One-liners for common cases
   - Natural language interfaces where sensible
   - Full power available when needed

2. Progressive complexity
   - Start with basic usage
   - Add capabilities as needed
   - No complexity penalty for simple cases

3. Smart defaults, explicit control
   - Auto-configuration for common cases
   - Resource discovery and management
   - Full control available when needed

## Architecture Overview

```mermaid
graph TB
    A[Strategic Layer] --> B[Planning]
    A --> C[Objective Management]
    A --> D[Resource Coordination]
    
    E[Tactical Layer] --> F[Execution]
    E --> G[Monitoring]
    E --> H[Signal Generation]
    
    B --> E
    G --> C
```

## Core Concepts

### 1. Reasoning Patterns (How to Think)

Purpose: Define the cognitive approach

Pure Patterns:

- Direct: Single LLM query → response
- Chain-of-Thought: Structured step-by-step thinking
- OODA: Observe-Orient-Decide-Act loop
- DANA: Neural search → symbolic execution

```mermaid
graph LR
    A[Input] --> B[Reasoning Pattern]
    B --> C[Output]
    
    subgraph "OODA Example"
    D[Observe] --> E[Orient]
    E --> F[Decide]
    F --> G[Act]
    end
```

### 2. Execution Strategies (How to Act)

Purpose: Define the execution flow

Pure Strategies:

- Single-Shot: One request → one response
- Iterative: Repeated try-evaluate-adjust
- Continuous: Ongoing operation
- Interactive: User-in-loop operation

```mermaid
stateDiagram-v2
    [*] --> Execute
    Execute --> Evaluate
    Evaluate --> Complete: Success
    Evaluate --> Execute: Need Adjustment
    Complete --> [*]
```

### 3. Workflows (What to Do)

Purpose: Define the task structure

Pure Workflows:

- Linear: Sequential steps
- Branching: Decision-based paths
- State Machine: Complex state transitions
- Event-Driven: Response patterns

```mermaid
stateDiagram-v2
    [*] --> Monitoring
    Monitoring --> Responding: Alert
    Responding --> Monitoring: Resolved
    Responding --> Alerting: Escalate
    Alerting --> Monitoring: Handled
```

## Integration Model

### Composition over Inheritance

Components combine through composition:

- Agents combine patterns, strategies, and workflows
- Each component remains pure and focused
- Mix and match based on needs

Example Combinations:

1. System Monitoring
   - Pattern: OODA Reasoning (how to think)
   - Strategy: Continuous Execution (how to act)
   - Workflow: State Machine (what to do)

2. Research Assistant
   - Pattern: Chain-of-Thought Reasoning
   - Strategy: Iterative Execution
   - Workflow: Branching Tasks

3. Chat Bot
   - Pattern: Direct Reasoning
   - Strategy: Interactive Execution
   - Workflow: Event-Driven

## Evolution Mechanisms

### Objective Evolution

```mermaid
graph TD
    A[Original Objective] --> B[Current Understanding]
    B --> C[Updated Objective]
    
    D[Planning Layer] --> B
    E[Reasoning Layer] --> B
    F[User Feedback] --> B
```

### Plan Evolution

```mermaid
graph TD
    A[Initial Plan] --> B[Execution]
    B --> C[Review]
    C --> D[Update Plan]
    D --> B
    
    E[New Information] --> C
    F[Resource Changes] --> C
    G[Performance Data] --> C
```

## Implementation Notes

1. Simple cases remain simple:
   - Direct reasoning is just one LLM call
   - Basic workflows are natural language → steps
   - Interactive modes use simple patterns

2. Complex cases are possible:
   - Full planning/reasoning cycle
   - Neural-symbolic integration
   - Multi-stage execution

3. User-Defined Workflows:
   - Natural language specifications
   - Runtime translation to plans
   - Flexible execution patterns

## Usage Examples

```python
# Simple: One-liner for common cases
agent = Agent.create("chat")
result = await agent.run("What is quantum computing?")

# Natural language workflow
agent = Agent.create("research", 
    workflow="Research fusion energy breakthroughs, focus on technical details")
result = await agent.run()

# Auto-configured monitoring
agent = Agent("monitor")\
    .with_auto_resources()\
    .with_workflow("Monitor CPU and memory, alert if usage exceeds 80%")

async with agent:
    await agent.run()

# Complex: Full control when needed
agent = Agent("expert")\
    .with_reasoning("dana")\
    .with_strategy("interactive")\
    .with_workflow(ComplexWorkflow(
        steps=[...],
        transitions={...},
        validation={...}
    ))\
    .with_resources({
        "llm": CustomLLM(...),
        "tools": CustomTools(...),
        "memory": PersistentMemory(...)
    })
```

## Resource Management

[All new sections remain exactly the same through Migration Guide section]

---

<p align="center">
Copyright © 2024 Aitomatic, Inc. All rights reserved.
</p>

<p align="center">
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
