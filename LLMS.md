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

## Part 1: Using OpenDXA as a Client

### Core Concepts
- **Progressive Complexity**: Start simple, scale to complex tasks
- **Composable Architecture**: Mix and match capabilities
- **Domain Expertise Integration**: Built-in system for expert knowledge
- **Resource Management**: Standardized integration of external tools via MCP

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

### Common Usage Patterns
- **Workflows**: Define objectives, add nodes, connect with edges
- **Resources**: Use MCP protocol, implement schema validation
- **Capabilities**: Extend base classes, integrate with resources
- **Reasoning**: Implement thinking patterns, handle context

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

## Part 2: Contributing to OpenDXA

### Project Structure
```
dxa/                    # Main package
├── agent/              # Agent implementation
│   ├── capability/     # Agent capabilities (memory, expertise)
│   ├── io/            # Input/output handlers
│   ├── resource/      # External resource integration
│   └── state/         # State management
├── common/             # Shared utilities
│   ├── graph/         # Graph data structures
│   ├── logging/       # Logging configuration
│   └── utils/         # Utility functions
├── execution/          # Execution system
│   ├── pipeline/      # Pipeline execution
│   ├── planning/      # Strategic planning
│   ├── reasoning/     # Reasoning patterns
│   └── workflow/      # Process workflows
├── factory/           # Factory components
└── __init__.py        # Package initialization

examples/               # Usage examples
├── notebooks/         # Jupyter notebooks
├── python/            # Python script examples
├── README.md          # Examples overview
└── __init__.py        # Package initialization

tests/                 # Test suite
├── agent/            # Agent system tests
├── execution/        # Execution system tests
└── common/           # Common utilities tests

docs/                 # Documentation
└── api/              # API documentation
```

### Documentation Structure
The project uses a hierarchical README structure:

- **Root README.md**: Project overview, installation, architecture
- **dxa/README.md**: Framework architecture and components
- **dxa/agent/README.md**: Agent system documentation
- **dxa/execution/README.md**: Execution system documentation
- **dxa/agent/capability/README.md**: Capability system
- **dxa/agent/resource/README.md**: Resource system and MCP
- **dxa/execution/workflow/README.md**: Workflow layer
- **dxa/execution/planning/README.md**: Planning layer
- **dxa/execution/reasoning/README.md**: Reasoning layer
- **dxa/execution/pipeline/README.md**: Pipeline layer
- **examples/README.md**: Examples overview and tutorials

### Type Information
Critical constraints to maintain:
- Workflows: Unique node_ids, valid node_types
- Resources: Schema validation, transport specification
- Arguments: Match inputSchema, handle required fields

### Testing Guidelines
- Test each layer independently
- Mock external resources
- Test workflow execution and error handling
- Test with large workflows and concurrent execution

### Best Practices for Contributing
1. Follow the three-layer architecture when adding new features
2. Maintain clean separation of concerns
3. Implement proper error handling and type validation
4. Keep components focused and single-purpose
5. Document interfaces and schemas clearly
6. Include type hints and follow existing patterns
7. Maintain layer separation during refactoring
8. Document edge cases and design decisions
