# Architecture: Core Components and Their Connections

This document explains how the core components of Dana Agent architecture work together: repositories, codec, prompt engineer, timeline, event, and observer.

## Table of Contents

1. [Overview](#overview)
2. [Core Components](#core-components)
3. [Component Initialization](#component-initialization)
4. [Runtime Flow (STAR Loop)](#runtime-flow-star-loop)
5. [Storage Architecture](#storage-architecture)
6. [Component Interactions](#component-interactions)

---

## Overview

Dana Agent uses a composition-based architecture where components work together through well-defined interfaces. The architecture follows these principles:

- **Repository Pattern**: Storage abstraction for prompts, timeline, events, and learning
- **Codec-Based Communication**: Structured LLM response format for reliable parsing
- **Timeline Management**: Unified chronological record of all interactions
- **Observer Pattern**: Extensible environment observation system
- **Separation of Concerns**: Each component has a single, well-defined responsibility

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        STARAgent                            │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Codec      │  │  PromptAPI   │  │  Timeline    │    │
│  │              │──│              │──│              │    │
│  │ - Instructions│  │ - System     │  │ - Entries    │    │
│  │ - Formatting │  │   Prompts    │  │ - Context    │    │
│  │ - Parsing    │  │ - LLM Msgs   │  │ - Persist    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                  │             │
│         └─────────────────┼──────────────────┘             │
│                           │                                │
│  ┌──────────────┐  ┌──────▼───────┐  ┌──────────────┐    │
│  │ CodecTool    │  │  Repository  │  │  EventLogAPI │    │
│  │ Caller       │  │  Factory      │  │              │    │
│  │              │  │              │  │ - Events     │    │
│  │ - Parse      │  │ - Prompt     │  │ - Persist    │    │
│  │ - Execute    │  │ - Timeline   │  └──────┬───────┘    │
│  └──────────────┘  │ - Event      │         │            │
│                    │ - Learning   │         │            │
│                    └──────┬───────┘         │            │
│                           │                │            │
│                    ┌──────▼───────┐  ┌──────▼───────┐    │
│                    │  Observer    │  │   Learner    │    │
│                    │              │  │              │    │
│                    │ - observe()  │  │ - Reflect    │    │
│                    │ - start()    │  │ - Learn      │    │
│                    │ - stop()     │  │ - Persist    │    │
│                    └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Repositories

**Purpose**: Storage abstraction layer providing consistent interfaces for persistence across different storage backends.

**Location**: `dana/repositories/`

**Key Files**:
- `repository_factory.py` - Factory pattern for creating repositories
- `repository_protocol.py` - Protocol definitions for all repository types
- `local_file_repository.py` - Local file system implementation

**Repository Types**:

1. **PromptRepository**: Manages prompt versions and snapshots
   - Stores system prompt templates
   - Manages prompt versions with provenance and metrics
   - Path: `{codec}/{agent_class}/prompts/`

2. **TimelineRepository**: Persists conversation timeline entries
   - Saves timeline entries per session
   - Reads entries for session replay
   - Path: `{codec}/{agent_class}/timeline/{session_id}/`

3. **EventRepository**: Stores observation events
   - Saves events from Observer
   - Events are observation-only (no actions/tool calls)
   - Path: `{codec}/{agent_class}/events/{session_id}/`

4. **LearningRepository**: Manages learning data
   - Acquisitive learning loops (per interaction)
   - Episodic learning (per session)
   - Feedback storage
   - Path: `{codec}/{agent_class}/learnings/{session_id}/`

**Repository Factory Pattern**:

```python
# From dana/repositories/repository_factory.py
class RepositoryFactory:
    def __init__(self):
        self._creators = {
            RepositoryType.PROMPT: (LocalPromptRepository, FileStorageConfig()),
            RepositoryType.TIMELINE: (LocalTimelineRepository, FileStorageConfig()),
            RepositoryType.EVENT: (LocalEventRepository, FileStorageConfig()),
            RepositoryType.LEARNING: (LocalLearningRepository, FileStorageConfig()),
        }
    
    def create(self, type: RepositoryType, **kwargs) -> RepositoryProtocol:
        creator, storage_config = self._creators[type]
        return creator.instantiate(storage_config, **kwargs)
```

**Storage Path Structure**:

```
.dana/dana_agent/
└── {codec_name}/              # e.g., "CSXMLCodec"
    └── {agent_class}/          # e.g., "HVACAgent"
        ├── prompts/
        │   ├── system_prompt_template/
        │   │   ├── versions/
        │   │   │   ├── v1.prompt
        │   │   │   └── v2.prompt
        │   │   ├── version.txt
        │   │   ├── provenance.json
        │   │   └── metrics.json
        │   ├── agents/
        │   ├── resources/
        │   └── workflows/
        ├── timeline/
        │   └── {session_id}/
        │       └── timeline.json
        ├── events/
        │   └── {session_id}/
        │       └── events.jsonl
        └── learnings/
            └── {session_id}/
                ├── acquisitive/
                │   └── loop_*.json
                ├── episodic/
                │   └── learnings.md
                └── feedback/
                    └── feedback.md
```

---

### 2. Codec

**Purpose**: Defines structured LLM response format (encoder-decoder) for reliable tool call parsing.

**Location**: `dana/core/knowledge/prompts/codecs/`

**Key File**: `abstract_codec.py`

**Responsibilities**:

1. **Tool Calling Instructions**: Provides format specification for LLM
   ```python
   @classmethod
   @abstractmethod
   def get_instruction(cls) -> str:
       """Get the instruction for the codec format."""
   ```

2. **Method Signature Formatting**: Formats tool signatures for prompts
   ```python
   @classmethod
   @abstractmethod
   def construct(cls, signature: MethodSignature) -> str:
       """Construct a formatted string from a method signature."""
   ```

3. **Response Parsing**: Parses LLM responses to extract tool calls
   ```python
   @classmethod
   @abstractmethod
   def parse_method_call(cls, xml_string: str) -> ToolCall:
       """Parse a method call from a formatted string."""
   ```

**Codec Format Example (CSXMLCodec)**:

```xml
<thinking>
Internal reasoning about what to do...
</thinking>

<function_call>
  <invoke name="ResourceName:methodName">
    <parameter name="param1">value1</parameter>
  </invoke>
</function_call>
```

**Usage**:
- **PromptEngineer**: Uses `codec.get_instruction()` to include format instructions in system prompts
- **CodecToolCaller**: Uses `codec.parse_method_call()` to parse LLM responses

**Integration Points**:

```92:104:dana_agent/dana/core/agent/star_agent.py
        self._codec = codec
        if codec is not None:
            # Use new PromptEngineerManager and CodecToolCaller
            from dana.core.knowledge.prompts.prompt_api import LocalPromptAPI
            self._prompt_engineer = prompt_api or LocalPromptAPI(self, codec=codec, repository_factory=self._repository_factory)
            self._tool_caller = CodecToolCaller(self, codec=codec)
        else:
            # Use old PromptEngineer and ToolCaller (backward compatibility)
            self._prompt_engineer = PromptEngineer(self)
            self._tool_caller = ToolCaller(self)
```

---

### 3. Prompt Engineer (LocalPromptAPI)

**Purpose**: Generates and manages system prompts for agents, resources, and workflows.

**Location**: `dana/core/knowledge/prompts/`

**Key Files**:
- `prompt_api.py` - Main LocalPromptAPI implementation
- `prompt_engineer/base_prompt_engineer.py` - Base classes for component prompts

**Responsibilities**:

1. **System Prompt Generation**: Constructs complete system prompts
   - Uses codec instructions for tool calling format
   - Includes agent identity, constraints, and available tools
   - Manages prompt templates with versioning

2. **Tool Prompt Generation**: Creates prompts for agents/resources/workflows
   - Uses codec to format method signatures
   - Combines descriptions with formatted tool calls

3. **LLM Message Building**: Converts Timeline to LLM messages
   - System prompt as first message
   - Timeline entries converted to conversation messages
   - Token-aware context management

**Key Methods**:

```python
# System prompt property (lazy-loaded and cached)
@property
def system_prompt(self) -> str:
    """Get the system prompt, generating if needed."""
    
# Build LLM request from timeline
def build_llm_request(self, timeline: Timeline) -> list[LLMMessage]:
    """Convert timeline to LLM messages."""
    
# Tool instruction from codec
@property
def tool_instruction_prompt(self) -> str:
    return self._codec.get_instruction()
```

**Prompt Template Structure**:

```59:84:dana_agent/dana/core/knowledge/prompts/prompt_api.py
TEMPLATE_SYSTEM_PROMPT = """
{{identity}}

<tool_calling>
You have tools at your disposal to solve the task. Follow these rules regarding tool calls:
1. ALWAYS follow the tool call schema <available_tools> exactly as specified and make sure to provide all necessary parameters.
2. The conversation may reference tools that are no longer available. NEVER call tools that are not explicitly provided.
3. **NEVER refer to tool names when speaking to the USER.** For example, instead of saying 'I need to use the edit_file tool to edit your file', just say 'I will edit your file'.
4. Only calls tools when they are necessary. If the USER's task is general or you already know the answer, just respond without calling tools.
5. Before calling each tool, first explain to the USER why you are calling it.
</tool_calling>

<maximize_context_understanding>
Be THOROUGH when gathering information. Make sure you have the FULL picture before replying. Use additional tool calls or clarifying questions as needed.
TRACE every symbol back to its definitions and usages so you fully understand it.
Look past the first seemingly relevant result. EXPLORE alternative implementations, edge cases, and varied search terms until you have COMPREHENSIVE coverage of the topic.
Bias towards not asking the user for help if you can find the answer yourself.
</maximize_context_understanding>

<available_tools>
{{tool_instruction_prompt}}

# Available tools:
{{available_tools_prompt}}
</available_tools>
"""
```

**Repository Integration**:

```114:118:dana_agent/dana/core/knowledge/prompts/prompt_api.py
        self._store = self._repository_factory.create(
            RepositoryType.PROMPT,
            agent=self._agent,
            component=None  # For system prompt template
        )
```

---

### 4. Timeline

**Purpose**: Unified chronological record of all agent interactions with efficient context management.

**Location**: `dana/core/agent/timeline.py`

**Responsibilities**:

1. **Entry Management**: Stores TimelineEntry objects chronologically
   - User messages, agent responses, tool calls, tool results
   - Learning events, agent thoughts

2. **LLM Message Conversion**: Converts entries to LLM messages
   - Role assignment (user/assistant/system)
   - Token-aware context building
   - Sliding window for recent entries

3. **Persistence**: Saves/loads timeline via TimelineRepository

**TimelineEntry Types**:

```27:37:dana_agent/dana/core/agent/timeline.py
class TimelineEntryType(Enum):
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    AGENT_THOUGHTS = "agent_thoughts"
    TOOL_CALL = "tool_call"
    FAILED_TOOL_CALL = "failed_tool_call"
    SUB_AGENT_RESPONSE = "sub_agent_response"
    RESOURCE_RESULT = "resource_result"
    WORKFLOW_RESULT = "workflow_result"
    UNKNOWN_TOOL_CALL = "unknown_tool_call"
    AGENT_LEARNING = "agent_learning"
```

**Key Methods**:

```python
# Add entry to timeline
def add_entry(self, entry: TimelineEntry) -> None:
    """Add entry to timeline."""
    
# Convert to LLM messages with token management
def to_llm_messages(self, max_tokens: int | None = None, 
                   separate_latest_user: bool = False) -> list[LLMMessage]:
    """Convert timeline entries to LLM messages."""
    
# Save timeline for session
def save(self, session_id: str) -> None:
    """Save timeline for a session."""
```

**Repository Integration**:

```227:228:dana_agent/dana/core/agent/timeline.py
        # Create repository via factory
        self._repository = repository_factory.create(RepositoryType.TIMELINE, agent=agent)
```

**Token Management**:

The Timeline uses a sliding window approach to manage context size:

```373:397:dana_agent/dana/core/agent/timeline.py
    def _build_context_with_token_limit(self, messages: list[LLMMessage], max_tokens: int) -> list[LLMMessage]:
        """
        Build context using token limit approach with sliding window.

        Args:
            messages: All messages in chronological order
            max_tokens: Maximum tokens to include

        Returns:
            List of LLMMessage objects within token limit
        """
        # Start with most recent messages and work backwards
        result = []
        current_tokens = 0

        for message in reversed(messages):
            message_tokens = self._estimate_tokens([message])

            if current_tokens + message_tokens > max_tokens:
                break

            result.insert(0, message)  # Insert at beginning to maintain chronological order
            current_tokens += message_tokens

        return result
```

---

### 5. Event & EventLogAPI

**Purpose**: Manages observation events from the environment (sensors, IoT devices, etc.).

**Location**: 
- `dana/common/schemas/event.py` - Event schema
- `dana/core/agent/components/event_log_api.py` - EventLog API

**Critical Rule**: **Events ONLY come from Observer.observe()**

- ✅ Events = Observations from environment/sensors
- ❌ NO action events
- ❌ NO tool call events
- ❌ NO feedback events
- ❌ NO agent response events

**Event Schema**:

```8:21:dana_agent/dana/common/schemas/event.py
class Event(BaseModel):
    """
    Single observation event in the event log.
    
    NOTE: Events ONLY come from Observer. No actions, tool calls, or feedback.
    Events = Observations from environment/sensors only.
    """
    type: str = "observation"  # Always "observation" - events only from observer
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: str = ""
    session_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)  # Observer data
    metadata: dict[str, Any] = Field(default_factory=dict)
```

**EventLogAPI Responsibilities**:

1. **Observation Recording**: Calls Observer.observe() and creates events
2. **Event Buffering**: Maintains in-memory buffer until save
3. **Persistence**: Saves events via EventRepository

**Key Methods**:

```64:90:dana_agent/dana/core/agent/components/event_log_api.py
    def observe_and_record(self) -> Event | None:
        """
        Observe environment via Observer and create event.
        
        This is the ONLY way events are created - from Observer.observe()
        No other sources (actions, tool calls, etc.) create events.
        
        Returns:
            Event if observer returned data, None otherwise
        """
        try:
            # Observer is the ONLY source of events
            data = self._observer.observe()
            if data:
                event = Event(
                    type="observation",  # Always "observation"
                    data=data,
                    metadata={"source": "observer"}
                )
                event.agent_id = self._agent.object_id
                event.session_id = self._current_session_id
                self._event_buffer.append(event)
                return event
        except Exception as e:
            # Log but don't crash
            logger.warning(f"Observer failed: {e}")
        return None
```

**Repository Integration**:

```61:62:dana_agent/dana/core/agent/components/event_log_api.py
        # Create repository via factory
        self._repository = repository_factory.create(RepositoryType.EVENT, agent=agent)
```

---

### 6. Observer

**Purpose**: Protocol for observing environment data (extension point for domain-specific sensors).

**Location**: `dana/core/agent/components/observer.py`

**Responsibilities**:

1. **Environment Observation**: Provides observe() method to collect sensor data
2. **Lifecycle Management**: start() and stop() methods for continuous monitoring
3. **Domain Extension**: Base for HVAC, IoT, and other domain-specific observers

**Observer Protocol**:

```13:40:dana_agent/dana/core/agent/components/observer.py
class ObserverProtocol(ABC):
    """
    Protocol for observing environment data.
    
    Events in the EventLog come ONLY from Observer.observe().
    This is the extension point for domain-specific sensors (HVAC, IoT, etc.).
    """
    
    @abstractmethod
    def observe(self) -> dict[str, Any]:
        """
        Observe the environment and return data.
        
        Returns:
            Dictionary with observed data (e.g., {"temp": 72.5, "zone": "floor_2"})
            Returns empty dict {} if no data available.
        """
        pass
    
    @abstractmethod
    def start(self) -> None:
        """Start observing (if needed for continuous monitoring)."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop observing."""
        pass
```

**NullObserver**: Default implementation that does nothing (used when no observer provided).

**Usage Pattern**:

```python
# Observer is optional - EventLog only created if observer provided
if observer is not None:
    self._event_log = EventLogAPI(
        agent=self,
        observer=observer,
        repository_factory=self._repository_factory,
    )
```

---

## Component Initialization

The STARAgent initializes all components in a specific order during `__init__`:

### Initialization Flow Diagram

```
STARAgent.__init__()
    │
    ├─> RepositoryFactory (provided or DEFAULT_REPOSITORY_FACTORY)
    │
    ├─> Codec (optional, determines system type)
    │   │
    │   ├─> If codec provided:
    │   │   ├─> LocalPromptAPI(codec, repository_factory)
    │   │   └─> CodecToolCaller(codec)
    │   │
    │   └─> If codec is None:
    │       ├─> PromptEngineer (legacy)
    │       └─> ToolCaller (legacy)
    │
    ├─> Timeline(repository_factory)
    │   └─> TimelineRepository via factory
    │
    ├─> Observer (optional)
    │   └─> If provided:
    │       └─> EventLogAPI(observer, repository_factory)
    │           └─> EventRepository via factory
    │
    └─> Learner (optional)
        └─> If provided:
            └─> LearningRepository via factory
```

### Initialization Code

```44:136:dana_agent/dana/core/agent/star_agent.py
    def __init__(
        self,
        agent_type: str | None = None,
        agent_id: str | None = None,
        llm_provider: str | None = None,
        model: str | None = None,
        config: dict[str, Any] | None = None,
        max_context_tokens: int = 4000,
        auto_register: bool = True,
        registry=None,
        codec=None,
        repository_factory: RepositoryFactory = DEFAULT_REPOSITORY_FACTORY,
        prompt_api : PromptAPIProtocol | None = None,
        observer: ObserverProtocol | None = None,
        learner: LearnerProtocol | None = None,
        **kwargs,
    ):
        """
        Initialize the STARAgent with composition-based architecture.

        Args:
            agent_type: Type of agent (e.g., 'coding', 'financial_analyst').
            agent_id: ID of the agent (defaults to None)
            llm_provider: LLM provider name (e.g., 'anthropic', 'openai')
            model: Model name to use (defaults to provider's default)
            config: Optional configuration dictionary
            max_context_tokens: Maximum tokens for timeline context
            auto_register: Whether to automatically register with the global registry
            registry: Specific registry to use (defaults to global registry)
            codec: Codec class to use for new prompt/tool system (if None, uses old system)
            **kwargs: Additional arguments passed to components
        """
        # Initialize base class first (handles registration)
        kwargs |= {
            "agent_type": agent_type,
            "agent_id": agent_id,
            "auto_register": auto_register,
            "registry": registry,
        }
        super().__init__(**kwargs)

        # Initialize LLM
        self._llm_config = {
            "provider": llm_provider,
            "model": model,
        }


        self._session_id = str(uuid4())
        # Conditional component initialization based on codec
        self._repository_factory = repository_factory
        self._codec = codec
        if codec is not None:
            # Use new PromptEngineerManager and CodecToolCaller
            from dana.core.knowledge.prompts.prompt_api import LocalPromptAPI
            self._prompt_engineer = prompt_api or LocalPromptAPI(self, codec=codec, repository_factory=self._repository_factory)
            self._tool_caller = CodecToolCaller(self, codec=codec)
        else:
            # Use old PromptEngineer and ToolCaller (backward compatibility)
            self._prompt_engineer = PromptEngineer(self)
            self._tool_caller = ToolCaller(self)

        # Initialize other components
        self._communicator = Communicator(self)
        self._state = State(self)
        # self._learner = learner or Learner(self, repository_factory=self._repository_factory)
        self._learner = learner
        if self._learner is not None:
            self._learner._agent = self

        # Determine storage_config for timeline and event_log

        # Initialize timeline at agent level with agent, codec, and storage_config
        self._timeline = Timeline(
            max_context_tokens=max_context_tokens,
            agent=self,
            repository_factory=self._repository_factory,
        )

        # Initialize EventLog API (only if observer AND codec provided)
        # Events ONLY come from Observer - no observer = no EventLog
        if observer is not None:
            from dana.core.agent.components.event_log_api import EventLogAPI
            
            self._event_log = EventLogAPI(
                agent=self,
                observer=observer,  # REQUIRED - EventLog only works with Observer
                repository_factory=self._repository_factory,
            )
        else:
            # No observer or codec = no EventLog (events only come from Observer)
            self._event_log = None

        self.with_resources(ToDoResource(resource_id="todo-resource"))
```

---

## Runtime Flow (STAR Loop)

The STAR (See-Think-Act-Reflect) loop is the core execution pattern. Here's how components interact:

### STAR Loop Flow Diagram

```
User Query
    │
    ▼
┌─────────────────┐
│   SEE Phase     │
│                 │
│ Timeline.add_   │
│ entry(USER_     │
│ MESSAGE)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  THINK Phase    │
│                 │
│ 1. PromptAPI.   │
│    build_llm_   │
│    request()    │──┐
│                 │  │
│    Timeline.    │  │ Uses Timeline
│    to_llm_      │  │ entries
│    messages()   │◄─┘
│                 │
│ 2. PromptAPI.   │
│    system_      │──┐
│    prompt       │  │ Uses Codec
│                 │  │ instructions
│    (includes    │  │
│    codec        │  │
│    format)      │◄─┘
│                 │
│ 3. LLM.chat()   │
│    (with codec  │
│    formatted    │
│    response)    │
│                 │
│ 4. CodecTool    │──┐
│    Caller.      │  │ Uses Codec
│    parse_llm_   │  │ to parse
│    response()   │◄─┘
│                 │
│ Timeline.add_   │
│ entry(AGENT_    │
│ THOUGHTS)       │
│ Timeline.add_   │
│ entry(TOOL_     │
│ CALL)           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ACT Phase     │
│                 │
│ CodecTool       │
│ Caller.         │
│ execute_tool_   │
│ calls()         │
│                 │
│ Timeline.add_   │
│ entry(RESOURCE_ │
│ RESULT)         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ REFLECT Phase   │
│                 │
│ Learner.        │──┐
│ _reflect_*()    │  │ Uses
│                 │  │ Learning
│ Timeline.add_   │  │ Repository
│ entry(AGENT_    │  │
│ LEARNING)       │◄─┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Persistence    │
│                 │
│ Timeline.save() │──┐
│                 │  │ Saves via
│ EventLog.save() │  │ Repositories
│ (if observer)   │  │
│                 │◄─┘
└─────────────────┘
```

### SEE Phase

```290:351:dana_agent/dana/core/agent/star_agent.py
    @observable
    def _see(self, trace_inputs: DictParams) -> DictParams:
        """
        SEE: See the user/caller inputs and produce percepts.

        Args:
            trace_inputs (DictParams): any new user/agent inputs, plus trace_outputs from the previous loop (if any)
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.
              - response (str): Response from the previous loop (if any)
              - tool_calls (list[DictParams]): Tool calls from the previous loop (if any)
              - tool_results (list[DictParams]): Tool results from the previous loop (if any)

        Returns:
            - trace_percepts (DictParams): the percepts produced by this SEE phase.
              - timeline (Timeline): Timeline of the agent, appending any new entries from our perceptions
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.
        """

        # Input parameter checking
        trace_inputs = trace_inputs or {}
        if self._do_exit_star_loop(trace_inputs):
            return {"trace_percepts": self._mark_star_loop_exit(trace_inputs)}

        previous_tool_calls: list[DictParams] = trace_inputs.get("tool_calls", None)
        if previous_tool_calls:
            # This is a subsequent loop - perceiving tool results
            tool_results = trace_inputs.get("tool_results", [])
            num_results = len(tool_results) if isinstance(tool_results, list) else 0

            # Add perception message for notification visibility
            trace_inputs["perception"] = f"Perceived {num_results} tool result(s)"

            del trace_inputs["response"]
            del trace_inputs["tool_calls"]
            del trace_inputs["tool_results"]
        else:
            # This is the first loop
            caller_message: str = trace_inputs.get("caller_message", trace_inputs.get("message", None))
            if not caller_message:
                return {"trace_percepts": self._mark_star_loop_exit(trace_inputs)}

            # Add caller_message to timeline with caller tracking
            if isinstance(caller_message, str):
                # Create new entry and mark it as latest
                new_entry = TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content=caller_message, is_latest_user_message=True)
                self._timeline.add_entry(new_entry)

            # Preserve caller_message for notifications but remove original keys
            trace_inputs.pop("message", None)  # Remove 'message' alias
            # Keep caller_message in trace_inputs for notification
            if "caller_message" not in trace_inputs:
                trace_inputs["caller_message"] = caller_message

        

        trace_inputs |= {"timeline": self._timeline}

        return super()._see(trace_inputs)
```

### THINK Phase

```353:457:dana_agent/dana/core/agent/star_agent.py
    @observable
    def _think(self, trace_percepts: DictParams) -> DictParams:
        """
        THINK: Think about the percepts and produce thoughts. This is where we make an LLM call.

        Args:
            trace_percepts (DictParams): the percepts produced by this SEE phase.
              - timeline (Timeline): Timeline of the agent.

        Returns:
            - trace_thoughts (DictParams): the thoughts produced by this THINK phase.
              - response (str): Response from the LLM
              - tool_calls (list[DictParams]): Tool calls from the LLM
        """

        # Input parameter checking
        trace_percepts = trace_percepts or {}
        if self._do_exit_star_loop(trace_percepts) or not trace_percepts:
            return {"trace_thoughts": self._mark_star_loop_exit(trace_percepts)}

        timeline: Timeline = trace_percepts.get("timeline", self._timeline)
        trace_percepts.pop("timeline", None)

        # Build LLM messages using PromptEngineer
        llm_messages = self._prompt_engineer.build_llm_request(timeline)

        # Query LLM with retry logic for empty responses
        response, reasoning, tool_calls = None, None, None
        failed_tool_calls = []
        for attempt in range(self.MAX_EMPTY_RESPONSE_RETRIES):
            llm_response = self.llm_client.chat_response_sync(llm_messages, agent_id=self.object_id, agent_type=self.agent_type, temperature=0)
            response, reasoning, tool_calls = self._tool_caller.parse_llm_response(llm_response)

            # Retry if both response and tool_calls are empty
            has_content = response and response.strip()
            has_tool_calls = tool_calls and len(tool_calls) > 0
            if has_content or has_tool_calls:
                break
            elif reasoning and "error" in reasoning.lower():
                from dana.common.llm.types import LLMMessage
                suggestion_message = LLMMessage(role="user", content=reasoning)
                failed_tool_calls.append(llm_response.content)
                if llm_messages and llm_messages[-1].role == "user" and "error" in llm_messages[-1].content.lower():
                    # Replace old suggestion message in case of consecutive errors
                    llm_messages[-1] = suggestion_message
                else:
                    # Add new suggestion message
                    llm_messages.append(suggestion_message)
            if attempt < self.MAX_EMPTY_RESPONSE_RETRIES - 1:
                logger.warning("Empty LLM response, retrying", attempt=attempt + 1)

        if failed_tool_calls:
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.FAILED_TOOL_CALL,
                    content=json.dumps(failed_tool_calls),
                )
            )

        if not tool_calls or len(tool_calls) == 0:
            response = response if (response and len(response) > 0) else "No response generated"
            timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.AGENT_RESPONSE,
                    content=response,
                )
            )
        else:
            if reasoning and len(reasoning) > 0:
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.AGENT_THOUGHTS,
                        content=reasoning,
                    )
                )

            if response and len(response) > 0:
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.AGENT_THOUGHTS,
                        content=response,
                    )
                )

            for tool_call in tool_calls:
                timeline.add_entry(
                    TimelineEntry(
                        entry_type=TimelineEntryType.TOOL_CALL,
                        content=str(tool_call),
                    )
                )

        # Output parameter checking
        assert isinstance(response, str)
        assert isinstance(tool_calls, list)
        trace_percepts |= {
            "response": response,
            "reasoning": reasoning,
            "tool_calls": tool_calls,
        }

        if tool_calls is None or len(tool_calls) == 0:
            trace_percepts = self._mark_star_loop_exit(trace_percepts)

        return super()._think(trace_percepts)
```

### ACT Phase

```459:534:dana_agent/dana/core/agent/star_agent.py
    @observable
    def _act(self, trace_thoughts: DictParams) -> DictParams:
        """
        ACT: Execute tool calls and return results.
        TODO: this is a good place to send interactive feedback to the user before making tool calls

        Args:
            trace_thoughts (DictParams): the thoughts produced by this THINK phase.
              - response (str): Response from the LLM from the THINK phase.
              - tool_calls (list[DictParams]): Tool calls from the THINK phase.
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.

        Returns:
            - trace_outputs (DictParams): the outputs produced by this ACT phase.
              - response (str): Response from the LLM from the THINK phase.
              - tool_calls (list[DictParams]): Tool calls from the THINK phase.
              - tool_results: list[DictParams]: Tool results from the ACT phase if there are tool calls
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.
        """

        # Input parameter checking
        trace_thoughts = trace_thoughts or {}
        if not trace_thoughts or self._do_exit_star_loop(trace_thoughts):
            return {"trace_outputs": self._mark_star_loop_exit(trace_thoughts)}

        tool_calls: list[DictParams] = trace_thoughts.get("tool_calls")

        # Execute tool calls using ToolCaller
        tool_results = self._tool_caller.execute_tool_calls(tool_calls)

        # Add tool results to timeline
        if isinstance(tool_results, list):
            for tool_result in tool_results:
                if isinstance(tool_result, dict):
                    # Determine entry type based on tool type
                    tool_type = tool_result.get("type")
                    if tool_type == "agent":
                        entry_type = TimelineEntryType.SUB_AGENT_RESPONSE
                    elif tool_type == "resource":
                        entry_type = TimelineEntryType.RESOURCE_RESULT
                    elif tool_type == "workflow":
                        entry_type = TimelineEntryType.WORKFLOW_RESULT
                    else:  # unknown
                        entry_type = TimelineEntryType.UNKNOWN_TOOL_CALL

                    self._timeline.add_entry(
                        TimelineEntry(
                            entry_type=entry_type,
                            content=tool_result.get("result", "Unknown tool result"),
                        )
                    )

            # Add a synthetic user message to prompt the agent to respond based on tool results
            # This ensures the next THINK phase has a user message to respond to
            # last_command_message = ""
            # for entry in self._timeline.timeline[::-1]:
            #     if entry.entry_type == TimelineEntryType.USER_MESSAGE:
            #         last_command_message = entry.content and "Please provide a response" not in entry.content
            #         break
            # self._timeline.add_entry(
            #     TimelineEntry(
            #         entry_type=TimelineEntryType.USER_MESSAGE,
            #         content=f"Please provide a response based on the tool results above to answer : {last_command_message}",
            #         is_latest_user_message=True,
            #     )
            # )

        # Output parameter checking
        assert isinstance(tool_results, list)
        trace_thoughts |= {"tool_results": tool_results}

        return super()._act(trace_thoughts)
```

### REFLECT Phase

```536:596:dana_agent/dana/core/agent/star_agent.py
    # @observable
    def _reflect(self, trace_outputs: DictParams) -> DictParams:
        """
        REFLECT: Reflect on the actions or episode, depending on the reflection phase.

        Args:
            trace_outputs (DictParams): the outputs produced by this ACT phase.
              - phase (LearningPhase): specifies which learning phase we are in
              - response (str): Response from the THINK phase.
              - tool_calls (list[DictParams]): Tool calls from the THINK phase.
              - tool_results (list[DictParams]): Tool results from the ACT phase.
              - caller_message (str): Caller message (may be user or another agent)
              - caller_type (str): Type of caller (agent or human)
              - caller_id (str): ID of the caller (agent.object_id or user) for conversation tracking.

        Returns:
            - trace_learning (DictParams): the learning produced by this REFLECT phase.
        """

        # Input parameter checking
        trace_outputs = trace_outputs or {}
        if not trace_outputs or self._do_exit_star_loop(trace_outputs):
            return {"trace_learning": self._mark_star_loop_exit(trace_outputs)}
        phase: LearningPhase = trace_outputs.get("phase") or LearningPhase.ACQUISITIVE

        trace_learning = {}
        if self._learner is not None:
            match phase:
                case LearningPhase.ACQUISITIVE:
                    trace_learning |= self._learner._reflect_acquisitive(trace_outputs)
                    trace_learning["learning_note"] = "Initial learning and trial-level plasticity"

                case LearningPhase.EPISODIC:
                    trace_learning |= self._learner._reflect_episodic(trace_outputs)
                    trace_learning["learning_note"] = "Episodic binding of information"

                case LearningPhase.INTEGRATIVE:
                    trace_learning |= self._learner._reflect_integrative(trace_outputs)
                    trace_learning["learning_note"] = "Offline replay and integration"

                case LearningPhase.RETENTIVE:
                    trace_learning |= self._learner._reflect_retentive(trace_outputs)
                    trace_learning["learning_note"] = "Long-term maintenance and habit formation"

                case _:
                    raise ValueError(f"Unknown learning phase {phase}")

            trace_learning |= {
                "timestamp": datetime.now().isoformat(),
                "phase": phase.value,
            }

            # Add to timeline for persistence
            self._timeline.add_entry(
                TimelineEntry(
                    entry_type=TimelineEntryType.AGENT_LEARNING,
                    content=f"Learning ({phase.value}): {trace_learning.get('learning_note', 'No learning note')}",
                )
            )

        return super()._reflect(trace_learning)
```

### Persistence After Query

```221:243:dana_agent/dana/core/agent/star_agent.py
    def query(self, **kwargs) -> DictParams:
        # Generate session_id if not provided
        new_session_id = kwargs.get("session_id")
        if new_session_id is not None:
            self.set_session_id(new_session_id)
        session_id = self._session_id
            

        # Set session_id for EventLog if it exists
        if hasattr(self, "_event_log") and self._event_log is not None:
            self._event_log._current_session_id = session_id

        try:
            result = super().query(**kwargs)
            return result
        finally:
            # Save events if EventLog exists
            if hasattr(self, "_event_log") and self._event_log is not None:
                self._event_log.save(session_id)
            
            # Save timeline (agent, codec, storage_config already set in __init__)
            if hasattr(self, "_timeline") and self._timeline is not None:
                self._timeline.save(session_id)
```

---

## Storage Architecture

### Repository Factory Pattern

The RepositoryFactory provides a centralized way to create repositories with consistent configuration:

```18:32:dana_agent/dana/repositories/repository_factory.py
class RepositoryFactory:
    def __init__(self):
        self._creators = {
            RepositoryType.PROMPT: (LocalPromptRepository, FileStorageConfig()),
            RepositoryType.TIMELINE: (LocalTimelineRepository, FileStorageConfig()),
            RepositoryType.EVENT: (LocalEventRepository, FileStorageConfig()),
            RepositoryType.LEARNING: (LocalLearningRepository, FileStorageConfig()),
        }

    def register(self, type: RepositoryType, creator: type[RepositoryProtocol], storage_config: StorageConfig) -> None:
        self._creators[type] = (creator, storage_config)

    def create(self, type: RepositoryType, **kwargs) -> RepositoryProtocol:
        creator, storage_config = self._creators[type]
        return creator.instantiate(storage_config, **kwargs)
```

### Storage Path Computation

Repositories compute storage paths based on:
1. **Codec**: Determines the top-level folder structure
2. **Agent Class**: Agent-specific subfolder
3. **Component**: For prompts, distinguishes agent/system/resource/workflow prompts
4. **Session ID**: For timeline, events, and learning data

**Codec Prefix Extraction**:

```62:78:dana_agent/dana/repositories/local_file_repository.py
    def _get_codec_prefix(self, agent: BaseAgent) -> str:
        """
        Compute codec prefix from agent's codec.
        
        Returns "default" if codec is None or has "magic" in qualname,
        otherwise returns the codec's qualname.
        
        Args:
            agent: Agent instance
            
        Returns:
            Codec prefix string
        """
        codec = self._extract_codec_from_agent(agent)
        if codec is None or "magic" in str(codec.__qualname__):
            return "default"
        return codec.__qualname__
```

**Path Structure Example**:

```
.dana/dana_agent/
└── CSXMLCodec/                          # Codec prefix
    └── HVACAgent__hvac_agent/           # Agent class + filename
        ├── prompts/
        │   ├── system_prompt_template/   # System prompt
        │   │   ├── versions/
        │   │   │   ├── v1.prompt
        │   │   │   └── v2.prompt
        │   │   └── version.txt
        │   ├── agents/                   # Sub-agent prompts
        │   ├── resources/                # Resource prompts
        │   └── workflows/                # Workflow prompts
        ├── timeline/
        │   └── session-001/              # Session-specific
        │       └── timeline.json
        ├── events/
        │   └── session-001/
        │       └── events.jsonl
        └── learnings/
            └── session-001/
                ├── acquisitive/
                │   └── loop_*.json
                ├── episodic/
                │   └── learnings.md
                └── feedback/
                    └── feedback.md
```

---

## Component Interactions

### Codec Integration Flow

```
┌─────────────┐
│   Codec     │
│             │
│ get_        │──┐
│ instruction │  │
│             │  │
│ construct() │  │
│             │  │
│ parse_      │  │
│ method_     │  │
│ call()      │  │
└──────┬──────┘  │
       │        │
       │        │
       ▼        │
┌──────────────┐│
│ PromptAPI   ││
│             ││
│ Uses codec. ││
│ get_        ││
│ instruction ││
│ for system  ││
│ prompt      ││
└──────────────┘│
                │
                │
                ▼
┌──────────────┐
│ CodecTool   │
│ Caller      │
│             │
│ Uses codec. │
│ parse_      │
│ method_     │
│ call() to   │
│ parse LLM   │
│ response    │
└─────────────┘
```

### Observer-EventLog Flow

```
┌──────────────┐
│  Observer    │
│              │
│ observe()    │──┐
│   returns    │  │
│   dict data  │  │
└──────────────┘  │
                  │
                  │
                  ▼
         ┌────────────────┐
         │  EventLogAPI   │
         │                │
         │ observe_and_   │
         │ record()       │
         │                │
         │ Creates Event  │
         │ from Observer  │
         │ data           │
         └────────┬───────┘
                  │
                  │
                  ▼
         ┌────────────────┐
         │ EventRepository│
         │                │
         │ save()         │
         │                │
         │ Stores to      │
         │ events.jsonl   │
         └────────────────┘
```

**Critical Rule**: Events ONLY come from Observer.observe(). No action events, tool call events, or feedback events are stored in EventLog.

### Timeline-PromptAPI Integration

```
┌──────────────┐
│  Timeline    │
│              │
│ add_entry()  │──┐
│              │  │
│ to_llm_      │  │
│ messages()   │  │
└──────────────┘  │
                  │
                  │
                  ▼
         ┌────────────────┐
         │  PromptAPI     │
         │                │
         │ build_llm_     │
         │ request()      │
         │                │
         │ 1. Gets system │
         │    prompt      │
         │ 2. Gets timeline│
         │    messages    │
         │ 3. Combines    │
         │    into LLM    │
         │    request     │
         └────────────────┘
```

### Repository Usage Pattern

All components follow the same pattern for repository access:

1. **Factory Creation**: RepositoryFactory.create(type, agent=agent, ...)
2. **Path Computation**: Repository computes path from codec + agent + component
3. **Storage Operations**: Save/load operations use computed paths
4. **Session Management**: Timeline, Event, and Learning repositories use session_id

---

## Summary

The Dana Agent architecture uses a composition-based design where:

1. **Repositories** provide storage abstraction for all persistent data
2. **Codec** defines structured communication format for LLM interactions
3. **PromptAPI** generates system prompts using codec and manages tool descriptions
4. **Timeline** maintains conversation history and converts to LLM messages
5. **EventLogAPI** records environment observations from Observer
6. **Observer** provides extensible interface for domain-specific sensors

All components are initialized through STARAgent and work together in the STAR (See-Think-Act-Reflect) loop, with persistence handled automatically via repositories after each query.

