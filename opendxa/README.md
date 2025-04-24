<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# OpenDXA - Domain-Expert Agent

The Domain-Expert Agent (OpenDXA) is an intelligent agent architecture designed to tackle complex domain-specific tasks with human-like expertise. At its heart is a unique architecture that combines declarative knowledge with imperative execution through a clear separation of concerns. The framework features advanced memory management with both short-term and long-term memory knowledge, enabling agents to learn from interactions and maintain context over extended periods. It includes robust knowledge-base management for structured storage and retrieval of domain knowledge, with support for versioning, evolution, and integration with external knowledge sources.

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

This architecture means you can:
- Start with simple knowledge bases
- Gradually expand domain expertise
- Scale to complex multi-agent systems
- Maintain clear separation between what agents know and how they act

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

## Core Concepts

1. **Knowledge**
   - Structured representation of domain expertise
   - Hierarchical organization of technical and domain knowledge
   - Versioned and evolvable knowledge bases
   - Integration with external knowledge sources

2. **Planning**
   - Task decomposition and sequencing
   - Resource allocation and optimization
   - Handling of constraints and dependencies
   - Dynamic plan adaptation

3. **Reasoning**
   - Logical inference and deduction
   - Pattern recognition and analysis
   - Decision making under uncertainty
   - Multi-agent coordination

4. **State Management**
   - World state tracking
   - Agent state maintenance
   - Context preservation
   - History and memory management

## Interaction Patterns

### Basic Interaction Pattern

The heart of OpenDXA is a consistent Planning-Knowledge interaction pattern:

1. **Basic Interaction Loop**:
   - Planning asks Knowledge: "How to solve X?"
   - Knowledge responds with one of three types:

     a. **Terminal** (Complete Solution)
        * Direct answer available in knowledge base
        * No further decomposition needed
        * Ready for immediate execution

     b. **Recursive** (Decomposable Solution)
        * Solution exists but requires multiple steps (with known workflows)
        * Each step may need further resolution
        * Natural hierarchical decomposition

     c. **Fallback** (Incomplete Solution)
        * No direct solution in knowledge base
        * Requires Reasoning to derive solution
        * Results stored for future reference

2. **Recursive Nature**:
   - For each step in a plan:
     - Same Planning-Knowledge interaction
     - All resolution through Knowledge
     - Natural termination at Complete Solutions
   - For Incomplete Solutions:
     - Planning delegates to Reasoning
     - Reasoning attempts to derive solution
     - Results are stored back in Knowledge
     - Future queries can use stored solutions

3. **Key Aspects**:
   - Consistent interaction pattern throughout
   - All knowledge access through Knowledge
   - Natural termination at Complete Solutions
   - Hierarchical decomposition for complex tasks
   - Continuous learning through Reasoning
   - Knowledge base evolution over time

### Single Agent Scenarios

#### 1. Simple Task

```mermaid
sequenceDiagram
    participant T as Task
    participant A as Agent
    participant AR as AgentRuntime
    participant P as Planning
    participant R as Reasoning
    participant K as Knowledge
    participant Res as Resources

    T->>A: Receive Task
    A->>AR: Forward Task
    AR->>P: Invoke Planner
    P->>K: How to solve Task?
    K->>K: Lookup Knowledge
    K-->>P: Return Direct Answer
    P->>R: Execute Answer
    R->>K: Apply Knowledge
    K->>Res: query(Resource)
    Res-->>K: Resource Response
    K-->>R: Execute Step
    R-->>P: Return Results
    P-->>AR: Return Results
    AR-->>A: Update State
    A-->>K: Improve Knowledge
```

#### 2. Complex Task

```mermaid
sequenceDiagram
    participant T as Task
    participant A as Agent
    participant AR as AgentRuntime
    participant P as Planning
    participant R as Reasoning
    participant K as Knowledge
    participant Res as Resources

    T->>A: Receive Complex Task
    A->>AR: Forward Task
    AR->>P: Invoke Planner
    P->>K: How to solve Task?
    K->>K: Lookup Knowledge
    K-->>P: Return Plan
    Note over K,P: Plan includes:<br/>- Subtask 1<br/>- Subtask 2<br/>- Subtask 3
    loop For Each Subtask
        P->>K: How to solve Subtask?
        K->>K: Lookup Knowledge
        K-->>P: Return Direct Answer
        P->>R: Execute Answer
        R->>K: Apply Knowledge
        K->>Res: query(Resource)
        Res-->>K: Resource Response
        K-->>R: Execute Step
        R-->>P: Return Results
    end
    P-->>AR: Return Combined Results
    AR-->>A: Update State
    A-->>K: Improve Knowledge
```

### Multi-Agent Scenarios

OpenDXA supports three main types of multi-agent interactions:

1. **Separate Tasks**
   - Multiple Agents working on different, independent tasks
   - Each Agent operates in its own domain
   - No coordination needed
   - Like different specialists in different fields

```mermaid
sequenceDiagram
    participant T1 as Task 1
    participant T2 as Task 2
    participant A1 as Agent 1
    participant A2 as Agent 2
    participant AR1 as AgentRuntime 1
    participant AR2 as AgentRuntime 2
    participant P1 as Planning 1
    participant P2 as Planning 2
    participant K1 as Knowledge 1
    participant K2 as Knowledge 2

    T1->>A1: Receive Task
    T2->>A2: Receive Task
    A1->>AR1: Forward Task
    A2->>AR2: Forward Task
    AR1->>P1: Invoke Planner
    AR2->>P2: Invoke Planner
    P1->>K1: How to solve Task?
    P2->>K2: How to solve Task?
    K1-->>P1: Return Answer
    K2-->>P2: Return Answer
    Note over A1,A2: Agents operate independently<br/>in their own domains
```

2. **Collaborative Tasks**
   - Multiple Agents working together on same task
   - Agents with complementary knowledge
   - Need to coordinate and share knowledge
   - Like a team of specialists working together

```mermaid
sequenceDiagram
    participant T as Task
    participant A1 as Agent 1
    participant A2 as Agent 2
    participant AR1 as AgentRuntime 1
    participant AR2 as AgentRuntime 2
    participant P1 as Planning 1
    participant P2 as Planning 2
    participant K1 as Knowledge 1
    participant K2 as Knowledge 2

    T->>A1: Receive Task
    A1->>AR1: Forward Task
    AR1->>P1: Invoke Planner
    P1->>K1: How to solve Task?
    K1-->>P1: Return Plan
    Note over K1,P1: Plan requires knowledge<br/>from Agent 2
    P1->>A2: Request Help
    A2->>AR2: Forward Request
    AR2->>P2: Invoke Planner
    P2->>K2: How to help?
    K2-->>P2: Return Answer
    P2-->>P1: Return Results
    P1-->>AR1: Return Combined Results
```

3. **Hierarchical Tasks**
   - One Agent delegating to other Agents
   - Parent Agent breaks down task
   - Child Agents handle specific aspects
   - Results flow back up the hierarchy

```mermaid
sequenceDiagram
    participant T as Task
    participant PA as Parent Agent
    participant CA1 as Child Agent 1
    participant CA2 as Child Agent 2
    participant PAR as Parent Runtime
    participant CAR1 as Child Runtime 1
    participant CAR2 as Child Runtime 2
    participant PP as Parent Planning
    participant CP1 as Child Planning 1
    participant CP2 as Child Planning 2

    T->>PA: Receive Task
    PA->>PAR: Forward Task
    PAR->>PP: Invoke Planner
    PP->>PP: Break Down Task
    PP->>CA1: Delegate Subtask 1
    PP->>CA2: Delegate Subtask 2
    CA1->>CAR1: Forward Subtask
    CA2->>CAR2: Forward Subtask
    CAR1->>CP1: Invoke Planner
    CAR2->>CP2: Invoke Planner
    CP1-->>PP: Return Results
    CP2-->>PP: Return Results
    PP-->>PAR: Return Combined Results
```

## Architecture Details

### System Architecture

#### Agent System ([documentation](agent/README.md))

1. **Core Components**
   - Agent - Declarative interface
   - AgentRuntime - Imperative execution
   - Knowledge - Agent abilities and knowledge
   - State System - Execution state management

2. **Key Features**
   - Clear separation of declarative and imperative aspects
   - Knowledge-based architecture
   - State tracking and persistence
   - Adaptive execution

#### Execution System ([documentation](execution/README.md))

1. **Components**
   - Planning - Strategic decomposition
   - Reasoning - Tactical execution

2. **Key Features**
   - Hierarchical execution
   - Dynamic adaptation
   - Progress tracking
   - Knowledge utilization

### Motivation

The Agent->Knowledge->Resources architecture provides two key benefits:

1. **Composable Knowledge**
   - An Agent can comprise multiple Knowledge bases
   - Each Knowledge base represents a distinct area of expertise or functionality
   - Knowledge can be added, removed, or updated independently
   - Enables building specialized agents by combining relevant Knowledge

2. **Hierarchical Knowledge Organization**
   - Knowledge can be hierarchically deep
   - Allows natural division of knowledge bases
   - Enables compartmentalization of expertise
   - Supports both broad and deep knowledge organization
   - Makes it easy to manage and apply knowledge:
     * Knowledge is organized by domain
     * Each knowledge base knows how to apply its knowledge
     * Knowledge updates are localized to relevant domains
     * Knowledge can combine information from multiple sources

For example:
```mermaid
graph TB
    A[Agent] --> C1[Medical Knowledge Base]
    A --> C2[Legal Knowledge Base]
    A --> C3[Technical Knowledge Base]
    
    C1 --> K1[Medical Knowledge Base]
    C1 --> K2[Patient Records]
    
    C2 --> K3[Legal Knowledge Base]
    C2 --> K4[Case Law]
    
    C3 --> K5[Technical Knowledge Base]
    C3 --> K6[Code Repository]
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

### Implementation Examples

#### Basic Usage

```python
# Simple Q&A
from opendxa.agent import Agent
from opendxa.agent.resource import LLMResource
answer = Agent().ask("What is quantum computing?")
```

#### Workflow Execution

```python
# Basic Workflow Execution
from opendxa.execution import WorkflowExecutor, ExecutionContext
from opendxa.execution.workflow import Workflow
from opendxa.common.graph import NodeType

# Create a workflow
workflow = Workflow(objective="Analyze customer feedback")
workflow.add_node(ExecutionNode(
    node_id="ANALYZE",
    node_type=NodeType.TASK,
    objective="Analyze feedback data"
))

# Set up execution
context = ExecutionContext(
    reasoning_llm=LLMResource(),
    planning_llm=LLMResource(),
    workflow_llm=LLMResource()
)
executor = WorkflowExecutor()
result = await executor.execute(workflow, context)
```

#### Advanced Usage

```python
# Advanced Usage with Custom Workflows
from opendxa.execution import ExecutionNode
from opendxa.common import DXA_LOGGER

# Configure logging
DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG, console=True)

# Create complex workflow with data dependencies
workflow = Workflow(objective="Research quantum computing")
workflow.add_node(ExecutionNode(
    node_id="GATHER",
    node_type=NodeType.TASK,
    objective="Gather research data",
    metadata={"output_key": "research_data"}
))
workflow.add_node(ExecutionNode(
    node_id="ANALYZE",
    node_type=NodeType.TASK,
    objective="Analyze findings",
    metadata={"input_key": "research_data"}
))
workflow.add_edge_between("GATHER", "ANALYZE")
```

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

## Documentation Map

- **Agent System**
  - [Agent Core](agent/README.md) - Factory and runtime
  - [Capabilities](agent/capability/README.md) - Cognitive abilities
  - [Resources](agent/resource/README.md) - Tools and services
  - [IO System](agent/io/README.md) - Environmental interaction
  - [State System](agent/state/README.md) - Execution state management

- **Execution System**
  - [Workflow](execution/workflow/README.md) - Process definition
  - [Planning](execution/planning/README.md) - Strategic planning
  - [Reasoning](execution/reasoning/README.md) - Tactical execution
  - [Pipeline](execution/pipeline/README.md) - Execution orchestration

- [Examples](../examples/README.md) - Usage patterns and tutorials

## Contributing

DXA is proprietary software developed by Aitomatic, Inc. Contributions are limited to authorized Aitomatic employees and contractors. If you're an authorized contributor:

1. Please ensure you have signed the necessary Confidentiality and IP agreements
2. Follow the internal development guidelines
3. Submit your changes through the company's approved development workflow
4. Contact the project maintainers for access to the Contributing Guide

For external users or organizations interested in collaborating with Aitomatic on DXA development, please contact our business development team.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
