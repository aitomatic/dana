# MVP Implementation Plan for Agentic Architecture

## Overview

This document outlines the MVP implementation plan for the agentic architecture, focusing on two use cases: CodingAgent and FinancialAnalyst. The implementation will be done in phases with comprehensive testing at each stage.

## Current Status (Updated)

### ✅ **COMPLETED PHASES:**
- **Phase 1.1**: Core Agent Framework - Complete with Timeline integration
- **Phase 1.4**: LLM Integration - Complete with stateless LLM integration
- **Timeline System**: Complete conversation management with multi-agent support
- **Multi-Agent Communication**: Agent Registry and messaging system
- **Testing**: 38/38 tests passing with comprehensive coverage

### 🔄 **CURRENT PHASE:**
- **Phase 1.2**: Resource Framework - **IN PROGRESS** (Next Priority)
  - Need to implement actual resource calling in `call_resource()`
  - Create Resource Registry system for external APIs
  - Add tool execution loop to complete conversational pattern

### ⏳ **PENDING PHASES:**
- **Phase 1.3**: Workflow Framework
- **Phase 1.5**: PromptEngineer Framework
- **Phase 2**: Use Case Implementations (CodingAgent, FinancialAnalyst)
- **Phase 3**: Advanced Features

### **Next Immediate Steps:**
1. Implement Resource Registry system
2. Make `call_resource()` actually work with external APIs
3. Add tool execution loop to complete thinking/communicating/doing cycle
4. Create comprehensive resource examples

## Project Structure

```
adana/
├── specs/
│   ├── imp/                           # Implementation plans and tracking
│   │   ├── mvp_implementation_plan.md
│   │   ├── phase1_core_infrastructure.md
│   │   ├── phase2_use_cases.md
│   │   └── phase3_advanced_features.md
│   ├── agentic_architecture.md        # High-level architecture
│   ├── core_agent_spec.md            # Core agent specification
│   ├── resource_spec.md              # Resource specification
│   ├── workflow_spec.md              # Workflow specification
│   ├── prompt_engineer_spec.md       # PromptEngineer specification
│   ├── llm_abstraction_spec.md       # LLM abstraction specification
│   ├── coding_agent_spec.md          # CodingAgent specification
│   └── financial_analyst_spec.md     # FinancialAnalyst specification
├── core/                              # Core framework components
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── state_manager.py
│   │   ├── conversational_loop.py
│   │   ├── llm_integration.py
│   │   └── tool_execution.py
│   ├── resource/
│   │   ├── __init__.py
│   │   ├── base_resource.py
│   │   ├── method_info.py
│   │   └── metadata_adapter.py
│   ├── workflow/
│   │   ├── __init__.py
│   │   ├── base_workflow.py
│   │   ├── workflow_step.py
│   │   └── workflow_registry.py
│   └── prompt_engineer/
│       ├── __init__.py
│       ├── prompt_engineer.py
│       ├── template_manager.py
│       └── evolution_engine.py
├── common/                            # Existing shared components
│   ├── llm/                          # Existing LLM infrastructure
│   │   ├── __init__.py
│   │   ├── llm.py
│   │   ├── types.py
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── factory.py
│   │   │   ├── anthropic.py
│   │   │   ├── openai.py
│   │   │   ├── ollama.py
│   │   │   └── [other providers]
│   │   └── tests/
│   └── config.py                     # Existing configuration management
├── lib/                               # Specific implementations
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── coding_agent.py
│   │   └── financial_analyst.py
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── file_system.py
│   │   ├── git.py
│   │   ├── terminal.py
│   │   ├── web_search.py
│   │   ├── market_data.py
│   │   └── financial_news.py
│   └── workflows/
│       ├── __init__.py
│       ├── coding_workflows.py
│       └── financial_workflows.py
├── tests/                             # Comprehensive test suite
│   ├── unit/
│   │   ├── test_agent.py
│   │   ├── test_resource.py
│   │   ├── test_workflow.py
│   │   └── test_prompt_engineer.py
│   ├── integration/
│   │   ├── test_coding_agent.py
│   │   └── test_financial_analyst.py
│   └── e2e/
│       ├── test_coding_scenarios.py
│       └── test_financial_scenarios.py
├── examples/                          # Example usage and demos
│   ├── coding_agent_demo.py
│   ├── financial_analyst_demo.py
│   └── basic_usage.py
└── docs/                             # Documentation
    ├── api_reference.md
    ├── user_guide.md
    └── developer_guide.md
```

## Implementation Phases

### Phase 1: Core Infrastructure (Weeks 1-3)

#### 1.1 Core Agent Framework (Week 1)
**Goal**: Implement the base Agent class with state management and conversational loop

**Deliverables**:
- `core/agent/base_agent.py` - Base Agent class
- `core/agent/state_manager.py` - State management utilities
- `core/agent/conversational_loop.py` - Conversational loop implementation
- `tests/unit/test_agent.py` - Unit tests for agent functionality

**Key Features**:
- State management with `.state` dictionary
- Resource and workflow registration
- Basic conversational loop
- Error handling and logging

**Testing Strategy**:
- Unit tests for state management
- Mock tests for conversational loop
- Integration tests with mock LLM provider

**Acceptance Criteria**:
- [x] Agent can be instantiated with LLM provider
- [x] State can be updated and retrieved
- [x] Resources and workflows can be registered
- [x] Basic chat functionality works with mock LLM
- [x] All unit tests pass with >90% coverage

**Status**: ✅ **COMPLETED** - Core Agent class implemented with Timeline integration and multi-agent communication

#### 1.2 Resource Framework (Week 1-2)
**Goal**: Implement the base Resource class with adaptive metadata and natural agent communication

**Deliverables**:
- `core/resource/base_resource.py` - Base Resource class
- `core/resource/method_info.py` - MethodInfo class
- `core/resource/metadata_adapter.py` - Adaptive metadata system
- `core/agent/agent_communication.py` - Agent-to-agent communication (separate from resources)
- `core/agent/base_prompts.py` - Base prompts class for agent-specific prompts
- `tests/unit/test_resource.py` - Unit tests for resource functionality
- `tests/unit/test_agent_communication.py` - Unit tests for agent communication
- `tests/unit/test_prompts.py` - Unit tests for prompt management

**Key Features**:
- Resource registration and querying
- Method metadata with adaptive docstrings
- Usage tracking and performance metrics
- Error handling and validation
- **Natural agent-to-agent communication** (separate from resources)
- **OODA-based conversational loop** with resource and agent calls
- **Prompt management system** with agent-specific prompt classes

**Design Approach**: 
- Natural separation between Resources (things that do work) and Agents (other thinking entities)
- Prompt storage convention: AgentPrompts classes in same file as agent, inheriting from BasePrompts

**Testing Strategy**:
- Unit tests for resource methods
- Mock tests for metadata adaptation
- Performance tests for resource queries
- Integration tests for agent communication

**Acceptance Criteria**:
- [ ] Resources can be registered with methods
- [ ] Resource queries work with proper error handling
- [ ] Metadata adaptation functions correctly
- [ ] Usage tracking and metrics work
- [ ] Agent-to-agent communication works naturally (separate from resources)
- [ ] OODA conversational loop integrates resources and agents
- [ ] Prompt management system works with agent-specific prompt classes
- [ ] BasePrompts class provides common prompt functionality
- [ ] All unit tests pass with >90% coverage

**Status**: 🔄 **IN PROGRESS** - Next priority phase for implementation

#### 1.3 Workflow Framework (Week 2)
**Goal**: Implement the base Workflow class with composition system

**Deliverables**:
- `core/workflow/base_workflow.py` - Base Workflow class
- `core/workflow/workflow_step.py` - WorkflowStep class
- `core/workflow/workflow_registry.py` - Workflow registry
- `tests/unit/test_workflow.py` - Unit tests for workflow functionality

**Key Features**:
- Workflow step composition
- Data flow between steps
- Error handling and retry logic
- Workflow registry management

**Testing Strategy**:
- Unit tests for workflow execution
- Integration tests for step composition
- Error handling tests

**Acceptance Criteria**:
- [ ] Workflows can be created with steps
- [ ] Data flows correctly between steps
- [ ] Error handling and retry logic work
- [ ] Workflow registry functions properly
- [ ] All unit tests pass with >90% coverage

**Status**: ⏳ **PENDING** - After Resource Framework completion

#### 1.4 LLM Integration (Week 2-3)
**Goal**: Integrate with existing LLM infrastructure

**Deliverables**:
- `core/agent/llm_integration.py` - LLM integration utilities
- `core/agent/tool_execution.py` - Tool execution framework
- `tests/unit/test_llm_integration.py` - Unit tests for LLM integration

**Key Features**:
- Integration with existing `adana/common/llm` system
- Tool calling through conversation history
- Provider switching support
- Conversation history management
- Error handling and retry logic

**Testing Strategy**:
- Unit tests for LLM integration
- Mock tests for tool execution
- Integration tests with existing LLM providers

**Acceptance Criteria**:
- [x] Seamless integration with existing LLM system
- [x] Tool calling works through conversation
- [x] Provider switching functions correctly
- [x] Conversation history is properly managed
- [x] All unit tests pass with >90% coverage

**Status**: ✅ **COMPLETED** - LLM integration working with Timeline-based conversation management

#### 1.5 PromptEngineer Framework (Week 3)
**Goal**: Implement prompt creation, combination, and evolution system

**Deliverables**:
- `core/prompt_engineer/prompt_engineer.py` - Main PromptEngineer class
- `core/prompt_engineer/template_manager.py` - Template management
- `core/prompt_engineer/evolution_engine.py` - Prompt evolution
- `tests/unit/test_prompt_engineer.py` - Unit tests for prompt system

**Key Features**:
- Prompt template system
- Context-aware prompt generation
- Prompt combination strategies
- Basic prompt evolution (MVP level)

**Testing Strategy**:
- Unit tests for prompt generation
- Template validation tests
- Context adaptation tests

**Acceptance Criteria**:
- [ ] Prompts can be generated from templates
- [ ] Context adaptation works correctly
- [ ] Prompt combination strategies work
- [ ] Template management functions properly
- [ ] All unit tests pass with >90% coverage

**Status**: ⏳ **PENDING** - After Resource and Workflow frameworks

### Phase 2: Use Case Implementations (Weeks 4-6)

#### 2.1 CodingAgent Implementation (Week 4)
**Goal**: Implement CodingAgent with file system, git, and terminal resources

**Deliverables**:
- `lib/agents/coding_agent.py` - CodingAgent implementation
- `lib/resources/file_system.py` - File system resource
- `lib/resources/git.py` - Git resource
- `lib/resources/terminal.py` - Terminal resource
- `lib/workflows/coding_workflows.py` - Coding workflows
- `tests/integration/test_coding_agent.py` - Integration tests

**Key Features**:
- File system operations (read, write, list, search)
- Git operations (status, commit, log, diff)
- Terminal command execution
- Basic coding workflows (debug, refactor)

**Testing Strategy**:
- Integration tests with real file system
- Mock tests for git operations
- Safety tests for terminal commands
- End-to-end workflow tests

**Acceptance Criteria**:
- [ ] File operations work correctly
- [ ] Git integration functions properly
- [ ] Terminal commands execute safely
- [ ] Basic workflows complete successfully
- [ ] All integration tests pass

#### 2.2 FinancialAnalyst Implementation (Week 5)
**Goal**: Implement FinancialAnalyst with market data and news resources

**Deliverables**:
- `lib/agents/financial_analyst.py` - FinancialAnalyst implementation
- `lib/resources/market_data.py` - Market data resource
- `lib/resources/financial_news.py` - Financial news resource
- `lib/workflows/financial_workflows.py` - Financial workflows
- `tests/integration/test_financial_analyst.py` - Integration tests

**Key Features**:
- Market data retrieval (mock implementation)
- Financial news aggregation
- Basic financial analysis workflows
- Portfolio analysis capabilities

**Testing Strategy**:
- Mock tests for market data APIs
- News aggregation tests
- Financial calculation tests
- Workflow execution tests

**Acceptance Criteria**:
- [ ] Market data retrieval works
- [ ] News aggregation functions properly
- [ ] Financial calculations are accurate
- [ ] Analysis workflows complete successfully
- [ ] All integration tests pass

#### 2.3 End-to-End Testing (Week 6)
**Goal**: Comprehensive testing of both use cases

**Deliverables**:
- `tests/e2e/test_coding_scenarios.py` - E2E coding tests
- `tests/e2e/test_financial_scenarios.py` - E2E financial tests
- `examples/coding_agent_demo.py` - Coding agent demo
- `examples/financial_analyst_demo.py` - Financial analyst demo

**Key Features**:
- Complete user scenarios
- Performance testing
- Error handling validation
- Documentation and examples

**Testing Strategy**:
- End-to-end scenario testing
- Performance benchmarking
- User acceptance testing
- Documentation validation

**Acceptance Criteria**:
- [ ] Complete user scenarios work
- [ ] Performance meets requirements
- [ ] Error handling is comprehensive
- [ ] Documentation is complete
- [ ] All E2E tests pass

### Phase 3: Advanced Features (Weeks 7-8)

#### 3.1 Enhanced PromptEngineer (Week 7)
**Goal**: Implement advanced prompt evolution and adaptation

**Deliverables**:
- Enhanced prompt evolution algorithms
- A/B testing framework for prompts
- Performance tracking and optimization
- Advanced template system

**Key Features**:
- Prompt performance tracking
- Automated prompt optimization
- A/B testing capabilities
- Advanced context adaptation

#### 3.2 Resource Metadata Learning (Week 7-8)
**Goal**: Implement adaptive learning for resource metadata

**Deliverables**:
- Feedback collection system
- Metadata adaptation algorithms
- Performance optimization
- Learning analytics

**Key Features**:
- Usage pattern analysis
- Automatic docstring improvement
- Performance optimization
- Learning feedback loops

#### 3.3 Production Readiness (Week 8)
**Goal**: Prepare for production deployment

**Deliverables**:
- Configuration management
- Logging and monitoring
- Error reporting
- Performance optimization
- Security hardening

**Key Features**:
- Production configuration
- Comprehensive logging
- Error monitoring
- Performance metrics
- Security best practices

## Testing Strategy

### Unit Testing
- **Coverage Target**: >90% for all core components
- **Framework**: pytest
- **Focus**: Individual component functionality
- **Mocking**: Extensive use of mocks for external dependencies

### Integration Testing
- **Coverage Target**: >80% for integration points
- **Framework**: pytest with real dependencies where safe
- **Focus**: Component interactions and data flow
- **Environment**: Controlled test environment

### End-to-End Testing
- **Coverage Target**: Complete user scenarios
- **Framework**: pytest with real agents
- **Focus**: Complete user workflows
- **Environment**: Production-like environment

### Performance Testing
- **Metrics**: Response time, throughput, memory usage
- **Tools**: pytest-benchmark, memory profilers
- **Targets**: <2s response time, <100MB memory usage
- **Load Testing**: Concurrent user scenarios

## Development Guidelines

### Code Quality
- **Linting**: flake8, black, mypy
- **Documentation**: Google-style docstrings
- **Type Hints**: Complete type annotations
- **Error Handling**: Comprehensive error handling

### Git Workflow
- **Branching**: Feature branches from main
- **Commits**: Conventional commit messages
- **Reviews**: All changes require review
- **CI/CD**: Automated testing on all PRs

### Documentation
- **API Reference**: Auto-generated from docstrings
- **User Guide**: Step-by-step usage examples
- **Developer Guide**: Architecture and extension guide
- **Examples**: Working code examples

## Risk Mitigation

### Technical Risks
- **LLM API Changes**: Abstracted through provider interface
- **Performance Issues**: Comprehensive testing and monitoring
- **Security Vulnerabilities**: Regular security audits
- **Data Privacy**: No sensitive data storage

### Project Risks
- **Scope Creep**: Strict phase boundaries
- **Timeline Delays**: Buffer time in each phase
- **Resource Constraints**: Prioritized feature set
- **Quality Issues**: Comprehensive testing strategy

## Success Metrics

### Phase 1 Success
- [ ] All core components implemented
- [ ] >90% unit test coverage
- [ ] Basic functionality working
- [ ] Documentation complete

### Phase 2 Success
- [ ] Both use cases implemented
- [ ] Integration tests passing
- [ ] E2E scenarios working
- [ ] Examples and demos complete

### Phase 3 Success
- [ ] Advanced features implemented
- [ ] Production-ready code
- [ ] Performance targets met
- [ ] Security requirements satisfied

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 3 weeks | Core infrastructure, LLM abstraction, basic PromptEngineer |
| Phase 2 | 3 weeks | CodingAgent, FinancialAnalyst, E2E testing |
| Phase 3 | 2 weeks | Advanced features, production readiness |
| **Total** | **8 weeks** | **Complete MVP with two use cases** |

## Next Steps

1. **Review and Approve Plan**: Review this implementation plan
2. **Set Up Development Environment**: Configure development tools and CI/CD
3. **Begin Phase 1**: Start with core agent framework implementation
4. **Regular Reviews**: Weekly progress reviews and adjustments
5. **Continuous Testing**: Implement testing as development progresses

This plan provides a structured approach to implementing the agentic architecture MVP with comprehensive testing and clear success criteria at each phase.
