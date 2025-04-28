<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../README.md)

# OpenDXA - Domain-Expert Agent Framework Documentation

This document provides a detailed overview of the OpenDXA framework's architecture, core concepts, features, and design philosophy. For a quick start and installation instructions, please refer to the project's [README.md](../README.md).

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

> "The real race in AI is the race to get right context to have AI Agents solve the user's problem fully. Organizing or indexing the right data, understanding a domain deeply, getting enough activity for useful memory, and connecting to the right tools. This is the big prize."
> 
> — Aaron Levie, CEO of Box

> "Domain expertise is key. It's the efficiency of focus."
> 
> — Christopher Nguyen, CEO of Aitomatic

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

## Core Concepts

OpenDXA is built around two fundamental aspects:

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

For detailed architecture information, see [Architecture Documentation](details/architecture.md).

## Key Features

- **Domain Expertise Integration** - Embed expert knowledge into agent behavior
- **Adaptive Knowledge Management** - Support for knowledge lifecycle including evolution and versioning
- **Declarative + Imperative Architecture** - Clear separation of knowledge and action for robust design
- **Agent Learning & Adaptability** - Mechanisms for agents to improve over time
- **Protocol Federation (NLIP)** - Interoperability between different agent communication standards
- **Progressive Complexity** - Start simple, scale to complex tasks
- **Composable Architecture** - Mix and match capabilities as needed
- **Built-in Best Practices** - Pre-configured templates for common patterns
- **Full Customization** - Complete control when needed

## Key Differentiators

### Business/Strategic Differentiators
1. **Declarative-Imperative Architecture**: Clear separation between what agents know and how they act
2. **Knowledge Management**: Built-in support for structured knowledge management and evolution
3. **Domain Expertise Integration**: Specifically designed to embed domain expertise into agents

### Engineering Approaches
1. **Progressive Complexity**: Start with simple implementations and progressively add complexity
2. **Composable Architecture**: Mix and match components as needed for highly customized agents
3. **Clean Separation of Concerns**: Maintain clear boundaries between description and execution layers

For detailed framework comparisons, see [Framework Comparison](details/comparison.md).

## Documentation Map

- **Architecture**
  - [Architecture Overview](details/architecture.md) - Core concepts and design
  - [Interaction Patterns](details/interaction_patterns.md) - Agent communication and workflows

- **Framework Comparison**
  - [Framework Comparison](details/comparison.md) - Comparison with other frameworks

- **Framework Core**
  - [Base Execution Concepts](details/base_execution.md) - Core execution interfaces and structures

- **Agent System**
  - [Agent Core Concepts](details/agent_system.md) - Agent factory, core concepts (Agent, Capability, Resource)
  - [Capability Concepts](details/capability_system.md) - BaseCapability interface and concepts
  - [Resource Concepts](details/resource_system.md) - BaseResource, common types, MCP integration
  - [IO System](../opendxa/common/io/README.md) - Environmental interaction
  - [State System](../opendxa/base/state/README.md) - Execution state management

- **Execution System**
  - [Planning Concepts](details/planning_system.md) - Strategic planning patterns and concepts
  - [Reasoning Concepts](details/reasoning_system.md) - Tactical execution patterns and concepts
  - [Pipeline Module Overview](../opendxa/execution/pipeline/README.md) - Module-level documentation
  - [Pipeline System Concepts](details/pipeline_system.md) - Detailed concepts and usage

- **Utilities**
  - [Logging](details/logging.md) - Logging configuration and usage
  - [Mixins](details/mixins.md) - Reusable component functionalities

- [Examples](../../examples/README.md) - Usage patterns and tutorials

## Contributing

DXA is proprietary software developed by Aitomatic, Inc. Contributions are limited to authorized Aitomatic employees and contractors. If you're an authorized contributor:

1. Please ensure you have signed the necessary Confidentiality and IP agreements
2. Follow the internal development guidelines
3. Submit your changes through the company's approved development workflow
4. Contact the project maintainers for access to the Contributing Guide

For external users or organizations interested in collaborating with Aitomatic on DXA development, please contact our business development team.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
