# OpenDXA and Dana Design Documentation

This directory contains the authoritative design specifications for the OpenDXA framework and the Dana language. These documents define the agent-native architecture that enables the convergence of AI coding assistance with autonomous execution, implementation details, and design decisions that guide the project.

## Organization

The design documents are organized into the following main sections:

1. **Dana Philosophy**: Core vision, goals, and guiding principles behind agent-native Dana and the convergence paradigm.
2. **Dana Language Specification**: Detailed definition of the agent-native Dana language itself – syntax, semantics, data types, functions, state management, context-aware execution, and pipeline composition.
3. **Dana Runtime and Execution**: How Dana code is executed within the agent-native runtime that bridges development and production, including the interpreter, sandbox, REPL, and the core **POET (Perceive → Operate → Enforce → Train) execution model**.
4. **Core Capabilities and Resources**: Core capabilities and resources abstraction model for Dana programs to interact with internal and external functionalities in multi-agent environments with context-aware adaptation.
5. **Agent and Orchestration**: Higher-level constructs for building intelligent agents and orchestrating complex workflows using Dana's agent-native features, self-improving pipelines, and convergence architecture.
6. **Tooling and Developer Experience**: Developer tools, IDE integration, debugging, testing frameworks, and other developer experience improvements for agent-native development that unifies assistance with autonomous execution.
7. **API Server Architecture**: [Dana API Server Architecture](06_api_server_architecture.md) — Design and implementation of the local API server for agent management and web integration.

## Document Status

All documents in this directory (outside of `archive/`) are considered **active design specifications**. They define the current and planned implementation of Dana and its role within OpenDXA. These are the authoritative sources for:

- Dana language syntax and semantics
- System architecture decisions related to Dana
- Implementation patterns and best practices for Dana components
- Design rationale and trade-offs

## For Contributors

When modifying Dana or its related OpenDXA components:

1. **Consult relevant design documents** before making changes.
2. **Update design documents** when making architectural or significant behavioral changes.
3. **Follow established patterns** and principles documented here.
4. **Maintain consistency** with the overall design philosophy.

## For Users & Developers

These documents provide deep technical insight into:

- How Dana language features work internally.
- The rationale behind specific design decisions.
- How to extend or integrate with Dana and OpenDXA at a deeper level.
- Understanding system behavior and limitations.

---

See Also:

- User-facing documentation (e.g., in `docs/for-engineers/`, `docs/for-contributors/`)