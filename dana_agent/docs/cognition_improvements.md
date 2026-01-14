# Cognition Subsystem Improvement Plan

## Summary

The cognition subsystem is **fully integrated and functional**. This document outlines improvements to enhance robustness, accuracy, and performance.

## High Priority Improvements

### 1. Token Estimation Accuracy

**Current State**: Uses simple heuristic `max(word_count, char_count // 4)`

**Problem**: Inaccurate token counting can lead to:
- Context truncation when it shouldn't happen
- Context overflow when it should be prevented
- Inefficient budget usage

**Solution**: Use `tiktoken` for accurate token counting

**Implementation**:
```python
# In dana/core/context/builder.py
try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
    _ENCODING = tiktoken.encoding_for_model("gpt-4")  # or claude equivalent
except ImportError:
    _TIKTOKEN_AVAILABLE = False

def _estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """Estimate token count with tiktoken if available, fallback to heuristic."""
    if _TIKTOKEN_AVAILABLE:
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback to heuristic
            pass
    
    # Fallback heuristic
    if not text:
        return 0
    words = text.split()
    return max(len(words), len(text) // 4)
```

**Files to Modify**:
- `dana_agent/dana/core/context/builder.py`
- `dana_agent/dana/core/memory/stmemory.py`
- `dana_agent/dana/core/agent/timeline.py`

**Dependencies**: Add `tiktoken` to `pyproject.toml` (optional dependency)

### 2. Integrative Phase LTMemory Querying

**Current State**: Integrative phase doesn't query LTMemory for connections

**Problem**: Missing opportunity to connect new experiences with past knowledge

**Solution**: Query LTMemory in integrative phase

**Implementation**:
```python
# In dana/core/agent/components/learner.py
def _reflect_integrative(self, trace_integrative: DictParams) -> DictParams:
    # Query LTMemory for existing knowledge
    existing_knowledge = ""
    ltmemory = getattr(self._agent, "_ltmemory", None)
    if ltmemory is not None:
        try:
            # Query for similar past experiences
            existing_knowledge = ltmemory.query(
                "What do I know about similar tasks or patterns?"
            )
        except Exception as e:
            logger.warning(f"Failed to query LTMemory in integrative phase: {e}")
    
    # Include existing_knowledge in LLM prompt for integration analysis
    # ... rest of integrative logic
```

**Files to Modify**:
- `dana_agent/dana/core/agent/components/learner.py` (both Learner and DefaultLearner)

### 3. Better Error Handling in ContextBuilder

**Current State**: Silently skips sources that fail to query

**Problem**: Failures are hidden, making debugging difficult

**Solution**: Add logging and optional error reporting

**Implementation**:
```python
# In dana/core/context/builder.py
import logging

logger = logging.getLogger(__name__)

def build(self, task: str = "") -> Context:
    # ...
    for name, source in self._sources.items():
        # ...
        elif isinstance(source, Queryable):
            query = task if task else f"What is relevant from {name}?"
            try:
                result = source.query(query)
                result_tokens = _estimate_tokens(result)
                if tokens_used + result_tokens <= self.token_budget:
                    parts.append(result)
                    sources_used.append(name)
                    tokens_used += result_tokens
            except Exception as e:
                logger.warning(
                    f"Failed to query source '{name}': {e}",
                    exc_info=True
                )
                # Optionally track failed sources
                # failed_sources.append(name)
```

**Files to Modify**:
- `dana_agent/dana/core/context/builder.py`

## Medium Priority Improvements

### 4. Source Prioritization

**Current State**: First-come-first-served when budget exceeded

**Problem**: Important sources might be skipped if added later

**Solution**: Implement priority-based selection

**Implementation**:
```python
class ContextBuilder:
    def __init__(self, token_budget: int = 100000):
        self.token_budget = token_budget
        self._sources: dict[str, tuple[str | Queryable, int]] = {}  # (source, priority)
    
    def add_source(self, name: str, source: str | Queryable, priority: int = 0) -> None:
        """Register a source with optional priority (higher = more important)."""
        self._sources[name] = (source, priority)
    
    def build(self, task: str = "") -> Context:
        # Sort sources by priority (descending)
        sorted_sources = sorted(
            self._sources.items(),
            key=lambda x: x[1][1],  # Sort by priority
            reverse=True
        )
        
        for name, (source, priority) in sorted_sources:
            # ... rest of logic
```

### 5. RLM Query Result Caching

**Current State**: Every query hits the LLM

**Problem**: Expensive and slow for repeated queries

**Solution**: Cache query results with TTL

**Implementation**:
```python
from functools import lru_cache
from datetime import datetime, timedelta

class ContextBuilder:
    def __init__(self, token_budget: int = 100000, cache_ttl_seconds: int = 300):
        # ...
        self._cache: dict[str, tuple[str, datetime]] = {}
        self._cache_ttl = timedelta(seconds=cache_ttl_seconds)
    
    def _get_cached_result(self, source_name: str, query: str) -> str | None:
        cache_key = f"{source_name}:{query}"
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                return result
            else:
                del self._cache[cache_key]
        return None
    
    def _cache_result(self, source_name: str, query: str, result: str):
        cache_key = f"{source_name}:{query}"
        self._cache[cache_key] = (result, datetime.now())
```

### 6. Better Memory Extraction

**Current State**: Simple string concatenation for memory storage

**Problem**: Memories might not capture important nuances

**Solution**: Use LLM to extract structured memories

**Implementation**:
```python
# In learner.py
def _extract_memories_with_llm(self, trace_retentive: DictParams) -> list[dict]:
    """Use LLM to extract structured memories from session."""
    prompt = f"""
    Extract key learnings from this session:
    
    User: {trace_retentive.get('caller_message', '')}
    Agent Response: {trace_retentive.get('response', '')}
    Tools Used: {trace_retentive.get('tool_calls', [])}
    
    Extract:
    1. Episodes (what happened)
    2. Lessons (what was learned)
    3. Patterns (recurring themes)
    
    Output as JSON array of memory objects.
    """
    
    # Use LLM to extract
    # ... LLM call ...
    # Parse and return structured memories
```

## Low Priority Improvements

### 7. Vector Search for LTMemory

**Current State**: Uses RLM for all queries (slow for large memory stores)

**Problem**: RLM is expensive and slow for simple similarity searches

**Solution**: Add optional vector search backend

**Implementation**: Use `sentence-transformers` or similar for embedding-based search

### 8. Memory Compression

**Current State**: All memories stored indefinitely

**Problem**: Memory file grows unbounded

**Solution**: Compress old memories into summaries

### 9. Cross-Session STMemory Persistence

**Current State**: STMemory is session-scoped only

**Problem**: Can't persist session state across restarts

**Solution**: Optional persistence layer for STMemory

## Implementation Priority

1. ✅ **Token Estimation** - High impact, low effort
2. ✅ **Integrative Querying** - High impact, low effort  
3. ✅ **Error Handling** - Medium impact, low effort
4. ⚠️ **Source Prioritization** - Medium impact, medium effort
5. ⚠️ **RLM Caching** - Medium impact, medium effort
6. ⚠️ **Memory Extraction** - Medium impact, high effort
7. 🔵 **Vector Search** - Low impact, high effort
8. 🔵 **Memory Compression** - Low impact, medium effort
9. 🔵 **STMemory Persistence** - Low impact, medium effort

## Testing Requirements

For each improvement:
- Unit tests for new functionality
- Integration tests with existing components
- Performance benchmarks where applicable
- Backward compatibility verification

## Documentation Updates

After implementing improvements:
1. Update `cognition_integration_status.md` with new features
2. Update component docstrings
3. Add examples showing new capabilities
4. Update specs if behavior changes significantly
