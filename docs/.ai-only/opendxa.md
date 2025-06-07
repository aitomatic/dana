# OpenDXA (Domain-eXpert Agent) Framework

> **⚠️ IMPORTANT FOR AI CODE GENERATORS:**
> Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
> NEVER use dot notation: `private.x`, `public.x`, etc.
> Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.

## Overview

OpenDXA is a comprehensive framework for building intelligent multi-agent systems with domain expertise, powered by Large Language Models (LLMs). It focuses on enabling the creation of agents that can effectively apply specialized knowledge to solve complex tasks across different domains.

## Core Components

### 1. Dana (Domain-Aware NeuroSymbolic Architecture)

Dana is an imperative programming language and execution runtime that forms the heart of the OpenDXA framework:

- **Universal Program Format**: A simple, deterministic language for expressing agent behaviors
- **Imperative Execution Model**: Clear control flow and state management
- **Structured State Management**: Four standard scopes for variable management:
  - `private:` - Agent-specific internal state
  - `public:` - Shared world state and observations
  - `system:` - Runtime configuration and execution state
  - `local:` - Function-specific temporary state (default scope for unscoped variables)
- **First-Class Reasoning**: Native LLM integration with the `reason()` statement
- **Function Composition**: Pipe operator (`|`) for creating reusable function pipelines
- **Module System**: Import Dana and Python modules with namespace support

Dana programs are executed by the Dana interpreter, which provides:
- Deterministic execution of standard operations
- Controlled LLM reasoning integration with IPV (Infer-Process-Validate) optimization
- State management and scope enforcement
- Tool and knowledge base integration
- Execution monitoring and logging

### 2. DANKE (Domain-Aware NeuroSymbolic Knowledge Engine) - Planned

DANKE is the planned knowledge management system that will implement the CORRAL methodology:
- **C**ollect: Gather and ingest domain knowledge
- **O**rganize: Structure and index knowledge
- **R**etrieve: Access and search for relevant knowledge
- **R**eason: Infer, contextualize, and generate insights
- **A**ct: Apply knowledge to take actions and solve problems
- **L**earn: Integrate feedback and improve knowledge over time

*Note: DANKE is currently in early development stages and not yet fully implemented.*

### 3. OpenDXA Framework Core

The framework orchestrates Dana components, providing:
- Agent lifecycle management
- Multi-agent coordination
- Tool integration and execution
- Resource management

## Key Differentiators

### Imperative Programming Model

Dana uses a clear, imperative programming model that developers find familiar and easier to reason about:

```dana
# Example Dana program
user_name = "Alice"  # Auto-scoped to local (preferred)
public:weather_temperature = 72

# Perform reasoning with IPV optimization
analysis = reason("Should we recommend a jacket?",
                       {"context": [user_name, public:weather_temperature]})

# Take action based on reasoning
if analysis == "yes":
    print("Recommend wearing a jacket")
else:
    print("No jacket needed")
```

This imperative approach provides:
- Clear execution flow and predictable behavior
- Easily auditable reasoning steps
- Traceable state changes
- Familiar control structures (if/else, loops)
- Function composition for building complex pipelines

### Domain Expertise Integration

OpenDXA excels at embedding expert knowledge into agent behavior:
- Structured representation of domain expertise
- Explicit reasoning with domain context
- Integration with existing knowledge sources
- Support for evolving knowledge over time

### Declarative + Imperative Architecture

OpenDXA combines:
- **Declarative Knowledge**: What the agent knows (domain facts, rules)
- **Imperative Execution**: How the agent acts (control flow, state changes)

This separation enables building maintainable, testable, and reliable agent systems.

## Architecture Flow

```
User Request
    ↓
Agent → Planning Layer → Dana Program Generation
    ↓
Dana Interpreter
    ↓
Statement Execution
    ↓
Function/Tool Calls → Resource Access
    ↓
State Management
    ↓
Response/Action
```

The agent receives a request, plans a response using Dana, executes the Dana program through the interpreter, which manages state and calls appropriate tools or resources, ultimately generating a response or taking action.

## Key Features

- **Domain Expertise Integration**: Embed expert knowledge into agent behavior
- **Adaptive Knowledge Management**: Support for knowledge lifecycle including evolution
- **Declarative + Imperative Architecture**: Clear separation of knowledge and action
- **Agent Learning & Adaptability**: Mechanisms for agents to improve over time
- **Protocol Federation (NLIP)**: Interoperability between agent communication standards

## Use Cases

OpenDXA is particularly well-suited for:
- Semiconductor manufacturing diagnostics
- Financial services automation
- Healthcare decision support
- Enterprise knowledge management
- Technical support automation
- Complex workflow orchestration

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>