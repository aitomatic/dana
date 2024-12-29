<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Core System

The Domain-Expert Agent (DXA) core system is an intelligent agent architecture designed to tackle complex domain-specific tasks with human-like expertise. At its heart is a unique three-layer graph architecture that breaks down high-level objectives into executable actions through a Why-What-How paradigm. The system maps business workflows (WHY) to concrete plans (WHAT), which are then executed through standardized reasoning patterns (HOW). This hierarchical decomposition allows agents to maintain strategic alignment while adapting to changing conditions - similar to how human experts combine domain knowledge with practical execution. Whether automating business processes, conducting research, or managing complex projects, DXA provides a flexible framework that combines strategic thinking with tactical execution.

## Architecture Overview

```mermaid
graph LR
    subgraph "Graph Mapping"
        direction LR
        G1[High-level Graph] --> G2[Detailed Graph]
        G2 --> G3[Execution Graph]
    end

    subgraph "Layer Architecture"
        direction LR
        W[Workflow Layer<br>WHY] --> P[Planning Layer<br>WHAT]
        P --> R[Reasoning Layer<br>HOW]
    end
```

### Layer Mapping Example

```mermaid
graph TB
    subgraph "Reasoning Layer (HOW)"
        direction LR
        R1[Observe<br>Gather Data] --> R2[Orient<br>Analyze Context]
        R2 --> R3[Decide<br>Choose Action]
        R3 --> R4[Act<br>Execute]
        R4 --> R1
    end

    subgraph "Planning Layer (WHAT)"
        direction LR
        P1[Analyze Competitors] --> P2[Survey Customers]
        P2 --> P3[Synthesize Findings]
        P3 --> P4[Create Report]
    end

   subgraph "Workflow Layer (WHY)"
        direction LR
        W1[Launch New Product] --> W2[Market Research]
        W2 --> W3[Product Development]
        W3 --> W4[Market Launch]
    end

    W2 -.->|Maps to| P1
    P1 -.->|Maps to| R1

    style W1 fill:#f9f,stroke:#333
    style W2 fill:#f9f,stroke:#333
    style W3 fill:#f9f,stroke:#333
    style W4 fill:#f9f,stroke:#333
    
    style P1 fill:#bbf,stroke:#333
    style P2 fill:#bbf,stroke:#333
    style P3 fill:#bbf,stroke:#333
    style P4 fill:#bbf,stroke:#333
    
    style R1 fill:#bfb,stroke:#333
    style R2 fill:#bfb,stroke:#333
    style R3 fill:#bfb,stroke:#333
    style R4 fill:#bfb,stroke:#333
```

### Core Components

1. **Workflow Layer (WHY)**
   - Defines high-level objectives and goals
   - Manages strategic direction
   - Tracks overall progress
   - See [Flow Documentation](flow/README.md)

2. **Planning Layer (WHAT)**
   - Determines concrete actions
   - Manages resource allocation
   - Adapts plans dynamically
   - See [Planning Documentation](planning/README.md)

3. **Reasoning Layer (HOW)**
   - Implements execution patterns
   - Handles tactical decisions
   - Processes feedback loops
   - See [Reasoning Documentation](reasoning/README.md)

## Key Features

- **Graph-based Architecture**: Each layer is represented as a directed graph
- **Hierarchical Mapping**: Nodes in higher layers map to subgraphs in lower layers
- **Dynamic Adaptation**: Plans and execution patterns adapt to changing conditions
- **State Management**: Each layer maintains its execution context
- **Progress Tracking**: Completion status propagates up through layers

## Core Modules

- [Agent](agent/README.md): Main execution controller
- [Planning](planning/README.md): Strategic action planning
- [Reasoning](reasoning/README.md): Tactical execution patterns
- [Capability](capability/README.md): Agent capabilities and skills
- [Resource](resource/README.md): Resource management
- [IO](io/README.md): Input/Output handling

## Implementation Example

```python
from dxa.core.agent import Agent
from dxa.core.planning import PlanningPattern
from dxa.core.reasoning import ReasoningPattern

# Create agent with layered execution
agent = Agent("expert_agent")\
    .with_workflow("product_launch")\
    .with_planning(PlanningPattern.DYNAMIC)\
    .with_reasoning(ReasoningPattern.OODA)

# Execute with hierarchical decomposition
async with agent:
    result = await agent.run({
        "objective": "Launch new product",
        "constraints": {
            "timeline": "Q3 2024",
            "budget": 1000000
        }
    })
```

## Layer Integration

The three layers work together through:

1. **Top-down Direction**
   - Workflow provides strategic context
   - Planning breaks down objectives
   - Reasoning implements actions

2. **Bottom-up Feedback**
   - Reasoning reports execution results
   - Planning adapts to outcomes
   - Workflow tracks progress

3. **State Management**
   - Each layer maintains graph position
   - Context flows between layers
   - Progress tracked at all levels

## Development Guidelines

1. **Graph Design**
   - Keep nodes focused and single-purpose
   - Define clear success criteria
   - Enable flexible mapping between layers

2. **Layer Separation**
   - Maintain clear Why-What-How separation
   - Avoid cross-layer dependencies
   - Use defined interfaces for communication

3. **State Handling**
   - Track progress explicitly
   - Maintain execution context
   - Enable state recovery

## See Also

- [Examples](../examples/README.md)
- [Documentation](../docs/README.md)
- [Tests](../tests/README.md)

---

<p align="center">
Copyright © 2024 Aitomatic, Inc. All rights reserved.
</p>

<p align="center">
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
