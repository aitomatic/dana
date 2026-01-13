# Learning Guide: Getting Started with Custom Learners

> **Looking for advanced details?** See [learning-advanced.md](./learning-advanced.md) for comprehensive implementation walkthroughs, advanced patterns, and complete reference examples.

This guide shows you how to implement custom learners for Dana agents using the STAR learning framework. We'll use examples from the HVAC Agent (`examples/agents/hvac`) to demonstrate practical implementations.

## Table of Contents

1. [Introduction](#1-introduction)
2. [Understanding the Learner Protocol](#2-understanding-the-learner-protocol)
3. [Simple Custom Learner Example](#3-simple-custom-learner-example)
4. [Integrating Learners with Agents](#4-integrating-learners-with-agents)

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
   - Example: "Cooling from 90°F to 72°F took 12 minutes with turbo mode"

2. **EPISODIC Learning** (Session-level)
   - Triggered: After completing a session or on-demand
   - Purpose: Recognize patterns across multiple interactions
   - Example: "When outdoor temp > 85°F, always add 2-minute buffer for cooling"

3. **INTEGRATIVE Learning** (Cross-session)
   - Triggered: Periodically or when merging sessions
   - Purpose: Combine learnings from multiple sessions

4. **RETENTIVE Learning** (Long-term)
   - Triggered: Periodically for knowledge consolidation
   - Purpose: Create persistent, general rules

### Why Custom Learners Matter

The default `Learner` class provides basic functionality, but custom learners enable:

- **Domain-specific learning strategies** tailored to your use case
- **Custom retrieval mechanisms** (BM25, embeddings, semantic search)
- **Feedback integration** for learning from outcomes
- **Specialized prompt engineering** for better insight extraction

**Example:** The HVAC Agent uses `WilliamLearner` to:
- Extract HVAC-specific metrics (cooling rates, buffer times)
- Learn from environment feedback (success/failure of temperature plans)
- Use BM25 search for retrieving relevant past experiences

---

## 2. Understanding the Learner Protocol

Custom learners must implement the `LearnerProtocol` interface to integrate with Dana agents.

### Required Methods

**Core reflection methods (MUST implement):**
- `_reflect_acquisitive()`: Called after each agent interaction
- `_reflect_episodic()`: Called after session or on-demand
- `_reflect_integrative()`: Optional - for cross-session learning
- `_reflect_retentive()`: Optional - for long-term consolidation

**Utility methods (SHOULD implement):**
- `query_learnings()`: Retrieve relevant past learnings
- `_load_acquisitive()` / `_load_episodic()`: Load stored learnings
- `save_feedback()` / `_load_feedback()`: Handle external feedback

### Basic Interface Structure

```python
from dana.core.agent.components.learner import LearnerProtocol
from dana.common.protocols import DictParams

class MyLearner(LearnerProtocol):
    def __init__(self, agent: "STARAgent", **kwargs):
        self._agent = agent
        # Initialize storage, search engine, etc.
    
    def _reflect_acquisitive(self, trace_acquisitive: DictParams) -> DictParams:
        """Extract insights from a single interaction."""
        # Your implementation here
        return {"trace_learning": {...}}
    
    def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
        """Analyze patterns across a session."""
        # Your implementation here
        return {"trace_learning": {...}}
    
    def query_learnings(self, query: str, phase: LearningPhase | None = None) -> str | None:
        """Retrieve relevant past learnings."""
        # Your implementation here
        return "Relevant learning content..."
```

### Learning Storage Pattern

Custom learners use the repository pattern for storage:

```
.dana/dana_agent/{codec_name}/{agent_class}/learnings/{session_id}/
├── acquisitive/
│   ├── loop_abc123.json   # Individual acquisitions
│   └── loop_def456.json
└── episodic/
    └── learnings.md        # Session-level patterns
```

**Key concepts:**
- **Repository pattern**: Abstract storage interface
- **Session-based**: Each session has isolated learning storage
- **Phase separation**: Acquisitive and episodic learnings stored separately
- **Retrievable**: Learnings can be queried and injected into agent prompts

---

## 3. Simple Custom Learner Example

Let's build a basic custom learner step-by-step using the HVAC Agent's `WilliamLearner` as our example.

### Basic Structure

```python
"""
Simple custom learner example.
"""
import json
from datetime import datetime
from uuid import uuid4
from pathlib import Path

from dana.core.agent.components.learner import LearnerProtocol
from dana.common.protocols import DictParams
from dana.common.llm.types import LLMMessage

class SimpleLearner(LearnerProtocol):
    """Basic custom learner with acquisitive and episodic learning."""
    
    def __init__(self, agent: "STARAgent"):
        self._agent = agent
        self.acquisitive_memory = []  # In-memory cache
        
        # Initialize repository for storage
        from dana.repositories.repository_factory import DEFAULT_REPOSITORY_FACTORY, RepositoryType
        factory = DEFAULT_REPOSITORY_FACTORY
        self._repository = factory.create(RepositoryType.LEARNING, agent=agent)
    
    @property
    def session_id(self) -> str | None:
        """Get current session ID from agent."""
        return getattr(self._agent, "_session_id", None)
```

### Acquisitive Learning (Simplified)

Acquisitive learning extracts insights from each interaction:

```python
def _reflect_acquisitive(self, trace_acquisitive: DictParams) -> DictParams:
    """Extract insights from a single interaction."""
    try:
        # Extract interaction data
        caller_message = trace_acquisitive.get("caller_message", "")
        response = trace_acquisitive.get("response", "")
        reasoning = trace_acquisitive.get("reasoning", "")
        
        # Build prompt for LLM to extract insights
        messages = [
            LLMMessage(
                role="system",
                content="Extract 2-3 key insights from this agent interaction."
            ),
            LLMMessage(
                role="user",
                content=f"Query: {caller_message}\nReasoning: {reasoning}\nResponse: {response}"
            )
        ]
        
        # Get LLM to extract learning
        llm_response = self._agent.llm_client.chat_response_sync(
            messages,
            agent_id=self._agent.object_id,
            agent_type=self._agent.agent_type,
        )
        
        learning_content = llm_response.content
        
        # Store learning
        loop_id = str(uuid4())
        self._store_acquisitive(loop_id, learning_content)
        self.acquisitive_memory.append(learning_content)
        
        return {
            "trace_learning": {
                "acquisitive_learning": learning_content,
                "loop_id": loop_id,
            }
        }
    except Exception as e:
        return {"trace_learning": {"error": str(e)}}

def _store_acquisitive(self, loop_id: str, content: str) -> None:
    """Store acquisitive learning to disk."""
    storage_path = self._repository._base_storage_path / "learnings" / self.session_id / "acquisitive"
    storage_path.mkdir(parents=True, exist_ok=True)
    
    file_path = storage_path / f"loop_{loop_id}.json"
    with open(file_path, 'w') as f:
        json.dump({
            "loop_id": loop_id,
            "timestamp": datetime.now().isoformat(),
            "learning_content": content,
        }, f, indent=2)
```

### Episodic Learning (Simplified)

Episodic learning analyzes patterns across a session:

```python
def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
    """Analyze patterns across a session."""
    try:
        # Load timeline for context
        timeline = self._agent._timeline
        timeline.timeline = list(timeline.read_since(checkpoint=-100))
        
        # Build prompt for pattern recognition
        messages = [
            LLMMessage(
                role="system",
                content="Analyze agent interactions and extract patterns, successful strategies, and actionable insights."
            ),
            LLMMessage(
                role="user",
                content=f"Timeline: {timeline.to_llm_messages(max_tokens=40000)}\n\nExtract key patterns and learnings."
            )
        ]
        
        # Get LLM to analyze patterns
        llm_response = self._agent.llm_client.chat_response_sync(
            messages,
            agent_id=self._agent.object_id,
            agent_type=self._agent.agent_type,
        )
        
        episodic_content = llm_response.content
        
        # Store episodic learning
        self._store_episodic(episodic_content)
        
        return {
            "trace_learning": {
                "episodic_learning": episodic_content,
                "timestamp": datetime.now().isoformat(),
            }
        }
    except Exception as e:
        return {"trace_learning": {"error": str(e)}}

def _store_episodic(self, content: str) -> None:
    """Store episodic learning to disk."""
    storage_path = self._repository._base_storage_path / "learnings" / self.session_id / "episodic"
    storage_path.mkdir(parents=True, exist_ok=True)
    
    file_path = storage_path / "learnings.md"
    with open(file_path, 'w') as f:
        f.write(content)
```

### Querying Learnings (Simplified)

Retrieve relevant past learnings:

```python
def query_learnings(self, query: str, phase: LearningPhase | None = None) -> str | None:
    """Retrieve relevant past learnings."""
    # Simple keyword-based search
    if phase == LearningPhase.ACQUISITIVE or phase is None:
        # Search acquisitive learnings
        for learning in self.acquisitive_memory:
            if query.lower() in learning.lower():
                return learning
    
    # Load episodic learning
    if phase == LearningPhase.EPISODIC or phase is None:
        storage_path = self._repository._base_storage_path / "learnings" / self.session_id / "episodic"
        file_path = storage_path / "learnings.md"
        if file_path.exists():
            with open(file_path, 'r') as f:
                episodic_content = f.read()
                if query.lower() in episodic_content.lower():
                    return episodic_content
    
    return None
```

---

## 4. Integrating Learners with Agents

### Attaching a Custom Learner

Attach your custom learner to an agent:

```python
from dana.core.agent.star_agent import STARAgent
from my_learner import SimpleLearner

class MyAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="my-agent",
            agent_id="my-agent-001",
            **kwargs
        )
        
        # Attach custom learner
        self._learner = SimpleLearner(agent=self)
```

### How Learning Works

**1. Acquisitive Learning (Automatic):**
- Triggered after each `agent.query()` call
- Agent automatically calls `learner._reflect_acquisitive()`
- Learning stored to disk and cached in memory

**2. Episodic Learning (Manual or Automatic):**
- Call manually: `agent._learner._reflect_episodic({})`
- Or trigger automatically at session end (if configured)

**3. Using Learnings in Agent Prompts:**
- Learnings can be injected into agent prompts
- Use `learner.query_learnings(query)` to retrieve relevant insights
- Add learnings to prompt context for better decision-making

### Complete Integration Example

```python
"""
Complete example: Agent with custom learner.
"""
from dana.core.agent.star_agent import STARAgent
from simple_learner import SimpleLearner

class MyAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="my-agent",
            agent_id="my-agent-001",
            llm_provider="llamastack",
            model="openai/gpt-4.1",
            **kwargs
        )
        
        # Attach custom learner
        self._learner = SimpleLearner(agent=self)

# Usage
agent = MyAgent()

# Query agent (triggers acquisitive learning automatically)
result = agent.query(
    caller_message="Create HVAC plan for meeting at 16:00",
    session_id="session-001"
)

# Trigger episodic learning manually
agent._learner._reflect_episodic({})

# Query past learnings
learning = agent._learner.query_learnings("cooling time")
print(f"Relevant learning: {learning}")
```

### Common Patterns

**Pattern 1: Learning from Feedback**
```python
# Save feedback
agent._learner.save_feedback(feedback_data)

# Use feedback in episodic learning
agent._learner._reflect_episodic({"feedback": feedback_data})
```

**Pattern 2: Retrieving Learnings**
```python
# Query acquisitive learnings
acquisitive = agent._learner.query_learnings(
    "cooling rate",
    phase=LearningPhase.ACQUISITIVE
)

# Query episodic learnings
episodic = agent._learner.query_learnings(
    "cooling patterns",
    phase=LearningPhase.EPISODIC
)
```

### Next Steps

- **Learn more:** See [learning-advanced.md](./learning-advanced.md) for:
  - Complete WilliamLearner implementation walkthrough
  - Feedback-aware learning (WilliamLearner2)
  - Specialized implementations (WilliamLearner3)
  - Advanced retrieval strategies (BM25, semantic search)
  - Storage architecture details
  - Best practices and patterns
- **Try it:** Check out `examples/agents/hvac/leaners/` for full working examples

---

**End of Basic Learning Guide**

For advanced topics, see [learning-advanced.md](./learning-advanced.md).

