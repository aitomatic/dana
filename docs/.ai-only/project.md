# OpenDXA Project Structure

This document provides an overview of the OpenDXA (Domain-eXpert Agent) Framework project structure, including key directories and configuration files.

## Directory Structure

```
opendxa/                         # Main package root
├── agent/                       # Agent system implementation
├── common/                      # Shared utilities and base classes
│   ├── config/                  # Configuration utilities
│   ├── mixins/                  # Reusable mixin classes
│   ├── resource/                # Base resource system
│   └── utils/                   # Utility functions
├── contrib/                     # Contributed modules and examples
├── dana/                        # Domain-Aware NeuroSymbolic Architecture
│   ├── repl/                    # Interactive REPL implementation
│   ├── sandbox/                 # Dana sandbox environment
│   │   ├── interpreter/         # Dana interpreter components
│   │   └── parser/              # Dana language parser
│   └── transcoder/              # NL to code translation
└── danke/                       # Domain-Aware NeuroSymbolic Knowledge Engine

bin/                            # Executable scripts and utilities

docs/                           # Project documentation
├── for-engineers/              # Practical guides, recipes, and references for developers
│   ├── setup/                  # Installation, configuration, migration guides
│   ├── recipes/                # Real-world examples and patterns
│   ├── reference/              # Language and API documentation
│   └── troubleshooting/        # Common issues and solutions
├── for-evaluators/             # Business and technical evaluation
│   ├── comparison/             # Competitive analysis and positioning
│   ├── roi-analysis/           # Cost-benefit and ROI calculations
│   ├── proof-of-concept/       # Evaluation and testing guides
│   └── adoption-guide/         # Implementation and change management
├── for-contributors/           # Development and extension guides
│   ├── architecture/           # System design and implementation
│   ├── codebase/              # Code navigation and understanding
│   ├── extending/             # Building capabilities and resources
│   └── development/           # Contribution and testing guidelines
├── for-researchers/            # Theoretical and academic content
│   ├── manifesto/             # Vision and philosophical foundations
│   ├── neurosymbolic/         # Technical and theoretical analysis
│   ├── research/              # Research opportunities and collaboration
│   └── future-work/           # Roadmap and future directions
├── archive/                    # Preserved original documentation
│   ├── original-dana/         # Original Dana language documentation
│   ├── original-core-concepts/ # Original core concepts documentation
│   └── original-architecture/ # Original architecture documentation
├── internal/                   # Internal planning and requirements
└── .ai-only/                  # AI assistant reference materials

examples/                       # Example code and tutorials
├── 01_getting_started/         # Basic examples for new users
├── 02_core_concepts/           # Core concept demonstrations
├── 03_advanced_topics/         # Advanced usage patterns
└── 04_real_world_applications/ # Real-world applications

tests/                          # Test suite
├── agent/                      # Agent tests
├── common/                     # Common utilities tests
├── dana/                       # Dana language tests
│   ├── repl/                   # REPL tests
│   ├── sandbox/                # Sandbox environment tests
│   │   ├── interpreter/        # Interpreter tests
│   │   └── parser/             # Parser tests
│   └── transcoder/             # Transcoder tests
└── execution/                  # Execution flow tests
```

### Key Configuration Files

#### `pyproject.toml`

Defines project dependencies and development tools using modern Python packaging standards.

#### `SOURCE_ME.sh`

Sets up the environment by installing dependencies and configuring paths.

- Uses uv sync to install dependencies from pyproject.toml
- Sets up the Python environment
- Configures PATH for Dana executables

#### `.env.example` (if present)
Example environment variable configuration for local development.

## Project Overview

OpenDXA is a comprehensive framework for building intelligent multi-agent systems with domain expertise, powered by Large Language Models (LLMs). It consists of two main components:

1. **Dana (Domain-Aware NeuroSymbolic Architecture)**: An imperative programming language and execution runtime for agent reasoning. Key components include:
   - **Parser**: Converts Dana source code into an Abstract Syntax Tree (AST) using a formal grammar
   - **Interpreter**: Executes Dana programs by processing the AST with optimized reasoning functions
   - **Sandbox**: Provides a safe execution environment with controlled state management
   - **Transcoder**: Translates between natural language and Dana code
   - **REPL**: Interactive environment for executing Dana code

2. **DANKE (Domain-Aware NeuroSymbolic Knowledge Engine)** *(Planned)*: A knowledge management system that will implement the CORRAL methodology (Collect, Organize, Retrieve, Reason, Act, Learn). Currently in early development stages.

The framework enables building domain-expert agents with clear, auditable reasoning steps and the ability to apply specialized knowledge to solve complex tasks across different domains. 

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>