# Reflection - Implementation Spec

## Goal

Implement the Reflection process that distills stmemory into ltmemory through four phases: Acquisitive, Episodic, Integrative, Retentive.

## Demo

When complete, run `examples/agents/reflection/example.py`:

```python
from dana.core.memory import STMemory, LTMemory
from dana.core.reflection import Reflection

# Simulate a session
stmem = STMemory()
stmem.append("user", "The deploy is failing")
stmem.append("agent", "Checking CI logs...")
stmem.append("observation", "Missing env var: DATABASE_URL")
stmem.append("agent", "Added to .env.example, deploy succeeded")
stmem.append("user", "Thanks! Always forget that one")

# Existing long-term memory
ltmem = LTMemory(path="./memories/")

# Run reflection
r = Reflection()
result = r.run(stmemory=stmem, ltmemory=ltmem)

# See what reflection produced
print("=== Reflection Summary ===")
print(result.summary)

print("\n=== Phase Outputs ===")
print(f"Acquisitive: {result.phases['acquisitive']}")
print(f"Episodic: {result.phases['episodic']}")
print(f"Integrative: {result.phases['integrative']}")
print(f"Retentive: {result.phases['retentive']}")

print(f"\n=== Memories Created: {len(result.memories_created)} ===")
for mem in result.memories_created:
    print(f"  [{mem['type']}] {mem['content'][:60]}...")
```

**What you'll see**: Each phase analyzing the session, culminating in memories stored to ltmemory.

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
- [ ] Run four phases in sequence
- [ ] Pass stmemory timeline to phases
- [ ] Query ltmemory in Integrative phase
- [ ] Store final memories to ltmemory in Retentive phase
- [ ] Return ReflectionResult with summary and phase outputs
- [ ] Use dana.common.llm.LLM for LLM calls

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
- [ ] Acquisitive prompt extracts candidates
- [ ] Episodic prompt creates narrative
- [ ] Integrative prompt queries ltmemory for connections
- [ ] Retentive prompt outputs JSON array of memories
- [ ] Parse Retentive output as JSON

### 3. ReflectionResult

```python
@dataclass
class ReflectionResult:
    summary: str                    # Human-readable summary
    phases: dict[str, str]          # Raw output from each phase
    memories_created: list[dict]    # Memories stored to ltmemory
```

Requirements:
- [ ] Capture output from each phase
- [ ] Generate summary from phases
- [ ] Track memories created

## Current Progress

Check these files to see what exists:
- `dana_agent/dana/core/reflection/reflection.py`
- `dana_agent/dana/core/reflection/__init__.py`
- `examples/agents/reflection/`

Update checkboxes above as you complete each requirement.

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

- [ ] Review code for KISS/YAGNI compliance
- [ ] Simplify any overly complex implementations
- [ ] Remove unnecessary abstractions
- [ ] Ensure code is readable and maintainable

## When Complete

Output in this file:
<promise>REFLECTION COMPLETE</promise>

## References

- PRD: [reflection-prd.md](./reflection-prd.md)
- Parent: [mind overview](./overview.md)
- Depends on: [memory](./memory-ralph.md) (stmemory input, ltmemory output)
- Depends on: dana.common.llm.LLM for phase execution
