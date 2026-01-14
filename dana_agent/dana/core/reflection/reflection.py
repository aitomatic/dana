"""Reflection process for distilling STMemory into LTMemory."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from dana.common.llm import LLM, LLMMessage
from dana.core.memory import LTMemory, STMemory


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
  {{"type": "lesson|episode|fact|pattern", "content": "...", "context": "..."}},
  ...
]
Output empty array [] if nothing worth storing.
""",
}


@dataclass
class ReflectionResult:
    """Output of reflection process."""

    summary: str
    phases: dict[str, str]
    memories_created: list[dict[str, Any]]


class Reflection:
    """Distills STMemory into LTMemory through four phases."""

    def __init__(
        self,
        llm_provider: str = "anthropic",
        llm_model: str = "claude-sonnet-4-20250514",
    ):
        self.llm = LLM(provider=llm_provider, model=llm_model)

    def run(self, stmemory: STMemory, ltmemory: LTMemory | None) -> ReflectionResult:
        """
        Run all four phases and store resulting memories.

        1. Acquisitive: identify what's worth capturing
        2. Episodic: summarize what happened
        3. Integrative: connect to existing knowledge
        4. Retentive: filter and store final memories
        """
        timeline = stmemory.to_text()
        phases: dict[str, str] = {}

        candidates = self._run_phase(
            "acquisitive",
            PHASE_PROMPTS["acquisitive"].format(timeline=timeline),
            timeline,
        )
        phases["acquisitive"] = candidates

        episode = self._run_phase(
            "episodic",
            PHASE_PROMPTS["episodic"].format(timeline=timeline),
            timeline,
        )
        phases["episodic"] = episode

        existing = ""
        if ltmemory is not None:
            existing = ltmemory.query("What do I know about similar tasks?")

        integration = self._run_phase(
            "integrative",
            PHASE_PROMPTS["integrative"].format(
                episode=episode,
                candidates=candidates,
                existing=existing,
            ),
            existing,
        )
        phases["integrative"] = integration

        retentive_output = self._run_phase(
            "retentive",
            PHASE_PROMPTS["retentive"].format(
                candidates=candidates,
                episode=episode,
                integration=integration,
            ),
            integration,
        )
        phases["retentive"] = retentive_output

        memories = self._parse_memories(retentive_output)
        if ltmemory is not None:
            for memory in memories:
                ltmemory.store(memory)

        summary = self._build_summary(episode, memories)
        return ReflectionResult(summary=summary, phases=phases, memories_created=memories)

    def _run_phase(self, phase: str, prompt: str, context: str) -> str:
        """Run single phase with LLM."""
        messages = [
            LLMMessage(role="system", content=f"Reflection phase: {phase}. Use the prompt strictly."),
            LLMMessage(role="user", content=prompt),
        ]
        response = self.llm.chat_response_sync(messages, reflection_context=context)
        return response.content if hasattr(response, "content") else str(response)

    def _parse_memories(self, raw: str) -> list[dict[str, Any]]:
        """Parse retentive output JSON into memory dicts."""
        if not raw:
            return []
        try:
            memories = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if not isinstance(memories, list):
            return []
        return [m for m in memories if isinstance(m, dict)]

    def _build_summary(self, episode: str, memories: list[dict[str, Any]]) -> str:
        """Build human-readable summary of reflection run."""
        memory_count = len(memories)
        episode_text = episode.strip() if episode else "No episode summary."
        return f"Reflection stored {memory_count} memories. Episode: {episode_text}"
