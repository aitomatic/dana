<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../README.md) | [Main Documentation](../docs/README.md)

# OpenDXA Design Documentation
This directory contains the authoritative design specifications for OpenDXA and the Dana language. These documents define the architecture, implementation details, and design decisions that guide the project.

## Organization

### Dana Language Design (`dana/`)
Core language specifications and design principles:

- **[Overview](dana/overview.md)** - Dana architecture and vision overview

- **[Language Specification](dana/language.md)** - Complete Dana language specification

- **[Syntax Reference](dana/syntax.md)** - Dana syntax rules and patterns

- **[Grammar Definition](dana/grammar.md)** - Formal grammar specification

- **[Manifesto](dana/manifesto.md)** - Philosophy and vision for Dana

- **[Design Principles](dana/design-principles.md)** - Core design principles

- **[Auto Type Casting](dana/auto-type-casting.md)** - Type system design

### System Architecture
Core system design and implementation:

- **[System Overview](system-overview.md)** - High-level architecture overview

- **[Interpreter](interpreter.md)** - Dana interpreter design and implementation

- **[Sandbox](sandbox.md)** - Execution sandbox design

- **[REPL](repl.md)** - Read-Eval-Print Loop design

- **[Functions](functions.md)** - Function system architecture

### Language Implementation
Parser and execution engine design:

- **[Parser](parser.md)** - Parser design and implementation

- **[AST](ast.md)** - Abstract Syntax Tree design

- **[AST Validation](ast-validation.md)** - AST validation procedures

- **[Transformers](transformers.md)** - AST transformation pipeline

- **[Transcoder](transcoder.md)** - Code transcoding system

- **[Type Checker](type-checker.md)** - Type checking system

### Core Concepts (`core-concepts/`)
Fundamental system concepts and patterns:

- **[Architecture](core-concepts/architecture.md)** - System architecture patterns

- **[Agent](core-concepts/agent.md)** - Agent system design

- **[Capabilities](core-concepts/capabilities.md)** - Capability system

- **[Execution Flow](core-concepts/execution-flow.md)** - Execution model

- **[State Management](core-concepts/state-management.md)** - State handling

- **[Mixins](core-concepts/mixins.md)** - Mixin pattern implementation

- **[Resources](core-concepts/resources.md)** - Resource management

- **[Conversation Context](core-concepts/conversation-context.md)** - Context handling


## Document Status

All documents in this directory are **active design specifications** that define the current and planned implementation of OpenDXA. These are the authoritative sources for:

- Language syntax and semantics
- System architecture decisions
- Implementation patterns and best practices
- Design rationale and trade-offs

## For Contributors

When modifying OpenDXA:

1. **Check relevant design docs** before making changes

2. **Update design docs** when making architectural changes

3. **Follow established patterns** documented here

4. **Maintain consistency** with design principles

## For Users

These documents provide deep technical insight into:

- How Dana language features work
- Why specific design decisions were made
- How to extend or integrate with OpenDXA
- Understanding system behavior and limitations

---

**See Also:**
- [User Documentation](../for-engineers/) - Practical guides and recipes
- [API Reference](../for-engineers/reference/) - Complete API documentation
- [Architecture Guide](../for-contributors/architecture/) - Implementation details 

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
