"""
Dana Skill - Composable task template data structure.

Fully compatible with Claude Code's SKILL.md schema for interoperability.
Skills define reusable task templates that execute within Dana agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import structlog


logger = structlog.get_logger()


@dataclass
class DanaSkill:
    """Skill definition compatible with Claude Code SKILL.md schema.

    Required fields:
        name: Skill identifier (lowercase, hyphens)
        description: When to trigger + keywords (max 1024 chars)
        path: Path to the SKILL.md file

    Execution fields:
        context_mode: "main" (default) or "fork" for isolated subagent
        agent: Subagent type for fork mode (Explore, Plan, general-purpose)
        model: Override LLM model for this skill

    Tool/Skill access:
        allowed_tools: List of tool patterns (None = all tools)
        allowed_skills: List of nested skills accessible in fork mode

    Visibility:
        user_invocable: Show in /slash menu (default: True)
        disable_model_invocation: Block auto-use by agent (default: False)

    Future:
        hooks: Lifecycle scripts (PreToolUse, PostToolUse, Stop)
    """

    # Required
    name: str
    description: str
    path: Path

    # Execution
    context_mode: Literal["main", "fork"] = "main"
    agent: str | None = None  # Explore, Plan, general-purpose
    model: str | None = None  # Override LLM model

    # Tools & Skills
    allowed_tools: list[str] | None = None  # None = all tools
    allowed_skills: list[str] | None = None  # For nested skill access

    # Visibility
    user_invocable: bool = True
    disable_model_invocation: bool = False

    # Hooks (future)
    hooks: dict | None = None

    # Lazy content loading
    _content: str | None = field(default=None, repr=False)

    @property
    def content(self) -> str:
        """Lazy-load skill content (body after frontmatter) from disk."""
        if self._content is None:
            try:
                raw = self.path.read_text(encoding="utf-8")
                _, body = _split_frontmatter(raw)
                self._content = body.strip()
            except Exception as e:
                logger.warning("Failed to load skill content", path=str(self.path), error=str(e))
                self._content = ""
        return self._content

    @property
    def scripts_dir(self) -> Path | None:
        """Return scripts/ directory if exists next to SKILL.md."""
        scripts_path = self.path.parent / "scripts"
        if scripts_path.is_dir():
            return scripts_path
        return None

    def substitute_arguments(self, arguments: str, session_id: str = "") -> str:
        """Substitute $ARGUMENTS and ${CLAUDE_SESSION_ID} in content.

        Args:
            arguments: Value to substitute for $ARGUMENTS
            session_id: Value to substitute for ${CLAUDE_SESSION_ID}

        Returns:
            Content with substitutions applied
        """
        result = self.content
        result = result.replace("$ARGUMENTS", arguments)
        result = result.replace("${CLAUDE_SESSION_ID}", session_id)
        return result


def parse_skill_md(path: Path) -> DanaSkill:
    """Parse a SKILL.md file into a DanaSkill object.

    Args:
        path: Path to SKILL.md file

    Returns:
        DanaSkill with parsed fields

    Raises:
        ValueError: If required fields are missing
    """
    raw = path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(raw)
    metadata = _parse_frontmatter(frontmatter)

    # Required fields
    name = metadata.get("name")
    if not name:
        # Fall back to directory name
        name = path.parent.name

    description = metadata.get("description", "")
    if len(description) > 1024:
        description = description[:1024]

    # Execution fields
    context_mode = metadata.get("context", "main")
    if context_mode not in ("main", "fork"):
        context_mode = "main"

    agent = metadata.get("agent")
    model = metadata.get("model")

    # Tools & Skills
    allowed_tools = _parse_tools_list(metadata.get("allowed-tools"))
    allowed_skills = _parse_skills_list(metadata.get("skills"))

    # Visibility
    user_invocable = metadata.get("user-invocable", True)
    if isinstance(user_invocable, str):
        user_invocable = user_invocable.lower() in ("true", "yes", "1")

    disable_model_invocation = metadata.get("disable-model-invocation", False)
    if isinstance(disable_model_invocation, str):
        disable_model_invocation = disable_model_invocation.lower() in ("true", "yes", "1")

    # Hooks (future)
    hooks = metadata.get("hooks")

    return DanaSkill(
        name=name,
        description=description,
        path=path,
        context_mode=context_mode,
        agent=agent,
        model=model,
        allowed_tools=allowed_tools,
        allowed_skills=allowed_skills,
        user_invocable=user_invocable,
        disable_model_invocation=disable_model_invocation,
        hooks=hooks,
        _content=body.strip(),
    )


def _split_frontmatter(content: str) -> tuple[str, str]:
    """Split content into YAML frontmatter and body.

    Args:
        content: Raw SKILL.md content

    Returns:
        Tuple of (frontmatter_str, body_str)
    """
    content = content.strip()

    if not content.startswith("---"):
        return "", content

    # Find closing ---
    lines = content.split("\n")
    end_idx = -1
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return "", content

    frontmatter = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :])

    return frontmatter, body


def _parse_frontmatter(frontmatter: str) -> dict:
    """Parse YAML frontmatter into a dictionary.

    Uses a simple parser to avoid PyYAML dependency.
    Handles basic key: value pairs and nested hooks structure.

    Args:
        frontmatter: YAML frontmatter string (without --- delimiters)

    Returns:
        Dictionary of parsed fields
    """
    if not frontmatter.strip():
        return {}

    try:
        import yaml

        return yaml.safe_load(frontmatter) or {}
    except ImportError:
        pass

    # Simple fallback parser for basic key: value pairs
    result = {}
    for line in frontmatter.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ": " in line:
            key, value = line.split(": ", 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            # Parse booleans
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False

            result[key] = value

    return result


def _parse_tools_list(tools_str: str | None) -> list[str] | None:
    """Parse allowed-tools string into list of patterns.

    Args:
        tools_str: Comma-separated tool patterns (e.g., "Read, Grep, Bash(git:*)")

    Returns:
        List of tool patterns, or None if not specified
    """
    if not tools_str:
        return None

    if isinstance(tools_str, list):
        return tools_str

    tools = []
    for tool in tools_str.split(","):
        tool = tool.strip()
        if tool:
            tools.append(tool)

    return tools if tools else None


def _parse_skills_list(skills_str: str | None) -> list[str] | None:
    """Parse skills string into list of skill names.

    Args:
        skills_str: Comma-separated skill names

    Returns:
        List of skill names, or None if not specified
    """
    if not skills_str:
        return None

    if isinstance(skills_str, list):
        return skills_str

    skills = []
    for skill in skills_str.split(","):
        skill = skill.strip()
        if skill:
            skills.append(skill)

    return skills if skills else None
