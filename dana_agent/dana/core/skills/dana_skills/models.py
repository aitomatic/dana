"""
Dana Skill - Skill definition and parsing.

Skills are composable task templates that extend agent capabilities.
At startup, only metadata (name, description) is loaded. Full content
is loaded on-demand when the skill is invoked.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Literal


@dataclass
class DanaSkill:
    """
    Skill definition - only metadata loaded at startup, content lazy-loaded.

    Supports two formats:
    1. YAML frontmatter (Claude Code style):
       ---
       name: skill-name
       description: Brief description
       context: fork
       allowed-tools: tool1, tool2
       disable-model-invocation: true
       ---

    2. Legacy inline format:
       # Skill Name
       Description (first non-heading line)
       context: fork
       allowed-tools: [tool1, tool2]
    """

    name: str  # Skill identifier (from directory name or frontmatter)
    description: str  # Brief description (max 200 chars)
    path: Path  # Path to SKILL.md
    context_mode: Literal["main", "fork"] = "main"  # Fork creates isolated context
    allowed_tools: list[str] | None = None  # Tool whitelist (None = all)
    allowed_skills: list[str] | None = None  # Skills this skill can invoke (None = none)
    disable_model_invocation: bool = False  # Whether this skill should be hidden from LLM

    # Lazy-loaded properties
    _content: str | None = field(default=None, repr=False)

    @property
    def content(self) -> str:
        """Load full SKILL.md content on demand."""
        if self._content is None:
            content = self.path.read_text()
            object.__setattr__(self, "_content", content)
            return content
        return self._content

    @property
    def scripts_dir(self) -> Path | None:
        """Path to scripts/ folder if it exists."""
        scripts = self.path.parent / "scripts"
        return scripts if scripts.exists() else None


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """
    Extract YAML frontmatter from content.

    Args:
        content: Full file content

    Returns:
        Tuple of (frontmatter dict, remaining content)
    """
    frontmatter: dict[str, str] = {}
    remaining = content

    # Check for YAML frontmatter (starts with ---)
    if content.startswith("---"):
        lines = content.split("\n")
        end_idx = -1

        # Find closing ---
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_idx = i
                break

        if end_idx > 0:
            # Parse frontmatter lines
            for line in lines[1:end_idx]:
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()

            # Remaining content after frontmatter
            remaining = "\n".join(lines[end_idx + 1 :]).strip()

    return frontmatter, remaining


def _parse_tools_list(value: str) -> list[str]:
    """
    Parse allowed-tools value (supports both formats).

    Formats:
    - Bracketed: [tool1, tool2]
    - Comma-separated: tool1, tool2

    Args:
        value: Raw value string

    Returns:
        List of tool patterns
    """
    # Remove brackets if present
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]

    # Split by comma and clean up
    return [t.strip() for t in value.split(",") if t.strip()]


def parse_skill_md(skill_md_path: Path) -> DanaSkill | None:
    """
    Parse SKILL.md supporting both YAML frontmatter and legacy formats.

    YAML Frontmatter Format (preferred):
        ---
        name: skill-name
        description: Brief description of the skill
        context: fork
        allowed-tools: bash:*, file:read
        skills: nested-skill1, nested-skill2
        ---

        # Skill Title
        ...instructions...

    Legacy Format:
        # Skill Name

        Description paragraph (first non-empty paragraph after heading).

        context: fork
        allowed-tools: [tool1, tool2]

    Args:
        skill_md_path: Path to SKILL.md file

    Returns:
        DanaSkill if successfully parsed, None otherwise
    """
    try:
        content = skill_md_path.read_text()

        # Try YAML frontmatter first
        frontmatter, body = _parse_frontmatter(content)

        # Name: frontmatter > directory name
        name = frontmatter.get("name") or skill_md_path.parent.name

        # Description: frontmatter > first non-heading line in body
        description = frontmatter.get("description", "")
        if not description:
            for line in body.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("---"):
                    description = line[:200]
                    break

        # Context mode: frontmatter > pattern match in content
        context_mode: Literal["main", "fork"] = "main"
        if frontmatter.get("context") == "fork" or "context: fork" in content:
            context_mode = "fork"

        # Allowed tools: frontmatter > bracketed pattern in content
        allowed_tools = None
        if "allowed-tools" in frontmatter:
            allowed_tools = _parse_tools_list(frontmatter["allowed-tools"])
        else:
            tools_match = re.search(r"allowed-tools:\s*\[([^\]]+)\]", content)
            if tools_match:
                allowed_tools = _parse_tools_list(tools_match.group(1))

        # Allowed skills: frontmatter > bracketed pattern in content
        allowed_skills = None
        if "skills" in frontmatter:
            allowed_skills = _parse_tools_list(frontmatter["skills"])
        else:
            skills_match = re.search(r"skills:\s*\[([^\]]+)\]", content)
            if skills_match:
                allowed_skills = _parse_tools_list(skills_match.group(1))

        # Disable model invocation: frontmatter only
        disable_model_invocation = False
        if frontmatter.get("disable-model-invocation", "").lower() == "true":
            disable_model_invocation = True

        return DanaSkill(
            name=name,
            description=description,
            path=skill_md_path,
            context_mode=context_mode,
            allowed_tools=allowed_tools,
            allowed_skills=allowed_skills,
            disable_model_invocation=disable_model_invocation,
        )
    except Exception:
        return None
