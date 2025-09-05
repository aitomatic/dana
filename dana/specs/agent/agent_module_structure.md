# Agent Module Structure Specification

## Overview

This document defines the module structure for the reorganized agent system with centralized AgentState and AgentMind containing all cognitive functions including memory.

## Module Structure

```
dana/core/agent/
├── __init__.py                 # Export AgentState, AgentInstance, AgentType
├── agent_state.py              # Central AgentState orchestrator
├── agent_instance.py           # Agent implementation (uses AgentState)
├── agent_type.py               # Agent type definitions
│
├── mind/                       # All cognitive functions
│   ├── __init__.py            # Export AgentMind
│   ├── agent_mind.py          # Main AgentMind class
│   ├── memory/                # Memory subsystem
│   │   ├── __init__.py        # Export MemorySystem
│   │   ├── memory_system.py  # Unified memory interface
│   │   ├── conversation.py   # Conversation memory
│   │   ├── working.py        # Working memory
│   │   ├── episodic.py       # Episodic memory
│   │   └── semantic.py       # Semantic memory
│   ├── models/                # Understanding models
│   │   ├── __init__.py
│   │   ├── user_model.py     # User understanding/preferences
│   │   └── world_model.py    # World/environment model
│   └── learning/              # Learning & adaptation
│       ├── __init__.py
│       ├── patterns.py        # Strategy/context patterns
│       └── adaptation.py      # Learning from experience
│
├── context/                    # Problem & execution context
│   ├── __init__.py            # Export ProblemContext, ExecutionContext
│   ├── problem_context.py     # Problem decomposition
│   └── execution_context.py   # Runtime state/resources
│
├── timeline/                   # Event logging (unchanged)
│   ├── __init__.py
│   ├── timeline.py           # Timeline class
│   └── events.py              # Event definitions
│
├── capabilities/               # Available actions
│   ├── __init__.py            # Export CapabilityRegistry
│   ├── registry.py            # Capability registry
│   ├── tools.py               # Tool definitions
│   └── strategies.py          # Strategy definitions
│
├── methods/                    # Agent methods/mixins (unchanged)
│   ├── __init__.py
│   ├── solving.py             # Solving methods
│   ├── reasoning.py           # Reasoning methods
│   ├── chat.py                # Chat methods
│   ├── converse.py            # Conversation methods
│   ├── llm.py                 # LLM interaction methods
│   ├── io.py                  # Input/output methods
│   └── logging.py             # Logging methods
│
└── utils/                      # Utilities (unchanged)
    ├── __init__.py
    ├── function_registry.py   # Function registration
    └── callbacks.py           # Callback utilities
```

## Module Descriptions

### Core Modules

#### `agent_state.py`
- **Purpose**: Central state orchestrator
- **Classes**: `AgentState`
- **Dependencies**: All subsystems (mind, context, timeline, capabilities, execution)
- **Key Methods**: 
  - `get_llm_context()` - Build optimized LLM context
  - `discover_resources_for_ctxeng()` - Support framework discovery

#### `agent_instance.py`
- **Purpose**: Agent implementation
- **Classes**: `AgentInstance`
- **Dependencies**: `AgentState`, methods mixins
- **Key Changes**: Uses centralized `self.state` instead of scattered attributes

#### `agent_type.py`
- **Purpose**: Agent type system
- **Classes**: `AgentType`
- **No Changes**: Remains as-is

### Mind Subsystem (`mind/`)

#### `mind/agent_mind.py`
- **Purpose**: Main cognitive system orchestrator
- **Classes**: `AgentMind`
- **Owns**: MemorySystem, UserModel, WorldModel, PatternLibrary, LearningSystem
- **Key Methods**:
  - `recall()` - Intelligent memory recall
  - `form_memory()` - Create new memories
  - `assess_context_needs()` - Prioritize context
  - `suggest_approach()` - Strategy selection

#### `mind/memory/memory_system.py`
- **Purpose**: Unified memory interface
- **Classes**: `MemorySystem`
- **Manages**: All memory types
- **Key Methods**:
  - `recall()` - Cross-memory recall
  - `store()` - Store new memories
  - `query()` - Query memories

#### `mind/memory/conversation.py`
- **Purpose**: Conversation memory
- **Classes**: `ConversationMemory`
- **Moved From**: `dana/frameworks/memory/conversation_memory.py`
- **Storage**: `~/.dana/chats/`

#### `mind/memory/working.py`
- **Purpose**: Working memory for current task
- **Classes**: `WorkingMemory`
- **New Module**: Extracted from agent instance `_memory`

#### `mind/memory/episodic.py`
- **Purpose**: Episodic memory of experiences
- **Classes**: `EpisodicMemory`
- **New Module**: For storing past problem-solving experiences

#### `mind/memory/semantic.py`
- **Purpose**: Semantic memory of facts
- **Classes**: `SemanticMemory`
- **New Module**: For domain knowledge

#### `mind/models/user_model.py`
- **Purpose**: User understanding
- **Classes**: `UserModel`, `UserProfile`
- **Extracted From**: `mind/agent_mind.py`
- **Storage**: `~/.models/users/`

#### `mind/models/world_model.py`
- **Purpose**: World/environment understanding
- **Classes**: `WorldModel`, `WorldState`
- **No Changes**: Remains as-is
- **Storage**: `~/.models/world/`

#### `mind/learning/patterns.py`
- **Purpose**: Pattern library
- **Classes**: `PatternLibrary`, `StrategyPattern`, `ContextPattern`
- **Extracted From**: `mind/agent_mind.py`
- **Storage**: `~/.models/strategies/`, `~/.models/contexts/`

#### `mind/learning/adaptation.py`
- **Purpose**: Learning from experience
- **Classes**: `LearningSystem`
- **New Module**: Centralized learning logic

### Context Subsystem (`context/`)

#### `context/problem_context.py`
- **Purpose**: Problem representation
- **Classes**: `ProblemContext`
- **Moved From**: `agent/context.py`
- **No Changes**: Logic remains same

#### `context/execution_context.py`
- **Purpose**: Runtime state
- **Classes**: `ExecutionContext`, `ResourceLimits`, `RuntimeMetrics`
- **New Module**: Extracted from `AgentState`
- **Contains**: workflow_id, recursion_depth, resource tracking

### Timeline Subsystem (`timeline/`)

No changes - remains as-is:
- `timeline.py` - Timeline class
- `events.py` - Event definitions

### Capabilities Subsystem (`capabilities/`)

#### `capabilities/registry.py`
- **Purpose**: Capability management
- **Classes**: `CapabilityRegistry`
- **New Module**: Extracted from `AgentState` and `AgentInstance`
- **Manages**: Tools, strategies, skills

#### `capabilities/tools.py`
- **Purpose**: Tool definitions
- **Classes**: `Tool`, `ToolRegistry`
- **Extracted From**: Various locations

#### `capabilities/strategies.py`
- **Purpose**: Strategy definitions
- **Classes**: `Strategy`, `StrategyRegistry`
- **Extracted From**: Various locations

### Methods (`methods/`)

No structural changes - remains as-is:
- Continue to be mixins used by `AgentInstance`
- Will use `self.state` instead of direct attributes

### Utils (`utils/`)

No changes - remains as-is:
- `function_registry.py`
- `callbacks.py`

## Import Examples

### Before (Current)
```python
from dana.core.agent import AgentInstance
from dana.core.agent.context import ProblemContext
from dana.frameworks.memory import ConversationMemory
```

### After (New Structure)
```python
from dana.core.agent import AgentInstance, AgentState
from dana.core.agent.context import ProblemContext, ExecutionContext
from dana.core.agent.mind import AgentMind
from dana.core.agent.mind.memory import MemorySystem, ConversationMemory
```

## Migration Path

### Phase 1: Create New Structure
1. Create new directories under `dana/core/agent/`
2. Create new base classes (`ExecutionContext`, `CapabilityRegistry`, `MemorySystem`)
3. Move `ConversationMemory` to `mind/memory/conversation.py`

### Phase 2: Refactor AgentState
1. Update `AgentState` to reference new subsystems
2. Add `get_llm_context()` method
3. Add resource discovery methods

### Phase 3: Refactor AgentMind
1. Move memory management into AgentMind
2. Extract `UserModel` and patterns to separate modules
3. Integrate `MemorySystem`

### Phase 4: Update AgentInstance
1. Use centralized `self.state`
2. Remove duplicate state tracking
3. Update method mixins to use `self.state`

### Phase 5: Update Frameworks
1. Update ContextEngine to use `AgentState`
2. Update tests
3. Update documentation

## Backwards Compatibility

### Maintained Interfaces
- `AgentInstance.solve_sync()` signature unchanged
- Method mixin interfaces unchanged
- Timeline event structure unchanged

### Deprecation Path
- Old memory access patterns will be deprecated with warnings
- Direct attribute access on AgentInstance will proxy to AgentState
- Grace period of 2 versions before removal

## Storage Locations

- `~/.dana/chats/` - Conversation memory
- `~/.models/users/` - User profiles
- `~/.models/strategies/` - Strategy patterns
- `~/.models/contexts/` - Context patterns
- `~/.models/world/` - World model data

## Benefits of New Structure

1. **Clear Organization**: Each subsystem in its own directory
2. **Reduced Coupling**: Clean interfaces between subsystems
3. **Better Testing**: Subsystems can be tested independently
4. **Easier Navigation**: Logical grouping of related code
5. **Framework Integration**: Single point for resource discovery
6. **Memory Unification**: All memory types in one place
7. **Cognitive Coherence**: Mind contains all cognitive functions