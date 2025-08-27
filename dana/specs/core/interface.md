# Design Document: Dana Interface System

<!-- text markdown -->
```text
Author: Christopher Nguyen
Version: 1.0
Date: 2025-08-01
Status: Design Phase
Implementation Tracker: dana-interface-implementation.md
```
<!-- end text markdown -->

## Problem Statement
**Brief Description**: Dana needs a type-safe interface system to define behavioral contracts for agents, workflows, and system components, using runtime method-call-time validation for maximum flexibility.

The Agent-Workflow FSM system and broader Dana ecosystem currently lacks:
- Formal contracts defining required methods for agents, workflows, and other components
- Type-safe polymorphism enabling different agent specializations and workflow types
- Runtime validation of interface compliance through Dana's existing function resolution system
- Clear behavioral specifications for reliable component composition
- Support for interface embedding and composition patterns

Without interface definitions, the type system cannot enforce contracts between agents and workflows, making it difficult to ensure reliable component interactions and enable safe polymorphic behavior. Dana's dynamic nature requires a flexible approach that validates interface compliance only when methods are actually called.

## Goals
**Brief Description**: Implement Go-style structural interfaces that integrate seamlessly with Dana's existing type system and function resolution.

**Specific Objectives**:
- Add `interface` keyword with structural typing semantics (types satisfy interfaces implicitly)
- Enable interface embedding for composition patterns
- Integrate with existing StructType foundation (agent_blueprint, resource, workflow)
- Leverage Dana's function resolution subsystem for runtime compliance checking
- Support polymorphic function parameters using interface types
- Maintain compatibility with existing struct functions and receiver syntax
- Follow IName convention for interface naming

**Success Criteria**:
- Interface types can be used in function parameters and return types
- Runtime validates interface compliance through function resolution
- Agent blueprints, resources, and workflows can satisfy interface contracts
- Interface embedding works for composition patterns
- Existing Dana code continues to work unchanged

## Non-Goals
**Brief Description**: Features explicitly excluded from this design.

- Traditional class-based inheritance or explicit interface implementation
- Interface versioning or evolution mechanisms
- Complex generic constraints or type parameters
- Performance optimization for interface dispatch
- Visual interface design tools or documentation generators

## Proposed Solution
**Brief Description**: Add `interface` keyword to Dana grammar that defines method contracts, with runtime validation through existing function resolution system.

The interface system follows Go's structural typing model where types automatically satisfy interfaces if they implement the required methods. This integrates naturally with Dana's existing function resolution and StructType foundation.

Key design principles:
- **Structural Typing**: Types satisfy interfaces implicitly by implementing required methods
- **Runtime Validation**: Use Dana's existing function resolution to validate interface compliance
- **StructType Integration**: Leverage existing StructType foundation for agent_blueprint, resource, workflow
- **Interface Embedding**: Support composition through embedded interfaces
- **Zero Breaking Changes**: Existing code continues to work unchanged

**KISS/YAGNI Analysis**: This design reuses Dana's existing function resolution infrastructure rather than building new dispatch mechanisms. We start with basic structural typing and interface embedding, avoiding complex features like generics or advanced type constraints until real usage demonstrates necessity.

## Proposed Design

### System Architecture Diagram
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Interface     │    │   StructType    │    │ Function        │
│   Definition    │    │   (agent,       │    │ Resolution      │
│                 │◄──►│   resource,     │◄──►│ System          │
│ interface IAgent│    │   workflow)     │    │                 │
│   method_specs  │    │                 │    │ validate()      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Runtime Type Checker                        │
│ - Check method signatures against interface specs         │
│ - Validate parameter and return types                     │  
│ - Handle interface embedding resolution                   │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### Interface Definition Syntax
**Brief Description**: Interfaces define method contracts including property accessors that types can satisfy implicitly through external functions using receiver patterns.

```dana
interface IAgent:
    # Core behavioral methods
    plan(problem: str) -> IWorkflow
    reason(question: str, context: dict) -> IAnalysis  
    solve(problem: str, ...params) -> ISolution
    execute(workflow: IWorkflow, data) -> IResult
    
    # Property accessors
    get_domain() -> str
    get_confidence_threshold() -> float
    get_is_active() -> bool
    set_confidence_threshold(threshold: float) -> None

interface IWorkflow:
    # Behavioral methods
    execute(agent: IAgent, data) -> ISolution
    validate() -> bool
    
    # Property accessors
    get_name() -> str
    get_timeout_seconds() -> int
    get_retry_count() -> int
    set_timeout_seconds(seconds: int) -> None

interface IAnalysis:
    # Property accessors (read-only for immutable analysis results)
    get_confidence() -> float
    get_reasoning() -> str
    get_recommendations() -> list[str]
    get_needs_action() -> bool
```

**Motivation**: Interface syntax uses property accessor methods rather than direct field declarations, maintaining behavioral contracts while preserving abstraction. This approach follows Go's conventional patterns and keeps interfaces focused on behavior rather than data structure, while still enabling property contract enforcement.

#### Interface Embedding
**Brief Description**: Interfaces can embed other interfaces to compose larger contracts, inheriting all methods including property accessors.

```dana
interface IReadable:
    read(buffer: bytes) -> int
    get_is_open() -> bool

interface IWritable:
    write(data: bytes) -> int
    get_is_writable() -> bool

interface IReadWriter:
    IReadable    # Embedded interface - inherits read() and get_is_open()
    IWritable    # Embedded interface - inherits write() and get_is_writable()
    close() -> bool

interface IQualityAgent:
    IAgent       # Embedded base interface - inherits all IAgent methods
    
    # Specialized behavioral methods
    inspect_batch(batch_id: str) -> IBatchReport
    classify_defect(image_data: bytes) -> IDefectType
    
    # Specialized property accessors
    get_inspection_mode() -> str
    get_defect_threshold() -> float
    set_inspection_mode(mode: str) -> None
```

**Motivation**: Interface embedding enables composition without inheritance complexity, following Go's proven model. Embedded interfaces contribute all their methods (behavioral and property accessors) to the containing interface, allowing for clean hierarchical contracts.

#### Runtime Validation Integration
**Brief Description**: Leverage Dana's existing function resolution system to validate interface compliance.

**Function Resolution Integration**:
- When a function parameter expects interface type, runtime checks if passed value implements required methods
- Use existing method lookup mechanisms to verify method signatures match interface specifications
- Validate return types and parameter types recursively for interface compliance

**Validation Points**:
```dana
def process_data(agent: IAgent, workflow: IWorkflow) -> IResult:
    # Runtime validates:
    # 1. agent implements plan(), reason(), solve(), execute()
    # 2. workflow implements name property, execute(), validate()
    # 3. Return type satisfies IResult interface
    return agent.execute(workflow, data)
```

#### StructType Integration
**Brief Description**: All existing Dana types (agent_blueprint, resource, workflow) can satisfy interface contracts through external functions using receiver patterns, including property accessor implementations.

```dana
# Agent blueprint defines data structure only
agent_blueprint QualityInspector:
    domain_name: str = "semiconductor"
    threshold: float = 0.015
    active: bool = true

# External receiver functions satisfy IAgent interface
def (inspector: QualityInspector) plan(problem: str) -> IWorkflow:
    return create_quality_workflow(problem, inspector.domain_name)

def (inspector: QualityInspector) reason(question: str, context: dict) -> IAnalysis:
    return analyze_with_domain_knowledge(question, context, inspector.domain_name)

def (inspector: QualityInspector) solve(problem: str, ...params) -> ISolution:
    workflow = inspector.plan(problem)
    return inspector.execute(workflow, params)

def (inspector: QualityInspector) execute(workflow: IWorkflow, data) -> IResult:
    return workflow.execute(inspector, data)

# Property accessor receiver functions
def (inspector: QualityInspector) get_domain() -> str:
    return inspector.domain_name

def (inspector: QualityInspector) get_confidence_threshold() -> float:
    return inspector.threshold

def (inspector: QualityInspector) get_is_active() -> bool:
    return inspector.active

def (inspector: QualityInspector) set_confidence_threshold(threshold: float) -> None:
    inspector.threshold = threshold

# Usage - runtime validates QualityInspector satisfies IAgent through receiver functions
inspector = QualityInspector()
domain = inspector.get_domain()                    # Property accessor
inspector.set_confidence_threshold(0.02)          # Property setter
result = process_data(inspector, workflow)        # ✓ Valid - inspector has all required receiver functions
```

**Motivation**: This maintains Dana's functional programming paradigm where data structures are separate from behavior, while enabling complete interface compliance through external receiver functions for both behavioral methods and property accessors. Internal field names can differ from interface property names, providing implementation flexibility.

### Grammar Integration
**Brief Description**: Add interface keyword to Dana grammar alongside existing type definition keywords.

**Suggested Grammar Changes** (for AI coder consideration):
```lark
// Add interface to definition types
definition: (STRUCT | RESOURCE | AGENT_BLUEPRINT | WORKFLOW | INTERFACE) NAME ":" [COMMENT] definition_block

// Add interface keyword
INTERFACE.2: "interface"

// Interface-specific block structure
definition_block: struct_block | interface_block
interface_block: _NL _INDENT [docstring] interface_members _DEDENT

interface_members: interface_member+
interface_member: interface_method | embedded_interface

// Interface methods include both behavioral methods and property accessors
interface_method: NAME "(" [parameters] ")" ["->" basic_type] [COMMENT] _NL
embedded_interface: NAME [COMMENT] _NL  // For interface embedding
```

**Key Integration Points**:
- Interface definitions contain only method signatures (behavioral + property accessors)
- Property accessors are regular methods following getter/setter naming conventions
- Reuse existing type annotation system for method signatures
- Leverage existing function parameter parsing for interface methods
- Interface names follow IName convention but grammar doesn't enforce this
- No special grammar needed for properties - they're just methods

## Proposed Implementation

### Core Implementation Strategy
**Brief Description**: Build on Dana's existing function resolution and type system rather than creating new mechanisms.

**Key Components**:
1. **Interface Type Representation**: Extend StructType to include interface specifications
2. **Method Signature Storage**: Store required method signatures and property types for each interface
3. **Compliance Checker**: Use function resolution to validate types satisfy interface contracts
4. **Type Annotation Integration**: Support interface types in function parameters and return types
5. **Embedding Resolver**: Flatten embedded interfaces into complete method sets

**Implementation Phases**:
1. **Phase 1**: Basic interface definition parsing and storage
2. **Phase 2**: Runtime compliance checking through function resolution
3. **Phase 3**: Interface embedding and composition support
4. **Phase 4**: Integration with existing agent_blueprint, resource, workflow types

### Runtime Validation Algorithm
**Brief Description**: Use existing function resolution to check interface compliance by finding receiver functions for both behavioral methods and property accessors at call sites.

```dana
def validate_interface_compliance(value, interface_type):
    for method_spec in interface_type.methods:
        # Look for receiver function: def (value_type: ValueType) method_name(...)
        receiver_func = find_receiver_function(type(value), method_spec.name)
        if not receiver_func:
            return false
        
        if not signatures_match(receiver_func.signature, method_spec.signature):
            return false
    
    # Property accessors are also methods in the interface
    for property_accessor in interface_type.property_accessors:
        receiver_func = find_receiver_function(type(value), property_accessor.name)
        if not receiver_func:
            return false
        
        if not signatures_match(receiver_func.signature, property_accessor.signature):
            return false
    
    return true

def find_receiver_function(value_type, method_name):
    # Search for functions with signature: def (receiver: value_type) method_name(...)
    return function_resolution_system.find_receiver_function(value_type, method_name)
```

**Property Accessor Validation**:
- Getters: `def (receiver: Type) get_property_name() -> PropertyType`
- Setters: `def (receiver: Type) set_property_name(value: PropertyType) -> None`
- Read-only properties: Only getter required
- Read-write properties: Both getter and setter required

### Error Handling
**Brief Description**: Provide clear error messages when types don't satisfy interface contracts.

**Error Types**:
- Missing required methods with signature details
- Method signature mismatches with expected vs. actual
- Missing required properties with type information
- Interface embedding resolution errors

**Error Messages**:
```
InterfaceComplianceError: QualityInspector does not satisfy IAgent interface:
  - Missing receiver function: def (inspector: QualityInspector) plan(problem: str) -> IWorkflow
  - Function signature mismatch: 
    Found: def (inspector: QualityInspector) solve(problem: str) -> str
    Expected: def (inspector: QualityInspector) solve(problem: str, ...params) -> ISolution
  - Missing property getter: def (inspector: QualityInspector) get_domain() -> str
  - Missing property setter: def (inspector: QualityInspector) set_confidence_threshold(threshold: float) -> None
  - Property accessor signature mismatch:
    Found: def (inspector: QualityInspector) get_confidence_threshold() -> int
    Expected: def (inspector: QualityInspector) get_confidence_threshold() -> float
```

### Integration Points
**Brief Description**: How interfaces integrate with existing Dana language features.

**Function Parameters**:
```dana
def coordinate_agents(agents: list[IAgent], problem: str) -> list[IResult]:
    # Runtime validates each agent in list satisfies IAgent
    return [agent.solve(problem) for agent in agents]
```

**Function Parameters**:
```dana
def coordinate_agents(agents: list[IAgent], problem: str) -> list[IResult]:
    # Runtime validates each agent in list satisfies IAgent (including property accessors)
    results = []
    for agent in agents:
        if agent.get_is_active():  # Property accessor call
            domain = agent.get_domain()  # Property accessor call  
            result = agent.solve(problem)  # Behavioral method call
            results.append(result)
    return results
```

**Agent Blueprint Integration**:
```dana
# Agent blueprint defines only data
agent_blueprint SmartInspector:
    domain_value: str = "quality"
    threshold_value: float = 0.02

# External receiver functions satisfy interface contracts
def (inspector: SmartInspector) plan(problem: str) -> IWorkflow:
    return self.reason("create workflow for " + problem)

def (inspector: SmartInspector) reason(question: str, context: dict) -> IAnalysis:
    return analyze_with_tolerance(question, context, inspector.threshold_value)

# Property accessor implementations
def (inspector: SmartInspector) get_domain() -> str:
    return inspector.domain_value

def (inspector: SmartInspector) get_confidence_threshold() -> float:
    return inspector.threshold_value

def (inspector: SmartInspector) set_confidence_threshold(threshold: float) -> None:
    inspector.threshold_value = threshold
```

**Struct Function Compatibility**:
```dana
# Struct defines data only
struct Point:
    x: float
    y: float

interface IMovable:
    translate(dx: float, dy: float) -> IMovable
    distance_from_origin() -> float
    
    # Property accessors
    get_x_coordinate() -> float
    get_y_coordinate() -> float
    set_coordinates(x: float, y: float) -> None

# External receiver functions satisfy interface
def (point: Point) translate(dx: float, dy: float) -> IMovable:
    return Point(x=point.x + dx, y=point.y + dy)

def (point: Point) distance_from_origin() -> float:
    return (point.x ** 2 + point.y ** 2) ** 0.5

# Property accessor implementations
def (point: Point) get_x_coordinate() -> float:
    return point.x

def (point: Point) get_y_coordinate() -> float:
    return point.y

def (point: Point) set_coordinates(x: float, y: float) -> None:
    point.x = x
    point.y = y

# Point now satisfies IMovable through receiver functions
def move_shape(shape: IMovable, dx: float, dy: float) -> IMovable:
    current_x = shape.get_x_coordinate()  # Property accessor
    current_y = shape.get_y_coordinate()  # Property accessor
    return shape.translate(dx, dy)        # Behavioral method
```