<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../README.md)

# OpenDXA - Powered by DANA

**Example: DANA agentic program**
```dana
# Local solve: ask for a diagnosis based on temperature
cause = local.solve(f"Diagnose the cause of high temperature: {temp}")

# Remote solve: ask another expert agent for a solution
fix = ai.hvac_expert_agent.solve(f"Suggest a fix for high temperature: {temp}, {cause}")

# Remote plan: get a troubleshooting plan from another agent
plan = ai.hvac_service_agent.plan(f"Plan steps to resolve high temperature: {temp}, {cause}, {fix}")

if is_safe(plan):
  # Execute on the plan
  result = execute(plan)
```

**Example: DANA agentic program (Finance Use Case)**
```dana
import aitomatic as ai

# Obtain applicant's credit score using a remote AI/agent
applicant.credit_score = ai.credit_agent.score(applicant)

# Local reasoning: log and check risk
if applicant.credit_score < 600:
    log(f"Low credit score detected: {applicant.credit_score}")
    # Ask a local function for a risk assessment
    applicant.risk = local.assess_risk(f"Assess risk for credit score: {applicant}")

    # Ask a remote finance expert agent for a recommendation
    recommendation = ai.finance_agent.recommend(f"Should we approve a loan for credit score: {applicant}?")

    # Log the recommendation
    log(f"Finance expert recommendation: {recommendation}")
else:
    log("Credit score is sufficient for standard processing")
```

**Note:**
In DANA, method calls like `credit_scoring_agent.score(applicant)` are automatically converted to a generic agentic call:
```dana
credit_scoring_agent.solve("Score this applicant", applicant)
```
This standardizes agent/service interactions in a human-readable, LLM-friendly way, allowing agents to expose their capabilities as a structured API, or as prompt-driven functions.

OpenDXA is the first agent framework enabled by the **DANA Language** and **DANA Sandbox**—a neurosymbolic programming environment that lets Agentic AI Engineers build, test, and share agent logic as straightforward, readable programs. 

**With DANA, you don't have to deal with boilerplate code or infrastructure paradigms like links, nodes, or graphs. You just write agent logic—clear, expressive, and powerful—like you always have.**

DANA's neurosymbolic architecture gives you the best of both worlds: the flexibility and fault-tolerance of natural language, and the determinism, explainability, and auditability of symbolic programming. 

Agents communicate and share executable knowledge (how-tos) via DANA, enabling a new era of programmable, collaborative AI. The **DANA Sandbox** provides an interactive playground for rapid development, debugging, and experimentation—making agentic AI accessible and productive for every engineer.

> **Try it now:**  
> - [DANA Sandbox Guide](dana/sandbox.md)  
> - [DANA Language Reference](dana/language.md)

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

For our development plans and future capabilities, see the [Development Roadmap](ROADMAP.md).

To immediately leverage domain expertise, you can also utilize Aitomatic's separate open-source [Domain Knowledge Base project]([link-to-knowledge-base-repo]) (provides both general technical knowledge and specific domain expertise, e.g., SOPs, taxonomies, specs), which is compatible with any agent framework, including OpenDXA.

> "The real race in AI is the race to get right context to have AI Agents solve the user's problem fully. Organizing or indexing the right data, understanding a domain deeply, getting enough activity for useful memory, and connecting to the right tools. This is the big prize."
>
> — Aaron Levie, CEO of Box

> "Domain expertise is key. It's the efficiency of focus."
>
> — Christopher Nguyen, CEO of Aitomatic

## 🚀 DANA Language & Sandbox: The Heart of OpenDXA Reasoning

OpenDXA's reasoning, planning, and tool use are powered by the **DANA Language** — a minimal, interpretable, and LLM-friendly program format. DANA enables agents to reason, act, and collaborate through structured, auditable programs.

**DANA Sandbox** provides an interactive playground for:
- Authoring and testing DANA programs
- Debugging agent logic step-by-step
- Experimenting with new reasoning patterns

> **Try it now:**  
> - [DANA Sandbox Guide](dana/sandbox.md)  
> - [DANA Language Reference](dana/language.md)

**Example DANA program:**
```dana
public.temp = 42
if public.temp > 40:
    log("High temperature detected!")
```

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
- **DANA Language** – Minimal, interpretable, and LLM-friendly program format for agent reasoning and tool use
- **DANA Sandbox** – Interactive playground for authoring, testing, and debugging DANA programs

## Key Differentiators

### Business/Strategic Differentiators
1. **Declarative-Imperative Architecture**: Clear separation between what agents know and how they act
2. **Knowledge Management**: Built-in support for structured knowledge management and evolution
3. **Domain Expertise Integration**: Specifically designed to embed domain expertise into agents
4. **DANA Language & Sandbox**: Core to agent reasoning, with interactive authoring and debugging

### Engineering Approaches
1. **Progressive Complexity**: Start with simple implementations and progressively add complexity
2. **Composable Architecture**: Mix and match components as needed for highly customized agents
3. **Clean Separation of Concerns**: Maintain clear boundaries between description and execution layers
4. **DANA as Reasoning Core**: All agent logic and tool use is expressed in DANA, testable in the Sandbox

For detailed framework comparisons, see [Framework Comparison](details/comparison.md).

## Documentation Map

- **Getting Started**
  - [Quick Start](getting-started/quickstart.md) - Your first OpenDXA agent
  - [Core Concepts](getting-started/core-concepts.md) - Fundamental concepts
  - [Examples](../../examples/README.md) - Usage patterns and tutorials
  - [Try DANA in the Sandbox](dana/sandbox.md)

- **DANA Language & Sandbox**
  - [DANA Language Reference](dana/language.md)
  - [DANA Sandbox Guide](dana/sandbox.md)
  - [DANA Syntax Reference](dana/syntax.md)
  - [DANA Examples](../examples/01_getting_started/)

- **Development Roadmap**
  - [Roadmap](ROADMAP.md) - Planned development path and future capabilities

- **Architecture**
  - [Overview](architecture/overview.md) - Core concepts and design
  - [Declarative-Imperative](architecture/declarative-imperative.md) - Key architectural differentiator
  - [Framework Comparison](architecture/comparison.md) - Comparison with other frameworks

- **Knowledge Management**
  - [Knowledge Management](knowledge/management.md) - Managing knowledge lifecycle
  - [Domain Expertise](knowledge/domain-expertise.md) - Integrating domain knowledge
  - [Knowledge Lifecycle](knowledge/lifecycle.md) - Evolution and versioning

- **Components**
  - [Agents](components/agents.md) - Agent factory and core concepts
  - [Capabilities](components/capabilities.md) - BaseCapability interface
  - [Resources](components/resources.md) - BaseResource and types

- **Execution**
  - [Base Execution](execution/base.md) - Core execution interfaces
  - [Planning](execution/planning.md) - Strategic planning patterns
  - [Reasoning](execution/reasoning.md) - Tactical execution patterns
  - [Pipeline](execution/pipeline.md) - Detailed concepts and usage

- **Development**
  - [Patterns](development/patterns/)
    - [Composition](development/patterns/composition.md) - Building with components
    - [Interaction](development/patterns/interaction.md) - Agent communication
  - [State Management](development/state.md) - Execution state
  - [Logging](development/logging.md) - Configuration and usage

## Contributing

DXA is proprietary software developed by Aitomatic, Inc. Contributions are limited to authorized Aitomatic employees and contractors. If you're an authorized contributor:

1. Please ensure you have signed the necessary Confidentiality and IP agreements
2. Follow the internal development guidelines
3. Submit your changes through the company's approved development workflow
4. Contact the project maintainers for access to the Contributing Guide

For external users or organizations interested in collaborating with Aitomatic on DXA development, please contact our business development team.

---

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
