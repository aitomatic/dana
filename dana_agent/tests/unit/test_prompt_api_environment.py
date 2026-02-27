"""
Unit tests for EnvironmentInfo environment and git properties.

Tests the environment_info, git_status, git_current_branch, git_main_branch,
and git_recent_commits properties extracted from LocalPromptAPI.
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

from dana.core.prompt.environment_info import EnvironmentInfo


def _make_env_info() -> EnvironmentInfo:
    """Create an EnvironmentInfo instance with a mock agent."""
    agent = Mock()
    agent.llm_client.model = "test-model"
    agent.llm_client.provider_name = "test-provider"
    return EnvironmentInfo(agent=agent, relative_path="TestCodec/test-agent/prompts")


class TestRunGitCommand:
    """Test the _run_git_command helper method."""

    def test_successful_command(self):
        env = _make_env_info()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="  output content  \n")
            result = env._run_git_command(["git", "status"])
        assert result == "output content"
        mock_run.assert_called_once()

    def test_failed_command_returns_default(self):
        env = _make_env_info()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="error")
            result = env._run_git_command(["git", "invalid"], default="fallback")
        assert result == "fallback"

    def test_timeout_returns_default(self):
        env = _make_env_info()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=10)
            result = env._run_git_command(["git", "log"], default="timeout-fallback")
        assert result == "timeout-fallback"

    def test_file_not_found_returns_default(self):
        env = _make_env_info()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            result = env._run_git_command(["git", "status"], default="not-found")
        assert result == "not-found"

    def test_os_error_returns_default(self):
        env = _make_env_info()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = OSError("some OS error")
            result = env._run_git_command(["git", "status"], default="os-error")
        assert result == "os-error"


class TestEnvironmentInfo:
    """Test the environment_info property."""

    def test_contains_working_directory(self):
        env = _make_env_info()
        result = env.environment_info
        assert "Working directory:" in result
        assert os.getcwd() in result

    def test_contains_git_repo_status(self):
        env = _make_env_info()
        result = env.environment_info
        assert "Is directory a git repo:" in result
        assert "Yes" in result or "No" in result

    def test_contains_platform(self):
        env = _make_env_info()
        result = env.environment_info
        assert "Platform:" in result
        assert sys.platform in result

    def test_contains_os_version(self):
        env = _make_env_info()
        result = env.environment_info
        assert "OS Version:" in result

    def test_contains_todays_date(self):
        env = _make_env_info()
        result = env.environment_info
        assert "Today's date:" in result
        assert date.today().isoformat() in result

    def test_git_repo_detection_yes(self):
        env = _make_env_info()
        with patch("os.path.isdir") as mock_isdir:
            mock_isdir.return_value = True
            result = env.environment_info
        assert "Is directory a git repo: Yes" in result

    def test_git_repo_detection_no(self):
        env = _make_env_info()
        with patch("os.path.isdir") as mock_isdir:
            mock_isdir.return_value = False
            result = env.environment_info
        assert "Is directory a git repo: No" in result


class TestGitStatus:
    """Test the git_status property."""

    def test_returns_porcelain_output(self):
        env = _make_env_info()
        with patch.object(env, "_run_git_command") as mock_git:
            mock_git.return_value = "M file.py\n?? new.txt"
            result = env.git_status
        assert result == "M file.py\n?? new.txt"
        mock_git.assert_called_once_with(["git", "status", "--porcelain"])

    def test_returns_empty_for_clean_repo(self):
        env = _make_env_info()
        with patch.object(env, "_run_git_command") as mock_git:
            mock_git.return_value = ""
            result = env.git_status
        assert result == ""


class TestGitCurrentBranch:
    """Test the git_current_branch property."""

    def test_returns_branch_name(self):
        env = _make_env_info()
        with patch.object(env, "_run_git_command") as mock_git:
            mock_git.return_value = "develop"
            result = env.git_current_branch
        assert result == "develop"
        mock_git.assert_called_once_with(["git", "rev-parse", "--abbrev-ref", "HEAD"])

    def test_returns_unknown_on_failure(self):
        env = _make_env_info()
        with patch.object(env, "_run_git_command") as mock_git:
            mock_git.return_value = ""
            result = env.git_current_branch
        assert result == "unknown"


class TestGitMainBranch:
    """Test the git_main_branch property."""

    def test_returns_from_symbolic_ref(self):
        env = _make_env_info()
        with patch.object(env, "_run_git_command") as mock_git:
            mock_git.return_value = "refs/remotes/origin/main"
            result = env.git_main_branch
        assert result == "main"

    def test_fallback_to_main_when_listed(self):
        env = _make_env_info()

        def mock_git_cmd(cmd, default=""):
            if "symbolic-ref" in cmd:
                return ""
            if "branch" in cmd:
                return "  main"
            return default

        with patch.object(env, "_run_git_command", side_effect=mock_git_cmd):
            result = env.git_main_branch
        assert result == "main"

    def test_fallback_to_master_when_listed(self):
        env = _make_env_info()

        def mock_git_cmd(cmd, default=""):
            if "symbolic-ref" in cmd:
                return ""
            if "branch" in cmd:
                return "  master"
            return default

        with patch.object(env, "_run_git_command", side_effect=mock_git_cmd):
            result = env.git_main_branch
        assert result == "master"

    def test_default_to_main_when_nothing_found(self):
        env = _make_env_info()
        with patch.object(env, "_run_git_command") as mock_git:
            mock_git.return_value = ""
            result = env.git_main_branch
        assert result == "main"


class TestGitRecentCommits:
    """Test the git_recent_commits property."""

    def test_returns_recent_commits(self):
        env = _make_env_info()
        commits = "abc1234 First commit\ndef5678 Second commit"
        with patch.object(env, "_run_git_command") as mock_git:
            mock_git.return_value = commits
            result = env.git_recent_commits
        assert result == commits
        mock_git.assert_called_once_with(["git", "log", "--oneline", "-n", "5"])

    def test_returns_empty_for_no_commits(self):
        env = _make_env_info()
        with patch.object(env, "_run_git_command") as mock_git:
            mock_git.return_value = ""
            result = env.git_recent_commits
        assert result == ""


class TestModelName:
    """Test the model_name property."""

    def test_returns_model_and_provider(self):
        env = _make_env_info()
        result = env.model_name
        assert result == "test-model from test-provider"
