<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
# OpenDXA Architecture

## Architecture Overview

The Domain-Expert Agent architecture is built around two fundamental aspects:

1. **Declarative Aspect**
   - Defines what the agent knows
   - Manages knowledge and resources
   - Handles domain expertise
   - Provides structured access to knowledge

2. **Imperative Aspect**
   - Implements planning and reasoning
   - Executes tasks using available knowledge
   - Manages state and context
   - Coordinates multi-agent interactions

This architecture is complemented by built-in knowledge management, enabling:
- Structured storage and retrieval of domain knowledge
- Versioning and evolution of knowledge
- Integration with external knowledge sources
- Efficient querying and reasoning over knowledge

```mermaid
graph LR
    subgraph DA["Declarative Aspect"]
        K[Knowledge]
        R[Resources]
        K --> R
    end

    subgraph IA["Imperative Aspect"]
        P[Planning]
        RE[Reasoning]
        P --- RE
    end

    subgraph S["State"]
        WS[WorldState]
        AS[AgentState]
        WS --- AS
    end

    DA --> IA
    IA --> S
```

## Knowledge Structure

### Technical Knowledge

```mermaid
graph TD
    subgraph "Technical Knowledge"
        direction TB
        TK1[Data Processing]
        TK2[Language Understanding]
    end

    subgraph "Data Processing"
        direction TB
        DP1[Analysis]
        DP2[Time Series]
        DP3[Pattern Recognition]
    end

    subgraph "Analysis"
        direction TB
        AN1[Statistical Analysis]
        AN2[Predictive Modeling]
        AN3[Anomaly Detection]
    end

    subgraph "Language Understanding"
        direction TB
        LU1[NLP]
        LU2[Text Processing]
        LU3[Document Analysis]
    end

    TK1 --> DP1
    TK1 --> DP2
    TK1 --> DP3
    DP1 --> AN1
    DP1 --> AN2
    DP1 --> AN3
    TK2 --> LU1
    TK2 --> LU2
    TK2 --> LU3
```

### Domain Knowledge

```mermaid
graph TD
    subgraph "Domain Knowledge"
        direction TB
        DK1[Semiconductor]
        DK2[Manufacturing]
    end

    subgraph "Semiconductor"
        direction TB
        SC1[Process Control]
        SC2[Yield Analysis]
        SC3[Equipment Monitoring]
    end

    subgraph "Process Control"
        direction TB
        PC1[Recipe Optimization]
        PC2[Parameter Control]
        PC3[Process Stability]
    end

    subgraph "Manufacturing"
        direction TB
        MF1[Quality Control]
        MF2[Production Optimization]
        MF3[Supply Chain]
    end

    DK1 --> SC1
    DK1 --> SC2
    DK1 --> SC3
    SC1 --> PC1
    SC1 --> PC2
    SC1 --> PC3
    DK2 --> MF1
    DK2 --> MF2
    DK2 --> MF3
```

## Implementation

### Engineering Approaches

OpenDXA follows three key engineering principles that guide its architecture and implementation:

1. **Progressive Complexity**
   - Start with simple implementations
   - Add complexity incrementally
   - Maintain clarity at each level
   - Enable gradual learning curve

2. **Composable Architecture**
   - Mix and match components
   - Highly customizable agents
   - Flexible integration points
   - Reusable building blocks

3. **Clean Separation of Concerns**
   - Clear component boundaries
   - Well-defined interfaces
   - Minimal dependencies
   - Maintainable codebase

## Project Structure

```text
opendxa/
├── agent/                  # Agent system
│   ├── capability/        # Cognitive abilities
│   ├── resource/         # External tools & services
│   ├── io/              # Input/Output handling
│   └── state/           # State management
├── common/               # Shared utilities
│   └── utils/           # Utility functions
│       └── logging.py   # Logging configuration
├── execution/            # Execution system
│   ├── pipeline/       # Pipeline execution
│   │   └── executor.py # WorkflowExecutor
│   ├── planning/       # Strategic planning
│   ├── workflow/       # Process workflows
│   │   └── workflow.py # Workflow implementation
│   └── reasoning/      # Reasoning patterns
└── factory/            # Factory components
```

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
