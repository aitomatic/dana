# Agent State Architecture

## Overview

The Agent State Architecture implements a centralized state management system where `AgentState` serves as the central hub coordinating all agent subsystems. This design eliminates duplication, provides clear separation of concerns, and creates a single source of truth for agent context.

## Core Design Principles

1. **Centralized Coordination**: AgentState owns and coordinates all subsystems
2. **Cognitive Unity**: All cognitive functions (memory, learning, reasoning) reside in AgentMind
3. **Clear Separation**: Each subsystem has a focused, non-overlapping responsibility
4. **Theory of Mind**: AgentMind provides intelligent modeling of users and the world
5. **Single Context Interface**: One method (`get_llm_context()`) provides optimized context for LLM calls

## Architecture Components

### 1. AgentState (Central Hub)

```python
@dataclass
class AgentState:
    """Central state hub that coordinates all agent subsystems."""
    
    # Core Components (owned references)
    problem_context: ProblemContext      # Current task/problem
    mind: AgentMind                      # ALL cognitive functions
    timeline: Timeline                   # Event log (audit trail)
    execution: ExecutionContext          # Runtime state & resources
    capabilities: CapabilityRegistry     # Available tools/strategies
    
    # Metadata
    session_id: str
    created_at: datetime
    last_updated: datetime
    
    def get_llm_context(self, depth: ContextDepth = "standard") -> dict:
        """Build optimal context for LLM based on current state."""
        
    def discover_resources_for_ctxeng(self) -> dict:
        """Helper for ContextEngine resource discovery."""
```

**Responsibilities:**
- Orchestrate all subsystems
- Provide unified context interface
- Manage session lifecycle
- Support resource discovery for frameworks

### 2. AgentMind (Cognitive System)

```python
class AgentMind:
    """Complete cognitive system including memory, understanding, and learning."""
    
    # Memory Systems (ALL memory types)
    memory: MemorySystem
    ├── conversation: ConversationMemory    # Dialog history
    ├── working: WorkingMemory             # Current task context
    ├── episodic: EpisodicMemory           # Past experiences
    └── semantic: SemanticMemory           # Facts & knowledge
    
    # Understanding Models
    user_model: UserModel                   # Theory of mind about users
    world_model: WorldModel                 # Environmental understanding
    
    # Learning & Adaptation
    patterns: PatternLibrary                # Learned strategies & contexts
    learning: LearningSystem                # Adaptation from experience
    
    def recall(self, query: str, context: ProblemContext) -> Memory:
        """Intelligent recall based on current context."""
        
    def form_memory(self, experience: Experience) -> None:
        """Decide what/how to remember from experience."""
        
    def assess_context_needs(self, problem: ProblemContext, depth: str) -> Priorities:
        """Determine what context is most important."""
        
    def suggest_approach(self, problem: ProblemContext) -> Approach:
        """Use memories + patterns to suggest approach."""
```

**Responsibilities:**
- Manage ALL memory types
- Model users and world
- Learn from experience
- Provide intelligent context prioritization
- Suggest optimal strategies

### 3. ProblemContext

```python
@dataclass
class ProblemContext:
    """Hierarchical problem decomposition and context."""
    
    problem_statement: str
    objective: str
    current: str | None = None
    depth: int = 0
    constraints: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    
    def create_subcontext(self, subproblem: str) -> ProblemContext:
        """Create child context for recursive solving."""
```

**Responsibilities:**
- Represent current problem/task
- Support hierarchical decomposition
- Track constraints and assumptions

### 4. ExecutionContext

```python
@dataclass
class ExecutionContext:
    """Runtime execution state and resource management."""
    
    workflow_id: str | None
    recursion_depth: int
    resource_limits: ResourceLimits
    current_metrics: RuntimeMetrics
    constraints: list[Constraint]
    
    def can_proceed(self) -> bool:
        """Check if execution can continue."""
        
    def get_constraints(self) -> dict:
        """Get current execution constraints."""
```

**Responsibilities:**
- Track execution state
- Manage resource limits
- Monitor runtime metrics
- Enforce constraints

### 5. CapabilityRegistry

```python
class CapabilityRegistry:
    """Registry of available capabilities and actions."""
    
    tools: dict[str, Tool]
    strategies: dict[str, Strategy]
    skills: dict[str, Skill]
    
    def get_available_actions(self) -> list[Action]:
        """Get currently available actions."""
        
    def can_execute(self, action: str) -> bool:
        """Check if action can be executed."""
```

**Responsibilities:**
- Manage available tools
- Track available strategies
- Provide capability discovery
- Validate action availability

### 6. Timeline

```python
class Timeline:
    """Immutable event log and audit trail."""
    
    events: list[TimelineEvent]
    
    def add_event(self, event: TimelineEvent) -> None:
        """Add event to timeline."""
        
    def get_recent_events(self, n: int) -> list[TimelineEvent]:
        """Get recent events for context."""
        
    def query_events(self, filters: dict) -> list[TimelineEvent]:
        """Query events with filters."""
```

**Responsibilities:**
- Maintain immutable event log
- Provide audit trail
- Support event queries
- Track conversation turns as events

## Key Design Decisions

### Memory Lives in Mind

**Rationale:**
- Memory is a cognitive function
- Learning requires memory access
- User modeling depends on conversation memory
- Natural conceptual alignment

**Benefits:**
- Unified memory interface
- Intelligent recall based on context
- Memory and learning are naturally connected
- Cleaner separation of concerns

### Timeline vs Memory

- **Timeline**: Immutable event log, "what happened", audit trail
- **Memory**: Processed, indexed, "what we learned/remember", cognitive function

### Single Context Interface

The `get_llm_context()` method provides:
- Automatic resource gathering
- Intelligent prioritization via AgentMind
- Template-aware context building
- Consistent interface for all LLM calls

## Integration Points

### ContextEngine Integration

```python
# ContextEngine can discover all resources from AgentState
engine = ContextEngine.from_agent_state(agent_state)

# Direct context assembly from state
enriched_context = engine.assemble_from_state(
    agent_state,
    template="problem_solving"
)
```

### Agent Instance Integration

```python
class AgentInstance:
    def __init__(self, ...):
        self.state = AgentState(
            problem_context=None,
            mind=AgentMind(),
            timeline=Timeline(),
            execution=ExecutionContext(),
            capabilities=CapabilityRegistry()
        )
    
    def solve_sync(self, problem: str):
        # Update problem context
        self.state.problem_context = ProblemContext(
            problem_statement=problem,
            objective="solve"
        )
        
        # Get optimized context
        context = self.state.get_llm_context()
        
        # Execute with context
        # ...
```

## Benefits

1. **Single Source of Truth**: All state in one place
2. **No Duplication**: Each concept lives exactly once
3. **Clear Boundaries**: Well-defined subsystem responsibilities
4. **Intelligent Context**: AgentMind provides smart prioritization
5. **Easy Integration**: Clean interfaces for frameworks
6. **Extensible**: New subsystems can be added easily
7. **Testable**: Clear separation enables unit testing
8. **Maintainable**: Logical organization reduces complexity

## Migration Notes

See `agent_state_migration.md` for detailed migration steps from the current architecture.