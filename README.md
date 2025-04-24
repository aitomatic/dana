<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# OpenDXA - Domain-Expert Agent Framework

OpenDXA is a Python framework that enables building intelligent multi-agent systems with domain expertise, powered by Large Language Models (LLMs). The framework features advanced memory management with both short-term and long-term memory capabilities, enabling agents to learn from interactions and maintain context over extended periods. It includes robust knowledge-base management for structured storage and retrieval of domain knowledge, with support for versioning, evolution, and integration with external knowledge sources. For detailed documentation, see the [main documentation](opendxa/README.md).

## License

OpenDXA is released under the [MIT License](LICENSE.md).

## Related Concepts

OpenDXA integrates with and supports several key protocols in the AI and agent development space:

- **A2A (Agent-to-Agent)**: Google's framework for enabling direct communication and collaboration between AI agents, focusing on structured interactions and task delegation. OpenDXA supports A2A for agent communication and coordination.

- **MCP (Model Context Protocol)**: Anthropic's protocol for managing context and state in AI systems, providing a standardized way to handle conversation history and system state. OpenDXA implements MCP for robust context management.

- **NLIP (Natural Language Interface Protocol)**: ECMA's standard for natural language interfaces, defining how systems should interpret and respond to human language inputs. OpenDXA significantly leverages NLIP as a unified protocol to translate and federate between A2A, MCP, and other agentic communication protocols, enabling seamless interoperability between different agent frameworks.

These protocols form the foundation of OpenDXA's communication and collaboration capabilities, with NLIP serving as the unifying layer that enables protocol translation and federation.

## What is OpenDXA?

OpenDXA is a framework for building intelligent agents powered by Large Language Models (LLMs). Its architecture is built around a clear distinction between declarative and imperative aspects:

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

## Key Differentiators

### Business/Strategic Differentiators
1. **Declarative-Imperative Architecture**: Clear separation between what agents know and how they act, enabling better maintainability and scalability
2. **Knowledge Management**: Built-in support for structured knowledge management and evolution
3. **Domain Expertise Integration**: Specifically designed to embed domain expertise into agents, making it particularly valuable for specialized fields

### Engineering Approaches
1. **Progressive Complexity**: Start with simple implementations and progressively add complexity
2. **Composable Architecture**: Mix and match components as needed for highly customized agents
3. **Clean Separation of Concerns**: Maintain clear boundaries between description and execution layers

### User-Friendly Practices
1. **Model Context Protocol (MCP)**: Standardized interface for all external resources
2. **Built-in Best Practices**: Pre-configured templates and patterns for common behaviors
3. **Resource Management**: Robust handling with support for different transport types
4. **Comprehensive Testing Support**: Encourages thorough testing at each layer
5. **Documentation-First Approach**: Extensive documentation structure for effective use

## Getting Started

First things first, set up your development environment:

```bash
# Clone the repository
git clone git@github.com:aitomatic/opendxa.git
cd opendxa

# Set up development environment (includes virtual environment, dependencies, and pre-commit hooks)
source ./RUN_ME.sh

# Or if you just need to activate the virtual environment and install the package
source ./VENV.sh
```

## Contents

- [What is OpenDXA?](#what-is-opendxa)
- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Framework Comparison](#strategic-framework-selection-matrix)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Logging](#logging)

## Key Features

- **Domain Expertise Integration** - Embed expert knowledge into agent behavior
- **Progressive Complexity** - Start simple, scale to complex tasks
- **Composable Architecture** - Mix and match capabilities as needed
- **Built-in Best Practices** - Pre-configured templates for common patterns
- **Full Customization** - Complete control when needed

## Installation

```bash
git clone <repository-url>
cd opendxa
bash setup_env.sh
source venv/bin/activate  # Windows: source venv/Scripts/activate
```

Prerequisites:

- Python 3.x
- bash shell (Unix) or Git Bash (Windows)

## Quick Start

```python
# Simple Q&A
from opendxa.agent import Agent
from opendxa.agent.resource import LLMResource
answer = Agent().ask("What is quantum computing?")

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

## Documentation

- **[Framework Overview](opendxa/README.md)** - Detailed system architecture
- **[Examples](examples/README.md)** - Usage patterns and tutorials
- **[Agent Documentation](opendxa/agent/README.md)** - Agent components
- **[Execution Documentation](opendxa/execution/README.md)** - Workflow, Planning, and Reasoning

## Strategic Framework Selection Matrix

OpenDXA provides distinct advantages in several key areas when compared to other agent frameworks:

| Use Case | OpenDXA | LangChain | AutoGPT | BabyAGI |
|----------|-----|-----------|----------|----------|
| **Quick Start** | ✨ Template-based initialization | Direct chain construction | Command interface | Simple task queue |
| **Simple Tasks** | ✨ Pre-configured templates | Chain composition | Command sequences | Task scheduling |
| **Complex Tasks** | ✨ Full cognitive architecture | Multiple chains | Command sequences | Task recursion |
| **Domain Expertise** | ✨ Built-in expertise system | Tool integration | Command-based tools | Task-based tools |
| **Autonomous Operation** | ✨ Structured autonomy | Chain automation | Free-form commands | Task loops |
| **Growth Path** | ✨ Seamless capability expansion | Chain rebuilding | New commands | New tasks |

✨ = Optimal choice for category

### Framework Selection Guide

| Need | Best Choice | Why |
|------|-------------|-----|
| Fast Start | OpenDXA/LangChain | Equivalent simplicity with better growth |
| Simple Tasks | OpenDXA/LangChain | Standard patterns with full power available |
| Complex Systems | OpenDXA | Superior architecture and capabilities |
| Expert Systems | OpenDXA | Native expertise and knowledge integration |
| Autonomous Agents | OpenDXA/AutoGPT | Structured autonomy with better control |

### Implementation Complexity

| Framework | Initial | Growth | Maintenance |
|-----------|---------|--------|-------------|
| OpenDXA | Low | Linear | Low |
| LangChain | Low | Step Function | Medium |
| AutoGPT | Low | Limited | High |
| BabyAGI | Low | Limited | Medium |

## Project Structure

```text
opendxa/                # Project root
├── opendxa/            # Main package
│   ├── agent/          # Agent implementation
│   │   ├── capability/ # Agent capabilities (memory, expertise)
│   │   ├── resource/   # Agent-specific resources
│   │   ├── agent.py    # Core Agent class
│   │   ├── agent_factory.py  # Agent creation factories
│   │   ├── agent_runtime.py  # Agent execution runtime
│   │   └── agent_state.py    # Agent state management
│   ├── common/         # Shared utilities
│   │   ├── graph/      # Graph data structures
│   │   ├── io/         # Input/Output handlers
│   │   ├── resource/   # External resources
│   │   │   ├── mcp/    # Model Context Protocol
│   │   │   ├── llm_resource.py  # LLM integration
│   │   │   └── human_resource.py  # Human-in-the-loop
│   │   ├── state/      # State management
│   │   └── utils/      # Utility functions
│   │       └── logging/  # Logging system
│   │
│   └── execution/      # Execution system
│       ├── pipeline/   # Pipeline execution
│       ├── planning/   # Strategic planning
│       │   └── yaml/   # YAML-based plan templates
│       ├── reasoning/  # Reasoning implementation
│       │   └── yaml/   # YAML-based reasoning templates
│       └── workflow/   # Process workflows
│           └── yaml/   # YAML-based workflow templates
│
├── examples/           # Usage examples
│   ├── python/         # Python script examples
│   │   ├── 01_getting_started/  # Basic usage
│   │   ├── 02_core_concepts/    # Core architecture
│   │   ├── 03_advanced_patterns/  # Advanced usage
│   │   └── 04_real_world_applications/  # Real-world use cases
│   └── tutorials/      # Jupyter notebook tutorials
│       ├── 01_getting_started/  # Introduction
│       ├── 02_core_concepts/    # Core layers
│       ├── 03_advanced_topics/  # Advanced features
│       └── 04_real_world_applications/  # Industry applications
│
├── tests/              # Test suite
│
├── contrib/            # Experimental and contributed code
│   └── README.md       # Contrib directory guidelines
│
└── docs/               # Documentation
    └── requirements/   # Industry-specific requirements
```

## Contributing

OpenDXA is proprietary software developed by Aitomatic, Inc. Contributions are limited to authorized Aitomatic employees and contractors. If you're an authorized contributor:

1. Please ensure you have signed the necessary Confidentiality and IP agreements
2. Follow the internal development guidelines
3. Submit your changes through the company's approved development workflow
4. Contact the project maintainers for access to the internal Contributing Guide

For external users or organizations interested in collaborating with Aitomatic on OpenDXA development, please contact our business development team.

## License

This software is proprietary and confidential. Copyright © 2025 Aitomatic, Inc. All rights reserved.

Unauthorized copying, transfer, or reproduction of this software, via any medium, is strictly prohibited. This software is protected by copyright law and international treaties.

## Logging

### Basic Usage

```python
from opendxa.common import DXA_LOGGER

DXA_LOGGER.info("Application started")
DXA_LOGGER.log_llm(
    prompt="What is 2+2?",
    response="4",
    model="gpt-3.5"
)
```

### Advanced Configuration

```python
from opendxa.common import DXA_LOGGER

# Configure logging with options
DXA_LOGGER.configure(
    level=DXA_LOGGER.DEBUG,
    console=True,
    log_data=True
)

# Get logger instance
logger = DXA_LOGGER.getLogger(__name__)

# Log execution signals
def process_signals(signals):
    for signal in signals:
        logger.debug("Processing signal: %s", signal)
```

### Signal Processing

```python
from opendxa.execution import ExecutionSignal

def process_execution_results(signals: list[ExecutionSignal]):
    results = {}
    for signal in signals:
        if hasattr(signal, 'content') and 'result' in signal.content:
            results[signal.content.get('node')] = signal.content['result']
    return results
```

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the MIT License.
</p>

<p align="center">
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>

## Interaction Patterns

### Basic Interaction Pattern

The heart of OpenDXA is a consistent Planning-Knowledge interaction pattern:

1. **Basic Interaction Loop**:
   - Planning asks Knowledge: "How to solve X?"
   - Knowledge responds with one of three types:
     a. **Complete Solution** (Terminal)
        * Direct answer available in knowledge base
        * No further decomposition needed
        * Ready for immediate execution
     b. **Decomposable Solution** (Recursive)
        * Solution exists but requires multiple steps
        * Each step may need further resolution
        * Natural hierarchical decomposition
     c. **Incomplete Solution** (Fallback)
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
    A[Agent] --> K1[Medical Knowledge]
    A --> K2[Legal Knowledge]
    A --> K3[Technical Knowledge]
    
    K1 --> KB1[Medical Knowledge Base]
    K1 --> KB2[Patient Records]
    
    K2 --> KB3[Legal Database]
    K2 --> KB4[Case Law]
    
    K3 --> KB5[Technical Documentation]
    K3 --> KB6[Code Repository]
```
