# Dana System Architecture

> **⚠️ IMPORTANT FOR AI CODE GENERATORS:**
> Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
> NEVER use dot notation: `private.x`, `public.x`, etc.
> Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.

## Overview

Dana is a comprehensive system for building intelligent multi-agent systems with domain expertise, powered by Large Language Models (LLMs). It focuses on enabling the creation of agents that can effectively apply specialized knowledge to solve complex tasks across different domains.

## Core Components

### 1. Dana Language (Domain-Aware NeuroSymbolic Architecture)

Dana is an imperative programming language and execution runtime that forms the heart of the system:

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
- Controlled LLM reasoning integration with optimized execution
- State management and scope enforcement
- Tool and knowledge base integration
- Execution monitoring and logging

### 2. POET (Probabilistic Orchestration of Execution Trees)

POET is the probabilistic execution framework that enables:
- **Fault Tolerance**: Automatic retry and recovery mechanisms
- **Determinism**: Consistent behavior despite probabilistic elements
- **Learning**: Adaptation based on execution history and outcomes
- **Domain Integration**: Specialized knowledge for specific problem domains

### 3. Agent Framework

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

# Perform reasoning
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

Dana excels at embedding expert knowledge into agent behavior:
- Structured representation of domain expertise
- Explicit reasoning with domain context
- Integration with existing knowledge sources
- Support for evolving knowledge over time

### Declarative + Imperative Architecture

Dana combines:
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
- **Protocol Federation**: Interoperability between agent communication standards

## Use Cases

Dana is particularly well-suited for:
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