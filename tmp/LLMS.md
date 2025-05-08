# OpenDXA (Domain-Expert Agent Framework) - AI Coder Guide

## Overview
OpenDXA is a framework for building intelligent agents with domain expertise using LLMs. It follows a three-layer architecture that maps business workflows to concrete plans to reasoning patterns:
- Workflows (WHY): Define what agents can do
- Plans (WHAT): Break down workflows into executable steps
- Reasoning (HOW): Execute steps using thinking patterns

## Key Differentiators

### Business/Strategic Differentiators
1. **Three-Layer Architecture**: Maps business workflows to concrete plans to reasoning patterns, creating a natural progression from requirements to implementation
2. **Domain Expertise Integration**: Specifically designed to embed domain expertise into agents, making it particularly valuable for specialized fields

### Engineering Approaches
1. **Progressive Complexity**: Start with simple implementations and progressively add complexity
2. **Composable Architecture**: Mix and match components as needed for highly customized agents
3. **Clean Separation of Concerns**: Maintain clear boundaries between different components

### User-Friendly Practices
1. **Model Context Protocol (MCP)**: Standardized interface for all external resources
2. **Built-in Best Practices**: Pre-configured templates and patterns for common behaviors
3. **Resource Management**: Robust handling with support for different transport types
4. **Comprehensive Testing Support**: Encourages thorough testing at each layer
5. **Documentation-First Approach**: Extensive documentation structure for effective use
6. **DANA Language**: Domain-specific language for implementing agent reasoning and knowledge representation

## Part 1: Using OpenDXA as a Client

### Core Concepts
- **Progressive Complexity**: Start simple, scale to complex tasks
- **Composable Architecture**: Mix and match capabilities
- **Domain Expertise Integration**: Built-in system for expert knowledge
- **Resource Management**: Standardized integration of external tools via MCP
- **Structured State Management**: Clearly defined memory spaces with different scopes

### Key Components
1. **Agent System**
   - Capability System: Defines agent abilities
   - Resource System: Integrates external tools
   - IO System: Handles input/output
   - State System: Manages agent state

2. **Execution System**
   - Workflow Layer: High-level task definition
   - Planning Layer: Step breakdown and dependencies
   - Reasoning Layer: Execution strategies
   - Pipeline Layer: Orchestration and flow

3. **DANA System** (Domain-Aware NeuroSymbolic Architecture)
   - Language: Strongly typed DSL for agent reasoning with variables, conditionals, loops, and functions
   - Runtime: Scoped execution context with standardized memory spaces
   - Interpreter: Visitor pattern-based execution of DANA programs
   - Function Registry: Registration and invocation of functions
   - Hooks: Extensible event-based customization points
   - LLM Integration: Via `reason()` statements and transcoding capabilities
   - DANKE: DANA Knowledge Engine for managing reusable domain expertise

### Common Usage Patterns
- **Workflows**: Define objectives, add nodes, connect with edges
- **Resources**: Use MCP protocol, implement schema validation
- **Capabilities**: Extend base classes, integrate with resources
- **Reasoning**: Implement thinking patterns, handle context
- **DANA**: Write domain-specific logic for agent reasoning with following features:
  - Strong typing with compile-time validation
  - Structured state access via scoped memory spaces
  - Integration with LLMs through `reason()` statements
  - Declarative programming model with clear semantics
  - Built-in logging with different severity levels

### Resource Integration
- Uses Model Context Protocol (MCP) for standardized tool integration
- Supports both STDIO and HTTP transport types
- Built-in tool discovery and schema validation
- Robust error handling and type safety

### Best Practices for Using OpenDXA
1. Start with simple workflows before adding complexity
2. Use MCP for external tool integration
3. Implement proper error handling
4. Keep components focused and single-purpose
5. Document your agent's capabilities and workflows
6. Use DANA for complex reasoning tasks and domain-specific logic
7. Leverage DANKE for reusable knowledge components

## Part 2: Contributing to OpenDXA

### Project Structure
```
opendxa/               # Main package
├── agent/             # Agent implementation
│   ├── capability/    # Agent capabilities (memory, expertise)
│   ├── resource/      # External resource integration
├── common/            # Shared utilities
│   ├── capability/    # Base capability system
│   ├── config/        # Configuration management
│   ├── db/            # Database models and storage
│   ├── graph/         # Graph data structures
│   ├── io/            # Input/output handlers
│   ├── mixins/        # Reusable class mixins
│   ├── resource/      # Base resource system
│   └── utils/         # Utility functions
├── dana/              # DANA language implementation
│   ├── io/            # DANA I/O handlers (LLMs, tools, agents, file operations)
│   ├── language/      # DANA language parser, AST, type checking, and validation
│   ├── runtime/       # Runtime context, interpreter, function registry, and hooks
│   └── transcoder/    # Bidirectional mapping between natural language and DANA code
├── danke/             # DANA Knowledge Engine for reusable knowledge components
└── __init__.py        # Package initialization

examples/               # Usage examples
├── 01_getting_started/ # Introductory examples
├── 02_core_concepts/   # Core concept examples
├── 03_advanced_topics/ # Advanced usage examples
├── 04_real_world_applications/ # Real-world application examples
├── dana/              # DANA language examples
│   ├── na/            # DANA code examples with .na extension
│   ├── reasoning_example.py # Example of DANA reasoning
│   ├── repl_example.py # Example of DANA REPL usage
│   └── run_examples.py # Script to run DANA examples
└── __init__.py        # Package initialization

tests/                 # Test suite
├── agent/            # Agent system tests
├── common/           # Common utilities tests
├── dana/             # DANA language tests
│   ├── test_context.py # RuntimeContext tests
│   ├── test_interpreter.py # Interpreter tests
│   ├── test_parser.py # Parser tests
│   ├── test_reason.py # Reasoning tests
│   └── test_transcoder.py # Transcoder tests
└── execution/        # Execution system tests

docs/                 # Documentation
├── architecture/     # Architecture documentation
├── cognitive-functions/ # Cognitive function docs
├── core-concepts/    # Core concept documentation
├── dana/             # DANA language documentation
│   ├── DANA.md       # DANA overview
│   ├── EXAMPLES.md   # DANA examples
│   ├── LANGUAGE.md   # DANA language reference
│   └── LLM.md        # DANA LLM integration
├── key-differentiators/ # Key differentiator docs
└── requirements/     # Requirements documentation
```

### Documentation Structure
The project uses a hierarchical README structure:

- **Root README.md**: Project overview, installation, architecture
- **opendxa/README.md**: Framework architecture and components
- **opendxa/agent/README.md**: Agent system documentation
- **opendxa/common/README.md**: Common utilities documentation
- **opendxa/dana/README.md**: DANA language documentation
- **opendxa/agent/capability/README.md**: Capability system
- **opendxa/agent/resource/README.md**: Resource system and MCP
- **opendxa/common/resource/README.md**: Base resource system
- **examples/README.md**: Examples overview and tutorials
- **docs/**: Comprehensive documentation by topic
- **docs/dana/**: DANA language detailed documentation

### DANA Language Overview

The DANA language is a domain-specific language (DSL) for implementing agent reasoning with the following key features:

1. **Language Processing**:
   - Abstract Syntax Tree (AST) for representing DANA programs
   - Parser with robust error handling
   - Type checker and validator for ensuring program correctness

2. **Runtime System**:
   - Visitor pattern-based interpreter
   - Scoped runtime context with standardized memory spaces
   - Function registry for managing callable functions
   - Hooks system for extensibility

3. **LLM Integration**:
   - `reason()` statements to invoke LLMs during program execution
   - Transcoder for converting between natural language and DANA code
   - Structured integration with the agent framework

4. **State Management**:
   - Explicit memory spaces: `agent`, `world`, `temp`, `execution`
   - Scoped variable access with visibility controls
   - Standardized state tracking during execution

5. **Core Features**:
   - Variables with strong typing
   - Conditionals and loops
   - Functions and modules
   - Logging capabilities
   - String formatting and manipulation
   - Reasoning capabilities through LLM integration

### Type Information
Critical constraints to maintain:
- Workflows: Unique node_ids, valid node_types
- Resources: Schema validation, transport specification
- Arguments: Match inputSchema, handle required fields
- DANA:
  - Strong typing for variables and expressions
  - Valid AST structure
  - Proper scope resolution
  - Correct hook registration and execution
  - Valid reason statements with appropriate prompts

### Testing Guidelines
- Test each layer independently
- Mock external resources
- Test workflow execution and error handling
- Test with large workflows and concurrent execution
- Test DANA language features:
  - Parser correctness and error handling
  - Type checking and validation
  - Interpreter execution for all language constructs
  - Runtime context and state management
  - Function registration and invocation
  - Transcoder bidirectional mapping
  - LLM integration through reason statements

### Best Practices for Contributing
1. Follow the three-layer architecture when adding new features
2. Maintain clean separation of concerns
3. Implement proper error handling and type validation
4. Keep components focused and single-purpose
5. Document interfaces and schemas clearly
6. Include type hints and follow existing patterns
7. Maintain layer separation during refactoring
8. Document edge cases and design decisions
9. Write tests for DANA language features:
   - Add parser tests for new syntax
   - Test interpreter behavior for new constructs
   - Validate type checking for new types
   - Test transcoder for new language features
   - Ensure hooks are properly registered and executed
