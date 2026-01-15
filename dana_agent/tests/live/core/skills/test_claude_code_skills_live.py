"""
Live E2E tests for ClaudeCodeSkills.

These tests actually invoke Claude Code CLI and generate real files.
Run manually with: pytest -m live tests/live/core/skills/ -v

Requirements:
- Claude Code CLI installed and authenticated
- Skills installed in ~/.claude/skills/
- Active Claude subscription
"""

from __future__ import annotations

import os
import tempfile

import pytest

from dana.core.skills import ClaudeCodeSkills


@pytest.mark.live
class TestClaudeCodeSkillsLive:
    """Live tests that actually invoke Claude Code."""

    def test_discover_real_skills(self):
        """Verify skill discovery works with actual ~/.claude/skills/ directory."""
        skills = ClaudeCodeSkills()

        assert skills.enabled, "Claude Code should be available"
        assert len(skills.skills) > 0, "Should discover at least one skill"

        skill_names = [skill["name"] for skill in skills.skills]
        print(f"Discovered skills: {skill_names}")

        assert "pptx" in skill_names, "pptx skill should be available"

    def test_execute_pptx_skill_creates_file(self):
        """E2E: Actually generate a .pptx file via Claude Code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills = ClaudeCodeSkills(output_dir=tmpdir)

            assert skills.enabled, "Claude Code should be available"

            output_path = os.path.join(tmpdir, "test_presentation.pptx")
            result = skills.execute(
                task=(
                    "Create a simple 2-slide presentation about testing. "
                    "Slide 1: Title 'Test Presentation'. "
                    "Slide 2: One bullet point saying 'This is a test'. "
                    f"Save to {output_path}"
                ),
                context="This is an automated test of the Claude Skills integration.",
            )

            print(f"Result: {result}")

            assert result["success"], f"Execution failed: {result['error']}"
            assert os.path.exists(output_path), f"Output file not created: {output_path}"

            file_size = os.path.getsize(output_path)
            assert file_size > 1000, f"File too small ({file_size} bytes), likely empty or corrupt"

            print(f"Successfully created {output_path} ({file_size} bytes)")

    def test_execute_with_context_injection(self):
        """E2E: Verify context is passed to Claude Code and reflected in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills = ClaudeCodeSkills(output_dir=tmpdir)

            assert skills.enabled, "Claude Code should be available"

            output_path = os.path.join(tmpdir, "q4_results.pptx")
            result = skills.execute(
                task=(
                    "Create a 2-slide presentation about Q4 results. "
                    "Include the revenue and growth numbers from context. "
                    f"Save to {output_path}"
                ),
                context="Q4 revenue: $5.2M, growth: 23%, new customers: 150",
            )

            print(f"Result: {result}")

            assert result["success"], f"Execution failed: {result['error']}"
            assert os.path.exists(output_path), f"Output file not created: {output_path}"

            file_size = os.path.getsize(output_path)
            assert file_size > 1000, f"File too small ({file_size} bytes)"

            print(f"Successfully created {output_path} ({file_size} bytes)")

    def test_filtered_skills(self):
        """E2E: Verify skill filtering works with real skills."""
        all_skills = ClaudeCodeSkills()
        all_count = len(all_skills.skills)

        filtered = ClaudeCodeSkills(skills=["pptx"])

        assert len(filtered.skills) == 1, "Should have exactly one skill"
        assert filtered.skills[0]["name"] == "pptx", "Should be pptx skill"
        assert len(filtered.skills) < all_count, "Filtered should have fewer skills"
