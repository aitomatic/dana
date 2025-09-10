# AgentState Architecture Migration Guide

## Overview

This guide provides a step-by-step migration path from the current distributed agent state to the new centralized AgentState architecture with AgentMind containing all cognitive functions.

## Migration Phases

### Phase 1: Foundation (Non-Breaking)
**Goal**: Create new structure alongside existing code

#### 1.1 Create New Directory Structure
```bash
dana/core/agent/
├── mind/
│   ├── memory/
│   ├── models/
│   └── learning/
├── context/
└── capabilities/
```

#### 1.2 Create New Base Classes
```python
# dana/core/agent/context/execution_context.py
@dataclass
class ExecutionContext:
    workflow_id: str | None = None
    recursion_depth: int = 0
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    current_metrics: RuntimeMetrics = field(default_factory=RuntimeMetrics)
    constraints: list[Constraint] = field(default_factory=list)

# dana/core/agent/capabilities/registry.py
class CapabilityRegistry:
    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self.strategies: dict[str, Strategy] = {}
        self.skills: dict[str, Skill] = {}

# dana/core/agent/mind/memory/memory_system.py
class MemorySystem:
    def __init__(self):
        self.conversation = ConversationMemory()
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
```

#### 1.3 Move ConversationMemory
```python
# Move from: dana/frameworks/memory/conversation_memory.py
# Move to:   dana/core/agent/mind/memory/conversation.py

# Add compatibility import in old location
# dana/frameworks/memory/conversation_memory.py
from dana.core.agent.mind.memory.conversation import ConversationMemory
__all__ = ['ConversationMemory']  # Backward compatibility
```

### Phase 2: AgentState Enhancement (Non-Breaking)
**Goal**: Enhance AgentState to be the central hub

#### 2.1 Update AgentState Class
```python
# dana/core/agent/agent_state.py
from .mind import AgentMind
from .context import ExecutionContext
from .capabilities import CapabilityRegistry

@dataclass
class AgentState:
    """Enhanced central state hub."""
    
    # Keep existing fields for compatibility
    current_problem: ProblemContext | None = None
    current_conversation_turn: int = 0
    timeline: Timeline = field(default_factory=Timeline)
    # ... other existing fields ...
    
    # Add new subsystems
    mind: AgentMind | None = None
    execution: ExecutionContext | None = None
    capabilities: CapabilityRegistry | None = None
    
    def __post_init__(self):
        """Initialize new subsystems if not provided."""
        if self.mind is None:
            self.mind = AgentMind()
        if self.execution is None:
            self.execution = ExecutionContext()
        if self.capabilities is None:
            self.capabilities = CapabilityRegistry()
        
        # Migrate existing data to new structure
        self._migrate_existing_data()
    
    def _migrate_existing_data(self):
        """Migrate existing fields to new subsystems."""
        if self.current_workflow_id:
            self.execution.workflow_id = self.current_workflow_id
        if self.execution_depth:
            self.execution.recursion_depth = self.execution_depth
        if self.available_strategies:
            for strategy in self.available_strategies:
                self.capabilities.strategies[strategy] = Strategy(strategy)
    
    def get_llm_context(self, depth: str = "standard") -> dict:
        """New unified context method."""
        # Implementation as specified
        pass
    
    # Keep old methods for compatibility with deprecation warnings
    def get_conversation_context(self, max_turns: int = 3) -> str:
        """Deprecated: Use get_llm_context() instead."""
        import warnings
        warnings.warn(
            "get_conversation_context is deprecated, use get_llm_context()",
            DeprecationWarning,
            stacklevel=2
        )
        return self._old_get_conversation_context(max_turns)
```

#### 2.2 Update AgentMind
```python
# dana/core/agent/mind/agent_mind.py
class AgentMind:
    """Enhanced with memory ownership."""
    
    def __init__(self):
        # Memory systems now owned by mind
        self.memory = MemorySystem()
        
        # Keep existing models
        self.user_model = UserModel()
        self.world_model = WorldModel()
        
        # Keep existing patterns
        self.patterns = PatternLibrary()
        self.learning = LearningSystem()
        
        # Migrate existing storage paths
        self._migrate_existing_data()
    
    def _migrate_existing_data(self):
        """Load existing data from old locations."""
        # Load from ~/.models/ if exists
        # Load from ~/.dana/chats/ if exists
        pass
```

### Phase 3: AgentInstance Integration (Breaking Changes)
**Goal**: Update AgentInstance to use centralized state

#### 3.1 Update AgentInstance
```python
# dana/core/agent/agent_instance.py
class AgentInstance:
    def __init__(self, agent_type: AgentType, values: dict):
        # ... existing init ...
        
        # Create centralized state
        self.state = AgentState()
        
        # Compatibility properties (with deprecation warnings)
        self._compatibility_mode = True
    
    @property
    def problem_context(self):
        """Compatibility property."""
        if self._compatibility_mode:
            warnings.warn("Direct access deprecated, use self.state.problem_context")
        return self.state.problem_context
    
    @problem_context.setter
    def problem_context(self, value):
        """Compatibility setter."""
        if self._compatibility_mode:
            warnings.warn("Direct access deprecated, use self.state.problem_context")
        self.state.problem_context = value
    
    # Update methods to use self.state
    def solve_sync(self, problem: str):
        """Updated to use centralized state."""
        self.state.problem_context = ProblemContext(
            problem_statement=problem,
            objective="solve"
        )
        
        # Use new context building
        context = self.state.get_llm_context()
        
        # Rest of implementation
```

#### 3.2 Update Method Mixins
```python
# dana/core/agent/methods/memory.py
class MemoryMixin:
    """Updated to use centralized state."""
    
    def remember_sync(self, key: str, value: Any):
        """Store in working memory via mind."""
        if hasattr(self, 'state') and self.state.mind:
            self.state.mind.memory.working.store(key, value)
        else:
            # Fallback for compatibility
            self._memory[key] = value
    
    def recall_sync(self, key: str) -> Any:
        """Recall from memory via mind."""
        if hasattr(self, 'state') and self.state.mind:
            return self.state.mind.memory.working.recall(key)
        else:
            # Fallback for compatibility
            return self._memory.get(key)
```

### Phase 4: Framework Updates (Breaking Changes)
**Goal**: Update frameworks to use new architecture

#### 4.1 Update ContextEngine
```python
# dana/frameworks/ctxeng/engine.py
class ContextEngine:
    @classmethod
    def from_agent(cls, agent: Any) -> "ContextEngine":
        """Updated to check for new state structure."""
        # Check if agent has new state structure
        if hasattr(agent, 'state') and isinstance(agent.state, AgentState):
            return cls.from_agent_state(agent.state)
        else:
            # Fallback to old discovery
            return cls._from_agent_legacy(agent)
    
    @classmethod
    def from_agent_state(cls, agent_state: AgentState) -> "ContextEngine":
        """New method for AgentState."""
        # Implementation as specified
        pass
```

#### 4.2 Update Tests
```python
# tests/unit/builtin_types/agent/test_agent_state.py
def test_centralized_state():
    """Test new centralized state."""
    state = AgentState()
    
    # Test new subsystems
    assert state.mind is not None
    assert state.execution is not None
    assert state.capabilities is not None
    
    # Test context building
    context = state.get_llm_context()
    assert "query" in context

def test_backward_compatibility():
    """Test backward compatibility."""
    state = AgentState()
    
    # Old field access should still work
    state.current_workflow_id = "test"
    assert state.execution.workflow_id == "test"
```

### Phase 5: Cleanup (Major Version)
**Goal**: Remove deprecated code

#### 5.1 Remove Deprecated Fields
```python
# dana/core/agent/agent_state.py
@dataclass
class AgentState:
    """Clean version without deprecated fields."""
    
    # Core components only
    problem_context: ProblemContext | None = None
    mind: AgentMind = field(default_factory=AgentMind)
    timeline: Timeline = field(default_factory=Timeline)
    execution: ExecutionContext = field(default_factory=ExecutionContext)
    capabilities: CapabilityRegistry = field(default_factory=CapabilityRegistry)
    
    # Metadata
    session_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # No more duplicate fields
```

#### 5.2 Remove Compatibility Code
- Remove compatibility properties from AgentInstance
- Remove fallback code from method mixins
- Remove legacy discovery from ContextEngine
- Clean up old import paths

## Migration Checklist

### For Each Component

- [ ] Create new module structure
- [ ] Implement new classes with tests
- [ ] Add compatibility layer
- [ ] Update dependent code
- [ ] Add deprecation warnings
- [ ] Update documentation
- [ ] Test backward compatibility
- [ ] Remove deprecated code (major version)

### Testing Strategy

#### Unit Tests
- Test each new subsystem independently
- Test AgentState integration
- Test backward compatibility

#### Integration Tests
- Test agent.solve() with new structure
- Test ContextEngine integration
- Test memory persistence

#### Migration Tests
- Test data migration from old to new structure
- Test compatibility properties
- Test deprecation warnings

## Risk Mitigation

### Gradual Migration
- Keep old code working during transition
- Provide compatibility layers
- Use feature flags if needed

### Data Migration
```python
# Utility script for data migration
def migrate_agent_data():
    """Migrate existing agent data to new structure."""
    # Migrate conversation memory
    old_path = Path("~/.dana/chats/").expanduser()
    new_path = Path("~/.models/memory/conversation/").expanduser()
    
    # Migrate user profiles
    # Migrate patterns
    # etc.
```

### Rollback Plan
- Tag release before migration
- Keep compatibility layer for 2 versions
- Document rollback procedure

## Timeline

### Version 1.x (Current)
- Phase 1: Foundation
- Phase 2: Enhancement
- Deprecation warnings added

### Version 2.0
- Phase 3: Integration
- Phase 4: Framework updates
- Full backward compatibility

### Version 3.0
- Phase 5: Cleanup
- Remove deprecated code
- Clean architecture only

## Benefits After Migration

1. **Cleaner Architecture**: Clear separation of concerns
2. **Better Performance**: No duplicate state tracking
3. **Easier Maintenance**: Logical module organization
4. **Improved Testing**: Isolated subsystems
5. **Framework Integration**: Single resource discovery point
6. **Cognitive Coherence**: Memory naturally part of mind
7. **Future Flexibility**: Easy to extend subsystems