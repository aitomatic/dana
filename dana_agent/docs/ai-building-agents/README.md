# Dana Framework Documentation

Welcome to the Dana Framework documentation - your complete guide to designing, implementing, and deploying STARAgent systems.

## Quick Navigation

### 🎯 I want to...

| Goal | Start Here |
|------|-----------|
| **Design a new agent system** | [Design Guides](./design/) |
| **Implement a resource/workflow/agent** | [Implementation Guides](./implementation/) |
| **Understand Dana API** | [API Reference](./api/) |
| **See code examples** | [Design Examples](./design/examples/) or [Templates](./implementation/templates/) |
| **Learn about specific topics** | See topics below |

---

## Documentation Structure

```
docs/
├── README.md (you are here)          # Main entry point
├── design/                           # How to DESIGN agent systems
│   ├── agent_team_design_guide.md   # Complete methodology
│   ├── agent_design_patterns.md     # Agent patterns
│   ├── workflow_design_patterns.md  # Workflow patterns
│   ├── resource_design_patterns.md  # Resource patterns
│   └── examples/                     # Worked design examples
├── implementation/                   # How to IMPLEMENT components
│   ├── creating_resources.md        # Step-by-step resource creation
│   ├── creating_workflows.md        # Step-by-step workflow creation
│   ├── creating_agents.md           # Step-by-step agent creation
│   ├── testing_guide.md             # Testing patterns
│   └── templates/                    # Code templates
├── api/                              # API REFERENCE
│   ├── base_classes.md              # BaseResource, BaseWorkflow, STARAgent
│   ├── decorators.md                # @tool_use, @observable, @validate_input
│   ├── llm_integration.md           # LLM class usage
│   └── validation.md                # Validation system
└── [technical notes]                 # Existing technical documents
```

---

## Getting Started Paths

### Path 1: Design → Implement (Recommended for New Projects)

**For**: Creating a new agent system from scratch

1. **Design Phase**
   - Read [Agent Team Design Guide](./design/agent_team_design_guide.md)
   - Study relevant [Design Patterns](./design/)
   - Look at [Design Examples](./design/examples/)
   - Create your design document

2. **Implementation Phase**
   - Follow [Implementation Guides](./implementation/)
   - Use [API Reference](./api/) as needed
   - Start with [Code Templates](./implementation/templates/)
   - Test using [Testing Guide](./implementation/testing_guide.md)

**Time**: 2-4 hours for design, 1-3 days for implementation (depending on complexity)

---

### Path 2: Quick Implementation (For Simple Cases)

**For**: Implementing a simple resource or workflow

1. Start with [Code Templates](./implementation/templates/)
2. Refer to [Implementation Guides](./implementation/) for your component type
3. Check [API Reference](./api/) for specific method details
4. Add tests per [Testing Guide](./implementation/testing_guide.md)

**Time**: 1-4 hours

---

### Path 3: Learning & Exploration

**For**: Understanding Dana architecture and capabilities

1. Read [Agent Team Design Guide](./design/agent_team_design_guide.md) - Core principles
2. Study [Design Examples](./design/examples/) - See complete designs
3. Browse [Design Patterns](./design/) - Learn proven patterns
4. Check codebase examples:
   - `dana/lib/agents/web_research.py` - Simple agent
   - `dana/apps/dana/dana_agent.py` - Coordinator agent
   - `contrib/expert_interview/` - Application

**Time**: 3-5 hours

---

## Core Concepts

### The Dana Architecture

Dana follows a compositional hierarchy:

```
Agent (Prompt-driven behavior)
  ├─> Sub-Agents (Specialists)
  ├─> Workflows (Deterministic orchestration)
  └─> Resources (Domain-agnostic capabilities)

Workflow (Deterministic logic)
  ├─> Other Workflows (Composition)
  └─> Resources (External capabilities)

Resource (Stateless capability)
  └─> Other Resources (Internal composition)
```

**Key Principle**: Maintain this hierarchy for order and composability.

### Domain Expertise Layers

- **Agents**: Domain-specific roles and decision-making
- **Workflows**: Domain-specific orchestration and logic
- **Resources**: Domain-agnostic capabilities (highly reusable)

### Determinism Through Workflows

Workflows provide the deterministic orchestration that pure LLM approaches lack:
- Predictable execution paths
- Reliable error handling
- Testable logic
- Observable behavior

---

## Documentation Sections

### [Design Guides](./design/)

**Purpose**: Learn HOW to design agent systems

**Key Documents**:
- **[Agent Team Design Guide](./design/agent_team_design_guide.md)** - Complete 5-phase methodology
- **[Agent Design Patterns](./design/agent_design_patterns.md)** - 4 core agent patterns
- **[Workflow Design Patterns](./design/workflow_design_patterns.md)** - 14 workflow patterns
- **[Resource Design Patterns](./design/resource_design_patterns.md)** - 11 resource patterns

**Examples**:
- **[Data Analysis Agent](./design/examples/data_analysis_agent_design.md)** - Single specialist
- **[Maritime Navigation](./design/examples/maritime_navigation_agent_design.md)** - Multi-agent system

**Read this when**: Starting a new agent system or improving existing design

---

### [Implementation Guides](./implementation/)

**Purpose**: Learn HOW to implement components in code

**Key Documents**:
- **[Creating Resources](./implementation/creating_resources.md)** - Step-by-step resource implementation
- **[Creating Workflows](./implementation/creating_workflows.md)** - Step-by-step workflow implementation
- **[Creating Agents](./implementation/creating_agents.md)** - Step-by-step agent implementation
- **[Testing Guide](./implementation/testing_guide.md)** - Testing patterns and practices

**Templates**:
- **[Resource Template](./implementation/templates/resource_template.py)** - Starter code
- **[Workflow Template](./implementation/templates/workflow_template.py)** - Starter code
- **[Agent Template](./implementation/templates/agent_template.py)** - Starter code

**Read this when**: Implementing designed components

---

### [API Reference](./api/)

**Purpose**: Detailed API documentation for Dana framework

**Key Documents**:
- **[Base Classes](./api/base_classes.md)** - BaseResource, BaseWorkflow, STARAgent
- **[Decorators](./api/decorators.md)** - @tool_use, @observable, @validate_input/output
- **[LLM Integration](./api/llm_integration.md)** - LLM class and async patterns
- **[Validation](./api/validation.md)** - Input/output validation system

**Read this when**: Need specific method signatures, parameters, or behavior details

---

## Common Workflows

### Creating a New Resource

1. Read [Resource Design Patterns](./design/resource_design_patterns.md)
2. Copy [Resource Template](./implementation/templates/resource_template.py)
3. Follow [Creating Resources Guide](./implementation/creating_resources.md)
4. Refer to [Base Classes API](./api/base_classes.md) as needed
5. Add tests per [Testing Guide](./implementation/testing_guide.md)

---

### Creating a New Workflow

1. Read [Workflow Design Patterns](./design/workflow_design_patterns.md)
2. Copy [Workflow Template](./implementation/templates/workflow_template.py)
3. Follow [Creating Workflows Guide](./implementation/creating_workflows.md)
4. Refer to [Base Classes API](./api/base_classes.md) as needed
5. Add tests per [Testing Guide](./implementation/testing_guide.md)

---

### Creating a New Agent

1. Design using [Agent Team Design Guide](./design/agent_team_design_guide.md)
2. Identify resources and workflows (create if needed)
3. Copy [Agent Template](./implementation/templates/agent_template.py)
4. Follow [Creating Agents Guide](./implementation/creating_agents.md)
5. Create prompt file (`.prt`) with PUBLIC_DESCRIPTION and PRIVATE_IDENTITY
6. Add tests per [Testing Guide](./implementation/testing_guide.md)

---

## Key Reference Tables

### Design Pattern Selection

| Scenario | Recommended Pattern | Document |
|----------|-------------------|----------|
| Single domain, focused task | Single Specialist | [Agent Patterns](./design/agent_design_patterns.md) |
| Multiple domains, need synthesis | Hierarchical Coordinator | [Agent Patterns](./design/agent_design_patterns.md) |
| 2-4 specialists, simple interaction | Peer Collaboration | [Agent Patterns](./design/agent_design_patterns.md) |
| Structured problem, clear steps | Workflow-Heavy | [Design Examples](./design/examples/) |

### Workflow Pattern Selection

| Scenario | Pattern | Document |
|----------|---------|----------|
| Steps depend on previous results | Sequential Pipeline | [Workflow Patterns](./design/workflow_design_patterns.md) |
| Independent operations | Parallel Execution | [Workflow Patterns](./design/workflow_design_patterns.md) |
| Mix of parallel and sequential | Phased Orchestration | [Workflow Patterns](./design/workflow_design_patterns.md) |
| Different paths based on input | Conditional Branching | [Workflow Patterns](./design/workflow_design_patterns.md) |

---

## Codebase Examples

### Agents
- `dana/lib/agents/web_research.py` - Single specialist pattern
- `dana/apps/dana/dana_agent.py` - Hierarchical coordinator
- `tests/live/agent/test_multi_agent_live.py` - Multi-agent test examples

### Workflows
- `dana/lib/workflows/web_research.py` - Sequential and phased patterns
- `dana/lib/workflows/conversation.py` - Fast path optimization
- `contrib/expert_interview/workflows/` - Complete application workflow

### Resources
- `dana/lib/resources/conversation.py` - LLM-powered resource
- `dana/lib/resources/web_research/search.py` - External API resource
- `contrib/expert_interview/resources/` - Domain-specific analysis resources

---

## Additional Resources

### Additional Technical Documentation
- [Callable Workflow Patterns](./design/callable_workflow_patterns.md) - Advanced workflow composition techniques
- [Prompt Caching](./api/prompt_caching.md) - LLM prompt caching for performance optimization

### External Documentation
- Dana specifications: `dana_agent/dana/specs/`
- Test examples: `dana_agent/tests/`
- Example applications: `dana_agent/contrib/`

---

## Contributing to Documentation

To improve these docs:
1. Identify gaps or unclear sections
2. Add examples from real implementations
3. Update patterns based on new learnings
4. Submit improvements

---

## Support

### Questions?
1. Check relevant documentation section
2. Look at codebase examples
3. Review test cases
4. Consult with team

### Found a Bug or Issue?
1. Check if it's documented in technical notes
2. Look at test cases for expected behavior
3. File an issue with reproduction steps

---

**Quick Links**:
- [Design Guide](./design/) | [Implementation Guide](./implementation/) | [API Reference](./api/)
- [Examples](./design/examples/) | [Templates](./implementation/templates/)
- [Patterns](./design/agent_design_patterns.md) | [Testing](./implementation/testing_guide.md)

---

**Last Updated**: October 2025
**Version**: 1.0
**Maintainers**: Dana Framework Team
