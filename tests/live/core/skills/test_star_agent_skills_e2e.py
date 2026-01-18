"""
E2E tests for STARAgent with Claude Skills integration.

These tests verify the FULL flow:
1. STARAgent receives a user query
2. Agent's LLM sees available skills and decides to use them
3. Agent autonomously calls ClaudeCodeSkills.execute()
4. Actual file is generated

Run manually with: pytest -m live tests/live/core/skills/test_star_agent_skills_e2e.py -v

Requirements:
- Claude Code CLI installed and authenticated
- Skills installed in ~/.claude/skills/
- Active Claude subscription
- LLM API key configured (for STARAgent's LLM)
"""

from __future__ import annotations

import os
import tempfile

import pytest

from dana.core.agent.star_agent import STARAgent


@pytest.mark.live
class TestSTARAgentSkillsE2E:
    """E2E tests: STARAgent query -> skill execution -> file output."""

    def test_star_agent_creates_presentation_from_query(self):
        """E2E: STARAgent receives query and autonomously creates .pptx file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = STARAgent(
                agent_type="test-skills-agent",
                skills_output_dir=tmpdir,
            )

            resource_ids = [resource.resource_id for resource in agent._resources]
            assert "claude-skills" in resource_ids, "Skills resource should be attached"

            output_path = os.path.join(tmpdir, "test_e2e.pptx")
            response = agent.query(
                message=(
                    "Create a simple 2-slide presentation about software testing. "
                    "Slide 1 should have the title 'Testing Fundamentals'. "
                    "Slide 2 should list 3 types of testing. "
                    f"Save the file to {output_path}"
                )
            )

            print(f"Agent response: {response}")

            assert os.path.exists(output_path), (
                f"Output file not created at {output_path}. "
                f"Agent may not have used the skills resource. Response: {response}"
            )

            file_size = os.path.getsize(output_path)
            assert file_size > 1000, f"File too small ({file_size} bytes)"

            print(f"SUCCESS: STARAgent created {output_path} ({file_size} bytes)")

    def test_star_agent_uses_context_in_skill_execution(self):
        """E2E: STARAgent passes conversation context to skill execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = STARAgent(
                agent_type="test-context-agent",
                skills_output_dir=tmpdir,
            )

            output_path = os.path.join(tmpdir, "q4_report.pptx")
            response = agent.query(
                message=(
                    "Our Q4 results: Revenue was $5.2 million, up 23% year-over-year. "
                    "We acquired 150 new enterprise customers. "
                    "Create a 2-slide executive summary presentation with these numbers. "
                    f"Save to {output_path}"
                )
            )

            print(f"Agent response: {response}")

            assert os.path.exists(output_path), (
                f"Output file not created. Agent response: {response}"
            )

            file_size = os.path.getsize(output_path)
            assert file_size > 1000, f"File too small ({file_size} bytes)"

            print(f"SUCCESS: Context-aware presentation created ({file_size} bytes)")

    def test_star_agent_with_filtered_skills(self):
        """E2E: Specialized agent with filtered skills works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from dana.core.skills import ClaudeCodeSkills

            agent = STARAgent(
                agent_type="doc-specialist",
                enable_skills=False,
            )

            filtered_skills = ClaudeCodeSkills(
                skills=["pptx", "docx"],
                output_dir=tmpdir,
            )
            agent.with_resources(filtered_skills)

            skill_names = [skill["name"] for skill in filtered_skills.skills]
            assert "pptx" in skill_names
            assert "xlsx" not in skill_names, "xlsx should be filtered out"

            output_path = os.path.join(tmpdir, "filtered_test.pptx")
            response = agent.query(
                message=(
                    "Create a simple 1-slide presentation titled 'Filtered Skills Test'. "
                    f"Save to {output_path}"
                )
            )

            print(f"Agent response: {response}")

            assert os.path.exists(output_path), f"File not created: {response}"
            print("SUCCESS: Filtered skills agent created presentation")
