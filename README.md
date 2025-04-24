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

OpenDXA is a framework for building intelligent agents powered by Large Language Models (LLMs). Its architecture is built around a clear distinction between description and execution:

1. **Description Layer**
   - Defines what the agent knows and can do
   - Manages knowledge bases and capabilities
   - Handles domain expertise and resources
   - Provides structured access to agent capabilities

2. **Execution Layer**
   - Implements planning and reasoning
   - Executes tasks using available capabilities
   - Manages state and context
   - Coordinates multi-agent interactions

This architecture is complemented by built-in knowledge-base management, enabling:
- Structured storage and retrieval of domain knowledge
- Versioning and evolution of knowledge bases
- Integration with external knowledge sources
- Efficient querying and reasoning over knowledge

```mermaid
graph TB
    subgraph "Description Layer"
        KB[Knowledge Base]
        C[Capabilities]
        E[Expertise]
        R[Resources]
    end

    subgraph "Execution Layer"
        P[Planning]
        RE[Reasoning]
        S[State]
    end

    KB --> P
    C --> P
    E --> RE
    R --> RE
    P --> RE
    RE --> S
    S --> P
```

This architecture means you can:
- Start with simple knowledge bases and capabilities
- Gradually expand domain expertise
- Scale to complex multi-agent systems
- Maintain clear separation between what agents know and how they act

## Key Differentiators

### Business/Strategic Differentiators
1. **Description-Execution Architecture**: Clear separation between what agents know and how they act, enabling better maintainability and scalability
2. **Knowledge-Base Management**: Built-in support for structured knowledge management and evolution
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
