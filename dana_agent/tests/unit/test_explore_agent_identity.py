"""
Unit tests for ExploreAgent identity template rendering.

Tests that the ExploreAgent's IDENTITY template renders correctly
with all environment and git variables populated.
"""

import re
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest


# Mock the problematic imports before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

from dana.core.knowledge.prompts.codecs import CSXMLCodec
from dana.core.prompt.prompt_api import LocalPromptAPI


class TestExploreAgentIdentityRendering:
    """Test that ExploreAgent's IDENTITY template renders correctly."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent with ExploreAgent's identity."""
        from dana.core.agent.base_agent import BaseAgent
        from dana.core.agent.builtin_agents.explore import IDENTITY

        class MockExploreAgent(BaseAgent):
            """Mock agent using ExploreAgent's identity."""

            def __init__(self, **kwargs):
                super().__init__(agent_type="explore_agent", agent_id="explore-test-123", **kwargs)
                self._identity_override = IDENTITY
                self._codec = Mock()
                self._codec.__qualname__ = "CSXMLCodec"
                # Mock LLM client for model_name
                self.llm_client = Mock()
                self.llm_client.model = "claude-3-sonnet"
                self.llm_client.provider_name = "anthropic"

        return MockExploreAgent()

    @pytest.fixture
    def mock_prompt_api(self, mock_agent):
        """Create a LocalPromptAPI with mocked git commands."""
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()

        api = LocalPromptAPI(
            agent=mock_agent,
            codec=CSXMLCodec,
            repository_factory=mock_factory,
        )
        return api

    def test_identity_has_no_unrendered_placeholders(self, mock_prompt_api):
        """Test that rendered identity has no {{variable}} placeholders."""
        with patch.object(mock_prompt_api._env, "_run_git_command") as mock_git:
            # Mock git commands to return realistic values
            def git_side_effect(cmd, default=""):
                if "status" in cmd:
                    return "M file.py"
                if "rev-parse" in cmd:
                    return "develop"
                if "symbolic-ref" in cmd:
                    return "refs/remotes/origin/main"
                if "log" in cmd:
                    return "abc1234 Recent commit"
                return default

            mock_git.side_effect = git_side_effect

            identity = mock_prompt_api.identity
            rendered = mock_prompt_api.render(identity)

        # Check for unrendered placeholders
        unrendered = re.findall(r"\{\{([^}]+)\}\}", rendered)
        assert unrendered == [], f"Found unrendered placeholders: {unrendered}"

    def test_identity_contains_environment_info(self, mock_prompt_api):
        """Test that rendered identity contains environment info."""
        with patch.object(mock_prompt_api._env, "_run_git_command") as mock_git:
            mock_git.return_value = ""

            identity = mock_prompt_api.identity
            rendered = mock_prompt_api.render(identity)

        assert "Working directory:" in rendered
        assert "Platform:" in rendered
        assert "OS Version:" in rendered
        assert "Today's date:" in rendered

    def test_identity_contains_git_status(self, mock_prompt_api):
        """Test that rendered identity contains git status."""
        with patch.object(mock_prompt_api._env, "_run_git_command") as mock_git:

            def git_side_effect(cmd, default=""):
                if "status" in cmd:
                    return "M modified.py\n?? untracked.txt"
                return default

            mock_git.side_effect = git_side_effect

            identity = mock_prompt_api.identity
            rendered = mock_prompt_api.render(identity)

        assert "Status:" in rendered
        assert "M modified.py" in rendered

    def test_identity_contains_git_current_branch(self, mock_prompt_api):
        """Test that rendered identity contains current branch."""
        with patch.object(mock_prompt_api._env, "_run_git_command") as mock_git:

            def git_side_effect(cmd, default=""):
                if "rev-parse" in cmd:
                    return "feature/test-branch"
                return default

            mock_git.side_effect = git_side_effect

            identity = mock_prompt_api.identity
            rendered = mock_prompt_api.render(identity)

        assert "Current branch:" in rendered
        assert "feature/test-branch" in rendered

    def test_identity_contains_git_main_branch(self, mock_prompt_api):
        """Test that rendered identity contains main branch."""
        with patch.object(mock_prompt_api._env, "_run_git_command") as mock_git:

            def git_side_effect(cmd, default=""):
                if "symbolic-ref" in cmd:
                    return "refs/remotes/origin/main"
                return default

            mock_git.side_effect = git_side_effect

            identity = mock_prompt_api.identity
            rendered = mock_prompt_api.render(identity)

        assert "Main branch" in rendered
        assert "main" in rendered

    def test_identity_contains_recent_commits(self, mock_prompt_api):
        """Test that rendered identity contains recent commits."""
        with patch.object(mock_prompt_api._env, "_run_git_command") as mock_git:

            def git_side_effect(cmd, default=""):
                if "log" in cmd:
                    return "abc1234 First commit\ndef5678 Second commit"
                return default

            mock_git.side_effect = git_side_effect

            identity = mock_prompt_api.identity
            rendered = mock_prompt_api.render(identity)

        assert "Recent commits:" in rendered
        assert "abc1234 First commit" in rendered

    def test_identity_contains_model_name(self, mock_prompt_api):
        """Test that rendered identity contains model name."""
        with patch.object(mock_prompt_api._env, "_run_git_command") as mock_git:
            mock_git.return_value = ""

            identity = mock_prompt_api.identity
            rendered = mock_prompt_api.render(identity)

        assert "claude-3-sonnet" in rendered
        assert "anthropic" in rendered

    def test_identity_with_git_not_available(self, mock_prompt_api):
        """Test that identity renders correctly when git is not available."""
        with patch.object(mock_prompt_api._env, "_run_git_command") as mock_git:
            # Simulate git not being available
            mock_git.return_value = ""

            identity = mock_prompt_api.identity
            rendered = mock_prompt_api.render(identity)

        # Should still render without errors
        unrendered = re.findall(r"\{\{([^}]+)\}\}", rendered)
        assert unrendered == [], f"Found unrendered placeholders: {unrendered}"

        # Should have default values
        assert "Current branch: unknown" in rendered
        assert "Main branch" in rendered  # Should default to "main"


class TestExploreAgentIdentityTemplate:
    """Test the ExploreAgent IDENTITY template structure."""

    def test_identity_template_has_required_placeholders(self):
        """Test that IDENTITY template has all required placeholders."""
        from dana.core.agent.builtin_agents.explore import IDENTITY

        required_placeholders = [
            "environment_info",
            "model_name",
            "git_current_branch",
            "git_main_branch",
            "git_status",
            "git_recent_commits",
        ]

        for placeholder in required_placeholders:
            assert f"{{{{{placeholder}}}}}" in IDENTITY, f"Missing placeholder: {placeholder}"

    def test_identity_template_contains_read_only_warning(self):
        """Test that IDENTITY template contains read-only mode warning."""
        from dana.core.agent.builtin_agents.explore import IDENTITY

        assert "READ-ONLY" in IDENTITY
        assert "STRICTLY PROHIBITED" in IDENTITY

    def test_identity_template_contains_env_section(self):
        """Test that IDENTITY template contains <env> section."""
        from dana.core.agent.builtin_agents.explore import IDENTITY

        assert "<env>" in IDENTITY
        assert "</env>" in IDENTITY
        assert "{{environment_info}}" in IDENTITY
