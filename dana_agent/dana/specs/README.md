# Agentic Architecture Design Specifications

## Overview

This directory contains comprehensive design specifications for a flexible, LLM-agnostic agentic architecture that uses Resources, Workflows, and a PromptEngineer to create specialized agents for different domains.

## Architecture Components

### 1. [Core Agent Class](core_agent_spec.md)
- **Agent**: Base agent class with state management and conversational loop
- **State Management**: Centralized `.state` dictionary for all agent state
- **Resource Management**: Registration and querying of resources
- **Workflow Management**: Execution of composed workflows
- **Conversational Loop**: Tool execution loop with LLM integration

### 2. [Resource Abstraction](resource_spec.md)
- **Resource**: Base class for external capabilities (web, database, RAG, IoT, etc.)
- **MethodInfo**: Metadata for resource methods with adaptive docstrings
- **ResourceMetadataAdapter**: Learning system for adaptive metadata
- **Concrete Resources**: FileSystem, WebSearch, Database, etc.

### 3. [Workflow Composition](workflow_spec.md)
- **Workflow**: Composed functions with data flow between steps
- **WorkflowStep**: Individual steps with input/output mapping
- **WorkflowRegistry**: Management of available workflows
- **WorkflowComposer**: Utilities for complex workflow composition

### 4. [PromptEngineer](prompt_engineer_spec.md)
- **PromptEngineer**: Handles all prompt creation, combination, and evolution
- **PromptTemplates**: Reusable prompt templates with variable substitution
- **PromptEvolutionEngine**: Learning system for prompt improvement
- **PromptAdaptationEngine**: Context-aware prompt adaptation

### 5. [LLM Abstraction Layer](llm_abstraction_spec.md)
- **LLMProvider**: Abstract interface for LLM providers
- **Concrete Providers**: Anthropic, OpenAI, Ollama, etc.
- **ProviderFactory**: Factory for creating providers
- **ProviderManager**: Load balancing and fallback management

## Use Case Implementations

### 1. [CodingAgent](coding_agent_spec.md)
Specialized agent for software engineering tasks:
- **Resources**: FileSystem, Git, Terminal, WebSearch, CodeAnalysis
- **Workflows**: DebugCode, RefactorCode, AddFeature, WriteTests
- **Capabilities**: Code analysis, debugging, refactoring, testing

### 2. [FinancialAnalyst](financial_analyst_spec.md)
Specialized agent for financial analysis:
- **Resources**: MarketData, FinancialNews, CompanyData, EconomicIndicators
- **Workflows**: AnalyzeStock, OptimizePortfolio, AssessRisk, MarketResearch
- **Capabilities**: Market analysis, portfolio optimization, risk assessment

## Key Design Principles

### 1. **LLM Agnostic**
- No dependency on specific LLM libraries
- Unified interface across providers
- Easy switching between models

### 2. **Resource-Based Capabilities**
- Resources provide external system access
- Adaptive metadata and learning
- Non-composable, focused capabilities

### 3. **Workflow Composition**
- Data flow through composed functions
- Stateless workflow execution
- Recursive workflow composition

### 4. **State-Driven Architecture**
- All state in centralized `.state` dictionary
- Persistent state across interactions
- State validation and management

### 5. **Prompt-Centric Design**
- PromptEngineer handles all prompt complexity
- Adaptive prompt evolution
- Context-aware prompt generation

### 6. **Conversational Loop Pattern**
- Maintains conversation history
- Tool execution loop
- Human-AI collaboration

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Base Agent class with state management
- [ ] Resource abstraction with adaptive metadata
- [ ] Workflow composition system
- [ ] Basic PromptEngineer
- [ ] LLM abstraction layer

### Phase 2: Use Case Implementations
- [ ] CodingAgent with file system, git, terminal resources
- [ ] FinancialAnalyst with market data, news, analysis resources
- [ ] Basic workflows for each agent type

### Phase 3: Advanced Features
- [ ] Adaptive learning system
- [ ] Prompt evolution mechanisms
- [ ] Resource metadata adaptation
- [ ] Performance optimization

### Phase 4: Production Features
- [ ] State persistence
- [ ] Multi-agent coordination
- [ ] Advanced workflow orchestration
- [ ] Monitoring and observability

## File Structure

```
adana/
├── specs/
│   ├── README.md
│   ├── agentic_architecture.md
│   ├── core_agent_spec.md
│   ├── resource_spec.md
│   ├── workflow_spec.md
│   ├── prompt_engineer_spec.md
│   ├── coding_agent_spec.md
│   ├── financial_analyst_spec.md
│   └── llm_abstraction_spec.md
├── core/
│   ├── agent.py
│   ├── resource.py
│   ├── workflow.py
│   ├── prompt_engineer.py
│   └── llm_providers.py
├── agents/
│   ├── coding_agent.py
│   └── financial_analyst.py
├── resources/
│   ├── file_system.py
│   ├── git.py
│   ├── market_data.py
│   └── web_search.py
├── workflows/
│   ├── coding_workflows.py
│   └── financial_workflows.py
└── examples/
    ├── coding_agent_demo.py
    └── financial_analyst_demo.py
```

## Key Differences from Original Implementation

### 1. **Resources vs Tools**
- Resources are higher-level capabilities
- Include web access, databases, RAG, IoT devices
- Adaptive metadata and learning
- Non-composable, focused functionality

### 2. **Workflows vs Tool Chaining**
- Workflows are composed functions
- Data flow through pipeline
- Stateless execution
- Recursive composition support

### 3. **State Management**
- Centralized `.state` dictionary
- Structured state organization
- State validation and persistence
- Context-aware state updates

### 4. **PromptEngineer**
- Handles all prompt complexity
- Template-based prompt generation
- Adaptive prompt evolution
- Context-aware prompt adaptation

### 5. **LLM Agnostic**
- No LangChain dependency
- Unified provider interface
- Easy provider switching
- Consistent behavior across models

## Benefits

### 1. **Flexibility**
- Easy to add new resources and workflows
- Support for different LLM providers
- Adaptable to different domains

### 2. **Maintainability**
- Clear separation of concerns
- Modular architecture
- Easy to test and debug

### 3. **Scalability**
- Resource-based capabilities
- Workflow composition
- State management

### 4. **Learning and Adaptation**
- Adaptive metadata
- Prompt evolution
- Performance tracking

### 5. **Domain Specialization**
- Specialized agents for different domains
- Domain-specific resources and workflows
- Tailored prompts and behaviors

## Next Steps

1. **Review and Refine**: Review all specifications for completeness and accuracy
2. **Implementation Planning**: Create detailed implementation plan with milestones
3. **Prototype Development**: Build core components and basic agents
4. **Testing and Validation**: Comprehensive testing of all components
5. **Documentation**: Create user guides and API documentation
6. **Examples and Demos**: Build comprehensive examples and demonstrations

This architecture provides a solid foundation for building sophisticated, domain-specific agents that can learn, adapt, and evolve over time while maintaining flexibility and maintainability.
