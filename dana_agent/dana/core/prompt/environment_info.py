"""Environment and git information provider for prompt templates.

Extracts environment/git/scratchpad properties from LocalPromptAPI into a
standalone, testable class. Properties are resolved via {{variable}} template
syntax in LocalPromptAPI.render().
"""

from datetime import date
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from dana.core.agent.base_agent import BaseAgent


class EnvironmentInfo:
    """Provides environment, git, and scratchpad info for prompt templates.

    Properties are read-only getters with no coupling to prompt logic.
    Note: scratchpad_directory creates dirs on access (side effect by design).
    Used by ExploreAgent and DanaCodingAgent templates via {{variable}} resolution.

    Args:
        agent: The agent instance (needed for llm_client, _session_id).
        relative_path: The codec-relative path for scratchpad directory construction.
    """

    def __init__(self, agent: "BaseAgent", relative_path: str):
        self._agent = agent
        self._relative_path = relative_path

    def _run_git_command(self, cmd: list[str], default: str = "") -> str:
        """Run a git command and return stdout, or default on failure."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.getcwd(),
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return default
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return default

    @property
    def environment_info(self) -> str:
        """Generate environment information for system prompt."""
        working_dir = os.getcwd()
        is_git_repo = os.path.isdir(os.path.join(working_dir, ".git"))
        is_git_str = "Yes" if is_git_repo else "No"
        plat = sys.platform
        os_version = f"{platform.system()} {platform.release()}"
        today = date.today().isoformat()

        return f"""Working directory: {working_dir}
Is directory a git repo: {is_git_str}
Platform: {plat}
OS Version: {os_version}
Today's date: {today}"""

    @property
    def model_name(self) -> str:
        return f"{self._agent.llm_client.model} from {self._agent.llm_client.provider_name}"

    @property
    def git_status(self) -> str:
        return self._run_git_command(["git", "status", "--porcelain"])

    @property
    def git_current_branch(self) -> str:
        branch = self._run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return branch if branch else "unknown"

    @property
    def git_main_branch(self) -> str:
        result = self._run_git_command(["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
        if result:
            return result.split("/")[-1]
        branches = self._run_git_command(["git", "branch", "--list", "main", "master"])
        if "main" in branches:
            return "main"
        if "master" in branches:
            return "master"
        return "main"

    @property
    def git_recent_commits(self) -> str:
        return self._run_git_command(["git", "log", "--oneline", "-n", "5"])

    @property
    def scratchpad_directory(self) -> str:
        # Deferred to avoid circular import at module level
        from dana.config.storage_config import FileStorageConfig

        workspace_folder = Path(FileStorageConfig().workspace_folder)

        relative_prompt_path = Path(self._relative_path)
        _session_id = getattr(self._agent, "_session_id", str(uuid4()))
        tmp_path = workspace_folder / relative_prompt_path.parent / "tmp" / _session_id / "scratchpad"
        tmp_path.mkdir(parents=True, exist_ok=True)
        return str(tmp_path.absolute())
