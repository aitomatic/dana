<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[◀ REPL](./repl.md) | [DANA ▶︎](./dana.md)

# DANA Transcoder

**Module**: `opendxa.dana.transcoder`

This document describes the DANA Transcoder module, which provides translation between natural language and DANA code, as well as interfaces for programmatic compilation and narration.

## Overview

The DANA Transcoder enables two-way translation:
- **Natural Language → DANA Code**: Converts user objectives or instructions into valid DANA programs using LLMs.
- **DANA Code → Natural Language**: Generates human-readable explanations of DANA programs.

This is achieved through a modular architecture with clear interfaces for extensibility and integration with LLMs.

## Main Components

- **Transcoder**: Main class for NL↔︎DANA translation. Uses an LLM resource and the DANA parser.
- **CompilerInterface**: Abstract interface for compilers that generate DANA ASTs from NL objectives.
- **NarratorInterface**: Abstract interface for narrators that generate NL descriptions from DANA ASTs.

## Transcoder Flow

**Natural Language to DANA Code:**

- `Transcoder.to_dana()`

```mermaid
graph LR
    NL[[Natural Language]] --> T[Transcoder]
    T --> DANA[[DANA Code]]
    style NL fill:#f9f,stroke:#333
    style DANA fill:#bff,stroke:#333
```

- `Compiler.compile()`

```mermaid
graph LR
    NL[[Natural Language]] --|compile|--> C[Compiler]
    C --|parse|--> AST[[DANA AST]]
    AST --> DANA[[DANA Code]]
    style NL fill:#f9f,stroke:#333
    style DANA fill:#bff,stroke:#333
``` 

**DANA Code to Natural Language:**

- `Transcoder.to_natural_language()`

```mermaid
graph LR
    DANA[[DANA Code]] --> T[Transcoder]
    T --> NL[[Natural Language]]
    style NL fill:#f9f,stroke:#333
    style DANA fill:#bff,stroke:#333
```

- `Narrator.narrate()`

```mermaid
graph LR
    DANA[[DANA Code]] --|parse|--> AST[[DANA AST]]
    AST --> N[Narrator]
    N --|explanation|--> NL[[Natural Language]]
    style NL fill:#f9f,stroke:#333
    style DANA fill:#bff,stroke:#333
```