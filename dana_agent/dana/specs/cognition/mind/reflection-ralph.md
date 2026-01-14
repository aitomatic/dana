# Reflection - Implementation Spec

**Status: 🔄 IN PROGRESS** (tests failing - bug in reflection.py)

## Goal

Implement the Reflection process that distills stmemory into ltmemory through four phases: Acquisitive, Episodic, Integrative, Retentive.

## Demo

Run: `examples/cognition/reflection/session_learning.py`

### Without Reflection (The Problem)

```python
# WITHOUT REFLECTION: Agent "learns" but never remembers

# Session 1: Fix deploy issue
agent.run("The deploy is failing")
# Agent discovers: "Missing DATABASE_URL in environment"
# Agent fixes it. Session ends.

# What got stored in memory?
print(timeline.entries)  # All 50 conversation turns
# ❌ Everything stored: user messages, tool calls, observations
# ❌ No filtering - important lessons mixed with noise
# ❌ No connection to past experiences
# ❌ Tomorrow: agent sees same issue, starts from scratch

# Session 2: Same issue!
agent.run("Deploy is broken again")
# ❌ No recall of "missing env vars cause deploy failures"
# ❌ Agent rediscovers the same lesson
# ❌ No pattern recognition: "This is the 3rd env var issue"
```

### With Reflection (The Solution)

```python
# WITH REFLECTION: Agent distills sessions into durable knowledge

from dana.core.memory import STMemory, LTMemory
from dana.core.reflection import Reflection

# Session happens...
stmem = STMemory()
stmem.append("user", "The deploy is failing")
stmem.append("agent", "Checking CI logs...")
stmem.append("observation", "Missing env var: DATABASE_URL")
stmem.append("agent", "Added to .env.example, deploy succeeded")
stmem.append("user", "Thanks! Always forget that one")

# Session ends → Reflection runs
ltmem = LTMemory(path="./memories/")
reflection = Reflection()
result = reflection.run(stmemory=stmem, ltmemory=ltmem)

# ✅ 4 phases distill the session:
#    Acquisitive: "User feedback: 'always forget' = common issue"
#    Episodic: "Fixed deploy by adding missing DATABASE_URL"
#    Integrative: "3rd env var issue this month - pattern emerging"
#    Retentive: Store lesson + pattern, skip noise

print(result.memories_created)
# → [
#     {"type": "lesson", "content": "Deploy failures often caused by missing env vars"},
#     {"type": "pattern", "content": "Env var issues are recurring - suggest .env validation"}
#   ]

# Session 2: Reflection pays off
past = ltmem.query("deploy failures")
# → "Deploy failures often caused by missing env vars"
# ✅ Agent immediately checks env vars
# ✅ Pattern recognition: "This matches a known recurring issue"
```

### What You'll See

```
=== Reflection Phases ===

Phase 1 - Acquisitive:
  Candidates: [lesson: env var causes deploy fail, fact: DATABASE_URL needed]

Phase 2 - Episodic:
  Summary: "User had deploy failure. Agent found missing DATABASE_URL,
            added to .env.example. User indicated this is a recurring issue."

Phase 3 - Integrative:
  Existing: "Previous session also had env var issue (API_KEY)"
  Connection: "Pattern: 3rd env var issue → systemic problem"

Phase 4 - Retentive:
  Storing: 2 memories (lesson + pattern)
  Skipping: Episode (similar to existing), fact (too specific)

=== Result ===
Memories created: 2
LTMemory now has: 15 total memories
```

## MVP Requirements

### 1. Reflection (`dana_agent/dana/core/reflection/reflection.py`)

```python
@dataclass
class ReflectionResult:
    """Output of reflection process."""
    summary: str
    phases: dict[str, str]  # phase name → output
    memories_created: list[dict]

class Reflection:
    """Distills stmemory into ltmemory through four phases."""

    def __init__(
        self,
        llm_provider: str = "anthropic",
        llm_model: str = "claude-sonnet-4-20250514"
    ):
        self.llm = LLM(provider=llm_provider, model=llm_model)

    def run(
        self,
        stmemory: STMemory,
        ltmemory: LTMemory
    ) -> ReflectionResult:
        """
        Run all four phases and store resulting memories.

        1. Acquisitive: identify what's worth capturing
        2. Episodic: summarize what happened
        3. Integrative: connect to existing knowledge
        4. Retentive: filter and store final memories
        """

    def _run_phase(
        self,
        phase: str,
        prompt: str,
        context: str
    ) -> str:
        """Run single phase with LLM."""
```

Requirements:
- [x] Run four phases in sequence
- [x] Pass stmemory timeline to phases
- [x] Query ltmemory in Integrative phase
- [x] Store final memories to ltmemory in Retentive phase
- [x] Return ReflectionResult with summary and phase outputs
- [x] Use dana.common.llm.LLM for LLM calls

### 2. Phase Prompts

```python
PHASE_PROMPTS = {
    "acquisitive": """
Analyze this session timeline. Identify what's worth capturing:
- New information learned
- Corrections or feedback received
- User preferences expressed
- Unexpected outcomes or insights

Timeline:
{timeline}

Output a list of candidate memories (may be empty if nothing noteworthy).
Format: One candidate per line, prefixed with type (lesson/fact/preference).
""",

    "episodic": """
Summarize what happened in this session as a brief narrative.
Focus on: task attempted, key steps, outcome, obstacles.

Timeline:
{timeline}

Output: A 2-3 sentence episode summary.
""",

    "integrative": """
Given this session and existing knowledge, identify connections:
- Similar past experiences
- Patterns emerging
- Knowledge to update or reinforce

Session summary:
{episode}

Candidate memories:
{candidates}

Existing knowledge:
{existing}

Output: Integration notes (what connects, what's new, what to update).
""",

    "retentive": """
Decide what to actually store in long-term memory.
Filter for: importance, non-redundancy, actionability.

Candidates:
{candidates}

Episode:
{episode}

Integration notes:
{integration}

Output: Final memories to store.
Format as JSON array:
[
  {"type": "lesson|episode|fact|pattern", "content": "...", "context": "..."},
  ...
]
Output empty array [] if nothing worth storing.
"""
}
```

Requirements:
- [x] Acquisitive prompt extracts candidates
- [x] Episodic prompt creates narrative
- [x] Integrative prompt queries ltmemory for connections
- [x] Retentive prompt outputs JSON array of memories
- [x] Parse Retentive output as JSON

### 3. ReflectionResult

```python
@dataclass
class ReflectionResult:
    summary: str                    # Human-readable summary
    phases: dict[str, str]          # Raw output from each phase
    memories_created: list[dict]    # Memories stored to ltmemory
```

Requirements:
- [x] Capture output from each phase
- [x] Generate summary from phases
- [x] Track memories created

## Example Files (`examples/cognition/reflection/`)

- `session_learning.py` - Full reflection demo with all 4 phases
- `learner_integration.py` - Shows Learner component using Reflection

## Files Implemented

- `dana_agent/dana/core/reflection/reflection.py` ⚠️ (has bug - see below)
- `dana_agent/dana/core/reflection/__init__.py` ✅
- `dana_agent/dana/core/agent/components/learner.py` ✅ (LTMemory integration)
- `examples/cognition/reflection/` ✅

## Bug to Fix

**Location**: `dana_agent/dana/core/reflection/reflection.py` lines 53-73

**Problem**: The `retentive` prompt template contains JSON example with curly braces:
```python
"retentive": """
...
Format as JSON array:
[
  {"type": "lesson|episode|fact|pattern", "content": "...", "context": "..."},
  ...
]
...
"""
```

Python's `.format()` interprets `{type}`, `{content}`, `{context}` as placeholders, causing `KeyError: '"type"'`.

**Fix**: Escape curly braces by doubling them:
```python
"retentive": """
...
Format as JSON array:
[
  {{"type": "lesson|episode|fact|pattern", "content": "...", "context": "..."}},
  ...
]
...
"""
```

## Tests Required

Create `dana_agent/tests/unit/test_reflection.py`:
- [ ] test_run_all_phases - executes all four phases
- [ ] test_acquisitive_phase - identifies candidates from timeline
- [ ] test_episodic_phase - creates narrative summary
- [ ] test_integrative_phase - queries ltmemory
- [ ] test_retentive_phase - outputs valid JSON
- [ ] test_stores_to_ltmemory - memories actually stored
- [ ] test_empty_session - handles no noteworthy content
- [ ] test_result_structure - ReflectionResult has all fields

Run tests with: `cd dana_agent && uv run pytest tests/unit/test_reflection.py -v`

## Success Criteria

1. All tests pass
2. Four phases run in sequence
3. Integrative queries ltmemory for context
4. Retentive stores final memories to ltmemory
5. Example runs and shows full reflection pipeline

## Before Marking Complete

- [ ] Fix bug in reflection.py (escape JSON curly braces)
- [ ] All tests pass
- [ ] Review code for KISS/YAGNI compliance
- [ ] Simplify any overly complex implementations
- [ ] Remove unnecessary abstractions
- [ ] Ensure code is readable and maintainable

## When Complete

**You MUST run tests before marking complete:**
```bash
cd dana_agent && uv run pytest tests/unit/test_reflection.py tests/unit/test_staragent_ltmemory.py -v
```

Only if ALL tests pass, output the completion tag:
`<promise>` + `TASK COMPLETE` + `</promise>`

## STARAgent Integration

### Current State: Learner Component

The `Learner` component at `dana.core.agent.components.learner` implements reflection with full LTMemory integration:

| Feature | Learner Status | Spec Requirement |
|---------|---------------|------------------|
| Acquisitive phase | ✅ `_reflect_acquisitive()` | ✅ |
| Episodic phase | ✅ `_reflect_episodic()` | ✅ |
| Integrative phase | ✅ `_reflect_integrative()` | ✅ |
| Retentive phase | ✅ `_reflect_retentive()` | ✅ |
| LLM-based analysis | ✅ `DefaultLearner` uses LLM | ✅ |
| Persist to LTMemory | ✅ `_reflect_retentive()` stores memories | ✅ |
| Query LTMemory | ✅ `query_learnings()` queries LTMemory | ✅ |
| Standalone Reflection class | ✅ `dana.core.reflection.Reflection` | Optional |

### Integration Tasks

| Task | Status | Description |
|------|--------|-------------|
| Wire Learner to LTMemory | ✅ Done | Accesses via `self._agent._ltmemory` |
| Persist in retentive phase | ✅ Done | `_reflect_retentive()` calls `ltmemory.store()` |
| Query in integrative phase | ✅ Done | `query_learnings()` calls `ltmemory.query()` |
| Add session end trigger | ⏸️ Deferred | Reflection triggered per-turn, not session end |
| Create standalone Reflection | ✅ Done | `dana.core.reflection.Reflection` class exists |

### Integration Code

```python
# Option A: Enhance existing Learner (Recommended)
# In learner.py

class Learner:
    def __init__(self, agent: "STARAgent", ...):
        self._agent = agent
        # LTMemory accessed via self._agent._ltmemory

    def _reflect_integrative(self, trace_integrative: DictParams) -> DictParams:
        # Query ltmemory for existing knowledge
        existing_knowledge = ""
        if self._agent._ltmemory:
            existing_knowledge = self._agent._ltmemory.query(
                "What do I know about similar tasks?"
            )

        # Include in LLM prompt for integration analysis
        # ...

    def _reflect_retentive(self, trace_retentive: DictParams) -> DictParams:
        # Extract memories to store
        memories = self._extract_memories_from_analysis(trace_retentive)

        # Persist to LTMemory
        if self._agent._ltmemory:
            for memory in memories:
                self._agent._ltmemory.store(memory)

        return {"trace_learning": {"memories_stored": len(memories)}}
```

```python
# Option B: Create standalone Reflection class
# In dana.core.reflection.reflection

class Reflection:
    def run(self, stmemory: STMemory, ltmemory: LTMemory) -> ReflectionResult:
        # Run all 4 phases
        candidates = self._acquisitive(stmemory)
        episode = self._episodic(stmemory)
        integration = self._integrative(candidates, episode, ltmemory)
        memories = self._retentive(candidates, episode, integration)

        # Store to ltmemory
        for memory in memories:
            ltmemory.store(memory)

        return ReflectionResult(...)
```

### Files Modified/Created
- `dana_agent/dana/core/agent/components/learner.py` ✅ (LTMemory integration added)
- `dana_agent/dana/core/reflection/__init__.py` ✅
- `dana_agent/dana/core/reflection/reflection.py` ✅
- `dana_agent/tests/unit/test_reflection.py` ✅
- `dana_agent/tests/unit/test_staragent_ltmemory.py` ✅
- `examples/cognition/reflection/session_learning.py` ✅
- `examples/cognition/reflection/learner_integration.py` ✅

## References

- PRD: [reflection-prd.md](./reflection-prd.md)
- Parent: [mind overview](./overview.md)
- Depends on: [memory](./memory-ralph.md) (stmemory input, ltmemory output)
- Depends on: dana.common.llm.LLM for phase execution
- Related: `dana.core.agent.components.learner` (existing implementation)
