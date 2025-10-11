# Design Document: Agent-Workflow FSM System

<!-- text markdown -->
```text
Author: Christopher Nguyen
Version: 4.0
Date: 2025-01-22
Status: Updated - Direct Dana Type System Integration
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
- Managing workflow discovery, storage, and lifecycle
- Coordinating multiple agents in complex problem-solving scenarios
- Ensuring reliable LLM communication with structured guarantees

Without this structure, agents become monolithic, processes become ad-hoc, and it's difficult to build reliable, maintainable AI automation systems.

## LLM Communication Guarantees

### **Structured LLM Interaction Design**

The system uses **YAML requests** and **JSON responses** to ensure reliable LLM communication under KISS principles.

#### **YAML Request Templates**
```yaml
# workflow_selection.yaml
system_prompt: |
  You are a workflow selection expert. Analyze the problem and select the most appropriate workflow.
  Respond with valid JSON only, no additional text.

task:
  type: workflow_selection
  problem: "{{problem}}"
  available_workflows:
    {{#each workflows}}
    - name: "{{name}}"
      description: "{{description}}"
      domain: "{{domain}}"
    {{/each}}

constraints:
  - Only select from available workflows listed above
  - If no workflow fits, respond with "create_new"
  - Provide confidence score between 0 and 1
  - Give brief reason for selection
  - Respond with valid JSON only

expected_response_format:
  {
    "selected_workflow": "workflow_name_or_create_new",
    "confidence": 0.95,
    "reason": "brief explanation",
    "alternatives": ["workflow1", "workflow2"]
  }
```

#### **JSON Response Validation**
```dana
def validate_json_response(response: str, expected_schema: dict) -> tuple[bool, dict]:
    """Validate JSON response against schema."""
    try:
        parsed = json.loads(response)
        if not validate_json_schema(parsed, expected_schema):
            return False, {"error": "Schema validation failed"}
        return True, parsed
    except json.JSONDecodeError as e:
        return False, {"error": f"Invalid JSON format: {e}"}
```

### **LLM Communication Guarantees**

#### **✅ Response Format Guarantees**
- Responses are always valid JSON
- Responses match expected schema
- Required fields are always present
- Data types are correct
- Enum values are valid

#### **✅ Response Quality Guarantees**
- Responses are within expected bounds
- Confidence scores are valid (0-1)
- Reasons are concise and relevant
- No malformed or unexpected responses

#### **✅ Reliability Guarantees**
- Invalid responses are caught and retried
- System doesn't crash on malformed responses
- Fallback behavior when LLM fails
- Consistent response handling

#### **✅ Predictability Guarantees**
- Response structure is always known
- Response validation is deterministic
- Error handling is consistent
- Retry logic is reliable

### **LLM Integration Strategy**

#### **Minimal LLM Dependency**
```dana
def execute_workflow_with_llm_enhancement(workflow: Workflow, agent: Agent, data: dict) -> dict:
    """Execute workflow with optional LLM enhancement."""
    # Core execution (LLM-free)
    result = execute_workflow_core(workflow, data)
    
    # Optional LLM enhancement
    if result.get("status") == "completed" and agent.has_llm_capability():
        enhanced_result = agent.enhance_result_safely(result)
        if enhanced_result.get("status") == "success":
            result.update(enhanced_result.get("enhancements", {}))
    
    return result
```

#### **Structured LLM Interface**
```dana
class YAMLRequestJSONResponseLLM:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.templates_dir = "templates/"
        self.schemas = load_response_schemas()
    
    def solve_structured(self, request_type: str, data: dict) -> dict:
        """Make YAML request and expect JSON response."""
        # Create YAML request from template
        yaml_request = self.create_yaml_request(request_type, data)
        
        # Make LLM call
        response = self.agent.solve(yaml_request)
        
        # Parse and validate JSON response
        is_valid, parsed_response = self.validate_json_response(response, request_type)
        
        if is_valid:
            return {"status": "success", "result": parsed_response}
        else:
            return {"status": "failed", "error": parsed_response.get("error")}
```

## Driving Use Cases

### Use Case 0: Add Two Numbers (No Workflow)
**Scenario**: User asks "What is 47 + 89?"

**Solution**: Agent handles directly without any workflow
```dana
result = agent.solve("47 + 89")  # Returns 136 via direct computation
```

**Key Insight**: Not every problem needs a workflow. Simple computations are handled directly by the agent, demonstrating that workflows are for *processes*, not calculations.

### Use Case 1: Equipment Health Check (Existing Workflow)
**Scenario**: Manufacturing plant needs daily automated health checks on critical equipment using standard operating procedures.

**Problem**: "Check equipment health for Line 3"

**Solution Flow**:
```dana
# Agent finds existing workflow in registry using structured LLM call
workflow = agent.plan_structured({
    "problem": "check equipment health",
    "available_workflows": ["daily_equipment_check", "data_analysis"]
})  # Returns existing 'daily_equipment_check' with confidence score

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

**Key Insight**: Common procedures are codified as reusable workflows and stored in a registry. Agents leverage existing, proven processes rather than reinventing them.

### Use Case 2: Custom Batch Analysis (Creates New Workflow)
**Scenario**: Pharmaceutical batch fails with unusual combination of contamination indicators and electrical anomalies not covered by standard procedures.

**Problem**: "Investigate batch B-2847 failure with contamination readings + power fluctuations"

**Solution Flow**:
```dana
# No existing workflow matches this specific combination
workflow = agent.plan_structured({
    "problem": "investigate unusual batch failure with contamination + electrical anomalies",
    "available_workflows": ["standard_batch_analysis", "contamination_check"]
})  # Returns "create_new" with confidence 0.85

# Agent synthesizes custom workflow using structured LLM calls
workflow = agent.create_workflow_structured({
    "problem": "investigate unusual batch failure with contamination + electrical anomalies",
    "domain": "pharmaceutical",
    "constraints": "must handle both contamination and electrical analysis"
})

# Agent synthesizes custom workflow
workflow custom_contamination_electrical_investigation:
    fsm: FSM = {
        states: [START, contamination_analysis, electrical_testing, cross_correlation, root_cause, COMPLETE],
        initial_state: START
    }
    
    def execute(self, agent: Agent, failure_data):
        # Decompose into sub-problems using structured LLM calls
        contamination = agent.solve_structured("data_analysis", {
            "analysis_type": "contamination_patterns",
            "data": failure_data.contamination
        })
        
        electrical = agent.solve_structured("data_analysis", {
            "analysis_type": "electrical_anomalies", 
            "data": failure_data.electrical
        })
        
        # Reason about correlation using structured LLM call
        correlation = agent.reason_structured({
            "context": {"contamination": contamination, "electrical": electrical},
            "question": "how are contamination and electrical issues related?",
            "reasoning_type": "correlation_analysis"
        })
        
        # Determine root cause
        if correlation.result.indicates_common_cause():
            root_cause = agent.solve_structured("root_cause_analysis", {
                "correlation_data": correlation.result,
                "analysis_type": "common_cause"
            })
        else:
            root_cause = agent.reason_structured({
                "context": correlation.result,
                "question": "prioritize independent failures",
                "reasoning_type": "prioritization"
            })
            
        return {"root_cause": root_cause, "remediation": agent.plan_structured({
            "problem": "fix " + root_cause,
            "available_workflows": ["standard_fix", "custom_fix"]
        })}
```

**Key Insight**: When no existing workflow fits, agents can synthesize new workflows by composing their cognitive capabilities (solve, reason, plan) into novel process structures. New workflows are automatically registered for future reuse.

### Use Case 3: Production Crisis Management (Multi-Agent Coordination)
**Scenario**: Manufacturing plant experiences critical equipment failure requiring immediate response from multiple specialized teams.

**Problem**: "Critical failure on Line 3 - equipment down, quality issues detected, supply chain impact"

**Solution Flow**:
```dana
# Framework spawns specialized agents with custom workflows
workflow crisis_response_framework:
    fsm: FSM = {
        states: [START, assess_severity, spawn_specialists, coordinate_response, implement_solution, verify, COMPLETE],
        transitions: conditional_based_on_severity()
    }
    
    def execute(self, coordinator: Agent, crisis_data):
        # Assess severity using structured LLM call
        severity = coordinator.reason_structured({
            "context": crisis_data,
            "question": "assess crisis severity and required response level",
            "reasoning_type": "severity_assessment"
        })
        
        if severity.result.is_critical():
            # Spawn specialist agents with custom workflows
            quality_agent = spawn_agent("quality_specialist")
            maintenance_agent = spawn_agent("maintenance_specialist")
            supply_agent = spawn_agent("supply_chain_specialist")
            
            # Each creates custom workflow for their domain using structured calls
            quality_workflow = quality_agent.plan_structured({
                "problem": "investigate contamination in crisis context",
                "domain": "quality_assurance",
                "urgency": "critical"
            })
            
            maint_workflow = maintenance_agent.plan_structured({
                "problem": "emergency equipment diagnosis",
                "domain": "maintenance",
                "urgency": "critical"
            })
            
            supply_workflow = supply_agent.plan_structured({
                "problem": "minimize supply chain disruption",
                "domain": "supply_chain",
                "urgency": "critical"
            })
            
            # Parallel execution with coordination
            results = parallel_execute([
                (quality_agent, quality_workflow, crisis_data.quality),
                (maintenance_agent, maint_workflow, crisis_data.equipment),
                (supply_agent, supply_workflow, crisis_data.supply)
            ])
            
            # Coordinator synthesizes solution using structured LLM call
            solution = coordinator.solve_structured("solution_integration", {
                "specialist_results": results,
                "integration_type": "crisis_response"
            })
            
            # Recursive check using structured LLM call
            if not solution.result.is_complete():
                remaining_issues = coordinator.reason_structured({
                    "context": solution.result,
                    "question": "identify remaining issues that need resolution",
                    "reasoning_type": "gap_analysis"
                })
                
                return coordinator.solve_structured("issue_resolution", {
                    "remaining_issues": remaining_issues.result,
                    "resolution_type": "crisis_continuation"
                })
                
        return solution
```

**Key Insight**: Complex scenarios require multi-agent coordination where each agent can create custom workflows for their specific sub-problems, demonstrating recursive problem-solving and dynamic workflow generation.

### Use Case Progression Summary
The four use cases demonstrate increasing complexity and capability:

| Use Case | Complexity | Key Capability | FSM Complexity | Workflow Source | Registry Usage | LLM Usage |
|----------|------------|----------------|----------------|-----------------|----------------|-----------|
| 0: Add Numbers | None | Direct execution | No FSM | No workflow | None | Structured computation |
| 1: Health Check | Simple | Workflow selection | Linear states | Existing library | Find existing | Structured selection |
| 2: Batch Analysis | Moderate | Workflow synthesis | Branching logic | Agent-created | Store new | Structured synthesis |
| 3: Production Crisis | Complex | Multi-agent coordination | Parallel + conditional | Dynamic generation | Multi-agent registry | Structured coordination |

This progression ensures we build capabilities incrementally while always having concrete validation criteria for each phase.

## Goals
**Brief Description**: Create a clean, composable architecture where agents provide cognitive capabilities and workflows define reusable process structures, as demonstrated by our four driving use cases.

**Specific Objectives**:
- **Direct Execution** (Use Case 0): Enable agents to handle simple problems without workflow overhead
- **Workflow Reuse** (Use Case 1): Support selection and execution of existing, proven workflows through registry
- **Workflow Synthesis** (Use Case 2): Allow agents to create custom workflows when no existing solution fits
- **Multi-Agent Coordination** (Use Case 3): Enable complex scenarios with recursive problem-solving and dynamic workflow generation
- **Workflow Management**: Provide comprehensive workflow discovery, storage, and lifecycle management
- **Mixed Action Types**: Support both direct function calls and intelligent agent.solve() calls in workflows
- **LLM Communication Reliability**: Ensure structured, validated LLM interactions using YAML requests and JSON responses
- Provide clear separation between agent intelligence and workflow process structure
- Make workflows agent-agnostic and reusable across different agent types

**Success Criteria**:
- Use Case 0: Simple calculations execute without workflow overhead (< 10ms)
- Use Case 1: Agent correctly selects existing workflows 95% of the time for standard procedures
- Use Case 2: Agent successfully synthesizes valid custom workflows for novel problem combinations
- Use Case 3: Multi-agent systems can coordinate through dynamic workflow generation
- Registry provides efficient workflow discovery and storage
- Workflows support mixed action types (functions and agent calls)
- Same workflow can be executed by different specialized agents
- New workflows can be added without modifying agent code
- LLM responses are 99% valid JSON with correct schema
- LLM communication errors are handled gracefully with retry logic

## Non-Goals
**Brief Description**: What we explicitly won't implement in this design.

- Direct agent-to-agent communication protocols (separate concern)
- Workflow versioning and deployment mechanisms (separate concern)
- Performance optimization for high-throughput scenarios (can be added later)
- Visual workflow design tools (separate concern)
- Workflow persistence and recovery (can be added later)
- Advanced workflow analytics and monitoring (can be added later)
- Complex LLM reasoning or creative tasks (focus on structured, predictable interactions)
- Real-time LLM streaming or conversational interfaces (focus on request-response pattern)

## Proposed Solution
**Brief Description**: Agents provide cognitive capabilities (plan, reason, solve, execute) while workflows contain FSMs that define process structure and state transitions. A workflow registry manages workflow discovery and storage. LLM communication uses structured YAML requests and JSON responses for reliability.

The architecture separates intelligence from process structure:
- **Agents** are intelligent actors that can plan, reason, solve problems, and execute workflows
- **Workflows** are reusable process definitions containing FSMs that manage state transitions
- **FSMs** are pure data structures defining states, transitions, and process flow
- **Registry** provides workflow discovery, storage, and lifecycle management
- **Recursion** happens when workflows call `agent.solve()`, spawning sub-workflows
- **Mixed Actions** allow workflows to contain both direct function calls and intelligent agent calls
- **Structured LLM Communication** uses YAML requests and JSON responses for reliability

This approach allows agents to focus on providing intelligence while workflows provide proven, reusable process structures. The FSM ensures clear state management and progress tracking. Structured LLM communication ensures reliable, predictable interactions.

**KISS/YAGNI Analysis**: This design prioritizes radical simplicity - four agent methods, FSMs as plain data, automatic sub-workflow handling by runtime, simple error patterns, basic registry functionality, and structured LLM communication. We explicitly avoid complex workflow engines, sophisticated error state machines, advanced validation, complex registry features, or open-ended LLM interactions until real usage demonstrates necessity. The architecture can evolve incrementally from simple linear workflows to complex multi-agent coordination as requirements emerge.

## Proposed Design

### System Architecture Diagram
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────────┐
│    Agent    │    │   Workflow   │    │     FSM     │    │   Registry      │
│             │    │              │    │             │    │                 │
│ plan()      │◄──►│ execute()    │◄──►│ states      │    │ find_by_name()  │
│ reason()    │    │ fsm: FSM     │    │ transitions │    │ find_similar()  │
│ solve()     │    │ name: str    │    │ current     │    │ register()      │
│ execute()   │    │              │    │             │    │ list_all()      │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────────┘
       ▲                   │                    │                   ▲
       │                   ▼                    │                   │
       │            ┌─────────────┐             │                   │
       │            │ Sub-Workflow│◄────────────┘                   │
       │            │ (Recursive) │                                 │
       └────────────┤             │                                 │
                    └─────────────┘                                 │
                                                                     │
                    ┌───────────────────────────────────────────────┘
                    │
                    ▼
            ┌─────────────────┐
            │ Execution Engine│
            │                 │
            │ State Transitions│
            │ Event Handling  │
            │ Context Mgmt    │
            └─────────────────┘
                    │
                    ▼
            ┌─────────────────┐
            │ LLM Interface   │
            │                 │
            │ YAML Requests   │
            │ JSON Responses  │
            │ Validation      │
            └─────────────────┘
```

### Component Details

#### Agent Interface
**Brief Description**: Agents provide four fundamental cognitive capabilities that workflows can leverage.

```dana
interface Agent:
    plan(problem: str) -> Workflow          # Select/create workflow for problem
    plan_structured(request: dict) -> Workflow  # Structured workflow selection
    reason(question: str, context: dict) -> Analysis  # Analysis and decisions  
    reason_structured(request: dict) -> Analysis  # Structured reasoning
    solve(problem: str, ...params) -> Solution        # Recursive problem solving
    solve_structured(request: dict) -> Solution       # Structured problem solving
    execute(workflow: Workflow, data) -> Result       # Execute any workflow
```

**Motivation**: These four methods represent the fundamental cognitive capabilities needed for problem-solving: strategic planning, analytical reasoning, problem decomposition, and process execution. The structured variants ensure reliable LLM communication through YAML requests and JSON responses.

**Key Design Decisions**:
- `plan()` returns workflows (not just data) to make processes first-class objects
- `solve()` enables recursive problem decomposition through sub-workflows
- `reason()` provides domain-specific analysis and decision-making, including the core decision tree for problem-solving strategy
- `execute()` allows agents to run any workflow, enabling composition
- Structured variants (`plan_structured()`, `reason_structured()`, `solve_structured()`) ensure reliable LLM communication

### Problem-Solving Decision Tree
**Brief Description**: The core decision tree that `agent.reason()` uses to determine the optimal approach for solving any given problem.

**Decision Tree Flow**:
1. **Direct LLM Solution**: If the problem is within the powers of the LLM to solve directly now, state so and return the answer.
2. **Dana Code Generation**: If the problem is simple but the LLM can create Dana code to be executed to solve, state so and share the Dana code to be executed for the answer.
3. **Existing Workflow**: If the problem is slightly more complicated, but matches one of the known workflows, solve it using that workflow.
4. **Custom Workflow Generation**: If the problem is slightly more complicated, and there is no existing workflow, the LLM generates such a workflow to be executed.

**Implementation Strategy**:
- `agent.solve()` calls `agent.reason()` to determine the optimal approach
- `agent.reason()` analyzes the problem and returns a structured decision with the chosen strategy
- The decision includes confidence scores, reasoning, and specific actions to take
- Each branch of the decision tree has specific implementation patterns and fallback mechanisms

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

#### Workflow Registry
**Brief Description**: Central repository for storing, discovering, and managing workflows.

**Registry Interface**:
- `register(workflow: Workflow, metadata: WorkflowMetadata) -> bool`
- `find_by_name(name: str) -> Workflow | None`
- `find_by_domain(domain: str) -> list[Workflow]`
- `find_similar(problem: str) -> list[Workflow]`
- `list_all() -> list[Workflow]`
- `remove(name: str) -> bool`
- `update(workflow: Workflow) -> bool`

**Workflow Metadata**:
- `name: str` - Workflow identifier
- `domain: str` - Problem domain (e.g., "equipment_maintenance")
- `description: str` - Human-readable description
- `tags: list[str]` - Searchable tags
- `version: str` - Version identifier
- `author: str` - Creator information
- `created_at: str` - Creation timestamp
- `last_updated: str` - Last modification timestamp
- `usage_count: int` - Number of times used
- `success_rate: float` - Success percentage
- `avg_execution_time: float` - Average execution duration
- `complexity_score: float` - Workflow complexity metric
- `dependencies: list[str]` - Required resources or workflows
- `examples: list[dict]` - Usage examples

**Motivation**: The registry enables workflow reuse, discovery, and lifecycle management. It provides the infrastructure needed for agents to find existing workflows and store new ones.

#### Workflow Execution Engine
**Brief Description**: Runtime system that executes workflows by managing FSM state transitions and handling events.

**Key Components**:
- **State Management**: Tracks current FSM state and manages transitions
- **Event System**: Generates and processes events that drive state transitions
- **Context Management**: Maintains data flow through workflow execution
- **Action Execution**: Handles different types of workflow actions (functions, agent calls)
- **Error Handling**: Manages failures and recovery strategies
- **Progress Tracking**: Monitors execution state and provides status updates

**Execution Flow**:
1. Initialize workflow with input data
2. Set FSM to initial state
3. While not in terminal state:
   - Execute current state action
   - Generate event based on action result
   - Transition to next state based on event
   - Update execution context
4. Return final result

**Motivation**: The execution engine provides the runtime infrastructure needed to actually run workflows. It separates execution logic from workflow definition, enabling better testing and debugging.

#### Structured LLM Interface
**Brief Description**: Reliable LLM communication using YAML requests and JSON responses.

**Key Components**:
- **YAML Request Templates**: Human-readable, flexible request templates
- **JSON Response Validation**: Structured, parseable response validation
- **Schema Validation**: JSON schema validation for response quality
- **Error Handling**: Graceful handling of LLM failures and invalid responses
- **Retry Logic**: Automatic retry with improved prompts on failures

**Communication Flow**:
1. Create YAML request from template
2. Send request to LLM
3. Parse JSON response
4. Validate response against schema
5. Handle errors and retry if needed
6. Return validated result

**Motivation**: Structured LLM communication ensures reliable, predictable interactions while maintaining the flexibility needed for intelligent problem-solving.

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
│ Registry Lookup │  │
│ - find_by_name()│  │
│ - find_similar()│  │
└─────────────────┘  │
     │               │
     ▼               │
┌─────────────────┐  │
│ Workflow        │  │
│ Creation/       │  │
│ Selection       │  │
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
│ Execution Engine│  │
│ - State Mgmt    │  │
│ - Event System  │  │
│ - Context Mgmt  │  │
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
│ Mixed Actions   │  │
│ - Functions     │  │
│ - agent.solve() │  │
│ - agent.reason()│  │
└─────────────────┘  │
     │               │
     ▼               │
┌─────────────────┐  │
│ LLM Interface   │  │
│ - YAML Request  │  │
│ - JSON Response │  │
│ - Validation    │  │
└─────────────────┘  │
     │               │
     ▼               │
┌─────────────────┐  │
│ Registry Store  │  │
│ - register()    │  │
│ - update()      │  │
└─────────────────┘  │
     │               │
     ▼               │
   Solution
```

## Advanced Design Concepts

### Recursive Problem-Solving Mechanism
**Brief Description**: The core mechanism that enables complex problem decomposition through recursive `agent.solve()` calls.

**Recursion Flow**:
1. **Entry Point**: `agent.solve(problem)` starts the autonomous run
2. **Problem Assessment**: Agent determines if problem needs workflow or direct solution
3. **Workflow Creation**: If needed, agent creates workflow via `agent.plan()`
4. **Workflow Execution**: Workflow executes with FSM state transitions
5. **Recursive Calls**: Workflow states call `agent.solve()` for sub-problems
6. **Sub-Workflow Spawning**: Each `agent.solve()` call may create new workflows
7. **Result Aggregation**: Results flow back up through the recursion stack
8. **Context Propagation**: Context flows down and results flow back up

**Recursion Control Mechanisms**:
- **Depth Limits**: Maximum recursion depth to prevent infinite loops
- **Circular Dependency Detection**: Identify when problems reference themselves
- **Base Case Identification**: Detect when problems are simple enough for direct solution
- **Context Management**: Track and propagate context through recursion levels
- **Resource Limits**: Prevent resource exhaustion from deep recursion

**Motivation**: Recursion enables the system to handle arbitrarily complex problems by breaking them down into manageable sub-problems. This is essential for Use Case 3 (Multi-Agent Coordination) and enables sophisticated problem-solving capabilities.

### Mixed Action Types in Workflows
**Brief Description**: Workflows can contain different types of actions, each optimized for specific tasks.

**Action Types**:

1. **Direct Function Calls**:
   - **Purpose**: Fast, predictable operations
   - **Examples**: Data loading, calculations, formatting, validation
   - **Characteristics**: Deterministic, testable, low latency
   - **Use Cases**: Data operations, system calls, simple transformations

2. **Intelligent agent.solve() Calls**:
   - **Purpose**: Complex problem decomposition and analysis
   - **Examples**: LLM-powered analysis, decision making, problem solving
   - **Characteristics**: Non-deterministic, intelligent, potentially slow
   - **Use Cases**: Complex reasoning, creative problem solving, domain-specific analysis

3. **Structured agent.solve_structured() Calls**:
   - **Purpose**: Reliable LLM interactions with guaranteed response format
   - **Examples**: Workflow selection, data analysis, reasoning
   - **Characteristics**: Structured, validated, reliable
   - **Use Cases**: Critical decision making, data analysis, workflow management

**Motivation**: Mixed actions allow workflows to optimize for both performance and intelligence. Direct functions provide speed and reliability, while intelligent agent calls provide sophisticated problem-solving capabilities. Structured agent calls ensure reliable LLM communication.

### Multi-Agent Coordination
**Brief Description**: Complex scenarios requiring multiple specialized agents working together.

**Coordination Patterns**:

1. **Master-Slave Coordination**:
   - **Pattern**: One coordinator agent manages multiple specialist agents
   - **Use Cases**: Crisis management, complex project coordination
   - **Implementation**: Coordinator creates and manages sub-workflows

2. **Peer-to-Peer Coordination**:
   - **Pattern**: Multiple agents work independently with shared context
   - **Use Cases**: Parallel analysis, distributed problem solving
   - **Implementation**: Shared registry and context management

3. **Hierarchical Coordination**:
   - **Pattern**: Agents organized in hierarchy with delegation
   - **Use Cases**: Large-scale systems, organizational workflows
   - **Implementation**: Nested workflow execution with delegation

**Coordination Mechanisms**:
- **Shared Registry**: Common workflow and context storage
- **Context Propagation**: Data flow between agents
- **Result Integration**: Combining results from multiple agents
- **Conflict Resolution**: Handling disagreements between agents
- **Progress Tracking**: Monitoring coordination progress

**Motivation**: Multi-agent coordination enables solving complex problems that require diverse expertise. This is essential for Use Case 3 and enables sophisticated real-world problem-solving.

## Proposed Implementation

### Core Architecture
**Brief Description**: Implementation centers on Dana struct functions and FSM data structures with clean agent-workflow separation, enhanced by registry, execution engine, and structured LLM communication.

**Key Components**:
1. **Agent Interface**: Four methods providing cognitive capabilities with structured variants
2. **FSM Struct**: Pure data structure for state management
3. **Workflow Struct**: Contains FSM and execution logic
4. **Workflow Registry**: Central repository for workflow discovery and storage
5. **Workflow Execution Engine**: Runtime system for workflow execution
6. **Structured LLM Interface**: YAML requests and JSON responses for reliable communication
7. **Pipeline Syntax**: Auto-generates simple FSMs from function composition
8. **Event System**: Drives state transitions based on agent actions
9. **Mixed Action Support**: Functions, agent calls, and workflow orchestration

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

**Registry Integration**: Agents automatically search the registry for existing workflows and store new workflows for future use.

**Structured LLM Integration**: All LLM interactions use YAML requests and JSON responses with validation and error handling.

**Testing Strategy**: 
- Unit tests for FSM data structure manipulation
- Integration tests for agent-workflow interaction
- Registry tests for workflow discovery and storage
- Execution engine tests for state transitions and event handling
- LLM interface tests for YAML/JSON communication
- End-to-end tests for complete workflow execution

### Agent Selection Strategy
**Brief Description**: Simple decision tree for workflow selection and creation.

```dana
agent.plan(problem) -> Workflow:
    # Step 1: Check if problem is simple enough for direct execution
    if is_simple_problem(problem):
        return None  # Direct computation via agent.solve()
    
    # Step 2: Search registry for existing workflows
    exact_workflow = agent.workflow_registry.find_by_name(problem)
    if exact_workflow:
        return exact_workflow
    
    # Step 3: Search for similar workflows
    similar_workflows = agent.workflow_registry.find_similar(problem)
    if similar_workflows:
        # Use structured LLM call to determine if any similar workflow can be adapted
        selection_result = agent.plan_structured({
            "problem": problem,
            "available_workflows": similar_workflows
        })
        
        if selection_result.result.selected_workflow != "create_new":
            return selection_result.result.selected_workflow
    
    # Step 4: Create new workflow if no suitable existing one
    creation_result = agent.create_workflow_structured({
        "problem": problem,
        "domain": extract_domain(problem),
        "constraints": extract_constraints(problem)
    })
    
    new_workflow = creation_result.result.workflow
    
    # Step 5: Register the new workflow for future use
    metadata = WorkflowMetadata(
        name=new_workflow.name,
        domain=extract_domain(problem),
        description=f"Auto-generated workflow for: {problem}",
        tags=extract_tags(problem),
        version="1.0",
        author="auto-generated"
    )
    agent.workflow_registry.register(new_workflow, metadata)
    
    return new_workflow
```

**Evolution Strategy**: Start with exact matching and basic creation. Add similarity matching and sophisticated synthesis only when simple approach proves insufficient.

## Implementation Priorities (KISS/YAGNI Approach)

### Phase 1: Minimal Viable System (4 weeks)
- Basic FSM struct and linear workflow execution
- Four agent methods with simple implementations  
- Basic workflow registry (in-memory storage)
- Try/catch error handling with single retry
- Exact-match workflow selection only
- Direct function calls in workflows
- Basic YAML request templates for LLM communication
- Simple JSON response validation

### Phase 2: Essential Extensions (6 weeks)  
- Simple workflow execution engine
- Branching FSMs when linear workflows prove insufficient
- Basic workflow validation (structural checks only)
- Simple workflow creation for unmatched problems
- Persistent workflow registry
- Intelligent agent.solve() calls in workflows
- Structured LLM interface with YAML requests and JSON responses
- JSON schema validation for response quality
- Retry logic for LLM failures

### Phase 3: Real-World Hardening (8 weeks)
- Enhanced error handling based on observed failure patterns
- Workflow similarity matching if exact-match proves limiting
- Advanced validation if debugging becomes difficult
- Recursion control mechanisms
- Workflow metadata management
- Multi-agent coordination support
- Advanced YAML templates with examples and constraints
- Comprehensive JSON schema validation
- LLM response quality monitoring and improvement

### Phase 4: Optimization (6 weeks)
- Performance improvements based on actual bottlenecks
- Sophisticated agent selection based on usage patterns
- Complex FSM features based on real requirements
- Distributed workflow registry
- Advanced workflow synthesis
- Workflow optimization and auto-tuning
- Workflow analytics and monitoring
- LLM communication optimization and caching
- Advanced error recovery and fallback mechanisms

**Key Principle**: Implement minimal functionality first, then evolve based on actual usage rather than anticipated complexity.

## Updated Implementation Architecture

### **Direct Dana Type System Integration**
Our implementation takes a **direct integration approach** with Dana's core type system:

#### **✅ Core Architecture**
```
dana/builtin_types/
├── agent_system.py          # AgentInstance extends Dana's AgentType
└── workflow_system.py       # WorkflowInstance extends Dana's WorkflowType

dana/registry/
├── resource_registry.py     # RESOURCE_REGISTRY (global)
└── workflow_registry.py     # WORKFLOW_REGISTRY (global)
```

#### **✅ Benefits of Direct Integration**
- **Deeper Integration**: Direct extension of Dana's core types
- **Less Code**: No wrapper layers or duplicate functionality
- **Better Performance**: No overhead from wrapper classes
- **More Maintainable**: Evolves with Dana's type system
- **Same Interface**: Achieves the same simple interface as planned

#### **✅ Cross-Platform Compatibility**
- **Python API**: Works seamlessly with Python code
- **Dana Language**: Works seamlessly with Dana language syntax
- **Unified Interface**: Same methods work in both environments

#### **✅ Implementation Status**
- **Phase 1**: ✅ COMPLETE - All 4 problems solved successfully
- **Phase 2**: 🔄 IN PROGRESS - Multi-resource integration
- **Phase 3**: 📋 PLANNED - Dynamic problem-solving
- **Phase 4**: 📋 PLANNED - Multi-agent coordination

This approach is **superior to the original plan** because it leverages Dana's existing architecture more effectively while achieving the same goals with better performance and maintainability.