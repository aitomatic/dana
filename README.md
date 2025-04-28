<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Main Documentation](docs/README.md)

# OpenDXA - Domain-Expert Agent Framework

## Overview

OpenDXA is a Python framework that enables building intelligent multi-agent systems with domain expertise, powered by Large Language Models (LLMs). It focuses on:

*   **Build Real Experts:** (Using your specific business knowledge - *Domain Expertise Integration*)
*   **Unlock Company Knowledge:** (Connect to your existing data & docs - *Enterprise Knowledge Leverage*)
*   **Manage Evolving Knowledge:** (Smart handling that keeps info current - *Adaptive Knowledge Management*)
*   **Agents That Learn & Improve:** (Get better automatically over time - *Agent Learning & Adaptability*)
*   **Reliable Answers from Your Data:** (Focus on accuracy & consistency - *Structured Knowledge Reliability*)
*   **Clear Design (Know vs. Act):** (Easier to build & maintain - *Declarative + Imperative Architecture*)
*   **Connect Different AI Systems:** (Works well with other tools/platforms - *Protocol Federation/NLIP*)

To immediately leverage domain expertise, you can also utilize Aitomatic's separate open-source [Domain Knowledge Base project]([link-to-knowledge-base-repo]) (provides both general technical knowledge and specific domain expertise, e.g., SOPs, taxonomies, specs), which is compatible with any agent framework, including OpenDXA.

For detailed documentation on the OpenDXA framework itself, see the [main documentation](docs/README.md).

> "The real race in AI is the race to get right context to have AI Agents solve the user's problem fully. Organizing or indexing the right data, understanding a domain deeply, getting enough activity for useful memory, and connecting to the right tools. This is the big prize."
> 
> — Aaron Levie, CEO of Box

> "Domain expertise is key. It's the efficiency of focus."
> 
> — Christopher Nguyen, CEO of Aitomatic

## License

OpenDXA is released under the [MIT License](LICENSE.md).

## Why OpenDXA?

OpenDXA stands out by enabling you to build truly expert agents grounded in your specific domain knowledge.

### For Business Users:

*   **Leverage Your *Existing* Knowledge Accurately:** Build agents that tap into your company's documents, databases, and expertise – *how?* using connectors and ingestion tools – ensuring relevance and high fidelity crucial for industrial or financial accuracy.
*   **Embed Deep Domain Expertise:** Go beyond generic AI. Create reliable agents that understand and apply your specialized processes and terminology – *how?* through structured knowledge representation and rule definition – for consistent, compliant results.
*   **Comprehensive & Adaptive Knowledge Management:** Manage the full lifecycle of knowledge. Build agents that learn and adapt as your knowledge base evolves – *how?* via built-in versioning, evolution tracking, and learning mechanisms – maintaining long-term value.
*   **True Interoperability:** Seamlessly connect agents and systems, even those based on different underlying standards (like A2A, MCP) – *how?* by using NLIP as a translation layer – preventing vendor lock-in.

### For Engineering Users:

*   **Integrate Diverse Enterprise Knowledge Sources:** Connect to and represent knowledge from various existing enterprise sources (docs, DBs, APIs) – *how?* using provided APIs and connectors designed for enterprise data formats – simplifying data integration.
*   **Robust & Maintainable Architecture:** The clear separation between *what* an agent knows (declarative) and *how* it acts (imperative) – *how?* enforced by distinct framework modules – facilitates building complex, testable, reliable, and scalable systems, especially with structured knowledge.
*   **Built-in Tools for Advanced Knowledge Management:** Utilize dedicated APIs for the full knowledge lifecycle (capture, structure, versioning, evolution, query) – *how?* through specific classes like `KnowledgeBase` and related utilities – supporting both structured and conceptual data for accuracy and consistency.
*   **Framework Support for Controlled Learning:** Implement agent learning grounded in updates to the managed knowledge base – *how?* via patterns linking feedback loops to knowledge update mechanisms – enabling adaptation while maintaining consistency.
*   **Solve Multi-Protocol Interoperability (NLIP Federation):** Leverage the NLIP implementation – *how?* through specific adapters and translators provided within the framework – to bridge communication between agents built on different standards (A2A, MCP).

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

For detailed architecture, core concepts, framework comparisons, and advanced usage, please see the **[Main Framework Documentation](docs/README.md)**.

Further documentation:

- **[Examples](examples/README.md)** - Usage patterns and tutorials
- **[Agent Documentation](opendxa/agent/README.md)** - Agent components
- **[Execution Documentation](opendxa/execution/README.md)** - Workflow, Planning, and Reasoning

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

## Support

For questions or support, please open an issue on the [GitHub repository](https://github.com/aitomatic/opendxa/issues).

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>

