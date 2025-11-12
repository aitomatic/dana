# Learning Guide: Advanced Topics and Implementation Details

> **New to custom learners?** Start with [learning-basic.md](./learning-basic.md) for a concise introduction and quick start guide.

This comprehensive guide covers advanced learning topics, complete implementation walkthroughs, feedback integration, retrieval strategies, and complete reference examples. We'll use examples from the HVAC Agent (`examples/agents/hvac`) to demonstrate practical implementations.

## Table of Contents

1. [Introduction](#1-introduction)
2. [Understanding the Learner Protocol](#2-understanding-the-learner-protocol)
3. [Example 1: WilliamLearner - Basic Custom Learner](#3-example-1-williamlearner---basic-custom-learner)
4. [Example 2: WilliamLearner2 - Feedback-Aware Learning](#4-example-2-williamlearner2---feedback-aware-learning)
5. [Example 3: WilliamLearner3 - Specialized Feedback Learning](#5-example-3-williamlearner3---specialized-feedback-learning)
6. [Integrating Custom Learners with Agents](#6-integrating-custom-learners-with-agents)
7. [Learning Storage Architecture](#7-learning-storage-architecture)
8. [Advanced Topics](#8-advanced-topics)
9. [Best Practices & Patterns](#9-best-practices--patterns)
10. [Complete Reference Example](#10-complete-reference-example)

---

## 1. Introduction

### STAR Learning Framework Overview

Dana agents use the **STAR (See-Think-Act-Reflect) learning framework** with four learning phases:

```
┌──────────────┐
│     SEE      │  Perceive environment & context
└──────┬───────┘
       │
┌──────▼───────┐
│    THINK     │  Reason about actions
└──────┬───────┘
       │
┌──────▼───────┐
│     ACT      │  Execute actions
└──────┬───────┘
       │
┌──────▼───────┐  ┌─────────────────────────────────┐
│   REFLECT    │──┤ ACQUISITIVE: Immediate learning │
└──────────────┘  │ EPISODIC: Session-level patterns│
                  │ INTEGRATIVE: Cross-session merge │
                  │ RETENTIVE: Long-term memory      │
                  └─────────────────────────────────┘
```

**Learning Phases:**

1. **ACQUISITIVE Learning** (Immediate)
   - Triggered: After each interaction (query → response)
   - Purpose: Extract insights from single experience
   - Storage: Individual `loop_*.json` files
   - Example: "Cooling from 90°F to 72°F took 12 minutes with turbo mode"

2. **EPISODIC Learning** (Session-level)
   - Triggered: After completing a session or on-demand
   - Purpose: Recognize patterns across multiple interactions
   - Storage: Single `learnings.md` file per session
   - Example: "When outdoor temp > 85°F, always add 2-minute buffer for cooling"

3. **INTEGRATIVE Learning** (Cross-session)
   - Triggered: Periodically or when merging sessions
   - Purpose: Combine learnings from multiple sessions
   - Storage: Aggregated learnings file
   - Example: "Across 50 sessions, turbo mode is cost-effective when time_until_meeting < 10 min"

4. **RETENTIVE Learning** (Long-term)
   - Triggered: Periodically for knowledge consolidation
   - Purpose: Create persistent, general rules
   - Storage: Long-term knowledge base
   - Example: "General rule: cooling_time = temp_diff / (turbo ? 2.5 : 1.5) + buffer"

### Why Custom Learners Matter

The default `Learner` class provides basic functionality, but custom learners enable:

- **Domain-specific learning strategies** tailored to your use case
- **Custom retrieval mechanisms** (BM25, embeddings, semantic search)
- **Feedback integration** for learning from outcomes
- **Specialized prompt engineering** for better insight extraction
- **Custom storage patterns** for efficient knowledge access

**Example:** The HVAC Agent uses `WilliamLearner` to:
- Extract HVAC-specific metrics (cooling rates, buffer times)
- Learn from environment feedback (success/failure of temperature plans)
- Use BM25 search for retrieving relevant past experiences
- Format learnings as actionable rules for future planning

### Learning Storage and Retrieval Architecture

Custom learners interact with Dana's repository pattern:

```
.dana/dana_agent/
└── {codec_name}/           # e.g., "CSXMLCodec"
    └── {agent_class}/      # e.g., "HVACAgent"
        ├── learnings/
        │   └── {session_id}/
        │       ├── acquisitive/
        │       │   ├── loop_abc123.json   # Individual acquisitions
        │       │   ├── loop_def456.json
        │       │   └── ...
        │       └── episodic/
        │           └── learnings.md        # Session-level patterns
        ├── feedback/
        │   └── {session_id}/
        │       └── feedback.md             # External feedback
        └── timeline/
            └── {session_id}/
                └── timeline.json           # Interaction history
```

**Key concepts:**
- **Repository pattern**: Abstract storage interface (`LearningRepositoryProtocol`)
- **Session-based**: Each session has isolated learning storage
- **Phase separation**: Acquisitive and episodic learnings stored separately
- **Retrievable**: Learnings can be queried and injected into agent prompts

---

## 2. Understanding the Learner Protocol

Custom learners must implement the `LearnerProtocol` interface to integrate with Dana agents.

### The LearnerProtocol Interface

**Reference:** `dana_agent/dana/core/agent/components/learner.py:32-61`

```python
from typing import Protocol
from dana.common.protocols import DictParams
from dana.common.protocols.types import LearningPhase

class LearnerProtocol(Protocol):
    """Protocol defining the interface for custom learners."""
    
    def __init__(self, agent: "STARAgent", repository_factory: "RepositoryFactory | None" = None):
        """
        Initialize learner with agent and optional repository factory.
        
        Args:
            agent: The agent instance this learner belongs to
            repository_factory: Optional factory for creating repositories
        """
        ...
    
    def _reflect_acquisitive(self, trace_acquisitive: DictParams) -> DictParams:
        """
        Reflect on acquisitions (immediate learning after each interaction).
        
        Args:
            trace_acquisitive: Data from the ACT phase containing:
                - caller_message: Original user query
                - response: Agent's response
                - reasoning: Agent's thinking
                - tool_calls: List of tool calls made
                - tool_results: List of tool results received
        
        Returns:
            trace_learning: Learning insights from this acquisition
        """
        ...
    
    def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
        """
        Reflect on an episode (session-level pattern recognition).
        
        Args:
            trace_episodic: Collection of experiences from the session
        
        Returns:
            trace_learning: Learning insights from the episode
        """
        ...
    
    def _reflect_integrative(self, trace_integrative: DictParams) -> DictParams:
        """
        Reflect on integration (cross-session learning).
        
        Args:
            trace_integrative: Collection of episodes to integrate
        
        Returns:
            trace_learning: Integrated learning insights
        """
        ...
    
    def _reflect_retentive(self, trace_retentive: DictParams) -> DictParams:
        """
        Reflect on retention (long-term knowledge consolidation).
        
        Args:
            trace_retentive: Long-term learning context
        
        Returns:
            trace_learning: Retentive learning insights
        """
        ...
    
    def query_learnings(self, query: str, phase: LearningPhase | None = None) -> str | None:
        """
        Query stored learnings for relevant insights.
        
        Args:
            query: Search query (e.g., "How to handle cooling when outdoor temp is high?")
            phase: Optional learning phase to query (ACQUISITIVE, EPISODIC, etc.)
        
        Returns:
            Relevant learning insights as string, or None if not found
        """
        ...
    
    def _load_acquisitive(self) -> list[str]:
        """Load all acquisitive learnings for current session."""
        ...
    
    def _load_episodic(self) -> str | None:
        """Load episodic learning for current session."""
        ...
    
    def _load_feedback(self) -> Any:
        """Load feedback data for current session."""
        ...
    
    def save_feedback(self, feedback: Any) -> None:
        """Save feedback data for current session."""
        ...
```

### Required Methods

**Core reflection methods (MUST implement):**
- `_reflect_acquisitive()`: Called after each agent interaction
- `_reflect_episodic()`: Called after session or on-demand
- `_reflect_integrative()`: Called for cross-session learning (optional in practice)
- `_reflect_retentive()`: Called for long-term consolidation (optional in practice)

**Utility methods (SHOULD implement):**
- `query_learnings()`: Retrieve relevant past learnings
- `_load_acquisitive()` / `_load_episodic()`: Load stored learnings
- `save_feedback()` / `_load_feedback()`: Handle external feedback

### Learning Phases and Their Purposes

Let's see how each phase works in the HVAC Agent context:

**1. Acquisitive Learning Example:**

*Trigger:* Agent creates an HVAC plan (one interaction)

*Input:*
```python
trace_acquisitive = {
    "caller_message": "CURRENT ENVIRONMENT: {temp: 90°F, meeting: 16:00}",
    "response": '{"plan": [{"time_on": "15:50", "time_off": "17:00", "use_turbo": false}]}',
    "reasoning": "Need 10 minutes to cool from 90°F to 72°F...",
    "tool_calls": [],
    "tool_results": []
}
```

*Output:*
```python
{
    "trace_learning": {
        "insight": "For 18°F cooling with 10min lead time, non-turbo mode is sufficient",
        "metrics": {"temp_diff": 18, "time_needed": 10, "mode": "non-turbo"},
        "timestamp": "2024-01-15T15:45:00"
    }
}
```

*Storage:* `.dana/.../learnings/{session_id}/acquisitive/loop_abc123.json`

**2. Episodic Learning Example:**

*Trigger:* After completing multiple interactions in a session

*Input:* Collection of acquisitive learnings + timeline + feedback

*Output:*
```markdown
## Session Learning Summary

### Pattern: High outdoor temperature requires buffer
When outdoor_temp > 85°F, add 2-minute buffer to cooling time estimates.
Observed in 5/5 cases during this session.

### Formula: Cooling time calculation
cooling_time_minutes = temp_diff_fahrenheit / cooling_rate + buffer
- cooling_rate (non-turbo): 1.5°F/min
- cooling_rate (turbo): 2.5°F/min
- buffer: 2 min when outdoor_temp > 85°F, else 1 min
```

*Storage:* `.dana/.../learnings/{session_id}/episodic/learnings.md`

### Repository-Based Storage Pattern

Custom learners use the repository pattern for storage:

```python
class WilliamLearner(LearnerProtocol):
    def __init__(self, agent: "STARAgent", repository_factory: "RepositoryFactory | None" = None):
        self._agent = agent
        
        # Create learning repository via factory
        from dana.repositories.repository_factory import DEFAULT_REPOSITORY_FACTORY, RepositoryType
        factory = repository_factory or DEFAULT_REPOSITORY_FACTORY
        self._repository = factory.create(RepositoryType.LEARNING, agent=agent)
    
    def _get_acquisitive_storage_path(self) -> Path:
        """Get storage path for acquisitive learnings."""
        return self._repository._base_storage_path / "learnings" / self.session_id / "acquisitive"
    
    def _get_episodic_storage_path(self) -> Path:
        """Get storage path for episodic learning."""
        return self._repository._base_storage_path / "learnings" / self.session_id / "episodic"
```

**Benefits:**
- Abstraction: Storage implementation can change without affecting learner code
- Testing: Easy to mock repositories for unit tests
- Flexibility: Can use local files, databases, or cloud storage

---

## 3. Example 1: WilliamLearner - Basic Custom Learner

Let's build a complete custom learner step-by-step using the HVAC Agent's `WilliamLearner` as our example.

**Reference:** `examples/agents/hvac/leaners/william_learner.py`

### 3.1 Structure and Initialization

A custom learner starts with proper initialization and setup:

```python
"""
Learner: Handles the four learning phases of STAR reflection.
"""
import json
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from structlog import get_logger
from dana.common.llm.types import LLMMessage
from dana.common.observable import observable
from dana.common.protocols import DictParams
from dana.common.protocols.types import LearningPhase
from dana.core.agent.components.learner import LearnerProtocol
from dana.common.llm.debug_logger import get_debug_logger
from dana.core.agent.timeline import TimelineEntry
from pathlib import Path
from rank_bm25 import BM25Okapi
import numpy as np

logger = get_logger()

if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent
    from dana.core.agent.timeline import Timeline
    from dana.repositories.repository_protocol import LearningRepositoryProtocol
    from dana.repositories.repository_factory import RepositoryFactory


class BM25SearchEngine:
    """Simple BM25-based search engine for retrieving relevant learnings."""
    
    def __init__(self, corpus: list[str]):
        self._original_corpus = corpus
        self.corpus = [self.text_to_words(text) for text in corpus]
        self.bm25 = BM25Okapi(self.corpus)
    
    @staticmethod
    def text_to_words(text: str) -> list[str]:
        """Convert text to list of lowercase words."""
        return [word.lower() for word in text.split(" ")]
    
    def search(self, query: str, n: int = 1) -> list[str]:
        """Search for top N most relevant documents."""
        top_n = self.get_top_n_indices(query, n)
        return [self._original_corpus[i] for i in top_n]
    
    def get_top_n_indices(self, query: str, n: int = 1) -> list[int]:
        """Get indices of top N documents."""
        scores = self.bm25.get_scores(self.text_to_words(query))
        return np.argsort(scores)[::-1][:n].tolist()


class WilliamLearner(LearnerProtocol):
    """Custom learner with BM25 search and repository-based storage."""
    
    def __init__(
        self, 
        agent: "STARAgent", 
        repository: "LearningRepositoryProtocol | None" = None,
        repository_factory: "RepositoryFactory | None" = None
    ):
        """
        Initialize the learner with agent and repository.
        
        Args:
            agent: The agent instance this learner belongs to
            repository: Learning repository (optional, will be created if None)
            repository_factory: Factory for creating repositories (optional)
        """
        # Store agent reference
        self._agent = agent
        
        # In-memory caches
        self.acquisitive_memory = []  # List of acquisitive learning strings
        self.episodic_memory = None   # Current episodic learning content
        
        # Initialize repository
        if repository:
            self._repository = repository
        elif agent:
            # Create repository using factory
            from dana.repositories.repository_factory import DEFAULT_REPOSITORY_FACTORY, RepositoryType
            factory = repository_factory or DEFAULT_REPOSITORY_FACTORY
            self._repository = factory.create(RepositoryType.LEARNING, agent=agent)
        else:
            self._repository = None
    
    @property
    def session_id(self) -> str | None:
        """Get current session ID from agent."""
        # Try agent's session_id first
        if hasattr(self._agent, "_session_id") and "magic" not in str(self._agent._session_id):
            return self._agent._session_id
        
        # Fall back to event log's session ID
        _event_log = getattr(self._agent, "_event_log", None)
        if _event_log is None or "magic" in str(_event_log):
            return None
        
        return _event_log._current_session_id
    
    def _get_acquisitive_storage_path(self) -> Path:
        """Get storage path for acquisitive learnings."""
        return self._repository._base_storage_path / "learnings" / self.session_id / "acquisitive"
    
    def _get_episodic_storage_path(self) -> Path:
        """Get storage path for episodic learning."""
        return self._repository._base_storage_path / "learnings" / self.session_id / "episodic"
    
    def _get_feedback_storage_path(self) -> Path:
        """Get storage path for feedback."""
        return self._repository._base_storage_path / "feedback" / self.session_id
```

**Key components:**

1. **BM25SearchEngine**: Lightweight search for retrieving relevant past learnings
2. **Memory caches**: In-memory storage for quick access
3. **Repository**: Persistent storage via repository pattern
4. **Session management**: Track current session for storage isolation

### 3.2 Acquisitive Learning Implementation

Acquisitive learning happens after each agent interaction. Here's the complete implementation:

```python
@observable
def _reflect_acquisitive(self, trace_acquisitive: DictParams) -> DictParams:
    """
    Reflect on acquisitions (immediate learning phase).
    
    This method is called after each agent query/response cycle.
    It extracts insights from a single interaction.
    
    Args:
        trace_acquisitive: Data from ACT phase containing:
            - caller_message (str): Original user query
            - response (str): Agent's response
            - reasoning (str): Agent's internal reasoning
            - tool_calls (list): Tool calls made
            - tool_results (list): Tool results received
    
    Returns:
        trace_learning: Learning insights from this acquisition
    """
    try:
        # Generate unique ID for this learning instance
        loop_id = str(uuid4())
        timestamp = datetime.now()
        
        # Extract key components from the trace
        caller_message = trace_acquisitive.get("caller_message", "")
        response = trace_acquisitive.get("response", "")
        reasoning = trace_acquisitive.get("reasoning", "")
        tool_calls = trace_acquisitive.get("tool_calls", [])
        tool_results = trace_acquisitive.get("tool_results", [])
        
        # Build context for LLM to analyze
        messages = []
        
        # System prompt for acquisitive learning
        system_prompt = """You are a learning assistant that extracts key insights from agent interactions.
        
Your task:
1. Analyze the user query, agent's reasoning, response, and any tool calls
2. Extract specific, actionable insights
3. Focus on:
   - What approach was used and why
   - Key decisions and their rationale
   - Important metrics or values
   - Patterns that could inform future decisions

Format your learning as concise bullet points.
Example: "When X condition, agent used Y approach because Z reason"
"""
        
        messages.append(LLMMessage(role="system", content=system_prompt))
        
        # Build interaction summary
        interaction_summary = f"""=== Interaction to Learn From ===

**User Query:**
{caller_message}

**Agent's Reasoning:**
{reasoning}

**Agent's Response:**
{response}

**Tool Calls Made:** {len(tool_calls)}
**Tool Results:** {len(tool_results)}

Extract 2-3 key learnings from this interaction."""
        
        messages.append(LLMMessage(role="user", content=interaction_summary))
        
        # Get LLM response for learning extraction
        llm_response = self._agent.llm_client.chat_response_sync(
            messages,
            agent_id=self._agent.object_id,
            agent_type=self._agent.agent_type,
            temperature=0.7,  # Slightly higher temperature for creative insights
        )
        
        learning_content = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
        
        # Store learning to disk
        self._store_acquisitive_learning(loop_id, {
            "loop_id": loop_id,
            "timestamp": timestamp.isoformat(),
            "caller_message": caller_message,
            "response": response,
            "reasoning": reasoning,
            "learning_content": learning_content,
            "tool_calls_count": len(tool_calls),
            "tool_results_count": len(tool_results),
        })
        
        # Add to in-memory cache
        self.acquisitive_memory.append(learning_content)
        
        # Prepare trace_learning result
        trace_learning = {
            "acquisitive_learning": learning_content,
            "loop_id": loop_id,
            "timestamp": timestamp.isoformat(),
        }
        
        logger.info(
            f"Acquisitive learning completed for loop {loop_id}",
            learning_length=len(learning_content),
            session_id=self.session_id,
        )
        
        return {"trace_learning": trace_learning}
        
    except Exception as e:
        logger.error(f"Acquisitive learning failed: {e}", exc_info=True)
        trace_learning = {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
        return {"trace_learning": trace_learning}


def _store_acquisitive_learning(self, loop_id: str, learning_data: dict) -> None:
    """Store acquisitive learning to disk."""
    try:
        storage_path = self._get_acquisitive_storage_path()
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Store as JSON file
        file_path = storage_path / f"loop_{loop_id}.json"
        with open(file_path, 'w') as f:
            json.dump(learning_data, f, indent=2)
        
        logger.debug(f"Stored acquisitive learning to {file_path}")
    except Exception as e:
        logger.error(f"Failed to store acquisitive learning: {e}")


def _load_acquisitive(self) -> list[str]:
    """Load all acquisitive learnings for current session."""
    try:
        storage_path = self._get_acquisitive_storage_path()
        if not storage_path.exists():
            return []
        
        learnings = []
        for file_path in sorted(storage_path.glob("loop_*.json")):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    learnings.append(data.get("learning_content", ""))
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
        
        return learnings
    except Exception as e:
        logger.error(f"Failed to load acquisitive learnings: {e}")
        return []
```

**Flow:**
1. **Extract** interaction data (query, reasoning, response, tool calls)
2. **Prompt LLM** to analyze and extract insights
3. **Store** learning with unique ID to disk as JSON
4. **Cache** learning in memory for quick retrieval
5. **Return** learning trace for agent's reflection phase

**Example output:**

*Stored file: `.dana/.../learnings/session-001/acquisitive/loop_abc123.json`*
```json
{
  "loop_id": "abc123-def456-...",
  "timestamp": "2024-01-15T15:45:23.123456",
  "caller_message": "CURRENT ENVIRONMENT: {indoor_temp: 90, outdoor_temp: 88, meeting: 16:00}",
  "response": "{\"plan\": [{\"time_on\": \"15:50\", ...}]}",
  "reasoning": "Need 10 minutes to cool from 90°F to 72°F...",
  "learning_content": "- When indoor temp is 90°F and outdoor temp is 88°F, agent estimated 10 minutes cooling time for 18°F drop\n- Agent chose non-turbo mode due to sufficient lead time (70 minutes before meeting)\n- Standard cooling rate used: approximately 1.8°F/min",
  "tool_calls_count": 0,
  "tool_results_count": 0
}
```

### 3.3 Episodic Learning Implementation

Episodic learning analyzes patterns across multiple interactions in a session:

```python
@observable
def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
    """
    Reflect on an episode (session-level pattern recognition).
    
    This method analyzes the entire session to extract high-level patterns,
    successful strategies, and areas for improvement.
    
    Args:
        trace_episodic: Collection of experiences from the session
    
    Returns:
        trace_learning: Learning insights from the episode
    """
    try:
        # Load previous episodic learning (if exists)
        previous_learning = self._load_episodic_learning()
        
        messages = []
        
        # System prompt for episodic learning
        system_prompt = """You are a learning and knowledge extraction assistant.

Your role is to analyze agent interactions and extract:
1. Patterns and recurring themes
2. What worked well and what didn't
3. Key insights and learnings
4. Actionable knowledge for future improvements
5. Relationships between actions and outcomes

Be analytical, concise, and focus on extracting actionable knowledge.
Format as markdown with clear sections."""
        
        messages.append(LLMMessage(role="system", content=system_prompt))
        
        # Load timeline for context
        timeline = self._agent._timeline
        timeline.timeline = list(timeline.read_since(checkpoint=-100))  # Last 100 entries
        
        # Convert timeline to LLM messages
        if timeline:
            timeline_messages = timeline.to_llm_messages(
                separate_latest_user=False,
                max_tokens=40000  # Allow large context for comprehensive learning
            )
            
            if timeline_messages:
                # Include previous learning if available
                if previous_learning:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=f"=== Previous Accumulated Learning ===\n{previous_learning}\n\nNow analyze the current session timeline:",
                        )
                    )
                
                # Wrap timeline in structured format
                timeline_lines = [
                    "<SESSION_TIMELINE>",
                    "Analyze the following agent interaction timeline:",
                    "",
                ]
                
                for msg in timeline_messages:
                    role_indicator = "USER" if msg.role == "user" else "AGENT"
                    timeline_lines.append(f"<{role_indicator}>{msg.content}</{role_indicator}>")
                
                timeline_lines.append("</SESSION_TIMELINE>")
                timeline_content = "\n".join(timeline_lines)
                messages.append(LLMMessage(role="user", content=timeline_content))
                
                # Add learning request
                if previous_learning:
                    learning_prompt = """Based on the previous accumulated learning and the current session timeline above, extract:

1. Key patterns and recurring behaviors
2. Successful strategies and approaches
3. Areas for improvement
4. Actionable insights for future interactions

Format: [Condition] → [Advice/Pattern]

Update your accumulated learning by consolidating insights from previous learning and this new session."""
                else:
                    learning_prompt = """Based on the session timeline above, extract:

1. Key patterns and recurring behaviors
2. Successful strategies and approaches
3. Areas for improvement
4. Actionable insights for future interactions

Format: [Condition] → [Advice/Pattern]"""
                
                messages.append(LLMMessage(role="user", content=learning_prompt))
        
        # Get LLM response for episodic learning
        llm_response = self._agent.llm_client.chat_response_sync(
            messages,
            agent_id=self._agent.object_id,
            agent_type=self._agent.agent_type,
        )
        
        episodic_content = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
        
        # Store episodic learning
        self._store_episodic_learning(episodic_content)
        
        # Update in-memory cache
        self.episodic_memory = episodic_content
        
        trace_learning = {
            "simple_summary": episodic_content,
            "learning_note": episodic_content,
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(
            f"Episodic learning completed",
            learning_length=len(episodic_content),
            session_id=self.session_id,
        )
        
        return {"trace_learning": trace_learning}
        
    except Exception as e:
        logger.error(f"Episodic learning failed: {e}", exc_info=True)
        trace_learning = {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
        return {"trace_learning": trace_learning}


def _store_episodic_learning(self, content: str) -> None:
    """Store episodic learning to disk."""
    try:
        storage_path = self._get_episodic_storage_path()
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Store as markdown file
        file_path = storage_path / "learnings.md"
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.debug(f"Stored episodic learning to {file_path}")
    except Exception as e:
        logger.error(f"Failed to store episodic learning: {e}")


def _load_episodic_learning(self) -> str | None:
    """Load episodic learning for current session."""
    try:
        storage_path = self._get_episodic_storage_path()
        file_path = storage_path / "learnings.md"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load episodic learning: {e}")
        return None
```

**Flow:**
1. **Load** previous episodic learning (if exists)
2. **Extract** timeline of all interactions in session
3. **Prompt LLM** with timeline + previous learning to identify patterns
4. **Store** consolidated learning as markdown
5. **Cache** in memory for retrieval

**Example output:**

*Stored file: `.dana/.../learnings/session-001/episodic/learnings.md`*
```markdown
## Session Learning Summary

### Pattern 1: High Outdoor Temperature Requires Buffer
[When outdoor_temp > 85°F] → Add 2-minute buffer to cooling time estimates
- Observed in 5/5 cases during this session
- Helps account for reduced cooling efficiency in hot conditions

### Pattern 2: Turbo Mode Decision Criteria
[When time_until_meeting < 15 minutes] → Use turbo mode
[When time_until_meeting >= 15 minutes] → Use non-turbo mode (cost optimization)
- Turbo mode cooling rate: ~2.5°F/min
- Non-turbo cooling rate: ~1.5°F/min

### Formula: Cooling Time Calculation
```
cooling_time_minutes = temp_diff_fahrenheit / cooling_rate + buffer
where:
  cooling_rate = 2.5 if turbo else 1.5
  buffer = 2 if outdoor_temp > 85 else 1
```

### Areas for Improvement
- Consider meeting duration for determining cooling end time
- Account for thermal mass effects in large rooms
```

### 3.4 Querying Learnings

The learner provides a `query_learnings()` method for retrieving relevant past learnings:

```python
@observable
def query_learnings(self, query: str, phase: LearningPhase | None = None) -> str | None:
    """
    Query stored learnings for relevant insights.
    
    This method is called during the agent's THINK phase to inject
    relevant past learnings into the current decision-making process.
    
    Args:
        query: Search query (e.g., agent's current reasoning or user query)
        phase: Optional learning phase to query (ACQUISITIVE or EPISODIC)
    
    Returns:
        Relevant learning insights as string, or None if not found
    """
    if phase == LearningPhase.ACQUISITIVE:
        # Query acquisitive learnings using BM25 search
        if not self.acquisitive_memory:
            # Load from disk if not in memory
            self.acquisitive_memory = self._load_acquisitive()
        
        if not self.acquisitive_memory:
            return None
        
        # Use BM25 to find most relevant learnings
        engine = BM25SearchEngine(self.acquisitive_memory)
        results = engine.search(query, n=3)  # Top 3 most relevant
        
        return "\n\n".join(results)
    
    elif phase == LearningPhase.EPISODIC:
        # Return episodic learning (single consolidated document)
        if not self.episodic_memory:
            # Load from disk if not in memory
            self.episodic_memory = self._load_episodic_learning()
        
        return self.episodic_memory
    
    else:
        # Default: query both phases
        acquisitive_results = self.query_learnings(query, LearningPhase.ACQUISITIVE)
        episodic_results = self.query_learnings(query, LearningPhase.EPISODIC)
        
        results = []
        if acquisitive_results:
            results.append(f"=== Recent Experiences ===\n{acquisitive_results}")
        if episodic_results:
            results.append(f"=== Accumulated Knowledge ===\n{episodic_results}")
        
        return "\n\n".join(results) if results else None
```

**How it's used:**

The agent automatically calls `query_learnings()` during its THINK phase:

```python
# In STARAgent._think() method
if self._learner:
    # Query learnings relevant to current context
    relevant_learnings = self._learner.query_learnings(
        query=caller_message,  # Use user query as search query
        phase=None  # Query all phases
    )
    
    if relevant_learnings:
        # Inject learnings into prompt
        prompt = f"{prompt}\n\n=== Relevant Past Learnings ===\n{relevant_learnings}"
```

**Example query:**

```python
learner = WilliamLearner(agent=agent)

# Query: "How to handle cooling when outdoor temperature is high?"
results = learner.query_learnings(
    "outdoor temperature high cooling",
    phase=LearningPhase.EPISODIC
)

# Results:
"""
## Pattern: High Outdoor Temperature Requires Buffer
[When outdoor_temp > 85°F] → Add 2-minute buffer to cooling time estimates
- Observed in 5/5 cases
- Helps account for reduced cooling efficiency
"""
```

**BM25 Search Benefits:**
- **Fast**: Simple term-based ranking, no neural models needed
- **Effective**: Works well for keyword-rich queries
- **Lightweight**: No external dependencies beyond rank_bm25
- **Interpretable**: Scores based on term frequency and document length

---

## 4. Example 2: WilliamLearner2 - Feedback-Aware Learning

WilliamLearner2 extends WilliamLearner with feedback-aware episodic learning, enabling the agent to learn from external feedback about its performance.

**Reference:** `examples/agents/hvac/leaners/william_learner2.py`

### 4.1 Extending Existing Learners

Inheritance allows you to extend base learners while preserving their functionality:

```python
from .william_learner import WilliamLearner
from dana.common.protocols import DictParams
from dana.common.llm.types import LLMMessage

class WilliamLearner2(WilliamLearner):
    """
    Enhanced learner with feedback-aware episodic learning.
    
    Overrides _reflect_episodic to check for feedback and implement
    different learning modes accordingly.
    """
    
    @property
    def _has_feedback(self) -> bool:
        """Check if feedback exists for current session."""
        try:
            storage_path = self._get_feedback_storage_path()
            feedback_file = storage_path / "feedback.md"
            return feedback_file.exists() and feedback_file.stat().st_size > 0
        except Exception:
            return False
```

**Key principle:** Override only what you need, inherit the rest.

### 4.2 Dual-Mode Episodic Learning

WilliamLearner2 implements two modes based on feedback availability:

```python
def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
    """
    Reflect on an episode with feedback-aware learning.
    
    Two modes:
    1. With feedback: Enhanced learning using performance feedback
    2. Without feedback: Falls back to parent's standard episodic learning
    """
    if self._has_feedback:
        # Mode: WITH FEEDBACK
        return self._reflect_episodic_with_feedback(trace_episodic)
    else:
        # Mode: WITHOUT FEEDBACK
        # Use standard episodic learning from parent class
        return super()._reflect_episodic(trace_episodic)
```

**Benefits:**
- Graceful degradation when feedback unavailable
- Backward compatibility with WilliamLearner
- Conditional enhancement without breaking existing functionality

### 4.3 Feedback-Integrated Learning

When feedback is available, WilliamLearner2 incorporates it into the learning analysis:

```python
def _reflect_episodic_with_feedback(self, trace_episodic: DictParams) -> DictParams:
    """Enhanced episodic learning when feedback is available."""
    try:
        # Load feedback from storage
        feedback_content = self._load_feedback()
        if not feedback_content:
            logger.warning("Feedback exists but could not be loaded")
            return super()._reflect_episodic(trace_episodic)
        
        # Load previous episodic learning (if exists)
        previous_learning = self._load_episodic_learning()
        
        messages = []
        
        # Enhanced system prompt: system-specific yet adaptable
        system_prompt = """You are a learning and knowledge extraction assistant with access to performance feedback.

Your role is to extract actionable advice from feedback that captures the specific system's actual characteristics, while formulating adaptable rules.

CRITICAL BALANCE:
- Extract THIS system's actual characteristics from feedback (observed rates, patterns, thresholds, behaviors)
- Calculate THIS system's specific performance metrics from feedback (e.g., rate = observed_change / observed_time)
- Extract value ranges and approximate values when they're useful
- Formulate rules as formulas/patterns/ranges that capture THIS system's characteristics but adapt to different scenarios

Guidelines for VALUE EXTRACTION:
- Extract specific values and ranges from feedback when useful (e.g., "this system processes at rate ~X-Y units/time")
- Express values as ranges, approximations, or formulas rather than exact constants
- Frame specific values as THIS system's observed characteristics that inform formulas

Guidelines for FORMULA CREATION:
- Use feedback to calculate THIS system's actual performance metrics from observed data
- Create formulas that incorporate THIS system's observed characteristics
- Extract THIS system's specific thresholds and patterns from feedback
- Formulate adaptable rules that work for THIS system across different scenarios

The learning must capture THIS specific system's characteristics from feedback (including useful value ranges), but express them as adaptable formulas/ranges that work across variations."""
        
        messages.append(LLMMessage(role="system", content=system_prompt))
        
        # Include feedback with emphasis on system-specific learning
        feedback_section = f"""=== PERFORMANCE FEEDBACK ===
{feedback_content}

This feedback contains actual performance data from the system. 
Extract specific metrics, rates, patterns, and formulas that characterize THIS system's behavior."""
        
        # Load timeline for context
        timeline = self._agent._timeline
        timeline.timeline = list(timeline.read_since(checkpoint=-100))
        
        # Convert timeline to messages
        if timeline:
            timeline_messages = timeline.to_llm_messages(
                separate_latest_user=False,
                max_tokens=40000
            )
            
            if previous_learning:
                messages.append(
                    LLMMessage(
                        role="user",
                        content=f"=== Previous Learning ===\n{previous_learning}\n\nNow analyze the session:",
                    )
                )
            
            messages.extend(timeline_messages)
        
        # Add feedback and learning request
        learning_prompt = f"""{feedback_section}

Based on the timeline and feedback above, extract:
1. THIS system's actual performance metrics (rates, thresholds, patterns) from feedback
2. Formulas that capture THIS system's characteristics but adapt to inputs
3. Value ranges observed in feedback that inform decision-making
4. Patterns specific to THIS system's behavior

Format: [Condition] → [Formula/Pattern with THIS system's observed values]
Example: "[When outdoor_temp > 85°F] → Use cooling_rate = 1.3°F/min (observed from feedback), so time = temp_diff / 1.3 + 2min buffer"
"""
        
        messages.append(LLMMessage(role="user", content=learning_prompt))
        
        # Get LLM response for enhanced learning
        llm_response = self._agent.llm_client.chat_response_sync(
            messages,
            agent_id=self._agent.object_id,
            agent_type=self._agent.agent_type,
            temperature=0.7,
        )
        
        episodic_content = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
        
        # Store and cache
        self._store_episodic_learning(episodic_content)
        self.episodic_memory = episodic_content
        
        trace_learning = {
            "simple_summary": episodic_content,
            "learning_note": episodic_content,
            "timestamp": datetime.now().isoformat(),
            "reflection_context": f"Feedback-aware learning: {len(feedback_content)} chars",
        }
        
        return {"trace_learning": trace_learning}
        
    except Exception as e:
        logger.error(f"Episodic learning with feedback failed: {e}", exc_info=True)
        return super()._reflect_episodic(trace_episodic)
```

**Key enhancements:**
- System prompt emphasizes extracting system-specific characteristics
- Feedback integrated with timeline for comprehensive context
- Formulas and value ranges extracted from actual performance data
- Falls back to parent implementation on error

### 4.4 Feedback Storage and Retrieval

```python
def save_feedback(self, feedback: Any) -> None:
    """Save feedback data for current session."""
    try:
        storage_path = self._get_feedback_storage_path()
        storage_path.mkdir(parents=True, exist_ok=True)
        
        file_path = storage_path / "feedback.md"
        with open(file_path, 'w') as f:
            if isinstance(feedback, dict):
                f.write(json.dumps(feedback, indent=2))
            else:
                f.write(str(feedback))
        
        logger.info(f"Saved feedback to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")


def _load_feedback(self) -> str | None:
    """Load feedback data for current session."""
    try:
        storage_path = self._get_feedback_storage_path()
        file_path = storage_path / "feedback.md"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load feedback: {e}")
        return None
```

**Usage in HVAC Agent:**

```python
# After agent creates plan and it's validated
feedback = get_feedback(
    current_indoor_temp=env_status["indoor_temp"],
    outdoor_temp=env_status["outdoor_temp"],
    current_time=env_status["current_time"],
    plan=plan["plan"],
    target_temps=plan["target_temps"],
    mode=plan["mode"],
    meeting_plan=env_status["meeting_plan"],
)

# Save feedback for learner
agent._learner.save_feedback(json.dumps(feedback, indent=2))

# Later trigger episodic learning
agent._learner._reflect_episodic({})
```

**Example feedback format:**

```json
{
  "overall_success": true,
  "action_feedbacks": [
    {
      "action_index": 0,
      "success": true,
      "target_temp_reached": true,
      "actual_cooling_rate": 1.8,
      "expected_cooling_rate": 1.5,
      "buffer_sufficient": true,
      "time_variance_minutes": -1.2
    }
  ],
  "insights": "Cooling was 20% faster than estimated. Outdoor temp was lower than expected."
}
```

---

## 5. Example 3: WilliamLearner3 - Specialized Feedback Learning

WilliamLearner3 demonstrates a more specialized approach with domain-specific prompts.

**Reference:** `examples/agents/hvac/leaners/william_learner3.py`

### 5.1 Specialized Prompts

WilliamLearner3 uses a highly specialized system prompt tailored to the HVAC domain:

```python
SYSTEM_PROMPT = """
You are the **HVAC-Learning Assistant**.
Convert every new **plan + execution feedback** cycle into concise Markdown **Learning Notes** that capture THIS system's real-world behaviour and actionable rules.

## Your 5 Obligations  
1. **Pair each action with its feedback** (`action_index` → feedback block).  
2. **Compute fresh metrics** for the pair  
   • `cooling_rate = (start_temp_f – target_temp_f) / time_needed_minutes`  
   • `buffer_gap  = meeting_start_time – reached_time` (− = late)  
3. **Label outcome** (`success` / `failed`) and explain why.  
4. **Maintain value ranges & formulas**—expand or tighten as evidence grows.
5. **Write guidance** that would have prevented today's failure next time. This should be a comprehensive guidance for the whole session, not just the current action with step by step advice when to use turbo mode, calculation formula and latest values like cooling rate (turbo/ non-turbo), buffer gap, etc.

### INPUT ORDER  
1. `<previous_learning> … </previous_learning>`  
2. CURRENT_ENVIRONMENT block  
3. PLAN block (array with `action_index`)  
4. `<feedback> … </feedback>`

### OUTPUT — Markdown ONLY  
```
<updated_learning>

[Condition: …] Observation → Advice

…
</updated_learning>
```

<previous_learning>
{previous_learning}
</previous_learning>
"""
```

**Characteristics:**
- Very specific to HVAC domain (cooling rates, buffer gaps, turbo mode)
- Structured obligations framework
- Explicit input/output format
- Incorporates previous learning directly

### 5.2 Streamlined Implementation

```python
class WilliamLearner3(WilliamLearner):
    """Simplified feedback-aware learner with specialized prompts."""
    
    def _reflect_episodic_with_feedback(self, trace_episodic: DictParams) -> DictParams:
        """Enhanced episodic learning with specialized HVAC prompts."""
        try:
            feedback_content = self._load_feedback()
            if not feedback_content:
                return super()._reflect_episodic(trace_episodic)
            
            previous_learning = self._load_episodic_learning()
            
            messages = []
            
            # Use specialized system prompt
            system_prompt = SYSTEM_PROMPT.format(previous_learning=previous_learning or "")
            messages.append(LLMMessage(role="system", content=system_prompt))
            
            # Load timeline
            timeline = self._agent._timeline
            timeline.timeline = list(timeline.read_since(checkpoint=-2))  # Just recent context
            
            if timeline:
                timeline_messages = timeline.to_llm_messages(
                    separate_latest_user=False,
                    max_tokens=40000
                )
                messages.extend(timeline_messages)
            
            # Add feedback with specific format
            feedback_section = f"<feedback>\n{feedback_content}\n</feedback>"
            learning_section = """Using the data above (plan, feedback, previous learning):

• Execute the 5-step process defined in SYSTEM_PROMPT.  
• Think silently first, then emit only the Markdown block required.

(Do not add narrative, JSON, or code.)"""
            
            messages.append(LLMMessage(role="user", content=f"{feedback_section}\n{learning_section}"))
            
            # Get LLM response
            llm_response = self._agent.llm_client.chat_response_sync(
                messages,
                agent_id=self._agent.object_id,
                agent_type=self._agent.agent_type,
                temperature=0.7,
            )
            
            episodic_content = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
            
            # Clean up output markers
            episodic_content = episodic_content.replace("<updated_learning>", "")
            episodic_content = episodic_content.replace("</updated_learning>", "")
            
            # Store and cache
            self._store_episodic_learning(episodic_content)
            self.episodic_memory = episodic_content
            
            trace_learning = {
                "simple_summary": episodic_content,
                "learning_note": episodic_content,
                "timestamp": datetime.now().isoformat(),
            }
            
            return {"trace_learning": trace_learning}
            
        except Exception as e:
            logger.error(f"Episodic learning with feedback failed: {e}", exc_info=True)
            return super()._reflect_episodic(trace_episodic)
```

**Trade-offs:**

| Aspect | General-Purpose (WilliamLearner2) | Specialized (WilliamLearner3) |
|--------|-----------------------------------|-------------------------------|
| **Flexibility** | Works across domains | HVAC-specific |
| **Precision** | Extracts general patterns | Extracts domain-specific metrics |
| **Maintenance** | One learner, many agents | Custom learner per domain |
| **Learning Quality** | Good, generic insights | Excellent, actionable formulas |
| **Prompt Engineering** | Moderate | High (domain expertise needed) |

**When to use specialized learners:**
- Domain has specific metrics/formulas (HVAC rates, financial ratios, etc.)
- You need highly actionable, quantitative insights
- You can invest time in prompt engineering
- Single-domain agent (not multi-purpose)

---

## 6. Integrating Custom Learners with Agents

Now let's see how to integrate custom learners into your agents.

### 6.1 Agent Initialization

There are two ways to attach a custom learner:

**Option 1: Pass during STARAgent initialization**

```python
from dana.core.agent.star_agent import STARAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec
from leaners.william_learner import WilliamLearner

class HVACAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="hvac-agent",
            agent_id="hvac-agent-001",
            llm_provider="llamastack",
            model="openai/gpt-4.1",
            codec=CSXMLCodec,
            learner=WilliamLearner(agent=None),  # Pass learner instance
            **kwargs
        )
```

**Option 2: Set after agent creation (recommended)**

```python
agent = HVACAgent()
agent._learner = WilliamLearner(agent=agent)  # Set learner after initialization
```

**Why Option 2 is recommended:**
- Learner needs agent reference for LLM client, timeline, etc.
- Circular dependency avoided
- More explicit and clear

### 6.2 Learning Triggers

**Automatic Acquisitive Learning:**

Acquisitive learning is triggered automatically after each `agent.query()` call:

```python
# User calls query
result = agent.query(caller_message="Create HVAC plan...", session_id="session-001")

# Behind the scenes, agent automatically calls:
# agent._learner._reflect_acquisitive(trace_acquisitive)
```

**Manual Episodic Learning:**

Episodic learning is typically triggered manually when you want to consolidate session learnings:

```python
# After multiple queries in a session
agent._learner._reflect_episodic({})
```

**Feedback Submission Workflow:**

```python
# 1. Agent creates plan
result = agent.query(caller_message=env_prompt, session_id="session-001")
plan = json.loads(result["response"])

# 2. Validate plan in environment (e.g., simulation or real system)
feedback = validate_plan(plan)  # Returns success/failure metrics

# 3. Save feedback for learner
agent._learner.save_feedback(json.dumps(feedback, indent=2))

# 4. Trigger episodic learning with feedback
agent._learner._reflect_episodic({})

# 5. Next query will use accumulated learning
result2 = agent.query(caller_message=new_env_prompt, session_id="session-001")
# Learner's query_learnings() automatically injects past learnings into prompt
```

### 6.3 Complete Integration Example

Here's the full integration from the HVAC Agent:

```python
"""
Complete HVAC Agent with WilliamLearner integration.
"""
import os
import json
from dana.core.agent.star_agent import STARAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec
from environment.hvac_api import get_env_status, get_feedback
from leaners.william_learner import WilliamLearner


class HVACAgent(STARAgent):
    def __init__(self, **kwargs):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "HVACAgent.xml")
        
        super().__init__(
            agent_type="hvac-agent",
            agent_id="hvac-agent-001",
            llm_provider="llamastack",
            model="openai/gpt-4.1",
            prompt_path=prompt_path,
            codec=CSXMLCodec,
            **kwargs
        )


# Usage example
if __name__ == "__main__":
    # 1. Create agent
    agent = HVACAgent()
    
    # 2. Attach custom learner
    agent._learner = WilliamLearner(agent=agent)
    
    session_id = "hvac-session-001"
    
    # 3. First query (agent learns from this)
    env_status = get_env_status()
    result = agent.query(
        caller_message=f"CURRENT ENVIRONMENT: {json.dumps(env_status, indent=2)}",
        session_id=session_id
    )
    
    # 4. Manually trigger acquisitive learning (optional, happens automatically)
    acquisitive_input = result.copy()
    acquisitive_input.setdefault("caller_message", f"CURRENT ENVIRONMENT: {json.dumps(env_status, indent=2)}")
    acquisitive_input.setdefault("tool_calls", [])
    acquisitive_input.setdefault("tool_results", [])
    agent._learner._reflect_acquisitive(acquisitive_input)
    
    # 5. Validate plan and get feedback
    plan = json.loads(result["response"])
    feedback = get_feedback(
        current_indoor_temp=env_status["indoor_temp"],
        outdoor_temp=env_status["outdoor_temp"],
        current_time=env_status["current_time"],
        plan=plan["plan"],
        target_temps=plan["target_temps"],
        mode=plan["mode"],
        meeting_plan=env_status["meeting_plan"],
    )
    
    # 6. Save feedback
    agent._learner.save_feedback(json.dumps(feedback, indent=2))
    
    # 7. Trigger episodic learning with feedback
    agent._learner._reflect_episodic({})
    
    print("Learning completed!")
    print(f"Acquisitive learnings: {len(agent._learner.acquisitive_memory)}")
    print(f"Episodic learning: {len(agent._learner.episodic_memory or '')} chars")
    
    # 8. Next query will automatically use learnings
    result2 = agent.query(
        caller_message=f"CURRENT ENVIRONMENT: {json.dumps(get_env_status(), indent=2)}",
        session_id=session_id
    )
    # Learner automatically injects relevant past learnings into the prompt
```

---

## 7. Learning Storage Architecture

Understanding the storage architecture helps you debug and optimize your custom learners.

### 7.1 Repository Pattern

Dana uses the repository pattern for all storage:

```python
from dana.repositories.repository_protocol import LearningRepositoryProtocol

class LearningRepositoryProtocol(Protocol):
    """Protocol defining the interface for learning repositories."""
    
    def save_learning(self, session_id: str, phase: LearningPhase, content: Any) -> None:
        """Save learning content for a session and phase."""
        ...
    
    def load_learning(self, session_id: str, phase: LearningPhase) -> Any:
        """Load learning content for a session and phase."""
        ...
    
    def list_sessions(self) -> list[str]:
        """List all available sessions."""
        ...
```

**Default implementation:** `LocalFileRepository`
- Stores to local filesystem
- Located in `.dana/dana_agent/` directory
- Organized by codec, agent class, and session

### 7.2 Storage Path Structure

```
.dana/dana_agent/
└── {codec_name}/              # e.g., "CSXMLCodec"
    └── {agent_class}/          # e.g., "HVACAgent"
        ├── learnings/
        │   └── {session_id}/   # e.g., "hvac-session-001"
        │       ├── acquisitive/
        │       │   ├── loop_<uuid1>.json
        │       │   ├── loop_<uuid2>.json
        │       │   └── ...
        │       └── episodic/
        │           └── learnings.md
        ├── feedback/
        │   └── {session_id}/
        │       └── feedback.md
        └── timeline/
            └── {session_id}/
                └── timeline.json
```

**Acquisitive vs Episodic Storage:**

| Aspect | Acquisitive | Episodic |
|--------|-------------|----------|
| **Files** | Multiple (`loop_*.json`) | Single (`learnings.md`) |
| **Format** | JSON | Markdown |
| **Granularity** | One per interaction | One per session |
| **Size** | Small (1-5KB each) | Medium (10-100KB) |
| **Retrieval** | BM25 search across all | Direct load |

---

## 8. Advanced Topics

### 8.1 Custom Retrieval Strategies

Beyond BM25, you can implement semantic search:

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticSearchLearner(WilliamLearner):
    """Learner with semantic search using embeddings."""
    
    def __init__(self, agent, **kwargs):
        super().__init__(agent, **kwargs)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.acquisition_embeddings = None
    
    def query_learnings(self, query: str, phase: LearningPhase | None = None) -> str | None:
        if phase == LearningPhase.ACQUISITIVE:
            if not self.acquisitive_memory:
                self.acquisitive_memory = self._load_acquisitive()
            
            if not self.acquisitive_memory:
                return None
            
            # Compute embeddings if not cached
            if self.acquisition_embeddings is None:
                self.acquisition_embeddings = self.embedding_model.encode(self.acquisitive_memory)
            
            # Encode query and find most similar
            query_embedding = self.embedding_model.encode([query])[0]
            similarities = np.dot(self.acquisition_embeddings, query_embedding)
            top_indices = np.argsort(similarities)[::-1][:3]
            
            return "\n\n".join([self.acquisitive_memory[i] for i in top_indices])
        
        # Fall back to parent for other phases
        return super().query_learnings(query, phase)
```

**Trade-offs:**
- **BM25**: Fast, lightweight, keyword-based, no GPU needed
- **Semantic**: Slower, requires models, meaning-based, GPU helpful
- **Hybrid**: Use both - BM25 for initial filtering, semantic for reranking

### 8.2 Cross-Session Learning

Implement integrative learning across multiple sessions:

```python
def _reflect_integrative(self, trace_integrative: DictParams) -> DictParams:
    """Integrate learnings from multiple sessions."""
    try:
        # Get all session IDs
        all_sessions = self._repository.list_sessions()
        
        # Load episodic learnings from recent sessions
        recent_learnings = []
        for session_id in all_sessions[-10:]:  # Last 10 sessions
            learning = self._load_episodic_learning_for_session(session_id)
            if learning:
                recent_learnings.append(f"=== Session {session_id} ===\n{learning}")
        
        if not recent_learnings:
            return {"trace_learning": {"error": "No sessions to integrate"}}
        
        # Prompt LLM to find cross-session patterns
        messages = [
            LLMMessage(
                role="system",
                content="You are integrating learnings across multiple sessions to find universal patterns and rules."
            ),
            LLMMessage(
                role="user",
                content=f"{'='*80}\n".join(recent_learnings) + "\n\nExtract patterns that appear consistently across sessions."
            )
        ]
        
        llm_response = self._agent.llm_client.chat_response_sync(messages, agent_id=self._agent.object_id, agent_type=self._agent.agent_type)
        
        integrated_learning = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
        
        # Store integrated learning
        self._store_integrated_learning(integrated_learning)
        
        return {"trace_learning": {"integrated_learning": integrated_learning}}
        
    except Exception as e:
        logger.error(f"Integrative learning failed: {e}")
        return {"trace_learning": {"error": str(e)}}
```

---

## 9. Best Practices & Patterns

### When to Create Custom Learners

**Create custom learners when:**
- ✅ Domain has specific metrics/formulas to extract
- ✅ You have external feedback/validation data
- ✅ Default learning is too generic for your use case
- ✅ You need specialized retrieval (embeddings, graph search, etc.)
- ✅ Custom storage requirements (database, cloud, etc.)

**Use default `Learner` when:**
- ✅ General-purpose agent without domain-specific needs
- ✅ Rapid prototyping phase
- ✅ Simple learning requirements
- ✅ Resource constraints (time/complexity)

### Prompt Engineering for Learning

**Good learning prompts:**
- Focus on **extracting actionable insights**
- Request **specific formats** (formulas, conditions, ranges)
- Emphasize **patterns** over individual cases
- Include **examples** of desired output
- Specify **conciseness** to avoid verbosity

**Example comparison:**

❌ **Bad:**
```
"Analyze the agent's interactions and tell me what you learned."
```

✅ **Good:**
```
"Extract 2-3 actionable patterns from the agent's interactions.
Format: [Condition] → [Action/Formula]
Example: [When temp_diff > 20°F] → Use turbo mode, time = temp_diff / 2.5 + 2min
Focus on quantitative insights with specific thresholds and formulas."
```

### Testing Custom Learners

```python
import pytest
from unittest.mock import Mock, MagicMock

def test_william_learner_acquisitive():
    """Test acquisitive learning."""
    # Mock agent
    agent = Mock()
    agent.object_id = "test-agent"
    agent.agent_type = "test"
    agent._session_id = "test-session"
    agent.llm_client = Mock()
    agent.llm_client.chat_response_sync = Mock(return_value=Mock(content="Test learning insight"))
    
    # Create learner
    learner = WilliamLearner(agent=agent)
    
    # Test acquisitive learning
    trace = {
        "caller_message": "Test query",
        "response": "Test response",
        "reasoning": "Test reasoning",
        "tool_calls": [],
        "tool_results": []
    }
    
    result = learner._reflect_acquisitive(trace)
    
    # Assertions
    assert "trace_learning" in result
    assert "acquisitive_learning" in result["trace_learning"]
    assert agent.llm_client.chat_response_sync.called


def test_feedback_aware_learner():
    """Test feedback-aware episodic learning."""
    # Mock agent with feedback
    agent = Mock()
    agent._session_id = "test-session"
    # ... setup ...
    
    learner = WilliamLearner2(agent=agent)
    
    # Save mock feedback
    learner.save_feedback({"success": True, "metrics": {"rate": 1.5}})
    
    # Test episodic learning
    result = learner._reflect_episodic({})
    
    # Assertions
    assert "trace_learning" in result
    assert learner._has_feedback == True
```

### Common Pitfalls

**Pitfall 1: Not handling missing learnings gracefully**

❌ **Bad:**
```python
def query_learnings(self, query: str) -> str:
    return "\n".join(self.acquisitive_memory)  # Crashes if empty
```

✅ **Good:**
```python
def query_learnings(self, query: str) -> str | None:
    if not self.acquisitive_memory:
        return None
    return "\n".join(self.acquisitive_memory)
```

**Pitfall 2: Forgetting to store learnings**

❌ **Bad:**
```python
def _reflect_acquisitive(self, trace):
    learning = self._extract_learning(trace)
    # Oops, not stored!
    return {"trace_learning": learning}
```

✅ **Good:**
```python
def _reflect_acquisitive(self, trace):
    learning = self._extract_learning(trace)
    self._store_acquisitive_learning(loop_id, learning)  # Store it!
    return {"trace_learning": learning}
```

**Pitfall 3: Not caching in memory**

❌ **Bad:**
```python
def query_learnings(self, query):
    # Loads from disk every time - slow!
    learnings = self._load_acquisitive()
    return search(learnings, query)
```

✅ **Good:**
```python
def query_learnings(self, query):
    if not self.acquisitive_memory:
        # Load once, cache in memory
        self.acquisitive_memory = self._load_acquisitive()
    return search(self.acquisitive_memory, query)
```

---

## 10. Complete Reference Example

Here's a complete end-to-end example showing all aspects of custom learning:

```python
"""
Complete HVAC Agent Learning Example
Demonstrates: WilliamLearner integration, feedback workflow, learning retrieval
"""
import os
import json
from datetime import datetime

from dana.core.agent.star_agent import STARAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec
from environment.hvac_api import get_env_status, get_feedback
from leaners.william_learner import WilliamLearner


class HVACAgent(STARAgent):
    def __init__(self, **kwargs):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "HVACAgent.xml")
        super().__init__(
            agent_type="hvac-agent",
            agent_id="hvac-agent-001",
            llm_provider="llamastack",
            model="openai/gpt-4.1",
            prompt_path=prompt_path,
            codec=CSXMLCodec,
            **kwargs
        )


def run_learning_demo():
    """Complete learning workflow demonstration."""
    print("=" * 80)
    print("HVAC Agent Learning Demo")
    print("=" * 80)
    
    # 1. Setup
    print("\n[1] Setting up agent with custom learner...")
    agent = HVACAgent()
    agent._learner = WilliamLearner(agent=agent)
    session_id = f"hvac-learning-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"    Session ID: {session_id}")
    
    # 2. Run multiple interactions
    print("\n[2] Running 3 agent interactions...")
    for i in range(3):
        print(f"\n    Interaction {i+1}/3:")
        
        # Get environment
        env_status = get_env_status()
        print(f"      Indoor temp: {env_status['indoor_temp']}°F")
        print(f"      Meeting at: {env_status['meeting_plan'][0]['start_time']}")
        
        # Query agent
        result = agent.query(
            caller_message=f"CURRENT ENVIRONMENT:\n{json.dumps(env_status, indent=2)}",
            session_id=session_id
        )
        
        plan = json.loads(result["response"])
        print(f"      Plan: Cool starting at {plan['plan'][0]['time_on']}")
        
        # Trigger acquisitive learning
        acquisitive_input = result.copy()
        acquisitive_input.setdefault("caller_message", f"CURRENT ENVIRONMENT:\n{json.dumps(env_status, indent=2)}")
        agent._learner._reflect_acquisitive(acquisitive_input)
        print(f"      ✓ Acquisitive learning saved")
        
        # Validate and get feedback
        feedback = get_feedback(
            current_indoor_temp=env_status["indoor_temp"],
            outdoor_temp=env_status["outdoor_temp"],
            current_time=env_status["current_time"],
            plan=plan["plan"],
            target_temps=plan["target_temps"],
            mode=plan["mode"],
            meeting_plan=env_status["meeting_plan"],
        )
        
        print(f"      Feedback: {feedback['overall_success']}")
    
    # 3. Save feedback from last interaction
    print("\n[3] Saving feedback from last interaction...")
    agent._learner.save_feedback(json.dumps(feedback, indent=2))
    print("    ✓ Feedback saved")
    
    # 4. Trigger episodic learning
    print("\n[4] Triggering episodic learning...")
    agent._learner._reflect_episodic({})
    print("    ✓ Episodic learning completed")
    
    # 5. View learning results
    print("\n[5] Learning Results:")
    print(f"    Acquisitive learnings: {len(agent._learner.acquisitive_memory)}")
    print(f"    Episodic learning: {len(agent._learner.episodic_memory or '')} characters")
    
    if agent._learner.episodic_memory:
        print("\n    Episodic Learning Preview:")
        preview = agent._learner.episodic_memory[:500]
        print(f"    {preview}...")
    
    # 6. Query learnings
    print("\n[6] Querying learnings...")
    query = "outdoor temperature high cooling"
    results = agent._learner.query_learnings(query, phase=None)
    
    if results:
        print(f"    Query: '{query}'")
        print(f"    Results (first 300 chars):")
        print(f"    {results[:300]}...")
    
    # 7. Use learnings in next interaction
    print("\n[7] Running new interaction with accumulated learnings...")
    env_status = get_env_status()
    result = agent.query(
        caller_message=f"CURRENT ENVIRONMENT:\n{json.dumps(env_status, indent=2)}",
        session_id=session_id
    )
    print("    ✓ Agent used past learnings automatically")
    print(f"    (Learnings injected into prompt during THINK phase)")
    
    # 8. Storage locations
    print("\n[8] Learning Storage Locations:")
    print(f"    Base path: .dana/dana_agent/CSXMLCodec/HVACAgent/")
    print(f"    Acquisitive: learnings/{session_id}/acquisitive/loop_*.json")
    print(f"    Episodic: learnings/{session_id}/episodic/learnings.md")
    print(f"    Feedback: feedback/{session_id}/feedback.md")
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    run_learning_demo()
```

**Expected Output:**

```
================================================================================
HVAC Agent Learning Demo
================================================================================

[1] Setting up agent with custom learner...
    Session ID: hvac-learning-demo-20240115-143022

[2] Running 3 agent interactions...

    Interaction 1/3:
      Indoor temp: 88.5°F
      Meeting at: 16:15
      Plan: Cool starting at 16:05
      ✓ Acquisitive learning saved
      Feedback: True

    Interaction 2/3:
      Indoor temp: 92.1°F
      Meeting at: 15:45
      Plan: Cool starting at 15:32
      ✓ Acquisitive learning saved
      Feedback: True

    Interaction 3/3:
      Indoor temp: 85.3°F
      Meeting at: 17:00
      Plan: Cool starting at 16:48
      ✓ Acquisitive learning saved
      Feedback: False

[3] Saving feedback from last interaction...
    ✓ Feedback saved

[4] Triggering episodic learning...
    ✓ Episodic learning completed

[5] Learning Results:
    Acquisitive learnings: 3
    Episodic learning: 487 characters

    Episodic Learning Preview:
    ## Session Learning Summary

    ### Pattern 1: High Outdoor Temperature Requires Buffer
    [When outdoor_temp > 85°F] → Add 2-minute buffer to cooling time estimates
    - Observed in 3/3 cases during this session
    - Helps account for reduced cooling efficiency in hot conditions

    ### Formula: Cooling Time Calculation
    ```
    cooling_time_minutes = temp_diff_fahrenheit / cooling_rate + buffer
    ...

[6] Querying learnings...
    Query: 'outdoor temperature high cooling'
    Results (first 300 chars):
    === Recent Experiences ===
    - When indoor temp is 92.1°F and outdoor temp is 90.2°F, agent estimated 15 minutes cooling time
    - Agent chose non-turbo mode due to sufficient lead time (45 minutes before meeting)
    - Standard cooling rate used: approximately 1.5°F/min

    === Accumulated Knowledge ===
    ## Pattern: High Outdoor...

[7] Running new interaction with accumulated learnings...
    ✓ Agent used past learnings automatically
    (Learnings injected into prompt during THINK phase)

[8] Learning Storage Locations:
    Base path: .dana/dana_agent/CSXMLCodec/HVACAgent/
    Acquisitive: learnings/hvac-learning-demo-20240115-143022/acquisitive/loop_*.json
    Episodic: learnings/hvac-learning-demo-20240115-143022/episodic/learnings.md
    Feedback: feedback/hvac-learning-demo-20240115-143022/feedback.md

================================================================================
Demo Complete!
================================================================================
```

---

**End of Learning Guide**

For questions or issues, refer to:
- Dana documentation: [docs/](../../)
- HVAC Agent README: `examples/agents/hvac/README.md`
- Codec Guide: `codec.md`

