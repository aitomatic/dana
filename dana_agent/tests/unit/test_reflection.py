"""Unit tests for Reflection."""

from dataclasses import asdict
from unittest.mock import MagicMock

from dana.core.memory import STMemory
from dana.core.reflection import Reflection, ReflectionResult


class FakeLTMemory:
    def __init__(self, query_response: str = "existing knowledge"):
        self.query_response = query_response
        self.query = MagicMock(side_effect=self._query)
        self.store = MagicMock(side_effect=self._store)
        self.stored = []

    def _query(self, question: str) -> str:
        return self.query_response

    def _store(self, memory: dict) -> None:
        self.stored.append(memory)


class StubReflection(Reflection):
    def __init__(self, outputs: dict[str, str]):
        self.outputs = outputs
        self.calls: list[tuple[str, str, str]] = []

    def _run_phase(self, phase: str, prompt: str, context: str) -> str:
        self.calls.append((phase, prompt, context))
        return self.outputs.get(phase, "")


def _build_stmemory() -> STMemory:
    stmem = STMemory()
    stmem.append("user", "Deploy failed again")
    stmem.append("agent", "Checking logs")
    stmem.append("observation", "Missing DATABASE_URL")
    return stmem


def test_run_all_phases():
    outputs = {
        "acquisitive": "lesson: env vars cause deploy issues",
        "episodic": "Fixed deploy by adding DATABASE_URL.",
        "integrative": "Pattern: recurring env var issues.",
        "retentive": '[{"type": "lesson", "content": "Missing env vars cause deploy failures", "context": "deploy"}]',
    }
    reflection = StubReflection(outputs)
    ltmemory = FakeLTMemory()

    result = reflection.run(stmemory=_build_stmemory(), ltmemory=ltmemory)

    phases = [call[0] for call in reflection.calls]
    assert phases == ["acquisitive", "episodic", "integrative", "retentive"]
    assert result.phases["acquisitive"] == outputs["acquisitive"]
    assert len(result.memories_created) == 1


def test_acquisitive_phase():
    reflection = StubReflection({
        "acquisitive": "lesson: env var issue",
        "episodic": "Episode summary",
        "integrative": "Integration notes",
        "retentive": "[]",
    })

    reflection.run(stmemory=_build_stmemory(), ltmemory=FakeLTMemory())

    phase, prompt, _ = reflection.calls[0]
    assert phase == "acquisitive"
    assert "Deploy failed again" in prompt


def test_episodic_phase():
    reflection = StubReflection({
        "acquisitive": "lesson: env var issue",
        "episodic": "Episode summary",
        "integrative": "Integration notes",
        "retentive": "[]",
    })

    result = reflection.run(stmemory=_build_stmemory(), ltmemory=FakeLTMemory())

    assert result.phases["episodic"] == "Episode summary"


def test_integrative_phase_queries_ltmemory():
    reflection = StubReflection({
        "acquisitive": "lesson: env var issue",
        "episodic": "Episode summary",
        "integrative": "Integration notes",
        "retentive": "[]",
    })
    ltmemory = FakeLTMemory()

    reflection.run(stmemory=_build_stmemory(), ltmemory=ltmemory)

    ltmemory.query.assert_called_once()


def test_retentive_phase_outputs_valid_json():
    reflection = StubReflection({
        "acquisitive": "lesson: env var issue",
        "episodic": "Episode summary",
        "integrative": "Integration notes",
        "retentive": '[{"type": "lesson", "content": "Do env var checks", "context": "deploy"}]',
    })

    result = reflection.run(stmemory=_build_stmemory(), ltmemory=FakeLTMemory())

    assert isinstance(result.memories_created, list)
    assert result.memories_created[0]["type"] == "lesson"


def test_stores_to_ltmemory():
    reflection = StubReflection({
        "acquisitive": "lesson: env var issue",
        "episodic": "Episode summary",
        "integrative": "Integration notes",
        "retentive": (
            '[{"type": "lesson", "content": "Check env vars", "context": "deploy"},'
            ' {"type": "pattern", "content": "Recurring config issues", "context": "ops"}]'
        ),
    })
    ltmemory = FakeLTMemory()

    reflection.run(stmemory=_build_stmemory(), ltmemory=ltmemory)

    assert len(ltmemory.stored) == 2


def test_empty_session():
    reflection = StubReflection({
        "acquisitive": "",
        "episodic": "",
        "integrative": "",
        "retentive": "[]",
    })
    ltmemory = FakeLTMemory()

    result = reflection.run(stmemory=STMemory(), ltmemory=ltmemory)

    assert result.memories_created == []


def test_result_structure():
    reflection = StubReflection({
        "acquisitive": "lesson: env var issue",
        "episodic": "Episode summary",
        "integrative": "Integration notes",
        "retentive": "[]",
    })

    result = reflection.run(stmemory=_build_stmemory(), ltmemory=FakeLTMemory())

    assert isinstance(result, ReflectionResult)
    result_dict = asdict(result)
    assert "summary" in result_dict
    assert "phases" in result_dict
    assert "memories_created" in result_dict
