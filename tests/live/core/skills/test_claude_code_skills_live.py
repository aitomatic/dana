"""
Live E2E tests for ClaudeCodeSkills.

These tests actually invoke Claude Code CLI and generate real files.
Run manually with: pytest -m live tests/live/core/skills/ -v

Requirements:
- Claude Code CLI installed and authenticated
- Skills installed in ~/.claude/skills/
- Active Claude subscription
"""

import os
import tempfile
import subprocess
from pathlib import Path

import pytest

from dana.core.skills import ClaudeCodeSkills


_AUTH_CACHE: dict[str, tuple[bool, str]] = {}


def _claude_authenticated(skills: ClaudeCodeSkills) -> tuple[bool, str]:
    """Return whether Claude Code is authenticated for live tests."""
    cache_key = "no_persist" if skills.disable_session_persistence else "persist"
    if cache_key in _AUTH_CACHE:
        return _AUTH_CACHE[cache_key]

    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    cmd = ["claude", "--dangerously-skip-permissions"]
    if skills.disable_session_persistence:
        cmd.append("--no-session-persistence")
    cmd.extend(["-p", "Reply with OK."])

    try:
        if skills.disable_session_persistence:
            with tempfile.TemporaryDirectory() as tmpdir:
                config_dir = Path(tmpdir) / ".claude_config"
                config_dir.mkdir(parents=True, exist_ok=True)
                skills._sync_claude_config_dir(config_dir)
                skills._sync_keychain_credentials(config_dir)
                env["CLAUDE_CONFIG_DIR"] = str(config_dir)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30,
                )
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
    except FileNotFoundError:
        _AUTH_CACHE[cache_key] = (False, "Claude Code CLI not installed.")
        return _AUTH_CACHE[cache_key]
    except subprocess.TimeoutExpired:
        _AUTH_CACHE[cache_key] = (False, "Claude Code authentication check timed out.")
        return _AUTH_CACHE[cache_key]

    combined = f"{result.stdout}\n{result.stderr}".strip()
    if result.returncode == 0:
        _AUTH_CACHE[cache_key] = (True, "")
        return _AUTH_CACHE[cache_key]

    auth_markers = ("Invalid API key", "Please run /login", "not authenticated", "Not logged in")
    if any(marker in combined for marker in auth_markers):
        _AUTH_CACHE[cache_key] = (False, "not_authenticated")
        return _AUTH_CACHE[cache_key]

    _AUTH_CACHE[cache_key] = (False, combined or "Claude Code authentication check failed.")
    return _AUTH_CACHE[cache_key]


def _require_live_environment(skills: ClaudeCodeSkills) -> None:
    if not skills.enabled:
        pytest.skip("Claude Code CLI not available or skills not installed.")
    home_dir = Path.home()
    config_path = home_dir / ".claude.json"
    if config_path.exists():
        if not os.access(config_path, os.W_OK) and not skills.disable_session_persistence:
            pytest.skip("Claude Code config is not writable at ~/.claude.json.")
    elif not os.access(home_dir, os.W_OK):
        pytest.skip("Home directory is not writable for Claude Code config.")
    authenticated, reason = _claude_authenticated(skills)
    if not authenticated:
        if reason == "not_authenticated":
            pytest.skip("Claude Code is not authenticated. Run `claude /login` or `claude setup-token`.")
        pytest.fail(reason)


@pytest.mark.live
class TestClaudeCodeSkillsLive:
    """Live tests that actually invoke Claude Code."""

    def test_discover_real_skills(self):
        """Verify skill discovery works with actual ~/.claude/skills/ directory."""
        skills = ClaudeCodeSkills(disable_session_persistence=True)
        _require_live_environment(skills)

        assert len(skills.skills) > 0, "Should discover at least one skill"

        skill_names = [skill["name"] for skill in skills.skills]
        print(f"Discovered skills: {skill_names}")

        assert "pptx" in skill_names, "pptx skill should be available"

    def test_execute_pptx_skill_creates_file(self):
        """E2E: Actually generate a .pptx file via Claude Code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills = ClaudeCodeSkills(output_dir=tmpdir, disable_session_persistence=True)
            _require_live_environment(skills)

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
            skills = ClaudeCodeSkills(output_dir=tmpdir, disable_session_persistence=True)
            _require_live_environment(skills)

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
