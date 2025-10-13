# Design Document: Agent-Workflow FSM System

<!-- text markdown -->
```text
Author: Christopher Nguyen
Version: 1.0
Date: 2025-08-01
Status: Design Phase
Implementation Tracker: agent-workflow-fsm-implementation.md
```
<!-- end text markdown -->

## Problem Statement
**Brief Description**: AI agents need a structured way to solve complex problems through reusable, composable processes while maintaining clear separation between intelligence and execution.

Current AI agent systems lack a clean architecture for:
- Decomposing complex problems into manageable workflows
- Reusing proven processes across different problem domains
- Maintaining clear state and progress tracking during execution
- Enabling agents to provide intelligence without being tightly coupled to specific processes
- Supporting both simple linear processes and complex multi-state workflows

Without this structure, agents become monolithic, processes become ad-hoc, and it's difficult to build reliable, maintainable AI automation systems.

## Driving Use Cases

### Use Case 0: Add Two Numbers (No Workflow)
**Scenario**: User asks "What is 47 + 89?"

**Solution**: Agent handles directly without any workflow
```dana
result = agent.execute_direct("47 + 89")  # Returns 136
```

**Key Insight**: Not every problem needs a workflow. Simple computations are handled directly by the agent, demonstrating that workflows are for *processes*, not calculations.

### Use Case 1: Equipment Health Check (Existing Workflow)
**Scenario**: Manufacturing plant needs daily automated health checks on critical equipment using standard operating procedures.

**Problem**: "Check equipment health for Line 3"

**Solution Flow**:
```dana
# Agent finds existing workflow
workflow = agent.plan("check equipment health")  # Returns existing 'daily_equipment_check'

# Execute standard procedure
result = agent.execute(workflow, {"equipment_id": "Line3"})
```

**Existing Workflow**:
```dana
workflow daily_equipment_check:
    fsm: FSM = {
        states: [START, check_sensors, verify_calibration, run_diagnostics, generate_report, COMPLETE],
        transitions: linear_progression()
    }
```

**Key Insight**: Common procedures are codified as reusable workflows. Agents leverage existing, proven processes rather than reinventing them.

### Use Case 2: Custom Batch Analysis (Creates New Workflow)
**Scenario**: Pharmaceutical batch fails with unusual combination of contamination indicators and electrical anomalies not covered by standard procedures.

**Problem**: "Investigate batch B-2847 failure with contamination readings + power fluctuations"

**Solution Flow**:
```dana
# No existing workflow matches this specific combination
workflow = agent.plan("investigate unusual batch failure with contamination + electrical anomalies")
# Agent creates NEW workflow

# Agent synthesizes custom workflow
workflow custom_contamination_electrical_investigation:
    fsm: FSM = {
        states: [START, contamination_analysis, electrical_testing, cross_correlation, root_cause, COMPLETE],
        initial_state: START
    }
    
    def execute(self, agent: Agent, failure_data):
        # Decompose into sub-problems
        contamination = agent.solve("analyze contamination patterns", failure_data.contamination)
        electrical = agent.solve("diagnose electrical anomalies", failure_data.electrical)
        
        # Reason about correlation
        correlation = agent.reason("how are contamination and electrical issues related?", 
                                 {"contamination": contamination, "electrical": electrical})
        
        # Determine root cause
        if correlation.indicates_common_cause():
            root_cause = agent.solve("find common cause", correlation)
        else:
            root_cause = agent.reason("prioritize independent failures", correlation)
            
        return {"root_cause": root_cause, "remediation": agent.plan("fix " + root_cause)}
```

**Key Insight**: When no existing workflow fits, agents can synthesize new workflows by composing their cognitive capabilities (solve, reason, plan) into novel process structures.

### Use Case 3: Multi-Agent Production Crisis (Deep Recursion + Coordination)
**Scenario**: Critical production line failure requiring coordinated response from quality, maintenance, and supply chain teams.

**Problem**: "Production line critical failure - contamination detected, equipment malfunction, supply chain impact"

**Solution Flow**:
```dana
# Crisis coordinator agent uses existing framework but creates custom sub-workflows
workflow = agent.plan("production crisis response")  # Uses 'crisis_response_framework'

# Framework spawns specialized agents with custom workflows
workflow crisis_response_framework:
    fsm: FSM = {
        states: [START, assess_severity, spawn_specialists, coordinate_response, implement_solution, verify, COMPLETE],
        transitions: conditional_based_on_severity()
    }
    
    def execute(self, coordinator: Agent, crisis_data):
        severity = coordinator.reason("assess crisis severity", crisis_data)
        
        if severity.is_critical():
            # Spawn specialist agents with custom workflows
            quality_agent = spawn_agent("quality_specialist")
            maintenance_agent = spawn_agent("maintenance_specialist")
            supply_agent = spawn_agent("supply_chain_specialist")
            
            # Each creates custom workflow for their domain
            quality_workflow = quality_agent.plan("investigate contamination in crisis context")
            maint_workflow = maintenance_agent.plan("emergency equipment diagnosis")
            supply_workflow = supply_agent.plan("minimize supply chain disruption")
            
            # Parallel execution with coordination
            results = parallel_execute([
                (quality_agent, quality_workflow, crisis_data.quality),
                (maintenance_agent, maint_workflow, crisis_data.equipment),
                (supply_agent, supply_workflow, crisis_data.supply)
            ])
            
            # Coordinator synthesizes solution
            solution = coordinator.solve("integrate specialist recommendations", results)
            
            # Recursive check
            if not solution.is_complete():
                return coordinator.solve("handle remaining issues", solution.gaps)
                
        return solution
```

**Key Insight**: Complex scenarios require multi-agent coordination where each agent can create custom workflows for their specific sub-problems, demonstrating recursive problem-solving and dynamic workflow generation.

### Use Case Progression Summary
The four use cases demonstrate increasing complexity and capability:

| Use Case | Complexity | Key Capability | FSM Complexity | Workflow Source |
|----------|------------|----------------|----------------|-----------------|
| 0: Add Numbers | None | Direct execution | No FSM | No workflow |
| 1: Health Check | Simple | Workflow selection | Linear states | Existing library |
| 2: Batch Analysis | Moderate | Workflow synthesis | Branching logic | Agent-created |
| 3: Production Crisis | Complex | Multi-agent coordination | Parallel + conditional | Dynamic generation |

This progression ensures we build capabilities incrementally while always having concrete validation criteria for each phase.

## Goals
**Brief Description**: Create a clean, composable architecture where agents provide cognitive capabilities and workflows define reusable process structures, as demonstrated by our four driving use cases.

**Specific Objectives**:
- **Direct Execution** (Use Case 0): Enable agents to handle simple problems without workflow overhead
- **Workflow Reuse** (Use Case 1): Support selection and execution of existing, proven workflows
- **Workflow Synthesis** (Use Case 2): Allow agents to create custom workflows when no existing solution fits
- **Multi-Agent Coordination** (Use Case 3): Enable complex scenarios with recursive problem-solving and dynamic workflow generation
- Provide clear separation between agent intelligence and workflow process structure
- Make workflows agent-agnostic and reusable across different agent types

**Success Criteria**:
- Use Case 0: Simple calculations execute without workflow overhead (< 10ms)
- Use Case 1: Agent correctly selects existing workflows 95% of the time for standard procedures
- Use Case 2: Agent successfully synthesizes valid custom workflows for novel problem combinations
- Use Case 3: Multi-agent systems can coordinate through dynamic workflow generation
- Same workflow can be executed by different specialized agents
- New workflows can be added without modifying agent code

## Non-Goals
**Brief Description**: What we explicitly won't implement in this design.

- Direct agent-to-agent communication protocols (separate concern)
- Workflow versioning and deployment mechanisms (separate concern)
- Performance optimization for high-throughput scenarios (can be added later)
- Visual workflow design tools (separate concern)
- Workflow persistence and recovery (can be added later)

## Proposed Solution
**Brief Description**: Agents provide cognitive capabilities (plan, reason, solve, execute) while workflows contain FSMs that define process structure and state transitions.

The architecture separates intelligence from process structure:
- **Agents** are intelligent actors that can plan, reason, solve problems, and execute workflows
- **Workflows** are reusable process definitions containing FSMs that manage state transitions
- **FSMs** are pure data structures defining states, transitions, and process flow
- **Recursion** happens when workflows call `agent.solve()`, spawning sub-workflows

This approach allows agents to focus on providing intelligence while workflows provide proven, reusable process structures. The FSM ensures clear state management and progress tracking.

**KISS/YAGNI Analysis**: This design prioritizes radical simplicity - four agent methods, FSMs as plain data, automatic sub-workflow handling by runtime, and simple error patterns. We explicitly avoid complex workflow engines, sophisticated error state machines, or advanced validation until real usage demonstrates necessity. The architecture can evolve incrementally from simple linear workflows to complex multi-agent coordination as requirements emerge.

## Proposed Design

### System Architecture Diagram
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│    Agent    │    │   Workflow   │    │     FSM     │
│             │    │              │    │             │
│ plan()      │◄──►│ execute()    │◄──►│ states      │
│ reason()    │    │ fsm: FSM     │    │ transitions │
│ solve()     │    │ name: str    │    │ current     │
│ execute()   │    │              │    │             │
└─────────────┘    └──────────────┘    └─────────────┘
       ▲                   │                    │
       │                   ▼                    │
       │            ┌─────────────┐             │
       │            │ Sub-Workflow│◄────────────┘
       │            │ (Recursive) │
       └────────────┤             │
                    └─────────────┘
```

### Component Details

#### Agent Interface
**Brief Description**: Agents provide four fundamental cognitive capabilities that workflows can leverage.

```dana
interface Agent:
    plan(problem: str) -> Workflow          # Select/create workflow for problem
    reason(question: str, context: dict) -> Analysis  # Analysis and decisions  
    solve(problem: str, ...params) -> Solution        # Recursive problem solving
    execute(workflow: Workflow, data) -> Result       # Execute any workflow
```

**Motivation**: These four methods represent the fundamental cognitive capabilities needed for problem-solving: strategic planning, analytical reasoning, problem decomposition, and process execution. This minimal interface keeps agents focused on intelligence rather than process mechanics.

**Key Design Decisions**:
- `plan()` returns workflows (not just data) to make processes first-class objects
- `solve()` enables recursive problem decomposition through sub-workflows
- `reason()` provides domain-specific analysis and decision-making
- `execute()` allows agents to run any workflow, enabling composition

#### FSM Structure
**Brief Description**: FSMs are pure data structures that define process states and transitions without embedded behavior.

```dana
struct FSM:
    states: list[str]                           # All possible states
    initial_state: str                          # Starting state
    current_state: str                          # Current execution state
    transitions: dict[str, str]                 # 'from_state:event' -> to_state
```

**Motivation**: Making FSMs pure data structures separates process definition from execution logic. This makes workflows more testable, debuggable, and analyzable. The FSM becomes a specification that the workflow execution engine interprets.

#### Workflow Structure  
**Brief Description**: Workflows are structs containing FSMs and execution logic that delegates intelligence to agents.

```dana
struct Workflow:
    name: str
    fsm: FSM

# Struct function with receiver syntax
def execute(workflow: Workflow, agent: Agent, data) -> Solution:
    workflow.fsm.current_state = workflow.fsm.initial_state
    context = {"data": data}
    
    while workflow.fsm.current_state not in terminal_states:
        event = handle_current_state(workflow, agent, context)
        transition_key = f"{workflow.fsm.current_state}:{event.type}"
        workflow.fsm.current_state = workflow.fsm.transitions[transition_key]
    
    return context["result"]
```

**Motivation**: Workflows focus on process orchestration while delegating intelligent decisions to agents. This separation allows the same workflow to be used by different agents with different capabilities and domain knowledge.

### Data Flow Diagram
```
User Problem
     │
     ▼
┌─────────────────┐
│ agent.solve()   │──┐
└─────────────────┘  │
     │               │ (Recursive)
     ▼               │
┌─────────────────┐  │
│ agent.plan()    │  │
└─────────────────┘  │
     │               │
     ▼               │
┌─────────────────┐  │
│ workflow.       │  │
│ execute(agent)  │  │
└─────────────────┘  │
     │               │
     ▼               │
┌─────────────────┐  │
│ FSM State       │  │
│ Transitions     │  │
└─────────────────┘  │
     │               │
     ▼               │
┌─────────────────┐  │
│ agent.reason()  │  │
│ agent.solve()   │──┘
└─────────────────┘
     │
     ▼
   Solution
```

## Proposed Implementation

### Core Architecture
**Brief Description**: Implementation centers on Dana struct functions and FSM data structures with clean agent-workflow separation.

**Key Components**:
1. **Agent Interface**: Four methods providing cognitive capabilities
2. **FSM Struct**: Pure data structure for state management
3. **Workflow Struct**: Contains FSM and execution logic
4. **Pipeline Syntax**: Auto-generates simple FSMs from function composition
5. **Event System**: Drives state transitions based on agent actions

**Pipeline Syntax Support**:
```dana
# Simple syntax auto-generates FSM
workflow batch_inspection() = collect_samples | run_tests | analyze_results

# Equivalent to:
workflow batch_inspection:
    fsm: FSM = auto_generate_linear_fsm(["collect_samples", "run_tests", "analyze_results"])
```

**State Name Generation**: Function names become state names directly (e.g., `collect_samples` function creates `collect_samples` state).

**Automatic Sub-Workflow Handling**: When workflows call `agent.solve()`, the runtime automatically spawns sub-workflows without explicit management. No need for developers to track execution stacks or sub-workflow lifecycle.

**Testing Strategy**: 
- Unit tests for FSM data structure manipulation
- Integration tests for agent-workflow interaction
- End-to-end tests for complex recursive scenarios
- Property-based testing for FSM state transition validity

#### Error Handling Strategy
**Brief Description**: Start with simple try/catch patterns, evolve based on real failure patterns.

```dana
def execute(workflow: Workflow, agent: Agent, data) -> Solution:
    try:
        return workflow.run_fsm(agent, data)
    except WorkflowError as e:
        if not workflow.retried:
            workflow.retried = true
            return workflow.execute(agent, data)  # Single retry
        else:
            raise WorkflowExecutionError(e)
```

**YAGNI Principle**: Avoid complex error state machines initially. Add sophisticated error handling only when specific failure patterns emerge in production.

#### Workflow Validation
**Brief Description**: Minimal essential validations to catch obvious errors.

```dana
def validate_workflow(workflow: Workflow) -> bool:
    return (workflow.fsm.states and 
            workflow.fsm.initial_state in workflow.fsm.states and
            workflow.fsm.transitions)
```

**KISS Principle**: Start with basic structural checks. Add complex validation (reachability analysis, etc.) only when debugging real issues.

#### Agent Selection Strategy
**Brief Description**: Simple decision tree for workflow selection and creation.

```dana
agent.plan(problem) -> Workflow:
    if is_arithmetic(problem):
        return None  # Direct computation
    
    exact_workflow = workflow_library.find_exact_match(problem)  
    if exact_workflow:
        return exact_workflow
    
    return create_simple_workflow(problem)  # Basic linear workflow
```

**Evolution Strategy**: Start with exact matching and basic creation. Add similarity matching and sophisticated synthesis only when simple approach proves insufficient.

## Implementation Priorities (KISS/YAGNI Approach)

### Phase 1: Minimal Viable System
- Basic FSM struct and linear workflow execution
- Four agent methods with simple implementations  
- Try/catch error handling with single retry
- Exact-match workflow selection only

### Phase 2: Essential Extensions  
- Branching FSMs when linear workflows prove insufficient
- Basic workflow validation (structural checks only)
- Simple workflow creation for unmatched problems

### Phase 3: Real-World Hardening
- Enhanced error handling based on observed failure patterns
- Workflow similarity matching if exact-match proves limiting
- Advanced validation if debugging becomes difficult

### Phase 4: Optimization
- Performance improvements based on actual bottlenecks
- Sophisticated agent selection based on usage patterns
- Complex FSM features based on real requirements

**Key Principle**: Implement minimal functionality first, then evolve based on actual usage rather than anticipated complexity.