# OpenDXA Interaction Patterns

## Basic Interaction Pattern

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

## Single Agent Scenarios

### 1. Simple Task

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

### 2. Complex Task

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

## Multi-Agent Scenarios

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