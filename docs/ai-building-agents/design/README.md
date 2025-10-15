# STARAgent Team Design Guides

## Overview

This directory contains comprehensive guides for designing STARAgent teams, workflows, and resources using the Dana framework. These guides are based on successful implementations and proven patterns extracted from production agent systems.

## Who Should Use These Guides

- **AI Engineers**: Building new agent systems for specific domains
- **System Architects**: Designing multi-agent architectures
- **Product Teams**: Understanding how to scope agent capabilities
- **Future AI Agents**: Learning how to create new agents autonomously

## Document Structure

```
design/
├── README.md (you are here)
├── agent_team_design_guide.md      # Main methodology
├── agent_design_patterns.md         # Agent patterns
├── agent_interface_patterns.md      # Interface patterns
├── workflow_design_patterns.md      # Workflow patterns
├── resource_design_patterns.md      # Resource patterns
└── examples/
    ├── data_analysis_agent_design.md
    └── maritime_navigation_agent_design.md
```

---

## Quick Start

### New to Agent Design?
**Start here**: [Agent Team Design Guide](./agent_team_design_guide.md)

This is the main methodology document that walks you through the entire design process from problem definition to implementation planning.

### Have a Specific Question?

| Question | Document |
|----------|----------|
| How do I structure an agent? | [Agent Design Patterns](./agent_design_patterns.md) |
| How do I create intuitive interfaces? | [Agent Interface Patterns](./agent_interface_patterns.md) |
| When should I use multiple agents? | [Agent Design Patterns](./agent_design_patterns.md) - Pattern selection guide |
| How do I orchestrate workflows? | [Workflow Design Patterns](./workflow_design_patterns.md) |
| Should I use parallel or sequential execution? | [Workflow Design Patterns](./workflow_design_patterns.md) - Execution patterns |
| How do I design reusable resources? | [Resource Design Patterns](./resource_design_patterns.md) |
| How do I handle errors gracefully? | [Resource Design Patterns](./resource_design_patterns.md) - Graceful degradation |
| Can I see a complete example? | [Examples](./examples/) directory |

---

## Core Documents

### 1. Agent Team Design Guide
**File**: [agent_team_design_guide.md](./agent_team_design_guide.md)

The comprehensive methodology for designing STARAgent teams.

**Contents**:
- Core principles (composition hierarchy, domain expertise layers, determinism)
- Five-phase design process
- Problem analysis framework
- Component identification methodology
- Specialization decomposition
- Composition strategies
- Validation checklists
- Common pitfalls and how to avoid them

**Use this when**: Starting a new agent system design from scratch

**Reading time**: 30-40 minutes

---

### 2. Agent Design Patterns
**File**: [agent_design_patterns.md](./agent_design_patterns.md)

Catalog of proven agent architecture patterns with real examples.

**Patterns covered**:
- **Single Specialist Agent**: Focused, domain-specific agent (e.g., WebResearchAgent)
- **Hierarchical Coordinator**: Coordinator managing specialists (e.g., DanaAgent)
- **Peer Collaboration**: Agents working together directly (e.g., Research + Analysis + Coordinator)
- **Workflow-Heavy Application**: Minimal agents, heavy workflow orchestration (e.g., Expert Interview)

**Also includes**:
- Identity patterns (PUBLIC_DESCRIPTION + IDENTITY)
- Composition patterns (fluent builder, module-level resources)
- Agent sizing guidelines
- Anti-patterns to avoid

**Use this when**: Deciding on agent architecture and structure

**Reading time**: 20-30 minutes

---

### 3. Workflow Design Patterns
**File**: [workflow_design_patterns.md](./workflow_design_patterns.md)

Comprehensive guide to designing deterministic, composable workflows.

**Execution patterns**:
- **Sequential Pipeline**: Chain dependent operations with `|` operator
- **Parallel Execution**: Independent operations with `asyncio.gather()`
- **Phased Orchestration**: Mix parallel and sequential (parallel gather → sequential process)
- **Conditional Branching**: Different paths based on conditions

**Composition patterns**:
- Pipe composition (`Workflow1() | Workflow2()`)
- CallableWorkflow wrapping
- Pre/post callable hooks

**Also includes**:
- Validation patterns
- Error handling patterns
- Resource integration patterns
- Performance optimization patterns

**Use this when**: Designing multi-step deterministic processes

**Reading time**: 25-35 minutes

---

### 4. Resource Design Patterns
**File**: [resource_design_patterns.md](./resource_design_patterns.md)

Best practices for designing reusable, domain-agnostic resources.

**Structural patterns**:
- Multiple focused methods
- LLM-powered resources
- External API resources

**Behavioral patterns**:
- Graceful degradation
- Fast path optimization
- Configurable behavior

**Interface patterns**:
- Consistent return format
- Method decorators (`@tool_use`, `@observable`)
- PUBLIC_DESCRIPTION documentation

**Also includes**:
- Internal helper methods
- Resource composition
- Anti-patterns to avoid
- Design checklist

**Use this when**: Creating new capabilities or wrapping external systems

**Reading time**: 20-25 minutes

---

## Worked Examples

### Example 1: Data Analysis Agent
**File**: [examples/data_analysis_agent_design.md](./examples/data_analysis_agent_design.md)

Complete design applying the methodology to a **single specialist agent** for data analysis.

**Problem**: Help analysts reason through and execute data analysis tasks in Python

**Architecture**: Single specialist agent with focused workflows

**Key learnings**:
- Reasoning-before-coding pattern
- Safe code execution
- Domain-agnostic resource design (PythonExecutionResource)
- Validation at multiple levels

**Best for**: Understanding single specialist agent design

**Reading time**: 15-20 minutes

---

### Example 2: Maritime Navigation Agent
**File**: [examples/maritime_navigation_agent_design.md](./examples/maritime_navigation_agent_design.md)

Complete design applying the methodology to a **hierarchical multi-agent system** for maritime navigation.

**Problem**: Assist ship captains with real-time navigation decisions in varying conditions

**Architecture**: Coordinator + 4 specialist agents (Navigation, Weather, Compliance, Traffic)

**Key learnings**:
- Multi-agent coordination
- Safety-critical design principles
- Parallel specialist consultation
- Conflict resolution and synthesis
- Clear separation of concerns

**Best for**: Understanding complex multi-agent hierarchical systems

**Reading time**: 20-25 minutes

---

## Key Concepts

### Compositional Hierarchy

The foundation of Dana architecture:

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

**Rule**: Maintain this hierarchy to preserve order while affording complexity.

### Domain Expertise Layers

- **Agents**: Domain-specific identity, roles, decision-making
- **Workflows**: Domain-specific orchestration and business logic
- **Resources**: Domain-agnostic capabilities (highly reusable)

**Why**: Resources reusable across domains, workflows composable within domains, agents provide specialized interfaces.

### Determinism Through Workflows

Workflows provide deterministic orchestration that pure LLM approaches lack:
- Predictable execution paths
- Reliable error handling
- Testable logic
- Observable behavior

### Specialization Benefits

Multi-agent systems offer:
- **Focus**: Narrow, well-defined responsibilities
- **Performance**: Smaller prompts perform better
- **Parallelism**: Independent agents work concurrently
- **Maintainability**: Changes isolated to specialists
- **Load Distribution**: Avoid oversized prompts

---

## Design Process Summary

### Phase 1: Problem Analysis
1. Define the problem clearly
2. Identify users and stakeholders
3. Establish success criteria
4. Document constraints
5. List required capabilities

### Phase 2: Component Identification
1. Identify reusable resources (from library)
2. Identify resources to create (domain-agnostic when possible)
3. Identify required workflows (domain-specific orchestration)
4. Decide on agent architecture (single vs multi)

### Phase 3: Specialization Decomposition
1. Define agent identities (PUBLIC + PRIVATE)
2. Define agent scope (responsibilities + non-responsibilities)
3. Define dependencies and outputs

### Phase 4: Composition Strategy
1. Design workflow orchestration patterns
2. Compose agents with workflows and resources
3. Choose coordination pattern (if multi-agent)

### Phase 5: Validation and Refinement
1. Validate component reusability
2. Check composition clarity
3. Verify specialization appropriateness
4. Ensure determinism where needed
5. Assess performance characteristics

---

## Success Patterns

Based on successful implementations:

### Pattern 1: Composition Over Creation
**Principle**: Reuse existing resources and workflows whenever possible

**Evidence**: Expert Interview achieved 90% code reduction by composing existing components

**Application**: Always check the library before creating new components

---

### Pattern 2: Domain-Agnostic Resources
**Principle**: Resources should be capability-focused, not domain-focused

**Evidence**: ConversationResource works across interviews, support, analysis, etc.

**Application**: Extract the general capability; leave domain logic to workflows

---

### Pattern 3: Phased Orchestration
**Principle**: Combine parallel gathering with sequential processing

**Evidence**: Expert Interview parallelizes extraction + analysis, then sequences gap detection + question generation

**Application**: Identify independent operations (parallelize) and dependent operations (sequence)

---

### Pattern 4: Minimal Agent Code
**Principle**: Agents should be mostly configuration and composition

**Evidence**: All successful agents are 15-40 lines of code

**Application**: If agent code is >100 lines, extract logic into workflows or resources

---

### Pattern 5: Clear Identity Definition
**Principle**: Both PUBLIC_DESCRIPTION and IDENTITY are essential

**Evidence**: All successful agents have both forms clearly defined

**Application**: Write both before implementing the agent

---

## Anti-Patterns to Avoid

### 1. God Agent
**Problem**: Single agent trying to do everything
**Solution**: Decompose into multiple specialists with optional coordinator

### 2. Domain-Specific Resource
**Problem**: Resource too specific to be reusable
**Solution**: Extract domain-agnostic capability; put domain logic in workflows

### 3. Insufficient Determinism
**Problem**: Relying on LLM for critical decision paths
**Solution**: Use workflows for deterministic logic; use LLM for reasoning

### 4. Unclear Agent Boundaries
**Problem**: Multiple agents with overlapping responsibilities
**Solution**: Define responsibilities AND non-responsibilities clearly

### 5. Sequential When Could Be Parallel
**Problem**: Missing performance optimization opportunity
**Solution**: Use `asyncio.gather()` for independent operations

---

## Quick Reference Tables

### When to Use Each Pattern

| Scenario | Recommended Pattern | Example |
|----------|-------------------|---------|
| Single domain, focused task | Single Specialist | WebResearchAgent |
| Multiple domains, need synthesis | Hierarchical Coordinator | DanaAgent, Maritime Navigation |
| 2-4 specialists, simple interaction | Peer Collaboration | Research + Analysis + Coordinator |
| Structured problem, clear steps | Workflow-Heavy Application | Expert Interview |

### Pattern Selection by Complexity

| Complexity | Agent Count | Pattern | Coordination |
|-----------|-------------|---------|--------------|
| Simple | 1 | Single Specialist | None |
| Moderate | 2-3 | Peer Collaboration | Direct communication |
| Complex | 4-7 | Hierarchical | Coordinator |
| Very Complex | 7+ | Hierarchical + Sub-coordinators | Multi-level |

---

## Additional Resources

### Codebase Examples

- **dana/lib/agents/web_research.py**: Single specialist pattern
- **dana/apps/dana/dana_agent.py**: Hierarchical coordinator
- **contrib/expert_interview/**: Workflow-heavy application
- **tests/live/agent/test_multi_agent_live.py**: Peer collaboration

### Related Documentation

- **dana/specs/**: Architectural specifications
- **dana/docs/**: Framework documentation
- **contrib/**: Example applications

---

## Getting Help

### Questions About These Guides

If you have questions about these design guides or need clarification:
1. Review the relevant pattern document
2. Check the worked examples
3. Look at codebase examples
4. Consult the team

### Design Review

Before implementing a new agent system:
1. Complete design following this methodology
2. Document your design decisions
3. Review with team using validation checklist
4. Get feedback before coding

---

## Contributing

These guides are living documents based on real-world experience. As we build more agent systems, we learn new patterns and refine existing ones.

To contribute:
1. Identify new patterns from successful implementations
2. Document the pattern with examples
3. Add to appropriate pattern document
4. Include in this index

---

## Version History

- **v1.0** (October 2025): Initial comprehensive design guides
  - Main methodology document
  - Three pattern documents (Agent, Workflow, Resource)
  - Two worked examples (Data Analysis, Maritime Navigation)

---

## Navigation Tips

- **First time here?** Read the [Agent Team Design Guide](./agent_team_design_guide.md) front-to-back
- **Designing an agent?** Follow the guide, refer to patterns as needed
- **Looking for examples?** Start with the worked examples most similar to your use case
- **Quick reference?** Use the quick reference tables in this README
- **Stuck?** Check the anti-patterns section in relevant pattern document

---

## License

These design guides are part of the Dana framework documentation.

---

**Last Updated**: October 2025
**Maintainers**: Dana Framework Team
