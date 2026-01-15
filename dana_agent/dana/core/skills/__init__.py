"""Claude Skills integration via Claude Code CLI.

Skills are ontological elements - reusable, composable capabilities that
define what an agent can do. This module provides the ClaudeCodeSkills
resource which discovers and exposes Claude Code skills to STARAgents.
"""

from .claude_code_skills import ClaudeCodeSkills

__all__ = ["ClaudeCodeSkills"]
