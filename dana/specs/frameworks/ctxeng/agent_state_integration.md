# ContextEngine and AgentState Integration

## Overview

This specification defines how the Context Engineering Framework (ctxeng) integrates with the new centralized AgentState architecture. The integration leverages AgentState as the single source of truth for all context, eliminating the need for complex resource discovery.

## Design Goals

1. **Simplified Discovery**: Single point to discover all resources
2. **Intelligent Context**: Leverage AgentMind for context prioritization
3. **Clean Interface**: Clear, minimal API between systems
4. **Optimal Performance**: Avoid duplicate context gathering
5. **Framework Independence**: ContextEngine remains decoupled from agent internals

## Integration Architecture

### Resource Discovery Flow

```
AgentState ──discover_resources()──> ContextEngine
    │                                      │
    ├─ problem_context ─────────────────> Resources
    ├─ mind.memory ─────────────────────> Resources
    ├─ timeline ────────────────────────> Resources
    ├─ execution ───────────────────────> Resources
    └─ capabilities ────────────────────> Resources
```

### Context Assembly Flow

```
AgentState ──get_llm_context()──> Unified Context
    │                                   │
    v                                   v
AgentMind ──assess_priorities()──> ContextEngine
    │                                   │
    v                                   v
Memory ──recall_relevant()──────> Template Assembly
                                        │
                                        v
                                  Optimized Prompt
```

## API Specifications

### ContextEngine Extensions

```python
class ContextEngine:
    """Extended to work with centralized AgentState."""
    
    @classmethod
    def from_agent_state(cls, agent_state: AgentState) -> "ContextEngine":
        """
        Create ContextEngine from centralized AgentState.
        
        Args:
            agent_state: The centralized agent state
            
        Returns:
            Configured ContextEngine instance
        """
        engine = cls()
        
        # Discover all resources from AgentState
        resources = agent_state.discover_resources_for_ctxeng()
        
        # Register each resource
        for name, resource in resources.items():
            engine.add_resource(name, resource)
        
        return engine
    
    def assemble_from_state(
        self, 
        agent_state: AgentState, 
        template: str = None,
        **options
    ) -> str:
        """
        Assemble context directly from AgentState.
        
        Args:
            agent_state: The centralized agent state
            template: Template name (auto-detected if None)
            **options: Additional assembly options
            
        Returns:
            Optimized prompt string
        """
        # Get unified context from AgentState
        context = agent_state.get_llm_context(
            depth=options.get("depth", "standard")
        )
        
        # Let AgentMind suggest priorities
        if agent_state.mind:
            priorities = agent_state.mind.assess_context_needs(
                agent_state.problem_context,
                template or "general"
            )
            context = self._apply_priorities(context, priorities)
        
        # Assemble with template
        query = context.get("query", "")
        return self.assemble(query, context, template=template, **options)
```

### AgentState Support

```python
class AgentState:
    """AgentState methods supporting ContextEngine."""
    
    def discover_resources_for_ctxeng(self) -> dict[str, Any]:
        """
        Discover all resources for ContextEngine.
        
        Returns:
            Dictionary of resource name to resource object
        """
        resources = {}
        
        # Core resources
        if self.timeline:
            resources["event_history"] = self.timeline
            resources["timeline"] = self.timeline
        
        if self.problem_context:
            resources["problem_context"] = self.problem_context
        
        if self.capabilities:
            resources["workflow_registry"] = self.capabilities
            resources["capabilities"] = self.capabilities
        
        # Mind resources
        if self.mind:
            resources["memory"] = self.mind.memory
            resources["user_model"] = self.mind.user_model
            resources["world_model"] = self.mind.world_model
            
        # Execution resources
        if self.execution:
            resources["execution_context"] = self.execution
            
        return resources
    
    def get_llm_context(self, depth: str = "standard") -> dict[str, Any]:
        """
        Build unified context for LLM calls.
        
        Args:
            depth: Context depth ("minimal", "standard", "comprehensive")
            
        Returns:
            Dictionary with all context needed for LLM
        """
        context = {}
        
        # Problem context
        if self.problem_context:
            context.update({
                "query": self.problem_context.problem_statement,
                "problem_statement": self.problem_context.problem_statement,
                "objective": self.problem_context.objective,
                "constraints": self.problem_context.constraints,
                "assumptions": self.problem_context.assumptions,
                "depth": self.problem_context.depth,
            })
        
        # Memory context (from mind)
        if self.mind:
            # Conversation memory
            if depth != "minimal":
                n_turns = {"minimal": 1, "standard": 3, "comprehensive": 10}.get(depth, 3)
                context["conversation_history"] = self.mind.recall_conversation(n_turns)
            
            # Relevant memories
            if self.problem_context:
                context["relevant_memory"] = self.mind.recall_relevant(self.problem_context)
            
            # User context
            context["user_context"] = self.mind.get_user_context()
        
        # Timeline context
        if self.timeline and depth != "minimal":
            n_events = {"standard": 5, "comprehensive": 20}.get(depth, 5)
            context["recent_events"] = self.timeline.get_recent_events(n_events)
        
        # Capabilities context
        if self.capabilities:
            context["available_strategies"] = self.capabilities.strategies
            context["available_tools"] = self.capabilities.tools
        
        # Execution context
        if self.execution:
            context["execution_state"] = {
                "workflow_id": self.execution.workflow_id,
                "recursion_depth": self.execution.recursion_depth,
                "constraints": self.execution.constraints,
            }
        
        return context
```

### Resource Adapter Updates

```python
class AgentStateResource(ContextResource):
    """Adapter for AgentState as a context resource."""
    
    def __init__(self, agent_state: AgentState):
        self.agent_state = agent_state
        
    def get_context_for(self, query: str, **options) -> dict[str, Any]:
        """Get context from AgentState."""
        depth = options.get("depth", "standard")
        return self.agent_state.get_llm_context(depth)
    
    def get_priority(self) -> float:
        """AgentState is highest priority resource."""
        return 1.0
```

## Integration Patterns

### Pattern 1: Direct State Integration

```python
# In agent_instance.py
class AgentInstance:
    def solve_sync(self, problem: str) -> Any:
        # Update problem context
        self.state.problem_context = ProblemContext(
            problem_statement=problem,
            objective="solve"
        )
        
        # Create context engine if needed
        if not self._context_engine:
            from dana.frameworks.ctxeng import ContextEngine
            self._context_engine = ContextEngine.from_agent_state(self.state)
        
        # Assemble context directly from state
        enriched_context = self._context_engine.assemble_from_state(
            self.state,
            template="problem_solving"
        )
        
        # Use enriched context for LLM call
        return self._execute_with_context(enriched_context)
```

### Pattern 2: Standalone Context Assembly

```python
# Standalone usage
from dana.core.agent import AgentState
from dana.frameworks.ctxeng import ContextEngine

# Create or get agent state
agent_state = AgentState(...)

# Create context engine
engine = ContextEngine.from_agent_state(agent_state)

# Assemble context for specific need
context = engine.assemble_from_state(
    agent_state,
    template="analysis",
    depth="comprehensive"
)
```

### Pattern 3: Custom Resource Addition

```python
# Add custom resources beyond AgentState
engine = ContextEngine.from_agent_state(agent_state)

# Add additional custom resources
engine.add_resource("custom_data", custom_resource)
engine.add_workflow("special_workflow", workflow_instance)

# Assemble with both AgentState and custom resources
context = engine.assemble(
    query="analyze data",
    template="analysis",
    custom_param="value"
)
```

## Template Compatibility

### Required Context Keys by Template

| Template | Required from AgentState | Optional from AgentState |
|----------|-------------------------|-------------------------|
| `problem_solving` | `problem_statement`, `objective` | `constraints`, `assumptions`, `recent_events` |
| `conversation` | `query`, `conversation_history` | `user_context`, `recent_events` |
| `analysis` | `query` | `relevant_memory`, `execution_state` |
| `general` | `query` | All available context |

### Context Priority Hints from AgentMind

```python
class AgentMind:
    def assess_context_needs(
        self, 
        problem: ProblemContext,
        template: str
    ) -> ContextPriorities:
        """
        Suggest context priorities for template.
        
        Returns:
            ContextPriorities with:
            - turns: Number of conversation turns needed
            - memory_depth: How deep to search memory
            - include_world: Whether world model is relevant
            - filters: Event filters for timeline
        """
        # Use learned patterns to determine priorities
        if template == "problem_solving":
            if self._is_complex_problem(problem):
                return ContextPriorities(
                    turns=5,
                    memory_depth="deep",
                    include_world=True,
                    filters=["solution", "error", "decision"]
                )
        # ...
```

## Benefits

### For ContextEngine

1. **Single Discovery Point**: One method to get all resources
2. **Pre-structured Context**: AgentState provides organized context
3. **Intelligent Prioritization**: AgentMind helps optimize context
4. **Clean Integration**: No need to understand agent internals

### For AgentState

1. **Clear Interface**: Well-defined context building method
2. **Reusable Context**: Same context for multiple frameworks
3. **Centralized Logic**: Context building in one place
4. **Consistent Output**: Standardized context structure

### For Overall System

1. **Reduced Coupling**: Clean boundaries between systems
2. **Better Performance**: No duplicate context gathering
3. **Easier Testing**: Can test integration points separately
4. **Future Flexibility**: Easy to add new context types

## Migration Path

### Phase 1: Add New Methods
- Add `from_agent_state()` to ContextEngine
- Add `discover_resources_for_ctxeng()` to AgentState
- Add `get_llm_context()` to AgentState

### Phase 2: Update Integration Points
- Update `agent_instance.py` to use new methods
- Keep backward compatibility with old discovery

### Phase 3: Deprecate Old Methods
- Mark old `from_agent()` as deprecated
- Add deprecation warnings
- Update documentation

### Phase 4: Remove Old Methods
- Remove deprecated methods after grace period
- Clean up old resource discovery code

## Testing Strategy

### Unit Tests
```python
def test_context_engine_from_agent_state():
    """Test ContextEngine creation from AgentState."""
    state = create_test_agent_state()
    engine = ContextEngine.from_agent_state(state)
    
    # Verify resources discovered
    assert "problem_context" in engine._resources
    assert "memory" in engine._resources
    assert "timeline" in engine._resources

def test_agent_state_context_building():
    """Test AgentState builds correct context."""
    state = create_test_agent_state()
    context = state.get_llm_context("standard")
    
    # Verify context structure
    assert "query" in context
    assert "conversation_history" in context
    assert "available_strategies" in context
```

### Integration Tests
```python
def test_end_to_end_context_assembly():
    """Test full context assembly flow."""
    agent = AgentInstance(...)
    result = agent.solve_sync("test problem")
    
    # Verify context was assembled correctly
    # Verify ContextEngine was used
    # Verify result is correct
```

## Future Enhancements

1. **Context Caching**: Cache assembled context for reuse
2. **Incremental Updates**: Update context incrementally
3. **Context Versioning**: Track context schema versions
4. **Analytics**: Track what context is most useful
5. **Optimization**: Learn optimal context per template