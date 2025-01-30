<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Workflow System

## 1. Introduction & Context

The DXA Workflow system translates process specifications into executable workflow graphs. It serves as a bridge between human-readable process descriptions and machine-executable plans, enabling agents to perform complex tasks through well-defined workflows.

### System Context

```mermaid
graph TB
    subgraph Inputs ["Process Specifications"]
        NL[Natural Language]
        STT[Structured Text]
        CD[Code Definition]
        YM[YAML/JSON]
    end
    
    subgraph Workflow ["Workflow Specification"]
        direction TB
        P[Parser/LLM]
        G[Graph Compiler]
        V[Validator]
        
        P --> G
        G --> V
    end
    
    subgraph Execution ["Planning & Reasoning"]
        AG[Agent Runtime]
        PL[Planning System]
        RS[Reasoning System]
        ST[State Management]
    end
    
    V --> AG
    AG --> PL
    PL --> RS
    RS --> ST
    ST --> AG
    
    %% Input connections
    NL --> P
    STT --> P
    CD --> P
    YM --> P
```

### Design Principles

1. **Natural Language First**: Workflows should be as easy to write as explaining them to a colleague
2. **Clear State Management**: Define requirements and effects without managing state
3. **Flexible Execution**: Define what to do, not how to do it

## 2. System Architecture

### Core Components

```mermaid
classDiagram
    DirectedGraph <|-- Workflow
    Node <|-- WorkflowNode
    Edge <|-- WorkflowEdge
    Workflow --> Objective
    Workflow --> Plan
    
    class DirectedGraph{
        +nodes: Dict[str, Node]
        +edges: Dict[str, Edge]
        +add_node()
        +add_edge()
        +cursor()
    }
    
    class Workflow{
        +objective: Objective
        +add_task()
        +add_decision()
        +to_plan()
    }
    
    class WorkflowNode{
        +type: str
        +description: str
        +requires: Dict
        +provides: Dict
    }
    
    class Plan{
        +steps: List[Step]
        +execute()
    }
```

### Integration Points

```python
from dxa.core.workflow import Workflow
from dxa.core.planning import SequentialPlanner
from dxa.core.state import WorldState, AgentState
from dxa.core.agent import Agent

# Workflow creation and planning
workflow = create_workflow(objective="Research quantum computing")
planner = SequentialPlanner()
plan = planner.create_plan(workflow)

# Execution
agent = Agent()
world_state = WorldState()
agent_state = AgentState()
result = agent.execute_plan(plan, world_state, agent_state)
```

## 3. Core Concepts

### Workflow Structure

```python
class Workflow(DirectedGraph):
    """Workflow implementation using directed graphs."""
    def __init__(self, objective: Optional[Union[str, Objective]] = None):
        super().__init__()
        self._objective = self._parse_objective(objective)
        
    def add_task(self, id: str, description: str, **kwargs) -> WorkflowNode:
        """Add a task node to the workflow."""
        node = WorkflowNode(id, "TASK", description, **kwargs)
        self.add_node(node)
        return node

    def add_decision(self, id: str, description: str, **kwargs) -> WorkflowNode:
        """Add a decision point to the workflow."""
        node = WorkflowNode(id, "DECISION", description, **kwargs)
        self.add_node(node)
        return node
```

### Node Types

1. **Task Nodes**

```python
task = workflow.add_task(
    id="research",
    description="Search recent papers",
    requires={"api_key": "str"},
    provides={"papers": "List[Paper]"}
)
```

1. **Decision Nodes**

```python
decision = workflow.add_decision(
    id="evaluate",
    description="Check findings",
    requires={"papers": "List[Paper]"},
    provides={"next_action": "str"}
)
```

1. **Control Nodes**

```python
start = workflow.get_start()  # START node
ends = workflow.get_ends()    # END nodes
```

### State Management

```python
# State requirements
node = WorkflowNode(
    id="verify_credit",
    requires={
        "credit_score": "float",
        "income": "float"
    },
    provides={
        "approval_status": "bool",
        "risk_level": "str"
    }
)

# State validation
def validate_node(node: WorkflowNode, state: WorldState) -> bool:
    return all(
        state.has(req) and state.validate(req, spec)
        for req, spec in node.requires.items()
    )
```

## 4. Basic Usage

### Creating Simple Workflows

```python
# Using factory method
workflow = create_sequential_workflow([
    "gather_data",
    "analyze_data",
    "summarize_findings"
], objective="Research topic")

# Using natural language
workflow = create_from_text("""
1. Search for recent papers
2. Analyze methodologies
3. Summarize findings
""")
```

### Adding Decision Points

```python
workflow = create_from_text("""
Process: Credit Application Review
Steps:
1. Check credit score
2. If score > 700:
   - Fast-track approval
   Else:
   - Request additional documents
3. Make final decision
""")
```

### Common Patterns

```python
# Research workflow
workflow = create_research_workflow(
    objective="Research quantum computing"
)

# Q&A workflow
workflow = create_basic_qa_workflow(
    objective="Answer user question"
)
```

## 5. Advanced Features

### Graph Traversal

```python
cursor = workflow.cursor()
while cursor.has_next():
    node = cursor.next()
    if node.type == "DECISION":
        next_node = evaluate_decision(node)
        cursor.set_next(next_node)
```

### Validation Framework

```python
# Structure validation
workflow.validate_structure()  # From DirectedGraph

# Resource validation
def validate_resources(workflow: Workflow) -> bool:
    required = set()
    provided = set()
    for node in workflow.nodes.values():
        required.update(node.requires.keys())
        provided.update(node.provides.keys())
    return required.issubset(provided)

# Add custom validation
workflow.add_validation_rule(validate_resources)
```

### Error Handling

```python
try:
    workflow = create_from_text(spec)
    workflow.validate()
except CycleDetectedError as e:
    logger.error(f"Invalid workflow structure: {e}")
except ResourceValidationError as e:
    logger.error(f"Invalid resource specification: {e}")
```

## 6. Integration Examples

### Research Task Example

```python
from dxa.core.workflow import create_research_workflow
from dxa.core.planning import SequentialPlanner
from dxa.core.agent import Agent

# Create workflow
workflow = create_research_workflow(
    objective="Research quantum computing advances"
)

# Create plan
planner = SequentialPlanner()
plan = planner.create_plan(workflow)

# Execute
agent = Agent(resources={"llm": LLMResource()})
result = agent.execute_plan(plan)
```

Generated workflow structure:

```mermaid
graph LR
    S[Start] --> G[Gather Information]
    G --> A[Analyze Papers]
    A --> E[Extract Key Findings]
    E --> SY[Synthesize Results]
    SY --> C[Create Summary]
    C --> END[End]
    
    %% Node details
    G --"papers found"--> D{Sufficient?}
    D --"yes"--> A
    D --"no"--> G
    
    %% Styling
    classDef start fill:#e1f5fe,stroke:#01579b
    classDef task fill:#f3e5f5,stroke:#4a148c
    classDef decision fill:#fff3e0,stroke:#e65100
    classDef end_ fill:#e8f5e9,stroke:#1b5e20
    
    class S,END start
    class G,A,E,SY,C task
    class D decision
```

### Monitoring Example

```python
workflow = create_monitoring_workflow(
    target="system_metrics",
    interval="1h",
    thresholds={
        "cpu_usage": "> 90%",
        "memory_usage": "> 85%"
    },
    actions={
        "alert": "notify_admin",
        "critical": "restart_service"
    }
)
```

Generated workflow structure:

```mermaid
graph TB
    S[Start] --> M[Monitor Metrics]
    M --> C{Check Thresholds}
    C --"Normal"--> W[Wait Interval]
    C --"Warning"--> A[Alert Admin]
    C --"Critical"--> R[Restart Service]
    W --> M
    A --> M
    R --> M
    
    %% Styling
    classDef start fill:#e1f5fe,stroke:#01579b
    classDef task fill:#f3e5f5,stroke:#4a148c
    classDef decision fill:#fff3e0,stroke:#e65100
    
    class S start
    class M,W,A,R task
    class C decision
```

## 7. API Reference

### Core Classes

```python
class Workflow(DirectedGraph):
    def add_task(self, id: str, description: str, **kwargs) -> WorkflowNode
    def add_decision(self, id: str, description: str, **kwargs) -> WorkflowNode
    def add_transition(self, from_id: str, to_id: str, condition: Optional[str] = None) -> WorkflowEdge
    def get_start(self) -> WorkflowNode
    def get_ends(self) -> List[WorkflowNode]
```

### Factory Functions

```python
def create_workflow() -> Workflow
def create_sequential_workflow(steps: List[Node], objective: str) -> Workflow
def create_basic_qa_workflow(objective: str = "Answer the question") -> Workflow
def create_research_workflow(objective: str = "Research the topic") -> Workflow
```

## 8. Future Development

1. **Advanced Natural Language Processing**
   - Context-aware parsing
   - Ambiguity resolution
   - Intent recognition

2. **Extended Validation**
   - Resource optimization
   - Path analysis
   - Performance prediction

3. **Pattern Library**
   - Industry-specific templates
   - Best practice patterns
   - Compliance workflows

---

<p align="center">
Copyright © 2024 Aitomatic, Inc. All rights reserved.
</p>

<p align="center">
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
