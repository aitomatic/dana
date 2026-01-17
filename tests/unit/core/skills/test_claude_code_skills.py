from __future__ import annotations

from pathlib import Path
import subprocess

from dana.core.skills import ClaudeCodeSkills


class DummyCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def make_skills_instance(tmp_path: Path) -> ClaudeCodeSkills:
    instance = object.__new__(ClaudeCodeSkills)
    instance._available = True
    instance._skills = [{"name": "pptx", "description": "PPTX"}]
    instance._output_dir = str(tmp_path)
    instance._timeout = 123
    instance._disable_session_persistence = False
    return instance


def test_init_default_values(monkeypatch, tmp_path):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    monkeypatch.setattr(ClaudeCodeSkills, "_discover_skills", lambda self: [])
    skills = ClaudeCodeSkills()

    assert skills._skills_dir == Path("~/.claude/skills").expanduser()
    assert skills._output_dir == "./skill_output"
    assert skills._timeout == 300
    assert skills._disable_session_persistence is False
    assert skills.resource_id == "claude-skills"


def test_init_custom_values(monkeypatch, tmp_path):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    monkeypatch.setattr(ClaudeCodeSkills, "_discover_skills", lambda self: [])
    skills = ClaudeCodeSkills(
        skills_dir=str(tmp_path),
        output_dir="/tmp/out",
        timeout=42,
        disable_session_persistence=True,
        resource_id="custom",
    )

    assert skills._skills_dir == tmp_path
    assert skills._output_dir == "/tmp/out"
    assert skills._timeout == 42
    assert skills._disable_session_persistence is True
    assert skills.resource_id == "custom"


def test_init_with_skill_filter(monkeypatch):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    monkeypatch.setattr(
        ClaudeCodeSkills,
        "_discover_skills",
        lambda self: [
            {"name": "pptx", "description": "PPTX"},
            {"name": "xlsx", "description": "XLSX"},
        ],
    )

    skills = ClaudeCodeSkills(skills=["xlsx"])
    assert skills.skills == [{"name": "xlsx", "description": "XLSX"}]


def test_check_claude_available_when_installed(monkeypatch):
    def fake_run(*_args, **_kwargs):
        return DummyCompleted(returncode=0)

    monkeypatch.setattr("subprocess.run", fake_run)
    instance = object.__new__(ClaudeCodeSkills)
    assert instance._check_claude_available() is True


def test_check_claude_available_when_not_installed(monkeypatch):
    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("subprocess.run", fake_run)
    instance = object.__new__(ClaudeCodeSkills)
    assert instance._check_claude_available() is False


def test_discover_skills_finds_skills(monkeypatch, tmp_path):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)

    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    pptx_dir = skill_dir / "pptx"
    pptx_dir.mkdir()
    (pptx_dir / "SKILL.md").write_text("Presentation output")

    skills = ClaudeCodeSkills(skills_dir=str(skill_dir))
    assert skills.all_skills == [{"name": "pptx", "description": "Presentation output"}]


def test_discover_skills_empty_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    skills = ClaudeCodeSkills(skills_dir=str(tmp_path))
    assert skills.all_skills == []


def test_discover_skills_missing_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    missing = tmp_path / "missing"
    skills = ClaudeCodeSkills(skills_dir=str(missing))
    assert skills.all_skills == []


def test_parse_skill_description_first_line(tmp_path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("Simple description\n# Heading")

    instance = object.__new__(ClaudeCodeSkills)
    assert instance._parse_skill_description(skill_md) == "Simple description"


def test_parse_skill_description_heading(tmp_path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("# Skill Title\nMore")

    instance = object.__new__(ClaudeCodeSkills)
    assert instance._parse_skill_description(skill_md) == "Skill Title"


def test_parse_skill_description_truncates(tmp_path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("a" * 300)

    instance = object.__new__(ClaudeCodeSkills)
    assert instance._parse_skill_description(skill_md) == "a" * 200


def test_filter_skills():
    instance = object.__new__(ClaudeCodeSkills)
    instance._all_skills = [
        {"name": "pptx", "description": "PPTX"},
        {"name": "xlsx", "description": "XLSX"},
    ]

    assert instance._filter_skills(["pptx"]) == [{"name": "pptx", "description": "PPTX"}]


def test_format_skills_for_docstring():
    instance = object.__new__(ClaudeCodeSkills)
    instance._skills = [
        {"name": "pptx", "description": "PPTX"},
        {"name": "xlsx", "description": "XLSX"},
    ]

    assert instance._format_skills_for_docstring() == "- pptx: PPTX\n- xlsx: XLSX"


def test_enabled_property_true():
    instance = object.__new__(ClaudeCodeSkills)
    instance._available = True
    instance._skills = [{"name": "pptx", "description": "PPTX"}]

    assert instance.enabled is True


def test_enabled_property_false_no_claude():
    instance = object.__new__(ClaudeCodeSkills)
    instance._available = False
    instance._skills = [{"name": "pptx", "description": "PPTX"}]

    assert instance.enabled is False


def test_enabled_property_false_no_skills():
    instance = object.__new__(ClaudeCodeSkills)
    instance._available = True
    instance._skills = []

    assert instance.enabled is False


def test_execute_returns_error_when_not_available(tmp_path):
    instance = object.__new__(ClaudeCodeSkills)
    instance._available = False
    instance._skills = [{"name": "pptx", "description": "PPTX"}]

    result = instance.execute("task")
    assert result["success"] is False
    assert "Claude Code CLI" in result["error"]


def test_execute_returns_error_when_no_skills(tmp_path):
    instance = object.__new__(ClaudeCodeSkills)
    instance._available = True
    instance._skills = []

    result = instance.execute("task")
    assert result["success"] is False
    assert "No skills available" in result["error"]


def test_execute_builds_prompt_with_context(monkeypatch, tmp_path):
    instance = make_skills_instance(tmp_path)

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return DummyCompleted(returncode=0, stdout="done")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = instance.execute("Do thing", context="Context here")

    assert result["success"] is True
    assert "-p" in captured["cmd"]
    prompt = captured["cmd"][captured["cmd"].index("-p") + 1]
    assert prompt == "Context from our conversation:\nContext here\n\nTask: Do thing"


def test_execute_builds_prompt_without_context(monkeypatch, tmp_path):
    instance = make_skills_instance(tmp_path)

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return DummyCompleted(returncode=0, stdout="done")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = instance.execute("Do thing")

    assert result["success"] is True
    prompt = captured["cmd"][captured["cmd"].index("-p") + 1]
    assert prompt == "Do thing"


def test_execute_unsets_api_key(monkeypatch, tmp_path):
    instance = make_skills_instance(tmp_path)

    def fake_run(cmd, **kwargs):
        env = kwargs.get("env", {})
        assert "ANTHROPIC_API_KEY" not in env
        return DummyCompleted(returncode=0, stdout="done")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    monkeypatch.setattr("subprocess.run", fake_run)

    result = instance.execute("Do thing")
    assert result["success"] is True


def test_execute_creates_output_dir(monkeypatch, tmp_path):
    instance = make_skills_instance(tmp_path / "out")

    def fake_run(cmd, **kwargs):
        return DummyCompleted(returncode=0, stdout="done")

    monkeypatch.setattr("subprocess.run", fake_run)
    instance.execute("Do thing")

    assert (tmp_path / "out").exists()


def test_execute_handles_timeout(monkeypatch, tmp_path):
    instance = make_skills_instance(tmp_path)

    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr("subprocess.run", fake_run)

    result = instance.execute("Do thing")
    assert result["success"] is False
    assert "timed out" in result["error"].lower()


def test_execute_handles_success(monkeypatch, tmp_path):
    instance = make_skills_instance(tmp_path)

    def fake_run(*_args, **_kwargs):
        return DummyCompleted(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    result = instance.execute("Do thing")
    assert result == {"success": True, "output": "ok", "error": ""}


def test_execute_handles_failure(monkeypatch, tmp_path):
    instance = make_skills_instance(tmp_path)

    def fake_run(*_args, **_kwargs):
        return DummyCompleted(returncode=2, stdout="", stderr="bad")

    monkeypatch.setattr("subprocess.run", fake_run)

    result = instance.execute("Do thing")
    assert result["success"] is False
    assert result["error"] == "bad"
