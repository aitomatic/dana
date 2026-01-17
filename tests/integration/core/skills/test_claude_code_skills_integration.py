from __future__ import annotations

from dana.core.agent.star_agent import STARAgent
from dana.core.skills import ClaudeCodeSkills


def test_star_agent_has_skills_by_default(monkeypatch):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    monkeypatch.setattr(
        ClaudeCodeSkills,
        "_discover_skills",
        lambda self: [{"name": "pptx", "description": "PPTX"}],
    )

    agent = STARAgent(agent_type="test-agent")
    resource_ids = [resource.resource_id for resource in agent._resources]

    assert "claude-skills" in resource_ids


def test_star_agent_skills_disabled():
    agent = STARAgent(agent_type="test-agent", enable_skills=False)
    resource_ids = [resource.resource_id for resource in agent._resources]

    assert "claude-skills" not in resource_ids


def test_star_agent_custom_output_dir(monkeypatch, tmp_path):
    captured = {}

    class DummySkills:
        def __init__(self, output_dir: str, **_kwargs):
            captured["output_dir"] = output_dir
            self.resource_id = "claude-skills"
            self.enabled = True

    import dana.core.skills as skills_module

    monkeypatch.setattr(skills_module, "ClaudeCodeSkills", DummySkills)

    output_dir = tmp_path / "skills"
    agent = STARAgent(agent_type="test-agent", skills_output_dir=str(output_dir))
    resource_ids = [resource.resource_id for resource in agent._resources]

    assert "claude-skills" in resource_ids
    assert captured["output_dir"] == str(output_dir)


def test_specialized_agent_filtered_skills(monkeypatch):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    monkeypatch.setattr(
        ClaudeCodeSkills,
        "_discover_skills",
        lambda self: [
            {"name": "pptx", "description": "PPTX"},
            {"name": "xlsx", "description": "XLSX"},
        ],
    )

    agent = STARAgent(agent_type="doc-specialist", enable_skills=False)
    filtered = ClaudeCodeSkills(skills=["pptx"])
    agent.with_resources(filtered)

    skill_names = [skill["name"] for skill in filtered.skills]
    assert skill_names == ["pptx"]
