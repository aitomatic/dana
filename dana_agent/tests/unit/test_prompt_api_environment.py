"""
Unit tests for LocalPromptAPI environment and git properties.

Tests the environment_info, git_status, git_current_branch, git_main_branch,
and git_recent_commits properties.
"""

from datetime import date
import os
import subprocess
import sys
from unittest.mock import MagicMock, Mock, patch


# Mock the problematic import before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

from dana.core.agent.base_agent import BaseAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec
from dana.core.prompt.prompt_api import LocalPromptAPI


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, **kwargs):
        super().__init__(agent_type="test_agent", agent_id="test-agent-123", **kwargs)
        self._codec = Mock()
        self._codec.__qualname__ = "TestCodec"


class TestRunGitCommand:
    """Test the _run_git_command helper method."""

    def test_successful_command(self):
        """Test that successful git commands return stdout."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="  output content  \n")
            result = api._run_git_command(["git", "status"])

        assert result == "output content"
        mock_run.assert_called_once()

    def test_failed_command_returns_default(self):
        """Test that failed commands return the default value."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="error")
            result = api._run_git_command(["git", "invalid"], default="fallback")

        assert result == "fallback"

    def test_timeout_returns_default(self):
        """Test that timeout returns the default value."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=10)
            result = api._run_git_command(["git", "log"], default="timeout-fallback")

        assert result == "timeout-fallback"

    def test_file_not_found_returns_default(self):
        """Test that FileNotFoundError returns the default value."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            result = api._run_git_command(["git", "status"], default="not-found")

        assert result == "not-found"

    def test_os_error_returns_default(self):
        """Test that OSError returns the default value."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = OSError("some OS error")
            result = api._run_git_command(["git", "status"], default="os-error")

        assert result == "os-error"


class TestEnvironmentInfo:
    """Test the environment_info property."""

    def test_contains_working_directory(self):
        """Test that environment_info contains working directory."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        result = api.environment_info
        assert "Working directory:" in result
        assert os.getcwd() in result

    def test_contains_git_repo_status(self):
        """Test that environment_info contains git repo status."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        result = api.environment_info
        assert "Is directory a git repo:" in result
        # Should be Yes or No
        assert "Yes" in result or "No" in result

    def test_contains_platform(self):
        """Test that environment_info contains platform."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        result = api.environment_info
        assert "Platform:" in result
        assert sys.platform in result

    def test_contains_os_version(self):
        """Test that environment_info contains OS version."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        result = api.environment_info
        assert "OS Version:" in result

    def test_contains_todays_date(self):
        """Test that environment_info contains today's date."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        result = api.environment_info
        assert "Today's date:" in result
        assert date.today().isoformat() in result

    def test_git_repo_detection_yes(self):
        """Test git repo detection when .git exists."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch("os.path.isdir") as mock_isdir:
            mock_isdir.return_value = True
            result = api.environment_info

        assert "Is directory a git repo: Yes" in result

    def test_git_repo_detection_no(self):
        """Test git repo detection when .git doesn't exist."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch("os.path.isdir") as mock_isdir:
            mock_isdir.return_value = False
            result = api.environment_info

        assert "Is directory a git repo: No" in result


class TestGitStatus:
    """Test the git_status property."""

    def test_returns_porcelain_output(self):
        """Test that git_status returns porcelain output."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch.object(api, "_run_git_command") as mock_git:
            mock_git.return_value = "M file.py\n?? new.txt"
            result = api.git_status

        assert result == "M file.py\n?? new.txt"
        mock_git.assert_called_once_with(["git", "status", "--porcelain"])

    def test_returns_empty_for_clean_repo(self):
        """Test that git_status returns empty for clean repo."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch.object(api, "_run_git_command") as mock_git:
            mock_git.return_value = ""
            result = api.git_status

        assert result == ""


class TestGitCurrentBranch:
    """Test the git_current_branch property."""

    def test_returns_branch_name(self):
        """Test that git_current_branch returns branch name."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch.object(api, "_run_git_command") as mock_git:
            mock_git.return_value = "develop"
            result = api.git_current_branch

        assert result == "develop"
        mock_git.assert_called_once_with(["git", "rev-parse", "--abbrev-ref", "HEAD"])

    def test_returns_unknown_on_failure(self):
        """Test that git_current_branch returns 'unknown' on failure."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch.object(api, "_run_git_command") as mock_git:
            mock_git.return_value = ""
            result = api.git_current_branch

        assert result == "unknown"


class TestGitMainBranch:
    """Test the git_main_branch property."""

    def test_returns_from_symbolic_ref(self):
        """Test that git_main_branch returns from symbolic-ref when available."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch.object(api, "_run_git_command") as mock_git:
            mock_git.return_value = "refs/remotes/origin/main"
            result = api.git_main_branch

        assert result == "main"

    def test_fallback_to_main_when_listed(self):
        """Test that git_main_branch falls back to 'main' when listed."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        def mock_git_cmd(cmd, default=""):
            if "symbolic-ref" in cmd:
                return ""
            if "branch" in cmd:
                return "  main"
            return default

        with patch.object(api, "_run_git_command", side_effect=mock_git_cmd):
            result = api.git_main_branch

        assert result == "main"

    def test_fallback_to_master_when_listed(self):
        """Test that git_main_branch falls back to 'master' when listed."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        def mock_git_cmd(cmd, default=""):
            if "symbolic-ref" in cmd:
                return ""
            if "branch" in cmd:
                return "  master"
            return default

        with patch.object(api, "_run_git_command", side_effect=mock_git_cmd):
            result = api.git_main_branch

        assert result == "master"

    def test_default_to_main_when_nothing_found(self):
        """Test that git_main_branch defaults to 'main' when nothing found."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch.object(api, "_run_git_command") as mock_git:
            mock_git.return_value = ""
            result = api.git_main_branch

        assert result == "main"


class TestGitRecentCommits:
    """Test the git_recent_commits property."""

    def test_returns_recent_commits(self):
        """Test that git_recent_commits returns recent commits."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        commits = "abc1234 First commit\ndef5678 Second commit"
        with patch.object(api, "_run_git_command") as mock_git:
            mock_git.return_value = commits
            result = api.git_recent_commits

        assert result == commits
        mock_git.assert_called_once_with(["git", "log", "--oneline", "-n", "5"])

    def test_returns_empty_for_no_commits(self):
        """Test that git_recent_commits returns empty for no commits."""
        agent = MockAgent()
        mock_factory = Mock()
        mock_factory.create.return_value = Mock()
        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

        with patch.object(api, "_run_git_command") as mock_git:
            mock_git.return_value = ""
            result = api.git_recent_commits

        assert result == ""
