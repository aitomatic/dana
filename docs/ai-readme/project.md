<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)

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
│   ├── sandbox/                 # DANA sandbox environment
│   │   ├── interpreter/         # DANA interpreter components
│   │   └── parser/              # DANA language parser
│   └── transcoder/              # NL to code translation
└── danke/                       # Domain-Aware NeuroSymbolic Knowledge Engine

bin/                            # Executable scripts and utilities

docs/                           # Project documentation
├── ai-readme/                  # AI-assisted documentation
├── architecture/               # System architecture
├── core-concepts/              # Framework core concepts
├── dana/                       # DANA language documentation
└── danke/                      # DANKE documentation

examples/                       # Example code and tutorials
├── 01_getting_started/         # Basic examples for new users
├── 02_core_concepts/           # Core concept demonstrations
├── 03_advanced_topics/         # Advanced usage patterns
└── 04_real_world_applications/ # Real-world applications

tests/                          # Test suite
├── agent/                      # Agent tests
├── common/                     # Common utilities tests
├── dana/                       # DANA language tests
│   ├── repl/                   # REPL tests
│   ├── sandbox/                # Sandbox environment tests
│   │   ├── interpreter/        # Interpreter tests
│   │   └── parser/             # Parser tests
│   └── transcoder/             # Transcoder tests
└── execution/                  # Execution flow tests
```

### Key Configuration Files

#### `pyproject.toml`
Main project configuration file containing:
- Project metadata (name, version, authors)
- Dependencies and optional dependencies
- Build system configuration
- Tool configurations (black, ruff, pylint, etc.)

#### `SOURCE_ME.sh`
Environment setup script that:
- Creates and activates a virtual environment
- Installs the OpenDXA package in development mode
- Sets up pre-commit hooks
- Installs dependencies from requirements.txt

#### `requirements.txt`
Lists all project dependencies for easy installation.

#### `.env.example` (if present)
Example environment variable configuration for local development.

## Project Overview

OpenDXA is a comprehensive framework for building intelligent multi-agent systems with domain expertise, powered by Large Language Models (LLMs). It consists of two main components:

1. **DANA (Domain-Aware NeuroSymbolic Architecture)**: An imperative programming language and execution runtime for agent reasoning. Key components include:
   - **Parser**: Converts DANA source code into an Abstract Syntax Tree (AST) using a formal grammar
   - **Interpreter**: Executes DANA programs by processing the AST
   - **Sandbox**: Provides a safe execution environment with controlled state management
   - **Transcoder**: Translates between natural language and DANA code
   - **REPL**: Interactive environment for executing DANA code

2. **DANKE (Domain-Aware NeuroSymbolic Knowledge Engine)**: A knowledge management system implementing the CORRAL methodology (Collect, Organize, Retrieve, Reason, Act, Learn).

The framework enables building domain-expert agents with clear, auditable reasoning steps and the ability to apply specialized knowledge to solve complex tasks across different domains. 

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>