from types import SimpleNamespace

from dana.core.agent.star_agent import STARAgent
from dana.core.skills.claude_code_skills import ClaudeCodeSkills
import dana.core.skills as skills_module


def test_star_agent_has_skills_by_default(monkeypatch):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    monkeypatch.setattr(
        ClaudeCodeSkills,
        "_discover_skills",
        lambda self: [{"name": "pptx", "description": "Slides"}],
    )

    agent = STARAgent(agent_type="test-agent")

    assert any(resource.resource_type == "claude-skills" for resource in agent.available_resources)


def test_star_agent_skills_disabled():
    agent = STARAgent(agent_type="test-agent", enable_skills=False)

    assert all(resource.resource_type != "claude-skills" for resource in agent.available_resources)


def test_star_agent_custom_output_dir(monkeypatch, tmp_path):
    captured = SimpleNamespace(output_dir=None)

    class FakeSkills:
        def __init__(self, output_dir="./skill_output", **kwargs):
            captured.output_dir = output_dir
            self._output_dir = output_dir
            self.resource_type = "claude-skills"

        @property
        def enabled(self):
            return True

    monkeypatch.setattr(skills_module, "ClaudeCodeSkills", FakeSkills)

    output_dir = tmp_path / "custom"
    agent = STARAgent(agent_type="test-agent", skills_output_dir=str(output_dir))

    assert captured.output_dir == str(output_dir)
    assert any(resource.resource_type == "claude-skills" for resource in agent.available_resources)


def test_specialized_agent_filtered_skills(monkeypatch, tmp_path):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)

    skills_dir = tmp_path / "skills"
    (skills_dir / "pptx").mkdir(parents=True)
    (skills_dir / "xlsx").mkdir(parents=True)
    (skills_dir / "pptx" / "SKILL.md").write_text("Presentation builder")
    (skills_dir / "xlsx" / "SKILL.md").write_text("Spreadsheet helper")

    agent = STARAgent(agent_type="test-agent", enable_skills=False)
    skills = ClaudeCodeSkills(skills=["pptx"], skills_dir=str(skills_dir))
    agent.with_resources(skills)

    assert [skill["name"] for skill in skills.skills] == ["pptx"]
    assert any(resource.resource_type == "claude-skills" for resource in agent.available_resources)
