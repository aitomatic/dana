"""Unit tests for ClaudeCodeSkills resource."""

from __future__ import annotations

from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from dana.core.skills import ClaudeCodeSkills


def _build_instance(**overrides) -> ClaudeCodeSkills:
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    defaults = {
        "_skills_dir": Path("~/.claude/skills").expanduser(),
        "_output_dir": "./skill_output",
        "_timeout": 300,
        "_available": True,
        "_all_skills": [],
        "_skills": [],
        "_disable_session_persistence": False,
    }
    for key, value in {**defaults, **overrides}.items():
        setattr(instance, key, value)
    return instance


def test_init_default_values(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    monkeypatch.setattr(ClaudeCodeSkills, "_discover_skills", lambda self: [])
    skills = ClaudeCodeSkills(auto_register=False)

    assert skills._output_dir == "./skill_output"
    assert skills._timeout == 300
    assert skills.resource_id == "claude-skills"
    assert skills._skills_dir == Path("~/.claude/skills").expanduser()


def test_init_custom_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    monkeypatch.setattr(ClaudeCodeSkills, "_discover_skills", lambda self: [])
    skills = ClaudeCodeSkills(
        skills_dir=str(tmp_path),
        output_dir="./out",
        timeout=123,
        resource_id="custom-skills",
        auto_register=False,
    )

    assert skills._skills_dir == tmp_path
    assert skills._output_dir == "./out"
    assert skills._timeout == 123
    assert skills.resource_id == "custom-skills"


def test_init_with_skill_filter(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        ClaudeCodeSkills,
        "_discover_skills",
        lambda self: [
            {"name": "pptx", "description": "PPTX"},
            {"name": "xlsx", "description": "XLSX"},
        ],
    )
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    skills = ClaudeCodeSkills(skills=["pptx"], auto_register=False)

    assert skills.skills == [{"name": "pptx", "description": "PPTX"}]


def test_check_claude_available_when_installed(monkeypatch: pytest.MonkeyPatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    assert instance._check_claude_available() is True


def test_check_claude_available_when_not_installed(monkeypatch: pytest.MonkeyPatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("no claude")

    monkeypatch.setattr(subprocess, "run", fake_run)
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)
    assert instance._check_claude_available() is False


def test_discover_skills_finds_skills(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    skill_dir = tmp_path / "pptx"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# PPTX\nCreate presentations.")

    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: False)
    skills = ClaudeCodeSkills(skills_dir=str(tmp_path), auto_register=False)

    assert skills.all_skills == [{"name": "pptx", "description": "PPTX"}]


def test_discover_skills_empty_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: False)
    skills = ClaudeCodeSkills(skills_dir=str(tmp_path), auto_register=False)

    assert skills.all_skills == []


def test_discover_skills_missing_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    missing_dir = tmp_path / "missing"
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: False)
    skills = ClaudeCodeSkills(skills_dir=str(missing_dir), auto_register=False)

    assert skills.all_skills == []


def test_parse_skill_description_first_line(tmp_path: Path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("First line description.\n\n# Heading")
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)

    assert instance._parse_skill_description(skill_md) == "First line description."


def test_parse_skill_description_heading(tmp_path: Path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("# Heading line\n\nBody")
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)

    assert instance._parse_skill_description(skill_md) == "Heading line"


def test_parse_skill_description_truncates(tmp_path: Path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("a" * 300)
    instance = ClaudeCodeSkills.__new__(ClaudeCodeSkills)

    assert len(instance._parse_skill_description(skill_md)) == 200


def test_filter_skills():
    instance = _build_instance(
        _all_skills=[
            {"name": "pptx", "description": "PPTX"},
            {"name": "xlsx", "description": "XLSX"},
        ]
    )

    assert instance._filter_skills(["xlsx"]) == [{"name": "xlsx", "description": "XLSX"}]


def test_format_skills_for_docstring():
    instance = _build_instance(
        _skills=[
            {"name": "pptx", "description": "PPTX"},
            {"name": "xlsx", "description": "XLSX"},
        ]
    )

    assert instance._format_skills_for_docstring() == "- pptx: PPTX\n- xlsx: XLSX"


def test_enabled_property_true():
    instance = _build_instance(_available=True, _skills=[{"name": "pptx", "description": "PPTX"}])
    assert instance.enabled is True


def test_enabled_property_false_no_claude():
    instance = _build_instance(_available=False, _skills=[{"name": "pptx", "description": "PPTX"}])
    assert instance.enabled is False


def test_enabled_property_false_no_skills():
    instance = _build_instance(_available=True, _skills=[])
    assert instance.enabled is False


def test_execute_returns_error_when_not_available():
    instance = _build_instance(_available=False)
    result = instance.execute(task="do something")

    assert result["success"] is False
    assert "Claude Code CLI is not installed" in result["error"]


def test_execute_returns_error_when_no_skills():
    instance = _build_instance(_available=True, _skills=[])
    result = instance.execute(task="do something")

    assert result["success"] is False
    assert "No skills available" in result["error"]


def test_execute_builds_prompt_with_context(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["prompt"] = cmd[-1]
        captured["env"] = kwargs.get("env", {})
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")

    instance = _build_instance(
        _available=True,
        _skills=[{"name": "pptx", "description": "PPTX"}],
        _output_dir=str(tmp_path / "out"),
        _timeout=10,
    )
    result = instance.execute(task="Do thing", context="Context here")

    assert result["success"] is True
    assert "Context from our conversation:" in captured["prompt"]
    assert "Task: Do thing" in captured["prompt"]
    assert "ANTHROPIC_API_KEY" not in captured["env"]


def test_execute_builds_prompt_without_context(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["prompt"] = cmd[-1]
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    instance = _build_instance(
        _available=True,
        _skills=[{"name": "pptx", "description": "PPTX"}],
        _output_dir=str(tmp_path / "out"),
    )
    result = instance.execute(task="Do thing")

    assert result["success"] is True
    assert captured["prompt"] == "Do thing"


def test_execute_unsets_api_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["env"] = kwargs.get("env", {})
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")

    instance = _build_instance(
        _available=True,
        _skills=[{"name": "pptx", "description": "PPTX"}],
        _output_dir=str(tmp_path / "out"),
    )
    instance.execute(task="Do thing")

    assert "ANTHROPIC_API_KEY" not in captured["env"]


def test_execute_creates_output_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    output_dir = tmp_path / "output"

    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    instance = _build_instance(
        _available=True,
        _skills=[{"name": "pptx", "description": "PPTX"}],
        _output_dir=str(output_dir),
    )

    assert output_dir.exists() is False
    instance.execute(task="Do thing")
    assert output_dir.exists() is True


def test_execute_handles_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=1)

    monkeypatch.setattr(subprocess, "run", fake_run)
    instance = _build_instance(
        _available=True,
        _skills=[{"name": "pptx", "description": "PPTX"}],
        _output_dir=str(tmp_path),
        _timeout=1,
    )
    result = instance.execute(task="Do thing")

    assert result["success"] is False
    assert "timed out after 1 seconds" in result["error"]


def test_execute_handles_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=0, stdout="done", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    instance = _build_instance(
        _available=True,
        _skills=[{"name": "pptx", "description": "PPTX"}],
        _output_dir=str(tmp_path),
    )
    result = instance.execute(task="Do thing")

    assert result == {"success": True, "output": "done", "error": ""}


def test_execute_handles_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="bad")

    monkeypatch.setattr(subprocess, "run", fake_run)
    instance = _build_instance(
        _available=True,
        _skills=[{"name": "pptx", "description": "PPTX"}],
        _output_dir=str(tmp_path),
    )
    result = instance.execute(task="Do thing")

    assert result == {"success": False, "output": "", "error": "bad"}
