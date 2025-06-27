# Agent Keyword Design Document - 3D Methodology

**Project**: OpenDXA Dana Language - Agent Keyword Implementation  
**Status**: DESIGN PHASE ✅ → READY FOR IMPLEMENTATION  
**Date**: January 2025  
**Author**: AI Assistant  
**Methodology**: 3D (Design-Driven Development)

---

## Executive Summary

**Brief Description**: Design and implement an `agent` keyword in the DANA language that enables declaring agents similar to structs but with built-in `plan()` and `solve()` methods that are automatically available through DANA's existing FunctionRegistry system, while maintaining compatibility with existing agent usage patterns.

**Key Innovation**: The agent keyword provides a struct-like declaration syntax with automatic default method registration using DANA's existing FunctionRegistry, enabling default behaviors while preserving method override capabilities and full backward compatibility.

**Architecture Decision**: Use existing `FunctionRegistry` for all method dispatch - no new registry systems needed. This leverages DANA's proven polymorphic dispatch system while maintaining KISS principles.

---

## Problem Statement

### Current Situation
Dana language currently supports agent functionality through:
- Agent statements: `agent(module=..., url=...)` for instantiation
- Agent pools: `agent_pool([agents...])` for management  
- External agent integration (A2A protocol, modules)

### Pain Points
1. **No declarative agent syntax**: Cannot define custom agent types with default behaviors
2. **No systematic method registration**: No way to register and override agent methods systematically
3. **Limited customization**: No way to define agent-specific default methods or override behaviors
4. **Missing abstraction**: No clear separation between agent type definition and instantiation

### Impact
- Developers cannot create reusable agent types with registered methods
- No systematic way to override default agent behaviors
- Limited code reusability and maintainability for agent systems
- Inconsistent patterns compared to struct definitions

### Context
This enhancement builds on Dana's existing struct registration system and FunctionRegistry, extending them to cover agent type registration while preserving full backward compatibility.

---

## Goals and Success Criteria

### Primary Goals
1. **Agent Declaration Syntax**: Enable `agent TypeName:` declarations similar to struct syntax
2. **Default Methods**: Provide universal `plan()` and `solve()` methods for all agents
3. **Method Override**: Allow custom implementations of plan/solve methods
4. **Seamless Integration**: Work with existing agent() and agent_pool() functionality
5. **Type Safety**: Full integration with Dana's type system and validation

### Success Criteria
- ✅ Agent declarations parse correctly and generate appropriate AST nodes
- ✅ Default plan() and solve() methods available on all agent instances
- ✅ Custom method implementations override defaults properly
- ✅ Existing agent usage patterns remain fully functional
- ✅ Type registry integration enables agent type checking
- ✅ All existing tests pass + comprehensive new test coverage

### Non-Goals
- Complex inheritance hierarchies (KISS principle)
- Runtime agent modification beyond method override
- Breaking changes to existing agent API

---

## Solution Architecture

### System Overview

**Key Architectural Decision**: Reuse DANA's existing `FunctionRegistry` for all method dispatch. This provides:
- Proven polymorphic dispatch system
- Method syntax transformation (`agent.plan()` → `plan(agent)`)
- Namespace management and function resolution
- No additional complexity or new registry systems

The agent keyword design follows the struct registration pattern using existing DANA infrastructure:

```
Dana Grammar (.lark)
    ↓
AST Nodes (AgentDefinition, AgentField) - NO AgentMethod needed
    ↓
Parser/Transformer (AgentDefinitionTransformer)
    ↓
Agent Type Registry (AgentTypeRegistry - inherits from StructTypeRegistry)
    ↓
FunctionRegistry (EXISTING - handles all method dispatch)
    ↓
Agent Instance (Runtime objects - inherits from StructInstance)
    ↓
Integration (Existing agent() and agent_pool() compatibility)
```

### Core Components

#### 1. Grammar Extensions
**File**: `opendxa/dana/sandbox/parser/dana_grammar.lark`
**Why Core**: The grammar defines how DANA parses `agent TypeName:` syntax. Without grammar support, the language can't recognize agent declarations. This is the foundational layer that enables all other agent functionality.

```lark
// Add agent definition to compound statements
compound_stmt: if_stmt
             | while_stmt  
             | for_stmt
             | function_def
             | try_stmt
             | with_stmt
             | struct_def
             | agent_def

// Agent definition syntax (identical to struct_def)
agent_def: "agent" NAME ":" [COMMENT] agent_block -> agent_definition

agent_block: _NL _INDENT agent_fields _DEDENT
agent_fields: agent_field+

// Agent fields (identical to struct fields)
agent_field: NAME ":" basic_type ["=" expr] [COMMENT] _NL -> agent_field
```

#### 2. AST Node Definitions
**File**: `opendxa/dana/sandbox/parser/ast.py`
**Why Core**: AST nodes represent parsed agent definitions in memory. They bridge the gap between grammar parsing and runtime execution, providing structured data that transformers and executors can process.

```python
@dataclass
class AgentDefinition:
    """Agent definition statement (e.g., agent MyAgent: name: str, domain: str)."""
    name: str
    fields: list["AgentField"]
    location: Location | None = None

@dataclass  
class AgentField:
    """A field in an agent definition."""
    name: str
    type_hint: TypeHint
    default_value: Expression | None = None
    location: Location | None = None

# NO AgentMethod class - methods are external functions following Go-style approach
```

#### 3. Agent Type Registry System
**File**: `opendxa/dana/sandbox/interpreter/agent_system.py`
**Why Core**: The registry system manages agent type definitions and instances at runtime. It provides type validation, instance creation, and integrates with FunctionRegistry for method dispatch.

```python
class AgentType(StructType):
    """Agent type definition (inherits all StructType functionality)."""
    
    def __post_init__(self):
        """Validate agent type and prepare for method registration."""
        super().__post_init__()  # Reuse all StructType validation
        # Agent-specific initialization can be added here if needed

class AgentTypeRegistry(StructTypeRegistry):
    """Agent registry (inherits all StructTypeRegistry functionality)."""
    
    @classmethod
    def register(cls, agent_type: AgentType, function_registry: FunctionRegistry) -> None:
        """Register agent type and default methods."""
        # Use inherited StructTypeRegistry registration
        super().register(agent_type)
        
        # Register default plan() and solve() methods in FunctionRegistry
        register_agent_defaults(agent_type, function_registry)
    
    @classmethod
    def create_instance(cls, agent_name: str, values: dict[str, Any]) -> "AgentInstance":
        """Create an agent instance from registered type."""
        agent_type = cls.get(agent_name)
        if not agent_type:
            raise ValueError(f"Agent type '{agent_name}' not found in registry")
        return AgentInstance(agent_type, values)

class AgentInstance(StructInstance):
    """Agent instance (inherits all StructInstance functionality)."""
    
    def __init__(self, agent_type: AgentType, values: dict[str, Any]):
        """Create agent instance using struct initialization."""
        super().__init__(agent_type, values)
        # Agent-specific initialization can be added here if needed

def register_agent_defaults(agent_type: AgentType, function_registry: FunctionRegistry) -> None:
    """Register default plan() and solve() methods using existing FunctionRegistry.
    
    Default methods are registered with low priority so custom implementations override them.
    This enables the key agent keyword behavior:
    1. All agents automatically get plan() and solve() methods
    2. Custom implementations override defaults via normal function registration
    3. Partial override: can override just plan() or just solve()
    """
    
    def create_default_plan(agent_instance: "AgentInstance", task: str) -> str:
        """Universal default plan method for all agent types."""
        return f"[Default] Planning task '{task}' for {agent_instance.name} (type: {agent_type.name})"
    
    def create_default_solve(agent_instance: "AgentInstance", problem: str) -> str:
        """Universal default solve method for all agent types."""
        return f"[Default] Solving problem '{problem}' for {agent_instance.name} (type: {agent_type.name})"
    
    # Register default methods with LOW PRIORITY (custom implementations override)
    function_registry.register(
        name="plan",
        func=create_default_plan,
        namespace="system",  # System namespace for defaults
        overwrite=False  # Don't overwrite existing custom implementations
    )
    
    function_registry.register(
        name="solve", 
        func=create_default_solve,
        namespace="system",  # System namespace for defaults
        overwrite=False  # Don't overwrite existing custom implementations
    )
```

#### 4. Registration Helper Functions
**File**: `opendxa/dana/sandbox/interpreter/agent_system.py`
**Why Core**: Helper functions bridge AST parsing and runtime registration. They convert parsed agent definitions into runtime types and integrate with existing DANA execution patterns.

```python
def create_agent_type_from_ast(agent_def: AgentDefinition) -> AgentType:
    """Create an AgentType from an AgentDefinition AST node."""
    if not isinstance(agent_def, AgentDefinition):
        raise TypeError(f"Expected AgentDefinition, got {type(agent_def)}")
    
    # Convert fields (same as struct fields)
    fields = {}
    field_order = []
    for field in agent_def.fields:
        fields[field.name] = field.type_hint.name
        field_order.append(field.name)
    
    return AgentType(name=agent_def.name, fields=fields, field_order=field_order)

def register_agent_from_ast(agent_def: AgentDefinition, function_registry: FunctionRegistry) -> AgentType:
    """Register an agent type from AST definition."""
    agent_type = create_agent_type_from_ast(agent_def)
    AgentTypeRegistry.register(agent_type, function_registry)
    return agent_type

def create_agent_instance(agent_name: str, **kwargs) -> AgentInstance:
    """Create an agent instance from registered type."""
    return AgentTypeRegistry.create_instance(agent_name, kwargs)
```

### Cross-Module Method Resolution Strategy

**Decision**: Implement **Phase 1-2 Workaround Approach** for initial release, with Phase 3+ enhancement as future improvement.

#### **Phase 1-2: Workaround Approach (RECOMMENDED)**
**Constraints**:
- One agent type per module
- Standard method names (`plan`, `solve`)
- Cross-module calls use explicit syntax: `module.plan(agent, args)`
- Same-module calls use method syntax: `agent.plan(args)`

**Benefits**:
- ✅ Much simpler implementation
- ✅ Leverages existing FunctionRegistry without modification
- ✅ Faster development and deployment
- ✅ Achieves 90% of desired functionality
- ✅ Clear, unambiguous method resolution

#### **Phase 3+: Enhanced Cross-Module Syntax (FUTURE)**
**Goal**: Enable `agent.plan(args)` syntax to work across all modules
**Requirements**: Enhanced import process, cross-module function binding, method resolution improvements

### Example Usage

Following the Go-style approach with default methods and optional overrides:

```dana
# File: basic_agent.na
# Agent definition (data-only, like Go structs)
agent BasicAgent:
    name: str
    domain: str = "general"

# NO CUSTOM METHODS DEFINED - Uses default plan() and solve()
# Default methods are automatically available via FunctionRegistry

# File: smart_agent.na  
# Agent definition (data-only)
agent SmartAgent:
    name: str
    knowledge_base: dict
    domain: str = "research"

# CUSTOM METHODS OVERRIDE DEFAULTS
# Override default plan() method with custom implementation
def plan(agent: SmartAgent, task: str) -> str:
    kb_size = len(agent.knowledge_base)
    return f"[Smart] Advanced planning {task} using {kb_size} knowledge items"

# Override default solve() method with custom implementation  
def solve(agent: SmartAgent, problem: str) -> str:
    return f"[Smart] AI-powered solution for {problem} using knowledge base"

# File: main.na
import basic_agent
import smart_agent

# Agent instantiation uses existing syntax
basic = agent(module=BasicAgent, name="Helper", domain="support")
smart = agent(module=SmartAgent, name="Einstein", knowledge_base={"physics": "quantum"}, domain="AI")

# METHOD CALLS - Phase 1-2 Approach
print("=== Cross-Module Calls (Explicit Syntax) ===")
# Cross-module calls use explicit module.function(agent, ...) syntax
plan_result1 = basic_agent.plan(basic, "help user")      # DEFAULT plan()
solve_result1 = basic_agent.solve(basic, "user issue")   # DEFAULT solve()
plan_result2 = smart_agent.plan(smart, "research topic") # CUSTOM plan()  
solve_result2 = smart_agent.solve(smart, "complex problem") # CUSTOM solve()

print(f"Basic Plan: {plan_result1}")   # Uses default implementation
print(f"Basic Solve: {solve_result1}") # Uses default implementation  
print(f"Smart Plan: {plan_result2}")   # Uses custom override
print(f"Smart Solve: {solve_result2}") # Uses custom override

print("=== Same-Module Method Syntax ===")
# Within each module, method syntax works via FunctionRegistry transformation:
# agent.plan("task") → plan(agent, "task")
```

**Key Features Demonstrated**:
1. **Default Methods**: All agents automatically get `plan()` and `solve()` methods
2. **Override Capability**: Define custom `plan()` or `solve()` functions to override defaults
3. **Partial Override**: Can override just `plan()` or just `solve()`, others remain default
4. **Dual Syntax Support**: 
   - **Same-module**: `agent.plan("task")` (method syntax sugar)
   - **Cross-module**: `module.plan(agent, "task")` (explicit function calls)
5. **Polymorphic Dispatch**: Same function name works for different agent types
6. **One Agent Per Module**: Clean separation avoiding cross-module dispatch complexity

---

## Implementation Phases

### Phase 1: Foundation & Grammar (Week 1)
**Goal**: Basic agent definition parsing and AST generation

**Tasks**:
1. Extend grammar with agent_def rules
2. Create AgentDefinition and AgentField AST nodes (NO AgentMethod)
3. Implement AgentDefinitionTransformer
4. Add agent_def to compound_stmt rule
5. Basic parsing tests

**Deliverables**:
- Updated `dana_grammar.lark` with agent rules
- New AST nodes in `ast.py`
- AgentDefinitionTransformer implementation
- Phase 1 test suite

**Success Criteria**:
- Agent definitions parse to correct AST nodes
- Fields properly separated and transformed
- Basic agent definition examples work

### Phase 2: Registry System Implementation (Week 2)  
**Goal**: Agent type registry system using existing FunctionRegistry

**Tasks**:
1. Implement AgentType and AgentTypeRegistry classes (inherit from Struct classes)
2. Create agent type registration from AST
3. Implement default method registration using existing FunctionRegistry
4. Add type validation logic
5. Registry tests

**Deliverables**:
- `agent_system.py` with type classes
- Registration and validation logic
- Integration with FunctionRegistry for default methods
- Phase 2 test suite

**Success Criteria**:
- Agent types properly registered and retrievable
- Default methods registered in FunctionRegistry with low priority
- Field type validation works correctly  
- Custom method override system functional

### Phase 3: Runtime Implementation (Week 3)
**Goal**: Agent instance creation with method access

**Tasks**:
1. Implement AgentInstance runtime class (inherit from StructInstance)
2. Integrate with FunctionRegistry for method dispatch
3. Test default plan() and solve() methods
4. Add agent instance field access
5. Runtime execution tests

**Deliverables**:
- `agent_instance.py` with runtime logic
- FunctionRegistry integration for method calls
- Method dispatch system
- Phase 3 test suite

**Success Criteria**:
- Agent instances created successfully from registry
- Method calls work via FunctionRegistry dispatch
- Default methods work when no custom methods defined
- Custom methods override defaults correctly

### Phase 4: Execution Integration (Week 4)
**Goal**: Full integration with Dana execution engine

**Tasks**:
1. Add agent definition execution to AgentHandler
2. Integrate with existing agent() function
3. Enable agent type instantiation from registry
4. Update agent pools to support new agent types
5. Integration tests

**Deliverables**:
- Updated `agent_handler.py` with definition execution
- Modified agent function to support agent types
- Agent pool compatibility updates
- Phase 4 test suite

**Success Criteria**:
- Agent definitions execute and register types
- agent() function works with registered agent types
- Agent pools accept new agent instances
- Backward compatibility maintained

### Phase 5: Method Execution System (Week 5)
**Goal**: Proper method execution with context binding

**Tasks**:
1. Implement method execution with agent context
2. Add proper parameter passing and return handling
3. Enable method chaining and composition
4. Performance optimizations
5. Advanced method tests

**Deliverables**:
- Enhanced method binding system
- Parameter validation logic
- Performance optimizations
- Phase 5 test suite

**Success Criteria**:
- Methods execute with proper agent context
- Parameters and return values handled correctly
- Method execution performance acceptable
- Complex method scenarios work

### Phase 6: Documentation & Polish (Week 6)
**Goal**: Complete documentation, examples, and final polish

**Tasks**:
1. Comprehensive documentation updates
2. Example agent definitions and usage
3. Integration with IDE support (VSCode)
4. Final test coverage and cleanup
5. Performance validation

**Deliverables**:
- Updated language documentation
- Agent keyword examples and tutorials
- IDE syntax highlighting updates
- Final test suite with >95% coverage

**Success Criteria**:
- Documentation complete and accurate
- Examples working and well-documented
- IDE support functional
- All tests passing with high coverage

---

## Implementation Progress Tracking

### Phase 1: Foundation & Grammar ⏳
- [ ] Extend grammar with agent_def rules
- [ ] Create AgentDefinition and AgentField AST nodes (NO AgentMethod)
- [ ] Implement AgentDefinitionTransformer
- [ ] Add agent_def to compound_stmt rule
- [ ] Basic parsing tests
- [ ] **Phase 1 Quality Gate**: Run `uv run pytest tests/ -v` - 100% pass required

### Phase 2: Registry System Implementation ⏳
- [ ] Implement AgentType and AgentTypeRegistry classes (inherit from Struct classes)
- [ ] Create agent type registration from AST
- [ ] Implement default method registration using existing FunctionRegistry
- [ ] Add type validation logic
- [ ] Registry tests
- [ ] **Phase 2 Quality Gate**: Run `uv run pytest tests/ -v` - 100% pass required

### Phase 3: Runtime Implementation ⏳
- [ ] Implement AgentInstance runtime class (inherit from StructInstance)
- [ ] Integrate with FunctionRegistry for method dispatch
- [ ] Test default plan() and solve() methods
- [ ] Add agent instance field access
- [ ] Runtime execution tests
- [ ] **Phase 3 Quality Gate**: Run `uv run pytest tests/ -v` - 100% pass required

### Phase 4: Execution Integration ⏳
- [ ] Add agent definition execution to AgentHandler
- [ ] Integrate with existing agent() function
- [ ] Enable agent type instantiation from registry
- [ ] Update agent pools to support new agent types
- [ ] Integration tests
- [ ] **Phase 4 Quality Gate**: Run `uv run pytest tests/ -v` - 100% pass required

### Phase 5: Method Execution System ⏳
- [ ] Implement method execution with agent context
- [ ] Add proper parameter passing and return handling
- [ ] Enable method chaining and composition
- [ ] Performance optimizations
- [ ] Advanced method tests
- [ ] **Phase 5 Quality Gate**: Run `uv run pytest tests/ -v` - 100% pass required

### Phase 6: Documentation & Polish ⏳
- [ ] Comprehensive documentation updates
- [ ] Example agent definitions and usage
- [ ] Integration with IDE support (VSCode)
- [ ] Final test coverage and cleanup
- [ ] Performance validation
- [ ] **Final Quality Gate**: Run `uv run pytest tests/ -v` - 100% pass required

---

## Quality Gates

### Design Phase ✅
- [x] Requirements clearly defined and validated
- [x] Architecture design complete and reviewed
- [x] Integration points identified and planned
- [x] Implementation phases defined with clear deliverables
- [x] Success criteria established for each phase

### Implementation Phase (Each Phase)
- [ ] All tasks completed according to specifications
- [ ] Unit tests written and passing (>90% coverage per phase)
- [ ] Integration tests validate phase objectives
- [ ] Performance benchmarks meet requirements
- [ ] Code review completed and approved
- [ ] Documentation updated for phase deliverables

### Validation Phase (Final)
- [ ] All phases completed successfully
- [ ] End-to-end testing complete
- [ ] Performance validation passed
- [ ] Backward compatibility verified
- [ ] Documentation complete and accurate
- [ ] Ready for production deployment

---

## Success Metrics

### Functional Metrics
- Agent definitions parse correctly (100% success rate)
- Agent types registered in AgentTypeRegistry
- Default methods registered in FunctionRegistry
- Default methods available on all agent instances
- Custom methods override defaults properly
- Existing agent functionality unchanged

### Performance Metrics
- Agent definition parsing <10ms overhead vs struct definitions
- Method registry lookup <1ms per method call
- Agent instantiation <5ms overhead vs existing agent() calls  
- Memory usage <15% increase vs existing agent system

### Quality Metrics
- >95% test coverage across all phases
- Zero breaking changes to existing API
- <10 linter warnings across all new code
- All example code executable and well-documented

---

## Conclusion

The agent keyword design leverages DANA's existing infrastructure, particularly the FunctionRegistry and StructType system, ensuring consistency and maintainability. The simplified approach (AgentTypeRegistry + existing FunctionRegistry) enables proper method registration and resolution while maintaining full backward compatibility.

**Key Benefits**:
- **Reuses Existing Infrastructure**: Uses existing FunctionRegistry and StructType system
- **Consistent with Structs**: Same polymorphic dispatch pattern as struct methods
- **KISS Principle Applied**: Simpler design using proven components
- **Default Behaviors**: Universal plan() and solve() methods reduce boilerplate
- **Override System**: Custom functions override defaults via existing FunctionRegistry
- **Compatibility**: Zero breaking changes to existing agent ecosystem
- **Clear Method Resolution**: Phase 1-2 workaround provides unambiguous method calls

**Architecture Decisions**:
- **No AgentMethodRegistry**: Use existing FunctionRegistry for all method dispatch
- **No AgentMethod AST**: Follow Go-style with external function definitions
- **Inherit from Struct Classes**: Maximize code reuse and consistency
- **Phase 1-2 Workaround**: One agent per module with explicit cross-module calls
- **Future Enhancement**: Phase 3+ can add seamless cross-module method syntax

**Next Steps**: Proceed with Phase 1 implementation using the defined architecture and workaround approach for cross-module method resolution.

---

## Appendix

### Grammar Comparison
```lark
// Struct definition (existing)
struct_def: "struct" NAME ":" [COMMENT] struct_block -> struct_definition
struct_block: _NL _INDENT struct_fields _DEDENT
struct_fields: struct_field+
struct_field: NAME ":" basic_type ["=" expr] [COMMENT] _NL -> struct_field

// Agent definition (new - identical to struct!)  
agent_def: "agent" NAME ":" [COMMENT] agent_block -> agent_definition
agent_block: _NL _INDENT agent_fields _DEDENT
agent_fields: agent_field+
agent_field: NAME ":" basic_type ["=" expr] [COMMENT] _NL -> agent_field
```

### File Modification Checklist

#### Core Files to Modify
- [ ] `opendxa/dana/sandbox/parser/dana_grammar.lark` - Grammar rules
- [ ] `opendxa/dana/sandbox/parser/ast.py` - AST node definitions  
- [ ] `opendxa/dana/sandbox/parser/transformer/statement_transformer.py` - Route to agent transformer
- [ ] `opendxa/dana/sandbox/parser/transformer/statement/agent_definition_transformer.py` - New transformer (create)
- [ ] `opendxa/dana/sandbox/interpreter/agent_system.py` - Type system (create)
- [ ] `opendxa/dana/sandbox/interpreter/executor/statement/agent_handler.py` - Execution integration

#### Supporting Files to Update
- [ ] `opendxa/dana/integration/vscode/syntaxes/dana.tmLanguage.json` - Syntax highlighting
- [ ] `bin/vim/dana.vim` - Vim syntax support
- [ ] `docs/reference/01_dana_language_specification/` - Documentation updates
- [ ] `examples/dana/` - Example agent definitions

#### Test Files to Create
- [ ] `tests/dana/sandbox/parser/test_agent_definition_parsing.py`
- [ ] `tests/dana/sandbox/interpreter/test_agent_system.py`  
- [ ] `tests/dana/sandbox/interpreter/test_agent_instance.py`
- [ ] `tests/dana/integration/test_agent_keyword_integration.py`

---

**End of Design Document** 