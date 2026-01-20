"""
ClaudeCodeSkills - Execute tasks using Claude Code skills via subprocess.

This resource discovers available skills from ~/.claude/skills/ and exposes
them to the agent's LLM for informed decision-making. Skills are ontological
elements that can be composed to create domain-specific agents.

Part of Dana's Cognitive Ontology vision.
"""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING

from structlog import get_logger

from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


if TYPE_CHECKING:
    from dana.common.protocols import Notifier

logger = get_logger()


class ClaudeCodeSkills(BaseResource):
    """Execute tasks using Claude Code skills via subprocess.

    This resource discovers available skills from ~/.claude/skills/ and
    exposes them to the agent's LLM for informed decision-making.

    Skills are ontological elements - composable capabilities that can be:
    - Discovered automatically (greedy default)
    - Filtered for specialized agents
    - Combined to create domain-specific agents

    Skills execute in a separate Claude Code process. Context from the
    current conversation must be passed explicitly via the context parameter.

    Usage:
        # Greedy default - all discovered skills
        skills = ClaudeCodeSkills()

        # Filtered - document skills only
        skills = ClaudeCodeSkills(skills=["pptx", "docx", "pdf"])

        # Custom skills directory
        skills = ClaudeCodeSkills(skills_dir="~/my-skills")
    """

    def __init__(
        self,
        skills: list[str] | None = None,
        skills_dir: str = "~/.claude/skills",
        output_dir: str = "./skill_output",
        timeout: int = 300,
        disable_session_persistence: bool = False,
        resource_id: str = "claude-skills",
        thought_callback: Callable[[str, str], None] | None = None,
        notifier: Notifier | None = None,
        streaming: bool = True,
        **kwargs,
    ):
        """
        Args:
            skills: List of skill names to expose. None = all discovered (greedy).
                Example: ["pptx", "xlsx"] for document specialist agent.
            skills_dir: Directory to discover skills from (default: ~/.claude/skills)
            output_dir: Default directory for skill output files
            timeout: Execution timeout in seconds (default: 300)
            disable_session_persistence: Disable Claude Code session persistence
            resource_id: Resource identifier
            thought_callback: Optional callback for progress/thought logging.
                Called with (phase, message) where phase is one of:
                'init', 'discover', 'execute', 'complete', 'error'
            notifier: Optional Notifier (agent) to broadcast progress messages to.
                When provided, progress will be displayed in the agent's thought log.
            streaming: Use streaming JSON output for real-time progress (default: True).
                Set to False for simpler subprocess.run behavior (useful for tests).
        """
        self._thought_callback = thought_callback
        self._notifier = notifier
        self._streaming = streaming
        self._log_thought("init", f"Initializing ClaudeCodeSkills with skills_dir={skills_dir}")

        self._skills_dir = Path(skills_dir).expanduser()
        self._output_dir = output_dir
        self._timeout = timeout
        self._disable_session_persistence = disable_session_persistence
        self._available = self._check_claude_available()

        if self._available:
            self._log_thought("init", "Claude Code CLI is available")
        else:
            self._log_thought("init", "Claude Code CLI is NOT available - skills will be disabled")

        self._all_skills = self._discover_skills()
        self._skills = self._filter_skills(skills) if skills else self._all_skills

        skill_names = [s["name"] for s in self._skills]
        self._log_thought("init", f"Initialized with {len(self._skills)} skills: {skill_names}")

        super().__init__(resource_type="claude-skills", resource_id=resource_id, **kwargs)

        self.execute.__func__.__doc__ = self.get_execute_docstring()

    def _log_thought(self, phase: str, message: str) -> None:
        """Log a thought/progress message.

        Args:
            phase: The current phase ('init', 'discover', 'execute', 'complete', 'error')
            message: The thought/progress message
        """
        # Always log to structlog
        logger.info(message, phase=phase, resource="claude-skills")

        # Broadcast through notifier if available (for agent UI display)
        notifier = getattr(self, "_notifier", None)
        if notifier and hasattr(notifier, "broadcast"):
            try:
                notifier.broadcast(
                    {
                        "skill_progress": {
                            "skill_id": "claude-skills",
                            "phase": phase,
                            "message": message,
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"Notifier broadcast failed: {e}")

        # Also call callback if provided (check for attribute existence for test compatibility)
        callback = getattr(self, "_thought_callback", None)
        if callback:
            try:
                callback(phase, message)
            except Exception as e:
                logger.warning(f"Thought callback failed: {e}")

    def _check_claude_available(self) -> bool:
        """Check if Claude Code CLI is installed."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _discover_skills(self) -> list[dict]:
        """Discover skills from skills_dir.

        Scans the skills directory for subdirectories containing SKILL.md files.
        Parses each SKILL.md to extract the skill name and description.

        Returns:
            List of skill dicts: [{"name": "pptx", "description": "..."}, ...]
        """
        skills: list[dict] = []

        self._log_thought("discover", f"Scanning for skills in {self._skills_dir}")

        if not self._skills_dir.exists():
            self._log_thought("discover", f"Skills directory does not exist: {self._skills_dir}")
            return skills

        for skill_path in self._skills_dir.iterdir():
            if not skill_path.is_dir():
                continue
            skill_md = skill_path / "SKILL.md"
            if not skill_md.exists():
                continue
            description = self._parse_skill_description(skill_md)
            skills.append(
                {
                    "name": skill_path.name,
                    "description": description,
                }
            )
            self._log_thought("discover", f"Found skill: {skill_path.name}")

        self._log_thought("discover", f"Discovered {len(skills)} total skills")
        return skills

    def _parse_skill_description(self, skill_md: Path) -> str:
        """Extract description from SKILL.md file.

        Looks for the first non-empty, non-heading line or the first heading.

        Args:
            skill_md: Path to SKILL.md file

        Returns:
            Description string (truncated to 200 chars)
        """
        try:
            content = skill_md.read_text()
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    return line[:200]
                if line.startswith("# "):
                    return line[2:][:200]
            return "Claude Code skill"
        except Exception:
            return "Claude Code skill"

    def _filter_skills(self, skill_names: list[str]) -> list[dict]:
        """Filter discovered skills to only those in skill_names.

        Args:
            skill_names: List of skill names to include

        Returns:
            Filtered list of skill dicts
        """
        return [skill for skill in self._all_skills if skill["name"] in skill_names]

    def _format_skills_for_docstring(self) -> str:
        """Format skills list for inclusion in execute() docstring.

        Returns:
            Formatted string listing available skills
        """
        if not self._skills:
            return "No skills available."

        return "\n".join([f"- {skill['name']}: {skill['description']}" for skill in self._skills])

    def _home_writable(self) -> bool:
        home = Path.home()
        if not os.access(home, os.W_OK):
            return False
        config_path = home / ".claude.json"
        if config_path.exists() and not os.access(config_path, os.W_OK):
            return False
        test_path = home / f".claude_write_test_{os.getpid()}"
        try:
            with open(test_path, "w", encoding="utf-8"):
                pass
            test_path.unlink(missing_ok=True)
        except OSError:
            try:
                test_path.unlink()
            except OSError:
                pass
            return False
        return True

    def _sync_claude_config_dir(self, target_dir: Path) -> None:
        """Populate a writable Claude config dir with config and skills."""
        source_home = Path.home()
        config_src = source_home / ".claude.json"
        config_dest = target_dir / ".claude.json"
        if config_src.exists():
            shutil.copyfile(config_src, config_dest)

        settings_src = source_home / ".claude" / "settings.json"
        settings_dest = target_dir / "settings.json"
        if settings_src.exists():
            shutil.copyfile(settings_src, settings_dest)

        skills_src = source_home / ".claude" / "skills"
        skills_dest = target_dir / "skills"
        if skills_src.exists():
            skills_dest.parent.mkdir(parents=True, exist_ok=True)
            if not skills_dest.exists():
                try:
                    os.symlink(skills_src, skills_dest)
                except OSError:
                    shutil.copytree(skills_src, skills_dest, dirs_exist_ok=True)

    def _sync_keychain_credentials(self, target_dir: Path) -> None:
        """Copy Claude Code keychain credentials to a new config dir (macOS only)."""
        if sys.platform != "darwin":
            return

        account = os.environ.get("USER")
        if not account:
            return

        source_service = "Claude Code-credentials"
        hashed = hashlib.sha256(str(target_dir).encode()).hexdigest()[:8]
        target_service = f"{source_service}-{hashed}"
        if target_service == source_service:
            return

        try:
            read = subprocess.run(
                ["security", "find-generic-password", "-a", account, "-s", source_service, "-w"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            return

        secret = read.stdout.strip()
        if not secret:
            return

        subprocess.run(
            ["security", "add-generic-password", "-U", "-a", account, "-s", target_service, "-w", secret],
            capture_output=True,
            text=True,
        )

    @property
    def enabled(self) -> bool:
        """Whether Claude Code is available and skills were discovered."""
        return self._available and len(self._skills) > 0

    @property
    def skills(self) -> list[dict]:
        """List of available skills."""
        return self._skills

    @property
    def all_skills(self) -> list[dict]:
        """List of all discovered skills (before filtering)."""
        return self._all_skills

    @property
    def disable_session_persistence(self) -> bool:
        """Whether Claude Code session persistence is disabled."""
        return self._disable_session_persistence

    def _build_execution_env(self) -> tuple[dict, str | None]:
        """Build environment variables for Claude Code subprocess.

        Returns:
            Tuple of (env dict without API key, extracted API key or None)
        """
        env = dict(os.environ)
        api_key = env.pop("ANTHROPIC_API_KEY", None)
        env.setdefault("CLAUDE_CODE_DISABLE_ATTACHMENTS", "1")
        env.setdefault("CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL", "true")
        env.setdefault("CHOKIDAR_USEPOLLING", "1")
        env.setdefault("CHOKIDAR_INTERVAL", "500")
        env.setdefault("WATCHPACK_POLLING", "true")
        return env, api_key

    def _build_command(self, prompt: str, output_path: Path, env: dict, streaming: bool = True) -> list[str]:
        """Build the Claude CLI command with appropriate flags.

        Args:
            prompt: The prompt to send to Claude
            output_path: Path for output files and config
            env: Environment dict to modify if using custom config dir
            streaming: Whether to use streaming JSON output (default: True)

        Returns:
            Command list ready for subprocess
        """
        cmd = ["claude", "--dangerously-skip-permissions"]

        if self._disable_session_persistence:
            cmd.append("--no-session-persistence")

        use_config_dir = self._disable_session_persistence or not self._home_writable()
        if use_config_dir:
            claude_config_dir = output_path.resolve() / ".claude_config"
            claude_config_dir.mkdir(parents=True, exist_ok=True)
            self._sync_claude_config_dir(claude_config_dir)
            self._sync_keychain_credentials(claude_config_dir)
            env["CLAUDE_CONFIG_DIR"] = str(claude_config_dir)
            env["HOME"] = str(claude_config_dir)

        # Add streaming output flags for real-time progress
        if streaming:
            cmd.extend(["--output-format", "stream-json", "--verbose"])

        cmd.extend(["-p", prompt])
        return cmd

    def _get_preexec_fn(self):
        """Get preexec function to raise file descriptor limits on Unix."""
        if os.name == "nt":
            return None

        def _raise_nofile_limit() -> None:
            try:
                import resource

                soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
                target = min(max(soft, 16384), hard)
                if target > soft:
                    resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
            except Exception:
                pass

        return _raise_nofile_limit

    def _run_claude_subprocess(
        self,
        cmd: list[str],
        env: dict,
        cwd: str,
        preexec_fn,
    ) -> subprocess.CompletedProcess:
        """Run Claude Code subprocess with given parameters."""
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=self._timeout,
            cwd=cwd,
            preexec_fn=preexec_fn,
        )

    def _run_claude_subprocess_streaming(
        self,
        cmd: list[str],
        env: dict,
        cwd: str,
        preexec_fn,
    ) -> dict:
        """Run Claude Code subprocess with streaming JSON output.

        Parses stream-json events in real-time and logs progress.

        Returns:
            dict with 'success', 'output', 'error' keys
        """
        import json

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=cwd,
            preexec_fn=preexec_fn,
        )

        output_lines = []
        final_result = None
        assistant_content = []

        try:
            # Read stdout line by line for streaming JSON
            while True:
                # Check if process has finished
                if process.poll() is not None:
                    break

                line = process.stdout.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                output_lines.append(line)

                try:
                    event = json.loads(line)
                    event_type = event.get("type", "")

                    if event_type == "system":
                        subtype = event.get("subtype", "")
                        if subtype == "init":
                            model = event.get("model", "unknown")
                            self._log_thought("execute", f"Claude Code initialized (model: {model})")
                        elif subtype == "hook_response":
                            pass  # Ignore hook responses

                    elif event_type == "assistant":
                        # Extract content from assistant message
                        message = event.get("message", {})
                        content = message.get("content", [])
                        for item in content:
                            if item.get("type") == "text":
                                text = item.get("text", "")
                                if text:
                                    assistant_content.append(text)
                                    # Log a preview of what Claude is saying
                                    preview = text[:100] + "..." if len(text) > 100 else text
                                    self._log_thought("execute", f"Claude: {preview}")
                            elif item.get("type") == "tool_use":
                                tool_name = item.get("name", "unknown")
                                self._log_thought("execute", f"Claude using tool: {tool_name}")

                    elif event_type == "result":
                        final_result = event
                        is_error = event.get("is_error", False)
                        result_text = event.get("result", "")
                        if is_error:
                            self._log_thought("error", f"Claude Code error: {result_text[:200]}")
                        else:
                            duration_ms = event.get("duration_ms", 0)
                            self._log_thought("execute", f"Claude Code completed in {duration_ms}ms")

                    elif event_type == "user":
                        # This might indicate waiting for input
                        self._log_thought("execute", "Claude Code waiting for input...")

                except json.JSONDecodeError:
                    # Not JSON, might be stderr or other output
                    if line:
                        output_lines.append(line)

            # Wait for process to complete with timeout
            try:
                process.wait(timeout=self._timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                return {
                    "success": False,
                    "output": "\n".join(output_lines),
                    "error": f"Execution timed out after {self._timeout} seconds",
                }

            # Read any remaining stderr
            stderr = process.stderr.read() if process.stderr else ""

            # Build result
            if final_result:
                return {
                    "success": not final_result.get("is_error", False),
                    "output": final_result.get("result", ""),
                    "error": stderr if final_result.get("is_error") else "",
                }
            else:
                # No final result event, fall back to collected content
                return {
                    "success": process.returncode == 0,
                    "output": " ".join(assistant_content) if assistant_content else "\n".join(output_lines),
                    "error": stderr if process.returncode != 0 else "",
                }

        except Exception as e:
            process.kill()
            return {
                "success": False,
                "output": "\n".join(output_lines),
                "error": str(e),
            }

    def _extract_error_output(self, result: subprocess.CompletedProcess) -> str:
        """Extract error output from subprocess result."""
        if result.stderr:
            return result.stderr
        if result.returncode != 0:
            return result.stdout
        return ""

    def _should_retry_with_api_key(self, result: subprocess.CompletedProcess, api_key: str | None) -> bool:
        """Check if we should retry with ANTHROPIC_API_KEY."""
        if result.returncode == 0 or not api_key:
            return False

        error_output = self._extract_error_output(result)
        retry_triggers = ("Invalid API key", "Please run /login", "Connection error")
        return any(trigger in error_output for trigger in retry_triggers)

    def _build_result_dict(self, result: subprocess.CompletedProcess) -> dict:
        """Build standard result dictionary from subprocess result."""
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": self._extract_error_output(result),
        }

    @tool_use
    def execute(self, task: str, context: str = "") -> dict:
        """Execute a task using Claude Code skills.

        Available skills:
        {skills_list}

        Use ONLY when user needs one of these specific capabilities.
        Do NOT use for general questions, code generation, or tasks these skills can't handle.

        Args:
            task: What you want done. Include output file path if creating files.
                Example: "Create a 5-slide presentation about AI. Save to ./skill_output/ai.pptx"
            context: Relevant information from the conversation that the skill needs.
                Example: "User mentioned: Q4 revenue $5.2M, growth 23%"

        Returns:
            dict with:
            - success (bool): Whether the task completed successfully
            - output (str): Output from Claude Code (summary of what was done)
            - error (str): Error message if failed, empty string if successful
        """
        self._log_thought("execute", f"Starting skill execution for task: {task[:100]}...")

        if not self._available:
            self._log_thought("error", "Claude Code CLI is not available")
            return {
                "success": False,
                "output": "",
                "error": "Claude Code CLI is not installed. Install with: npm install -g @anthropic-ai/claude-code",
            }

        if not self._skills:
            self._log_thought("error", "No skills available to execute task")
            return {
                "success": False,
                "output": "",
                "error": "No skills available. Install skills in ~/.claude/skills/",
            }

        self._log_thought("execute", f"Available skills for this task: {[s['name'] for s in self._skills]}")

        prompt = f"Context from our conversation:\n{context}\n\nTask: {task}" if context else task
        output_path = Path(self._output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self._log_thought("execute", f"Output directory: {output_path.absolute()}")

        env, api_key = self._build_execution_env()
        use_streaming = getattr(self, "_streaming", True)
        cmd = self._build_command(prompt, output_path, env, streaming=use_streaming)
        cwd = str(output_path)
        preexec_fn = self._get_preexec_fn()

        self._log_thought("execute", f"Invoking Claude Code subprocess (timeout: {self._timeout}s)")

        try:
            if use_streaming:
                # Use streaming subprocess for real-time progress
                result_dict = self._run_claude_subprocess_streaming(cmd, env, cwd, preexec_fn)

                # Check if we need to retry with API key
                if not result_dict["success"] and api_key:
                    error = result_dict.get("error", "")
                    retry_triggers = ("Invalid API key", "Please run /login", "Connection error")
                    if any(trigger in error for trigger in retry_triggers):
                        self._log_thought("execute", "Retrying with API key authentication...")
                        env["ANTHROPIC_API_KEY"] = api_key
                        result_dict = self._run_claude_subprocess_streaming(cmd, env, cwd, preexec_fn)
            else:
                # Use simple subprocess.run (for tests/backwards compatibility)
                result = self._run_claude_subprocess(cmd, env, cwd, preexec_fn)
                self._log_thought("execute", f"Subprocess completed with return code: {result.returncode}")

                if self._should_retry_with_api_key(result, api_key):
                    self._log_thought("execute", "Retrying with API key authentication...")
                    env["ANTHROPIC_API_KEY"] = api_key
                    result = self._run_claude_subprocess(cmd, env, cwd, preexec_fn)
                    self._log_thought("execute", f"Retry completed with return code: {result.returncode}")

                result_dict = self._build_result_dict(result)

            if result_dict["success"]:
                self._log_thought("complete", "Task completed successfully")
                # Log a preview of the output (first 200 chars)
                output_preview = result_dict["output"][:200] if result_dict["output"] else "(no output)"
                self._log_thought("complete", f"Output preview: {output_preview}...")
            else:
                error_preview = result_dict["error"][:200] if result_dict["error"] else "(unknown error)"
                self._log_thought("error", f"Task failed: {error_preview}")

            return result_dict

        except subprocess.TimeoutExpired:
            self._log_thought("error", f"Execution timed out after {self._timeout} seconds")
            return {
                "success": False,
                "output": "",
                "error": f"Execution timed out after {self._timeout} seconds",
            }
        except Exception as exc:
            self._log_thought("error", f"Unexpected error: {exc}")
            return {
                "success": False,
                "output": "",
                "error": str(exc),
            }

    def get_execute_docstring(self) -> str:
        """Get the execute method's docstring with skills list populated."""
        base_doc = """Execute a task using Claude Code skills.

Available skills:
{skills_list}

Use ONLY when user needs one of these specific capabilities.
Do NOT use for general questions, code generation, or tasks these skills can't handle.

Args:
    task: What you want done. Include output file path if creating files.
        Example: "Create a 5-slide presentation about AI. Save to ./skill_output/ai.pptx"
    context: Relevant information from the conversation that the skill needs.
        Example: "User mentioned: Q4 revenue $5.2M, growth 23%"

Returns:
    dict with:
    - success (bool): Whether the task completed successfully
    - output (str): Output from Claude Code (summary of what was done)
    - error (str): Error message if failed, empty string if successful
"""
        return base_doc.format(skills_list=self._format_skills_for_docstring())
