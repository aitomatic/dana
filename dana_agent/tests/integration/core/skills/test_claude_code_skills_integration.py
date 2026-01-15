"""Integration tests for ClaudeCodeSkills and STARAgent integration."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from dana.core.agent.star_agent import STARAgent
from dana.core.skills import ClaudeCodeSkills


def _mock_skills(monkeypatch: pytest.MonkeyPatch, skills: list[dict]):
    monkeypatch.setattr(ClaudeCodeSkills, "_check_claude_available", lambda self: True)
    monkeypatch.setattr(ClaudeCodeSkills, "_discover_skills", lambda self: skills)


def test_star_agent_has_skills_by_default(monkeypatch: pytest.MonkeyPatch):
    _mock_skills(monkeypatch, [{"name": "pptx", "description": "PPTX"}])
    with patch("dana.core.agent.star_agent.LLM"):
        agent = STARAgent(agent_type="test", auto_register=False)

    assert any(resource.resource_type == "claude-skills" for resource in agent.available_resources)


def test_star_agent_skills_disabled(monkeypatch: pytest.MonkeyPatch):
    _mock_skills(monkeypatch, [{"name": "pptx", "description": "PPTX"}])
    with patch("dana.core.agent.star_agent.LLM"):
        agent = STARAgent(agent_type="test", auto_register=False, enable_skills=False)

    assert not any(resource.resource_type == "claude-skills" for resource in agent.available_resources)


def test_star_agent_custom_output_dir(monkeypatch: pytest.MonkeyPatch):
    _mock_skills(monkeypatch, [{"name": "pptx", "description": "PPTX"}])
    with patch("dana.core.agent.star_agent.LLM"):
        agent = STARAgent(agent_type="test", auto_register=False, skills_output_dir="./custom-output")

    skills_resource = next(
        resource for resource in agent.available_resources if resource.resource_type == "claude-skills"
    )
    assert skills_resource._output_dir == "./custom-output"


def test_specialized_agent_filtered_skills(monkeypatch: pytest.MonkeyPatch):
    _mock_skills(
        monkeypatch,
        [
            {"name": "pptx", "description": "PPTX"},
            {"name": "xlsx", "description": "XLSX"},
        ],
    )
    skills = ClaudeCodeSkills(skills=["pptx"], auto_register=False)

    assert skills.skills == [{"name": "pptx", "description": "PPTX"}]
