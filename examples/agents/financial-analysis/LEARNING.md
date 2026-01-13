# Learning System Guide

This guide explains how the learning system works in the STAR agent framework and how to customize the learning phases.

## Overview

The learning system implements a four-phase STAR reflection pattern:
- **ACQUISITIVE**: Immediate learning from each interaction (trial-level plasticity)
- **EPISODIC**: Session-level learning from collections of experiences
- **INTEGRATIVE**: Multi-episode integration (offline replay)
- **RETENTIVE**: Long-term maintenance and habit formation

## Architecture

### Learning Flow

```
STAR Loop (See-Think-Act-Reflect)
    ↓
_act() produces trace_outputs
    ↓
_reflect() dispatches based on LearningPhase
    ↓
    ├─ ACQUISITIVE → _reflect_acquisitive() → Stores per-loop JSON
    ├─ EPISODIC → _reflect_episodic() → Stores session markdown
    ├─ INTEGRATIVE → _reflect_integrative() → Multi-session integration
    └─ RETENTIVE → _reflect_retentive() → Long-term retention
```

### How Learning Affects Agent Behavior

Learning is integrated into the agent's decision-making through two mechanisms:

#### 1. System Prompt Integration (Episodic Learning)

**Location**: `prompt_engineer.py` lines 515-521, 551

Episodic learnings are automatically included in the system prompt:

```python
def _get_learnings_section(self) -> str:
    """Get the learnings section."""
    episodic_learnings = self._agent._learner.query_learnings("ANYTHING", LearningPhase.EPISODIC)
    episodic_content = episodic_learnings if episodic_learnings else None
    return f"""<LEARNINGS>
{episodic_content}
</LEARNINGS>"""
```

The learnings section is added to the system prompt structure (line 551), providing the agent with accumulated knowledge from previous sessions.

#### 2. Context-Aware Retrieval (Acquisitive Learning)

**Location**: `prompt_engineer.py` lines 812-816

Acquisitive learnings are retrieved dynamically based on the current user message:

```python
latest_msg = messages[-1].content if messages else None
if latest_msg:
    related_acquisitive_learnings = self._agent._learner.query_learnings(
        latest_msg, LearningPhase.ACQUISITIVE
    )
    if related_acquisitive_learnings:
        messages.append(LLMMessage(
            role="system", 
            content=f"Learning from the past : {related_acquisitive_learnings}"
        ))
```

This uses BM25 search to find relevant past learnings and injects them as a system message, providing immediate context from similar past interactions.

## Implementation Details

### `_reflect_acquisitive` - Immediate Learning

**Location**: `william_learner.py` lines 109-182

#### Current Implementation

1. **Generates Learning Note**: Calls `_reflect_action()` which uses an LLM to analyze the interaction and generate a learning note in the format: `[Condition] [Advice of what should do]`

2. **Stores Complete Context**: Saves a JSON file per loop containing:
   - Loop metadata (loop_id, timestamp, session_id)
   - Timeline context (last 5 entries before user message)
   - Full interaction data (caller_message, response, reasoning, tool_calls, tool_results)
   - Generated learning_note

3. **Storage**: 
   - Path: `{codec}/{agent_class}__{filename}/learnings/{session_id}/acquisitive/`
   - Filename: `loop_{timestamp}_{loop_id_short}.json`
   - In-memory: Appends to `self.acquisitive_memory` list

4. **Retrieval**: Uses BM25 search engine to find top 3 most relevant learning notes based on query similarity

#### Customization Guide

**Override `_reflect_acquisitive`** to customize:

1. **Learning Note Format**:
   ```python
   def _reflect_acquisitive(self, trace_acquisitive: DictParams) -> DictParams:
       # Customize the learning extraction
       result = self._reflect_action(trace_acquisitive)
       learning_note = result["trace_learning"].get("learning_note", "")
       
       # Add your custom processing here
       # e.g., structured extraction, sentiment analysis, etc.
       
       # Store with your custom format
       loop_data = {
           # ... your custom structure
           "learning_note": learning_note,
           "custom_field": your_custom_value,
       }
       self._store_acquisitive_loop_json(loop_data, loop_id, timestamp)
       return {"trace_learning": trace_learning}
   ```

2. **Storage Structure**: Modify `loop_data` dictionary to include additional fields or change the structure

3. **Context Selection**: Change `_get_timeline_context_for_loop()` to include different timeline entries or context sources

4. **Learning Note Generation**: Override `_reflect_action()` to change the LLM prompt or extraction logic

5. **Retrieval Strategy**: Modify `query_learnings()` to use different search algorithms (e.g., semantic search, embeddings) instead of BM25

### `_reflect_episodic` - Session-Level Learning

**Location**: `william_learner.py` lines 184-342

#### Current Implementation

1. **Loads Previous Learning**: Retrieves accumulated episodic learning from previous sessions

2. **Analyzes Full Timeline**: Converts the entire session timeline (up to 40,000 tokens) into LLM messages

3. **Consolidates Learning**: Uses LLM to:
   - Extract patterns and recurring themes
   - Identify what worked well and what didn't
   - Generate actionable insights
   - Consolidate with previous episodic learning

4. **Storage**:
   - Path: `{codec}/{agent_class}__{filename}/learnings/{session_id}/episodic/`
   - Filename: `learnings.md`
   - Format: Markdown text with `[Condition] [Advice]` format

5. **Retrieval**: Returns the entire episodic learning content when queried

#### Customization Guide

**Override `_reflect_episodic`** to customize:

1. **Analysis Scope**:
   ```python
   def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
       # Customize what gets analyzed
       timeline = self._agent._timeline
       
       # Change checkpoint to analyze different time ranges
       timeline.timeline = list(timeline.read_since(checkpoint=-50))  # Last 50 entries
       
       # Or filter specific entry types
       filtered_timeline = [e for e in timeline.timeline 
                           if e.entry_type == TimelineEntryType.USER_MESSAGE]
       
       # Your custom analysis...
   ```

2. **LLM Prompt Customization**:
   ```python
   # Modify the system prompt (lines 202-212)
   system_prompt = """Your custom learning extraction prompt...
   Focus on specific aspects you care about:
   - Domain-specific patterns
   - User preference extraction
   - Error pattern analysis
   - Performance metrics
   """
   
   # Modify the learning prompt (lines 255-276)
   learning_prompt = """Your custom learning request...
   Extract learnings in your preferred format:
   - Structured JSON
   - Bullet points
   - Decision trees
   - Custom format
   """
   ```

3. **Learning Format**: Change the output format from markdown to JSON, structured data, or your custom format

4. **Consolidation Strategy**: Implement custom logic for merging previous learning with new insights:
   ```python
   # Instead of simple LLM consolidation, you could:
   # - Weight learnings by recency
   # - Conflict resolution
   # - Categorization and organization
   # - Statistical analysis
   ```

5. **Storage Location**: Modify `_get_episodic_storage_path()` to use different storage locations or formats

6. **Multi-Session Analysis**: Extend to analyze multiple sessions together:
   ```python
   # Load learnings from multiple sessions
   all_episodic_learnings = []
   for session_id in session_ids:
       learning = self._load_episodic_for_session(session_id)
       all_episodic_learnings.append(learning)
   
   # Analyze together
   consolidated = self._analyze_multiple_sessions(all_episodic_learnings)
   ```

## Integration Points

### STAR Agent Reflection

**Location**: `star_agent.py` lines 539-597

The `_reflect()` method in `STARAgent` orchestrates learning:

```python
def _reflect(self, trace_outputs: DictParams) -> DictParams:
    phase: LearningPhase = trace_outputs.get("phase") or LearningPhase.ACQUISITIVE
    
    match phase:
        case LearningPhase.ACQUISITIVE:
            trace_learning |= self._learner._reflect_acquisitive(trace_outputs)
        case LearningPhase.EPISODIC:
            trace_learning |= self._learner._reflect_episodic(trace_outputs)
        # ... other phases
```

### Automatic Triggering

- **Acquisitive**: Triggered automatically after each STAR loop (see `base_star_agent.py` lines 254-267)
- **Episodic**: Must be triggered manually by calling `query()` with `phase=LearningPhase.EPISODIC`

## Customization Examples

### Example 1: Custom Learning Format

```python
class CustomLearner(WilliamLearner):
    def _reflect_action(self, trace_action: DictParams) -> DictParams:
        # Extract structured data instead of free text
        result = {
            "success": self._evaluate_success(trace_action),
            "patterns": self._extract_patterns(trace_action),
            "recommendations": self._generate_recommendations(trace_action),
        }
        return {"trace_learning": result}
```

### Example 2: Semantic Search for Retrieval

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticLearner(WilliamLearner):
    def __init__(self, agent):
        super().__init__(agent)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeddings = []
    
    def query_learnings(self, query: str, phase: LearningPhase) -> str | None:
        if phase == LearningPhase.ACQUISITIVE:
            if not self.embeddings:
                self._build_embeddings()
            
            query_embedding = self.encoder.encode(query)
            similarities = np.dot(self.embeddings, query_embedding)
            top_indices = np.argsort(similarities)[::-1][:3]
            
            return "\n".join([self.acquisitive_memory[i] for i in top_indices])
```

### Example 3: Domain-Specific Learning

```python
class FinancialLearner(WilliamLearner):
    def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
        # Extract financial-specific patterns
        financial_patterns = self._extract_financial_patterns()
        error_patterns = self._analyze_errors()
        user_preferences = self._extract_user_preferences()
        
        # Custom consolidation
        learning = {
            "financial_patterns": financial_patterns,
            "error_patterns": error_patterns,
            "user_preferences": user_preferences,
        }
        
        # Store in structured format
        self._store_episodic_learning_json(learning)
        return {"trace_learning": learning}
```

## Storage Structure

### Acquisitive Learning

```
.dana/{codec}/{AgentClass}__{filename}/learnings/{session_id}/acquisitive/
├── loop_20240101_120000_123456_abc12345.json
├── loop_20240101_120100_234567_def67890.json
└── ...
```

Each JSON file contains:
- `loop_id`: Unique identifier
- `timestamp`: ISO format timestamp
- `session_id`: Session identifier
- `timeline_context`: Recent timeline entries
- `caller_message`: User's message
- `response`: Agent's response
- `reasoning`: Agent's reasoning
- `tool_calls`: Tools used
- `tool_results`: Tool outputs
- `learning_note`: Extracted learning

### Episodic Learning

```
.dana/{codec}/{AgentClass}__{filename}/learnings/{session_id}/episodic/
└── learnings.md
```

Markdown file contains accumulated learning in format:
```
[Condition] [Advice of what should do]
[Condition] [Advice of what should do]
...
```

## Best Practices

1. **Keep Learning Notes Concise**: Focus on actionable insights
2. **Use Structured Formats**: Consider JSON for easier parsing later
3. **Handle Errors Gracefully**: Learning failures shouldn't break the agent
4. **Consider Privacy**: Be mindful of what data is stored in learning files
5. **Test Custom Learners**: Ensure your custom learner implements the full `LearnerProtocol`
6. **Monitor Storage**: Learning files can accumulate quickly
7. **Version Learning Format**: If you change formats, handle migration of old data

## Troubleshooting

### Learning Not Appearing in System Prompt

- Check that episodic learning file exists at the expected path
- Verify `query_learnings()` returns non-None for EPISODIC phase
- Check that `_get_learnings_section()` is called in system prompt generation

### Acquisitive Learning Not Retrieved

- Verify `acquisitive_memory` is populated
- Check BM25 search is working correctly
- Ensure learning notes are stored in the expected format
- Verify query similarity is sufficient

### Storage Issues

- Check `FileStorageConfig().workspace_folder` is writable
- Verify session_id is set correctly
- Ensure directory creation permissions

## Next Steps

To customize learning:

1. Create a subclass of `WilliamLearner` (or `LearnerProtocol`)
2. Override `_reflect_acquisitive` and/or `_reflect_episodic`
3. Optionally override `query_learnings` for custom retrieval
4. Pass your custom learner to `STARAgent(learner=YourCustomLearner())`

For more examples, see `examples/agents/financial-analysis/leaners/william_learner.py`.

