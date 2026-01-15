from pathlib import Path
import subprocess
from types import SimpleNamespace

from dana.core.skills import ClaudeCodeSkills
import dana.core.skills.claude_code_skills as claude_skills


def _make_instance(tmp_path: Path) -> ClaudeCodeSkills:
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._available = True
    instance._skills = [{"name": "pptx", "description": "Slides"}]
    instance._output_dir = str(tmp_path / "out")
    instance._timeout = 10
    return instance


def test_init_default_values(tmp_path, monkeypatch):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)

    skills = ClaudeCodeSkills(skills_dir=str(tmp_path))

    assert skills._skills_dir == tmp_path
    assert skills._output_dir == "./skill_output"
    assert skills._timeout == 300
    assert skills.resource_id == "claude-skills"


def test_init_custom_values(tmp_path, monkeypatch):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)

    skills = ClaudeCodeSkills(
        skills_dir=str(tmp_path),
        output_dir="./custom-output",
        timeout=123,
        resource_id="custom-id",
    )

    assert skills._skills_dir == tmp_path
    assert skills._output_dir == "./custom-output"
    assert skills._timeout == 123
    assert skills.resource_id == "custom-id"


def test_init_with_skill_filter(tmp_path, monkeypatch):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)

    skills_dir = tmp_path / "skills"
    (skills_dir / "pptx").mkdir(parents=True)
    (skills_dir / "xlsx").mkdir(parents=True)
    (skills_dir / "pptx" / "SKILL.md").write_text("Presentation builder")
    (skills_dir / "xlsx" / "SKILL.md").write_text("Spreadsheet helper")

    skills = ClaudeCodeSkills(skills=["pptx"], skills_dir=str(skills_dir))

    assert [skill["name"] for skill in skills.skills] == ["pptx"]


def test_check_claude_available_when_installed(monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(claude_skills.subprocess, "run", fake_run)

    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    assert instance._check_claude_available() is True


def test_check_claude_available_when_not_installed(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("claude not found")

    monkeypatch.setattr(claude_skills.subprocess, "run", fake_run)

    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    assert instance._check_claude_available() is False


def test_discover_skills_finds_skills(tmp_path):
    skills_dir = tmp_path / "skills"
    (skills_dir / "pptx").mkdir(parents=True)
    (skills_dir / "pdf").mkdir(parents=True)
    (skills_dir / "pptx" / "SKILL.md").write_text("Presentation builder")
    (skills_dir / "pdf" / "SKILL.md").write_text("# PDF tools")

    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._skills_dir = skills_dir

    skills = instance._discover_skills()
    skill_names = {skill["name"] for skill in skills}

    assert skill_names == {"pptx", "pdf"}


def test_discover_skills_empty_dir(tmp_path):
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._skills_dir = tmp_path

    assert instance._discover_skills() == []


def test_discover_skills_missing_dir(tmp_path):
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._skills_dir = tmp_path / "missing"

    assert instance._discover_skills() == []


def test_parse_skill_description_first_line(tmp_path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("\n\nFirst line description\n# Heading")

    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)

    assert instance._parse_skill_description(skill_md) == "First line description"


def test_parse_skill_description_heading(tmp_path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("# Heading Title\nMore text")

    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)

    assert instance._parse_skill_description(skill_md) == "Heading Title"


def test_parse_skill_description_truncates(tmp_path):
    long_text = "a" * 250
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(long_text)

    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)

    description = instance._parse_skill_description(skill_md)

    assert len(description) == 200


def test_filter_skills():
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._all_skills = [
        {"name": "pptx", "description": "Slides"},
        {"name": "xlsx", "description": "Sheets"},
    ]

    filtered = instance._filter_skills(["xlsx"])

    assert filtered == [{"name": "xlsx", "description": "Sheets"}]


def test_format_skills_for_docstring():
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._skills = [
        {"name": "pptx", "description": "Slides"},
        {"name": "pdf", "description": "Docs"},
    ]

    formatted = instance._format_skills_for_docstring()

    assert formatted == "- pptx: Slides\n- pdf: Docs"


def test_enabled_property_true():
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._available = True
    instance._skills = [{"name": "pptx", "description": "Slides"}]

    assert instance.enabled is True


def test_enabled_property_false_no_claude():
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._available = False
    instance._skills = [{"name": "pptx", "description": "Slides"}]

    assert instance.enabled is False


def test_enabled_property_false_no_skills():
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._available = True
    instance._skills = []

    assert instance.enabled is False


def test_execute_returns_error_when_not_available():
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._available = False
    instance._skills = [{"name": "pptx", "description": "Slides"}]

    result = instance.execute(task="Do it")

    assert result["success"] is False
    assert "not installed" in result["error"]


def test_execute_returns_error_when_no_skills():
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    instance._available = True
    instance._skills = []

    result = instance.execute(task="Do it")

    assert result["success"] is False
    assert "No skills available" in result["error"]


def test_execute_builds_prompt_with_context(tmp_path, monkeypatch):
    instance = _make_instance(tmp_path)

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(claude_skills.subprocess, "run", fake_run)

    result = instance.execute(task="Do it", context="ctx")

    assert result["success"] is True
    assert captured["cmd"][0:3] == ["claude", "--dangerously-skip-permissions", "-p"]
    assert captured["cmd"][3] == "Context from our conversation:\nctx\n\nTask: Do it"


def test_execute_builds_prompt_without_context(tmp_path, monkeypatch):
    instance = _make_instance(tmp_path)

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(claude_skills.subprocess, "run", fake_run)

    instance.execute(task="Do it")

    assert captured["cmd"][3] == "Do it"


def test_execute_unsets_api_key(tmp_path, monkeypatch):
    instance = _make_instance(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["env"] = kwargs.get("env")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(claude_skills.subprocess, "run", fake_run)

    instance.execute(task="Do it")

    assert "ANTHROPIC_API_KEY" not in captured["env"]


def test_execute_creates_output_dir(tmp_path, monkeypatch):
    output_dir = tmp_path / "output"
    instance = _make_instance(tmp_path)
    instance._output_dir = str(output_dir)

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(claude_skills.subprocess, "run", fake_run)

    instance.execute(task="Do it")

    assert output_dir.exists()


def test_execute_handles_timeout(tmp_path, monkeypatch):
    instance = _make_instance(tmp_path)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=instance._timeout)

    monkeypatch.setattr(claude_skills.subprocess, "run", fake_run)

    result = instance.execute(task="Do it")

    assert result["success"] is False
    assert "timed out" in result["error"]


def test_execute_handles_success(tmp_path, monkeypatch):
    instance = _make_instance(tmp_path)

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="done", stderr="")

    monkeypatch.setattr(claude_skills.subprocess, "run", fake_run)

    result = instance.execute(task="Do it")

    assert result == {"success": True, "output": "done", "error": ""}


def test_execute_handles_failure(tmp_path, monkeypatch):
    instance = _make_instance(tmp_path)

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="nope", stderr="boom")

    monkeypatch.setattr(claude_skills.subprocess, "run", fake_run)

    result = instance.execute(task="Do it")

    assert result == {"success": False, "output": "nope", "error": "boom"}
