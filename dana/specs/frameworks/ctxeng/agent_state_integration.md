# ContextEngineer and AgentState Integration

## Overview

This specification defines how the Context Engineering Framework (ctxeng) integrates with the centralized AgentState architecture. The integration leverages AgentState as the single source of truth for context assembly, with ContextEngineer focusing purely on prompt generation.

## Design Goals

1. **Clear Separation**: AgentState owns context assembly, ContextEngineer owns prompt generation
2. **Type Safety**: Structured ContextData provides type-safe context assembly
3. **Single Source of Truth**: AgentState is the authoritative source for all context
4. **Clean Interface**: Simple, focused APIs between components
5. **Framework Independence**: ContextEngineer remains decoupled from agent internals

## Integration Architecture

### Context Assembly Flow

```
User Query
    ↓
SolvingMixin.solve_sync()
    ↓
AgentState.assemble_context_data()  ← Single source of truth
    │
    ├─ Extract problem context
    ├─ Extract conversation context  
    ├─ Extract memory context
    ├─ Extract execution context
    └─ Extract resource context
    ↓
ContextData (structured, type-safe)
    ↓
ContextEngineer.engineer_context_structured()  ← Pure prompt generation
    ↓
Rich XML/Text Prompt
    ↓
LLM Processing
```

### Component Responsibilities

```
AgentState:
├─ Assembles structured ContextData from all state components
├─ Handles type conversion and validation
└─ Provides single source of truth for agent context

ContextEngineer:
├─ Receives structured ContextData
├─ Applies template selection and formatting
├─ Generates rich prompts (XML/Text)
└─ Focuses purely on prompt generation

SolvingMixin:
├─ Orchestrates the flow between AgentState and ContextEngineer
├─ Handles lazy initialization of ContextEngineer
└─ Integrates context engineering into agent solve workflow
```

## API Specifications

### AgentState Extensions

```python
class AgentState:
    """Extended to assemble structured context for ContextEngineer."""
    
    def assemble_context_data(self, query: str, template: str = "general") -> ContextData:
        """
        Assemble structured ContextData from agent state.
        
        This method creates a comprehensive ContextData object by extracting
        relevant information from all agent state components.
        
        Args:
            query: The query string
            template: Template name to use
            
        Returns:
            ContextData populated with agent state information
        """
        from dana.frameworks.ctxeng import (
            ContextData,
            ProblemContextData,
            WorkflowContextData,
            ConversationContextData,
            ResourceContextData,
            MemoryContextData,
            ExecutionContextData,
        )
        
        # Create base context data
        context_data = ContextData.create_for_agent(query=query, template=template)
        
        # Extract problem context
        if self.problem_context:
            context_data.problem = ProblemContextData(
                problem_statement=self.problem_context.problem_statement,
                objective=self.problem_context.objective,
                original_problem=self.problem_context.original_problem,
                depth=self.problem_context.depth,
                constraints=self.problem_context.constraints,
                assumptions=self.problem_context.assumptions,
            )
        
        # Extract conversation context
        if self.mind and self.mind.memory:
            conversation_history = self.mind.recall_conversation(3)
            if isinstance(conversation_history, list):
                conversation_history = "\n".join(str(item) for item in conversation_history)
            elif not isinstance(conversation_history, str):
                conversation_history = str(conversation_history)
            
            context_data.conversation = ConversationContextData(
                conversation_history=conversation_history,
                recent_events=self._get_recent_events(),
                user_preferences=self.mind.get_user_context(),
                context_depth="standard",
            )
        
        # Extract memory context
        if self.mind:
            relevant_memories = self.mind.recall_relevant(self.problem_context) if self.problem_context else []
            if not isinstance(relevant_memories, list):
                relevant_memories = [str(relevant_memories)] if relevant_memories else []
            else:
                relevant_memories = [str(memory) for memory in relevant_memories]
            
            context_priorities = self.mind.assess_context_needs(self.problem_context, "standard") if self.problem_context else []
            if not isinstance(context_priorities, list):
                context_priorities = [str(context_priorities)] if context_priorities else []
            else:
                context_priorities = [str(priority) for priority in context_priorities]
            
            context_data.memory = MemoryContextData(
                relevant_memories=relevant_memories,
                user_model=self.mind.get_user_context(),
                world_model=self.mind.world_model.to_dict() if self.mind.world_model else {},
                context_priorities=context_priorities,
            )
        
        # Extract execution context
        if self.execution:
            context_data.execution = ExecutionContextData(
                session_id=self.session_id,
                execution_constraints=self.execution.get_constraints(),
                environment_info={},
            )
        
        # Extract resource context
        if self.capabilities:
            context_data.resources = ResourceContextData(
                available_resources=list(self.capabilities.get_available_tools().keys()),
                resource_limits=self.execution.resource_limits.to_dict() if self.execution else {},
                resource_usage=self.execution.current_metrics.to_dict() if self.execution else {},
                resource_errors=[],
            )
        
        return context_data
    
    def _get_recent_events(self) -> list[str]:
        """Get recent events from timeline for context."""
        if not self.timeline or not self.timeline.events:
            return []
        
        try:
            events = self.timeline.events[-5:]  # Last 5 events
            return [f"{e.event_type}: {e.data.get('description', 'No description')}" for e in events]
        except Exception:
            return []
```

### ContextEngineer Integration

```python
class ContextEngineer:
    """Simplified ContextEngineer that works with structured ContextData."""
    
    def engineer_context_structured(
        self,
        context_data: ContextData,
        **options,
    ) -> str:
        """
        Engineer optimized context using structured ContextData.
        
        Args:
            context_data: Structured context data object
            **options: Additional options
            
        Returns:
            Optimized prompt string (XML or text format)
        """
        # Convert structured data to dictionary for template processing
        context_dict = context_data.to_dict()
        
        # Use the structured data's template and query
        query = context_data.query
        template = context_data.template
        
        # Apply relevance filtering and token optimization
        optimized_context = self._optimize_context(context_dict, query, template, options)
        
        # Get template and assemble final prompt
        template_obj = self._template_manager.get_template(template, self.format_type)
        return template_obj.assemble(query, optimized_context, options)
```

### SolvingMixin Integration

```python
class SolvingMixin:
    """Mixin that integrates ContextEngineer into agent solve workflow."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._context_engineer = None  # Lazy initialization
    
    @property
    def context_engineer(self) -> ContextEngineer:
        """Get or create the context engineer for this agent."""
        if self._context_engineer is None:
            self._context_engineer = ContextEngineer.from_agent(self)
        return self._context_engineer
    
    def solve_sync(self, problem_or_workflow: str | WorkflowInstance, **kwargs) -> Any:
        """Enhanced solve method with context engineering."""
        if isinstance(problem_or_workflow, str):
            # Set problem context in centralized state
            self.state.set_problem_context(ProblemContext(problem_statement=problem_or_workflow))
            
            # Let AgentState assemble its own ContextData
            context_data = self.state.assemble_context_data(problem_or_workflow, template="problem_solving")
            
            # Use ContextEngineer with structured data
            rich_prompt = self.context_engineer.engineer_context_structured(context_data)
            problem_or_workflow = rich_prompt
        
        # Continue with workflow planning and execution
        workflow = self.plan_sync(problem_or_workflow, **kwargs)
        return workflow.execute(**kwargs)
```

## Benefits of the New Architecture

### 1. **Clear Separation of Concerns**
- **AgentState**: Owns context assembly logic and is the single source of truth
- **ContextEngineer**: Focuses purely on prompt generation and template management
- **SolvingMixin**: Orchestrates the flow between components

### 2. **Type Safety**
- **Structured ContextData**: Provides type-safe context assembly with validation
- **Explicit Interfaces**: Clear contracts between components
- **Better Error Handling**: Type checking catches issues early

### 3. **Simplified Integration**
- **Single Method**: `AgentState.assemble_context_data()` handles all context assembly
- **Lazy Initialization**: ContextEngineer is created only when needed
- **Clean API**: Simple, focused methods with clear responsibilities

### 4. **Maintainability**
- **Single Source of Truth**: All context logic centralized in AgentState
- **Easy Testing**: Each component can be tested independently
- **Clear Dependencies**: Explicit relationships between components

## Migration Guide

### From Old Architecture
The old architecture used resource discovery and manual context assembly:

```python
# Old approach (removed)
ctx = ContextEngine.from_agent(agent)
ctx.add_resource("memory", agent.mind.memory)
ctx.add_workflow("current", workflow)
prompt = ctx.assemble(query, context, template="problem_solving")
```

### To New Architecture
The new architecture uses structured context assembly:

```python
# New approach (current)
context_data = agent.state.assemble_context_data(query, template="problem_solving")
prompt = agent.context_engineer.engineer_context_structured(context_data)
```

### Key Changes
1. **No Resource Discovery**: AgentState handles all context extraction internally
2. **Structured Data**: ContextData provides type-safe context assembly
3. **Simplified API**: Single method for context assembly, single method for prompt generation
4. **Better Integration**: Seamless integration with agent solve workflow
