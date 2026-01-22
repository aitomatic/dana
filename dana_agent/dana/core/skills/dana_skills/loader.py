"""
Skill Loader - Discovery and registry for Dana skills.

Discovers skills from standard directories and provides access by name.
Compatible with both Dana (.dana/skills) and Claude Code (.claude/skills) locations.
"""

from __future__ import annotations

from pathlib import Path

import structlog

from .models import DanaSkill, parse_skill_md


logger = structlog.get_logger()


# Default directories to search for skills (priority order: later overrides earlier)
DEFAULT_SKILL_DIRS = [
    Path.home() / ".dana" / "skills",
    Path.cwd() / ".dana" / "skills",
    Path.home() / ".claude" / "skills",  # Claude Code compatibility
    Path.cwd() / ".claude" / "skills",  # Claude Code compatibility
]


class SkillLoader:
    """Discover and manage Dana skills.

    Scans configured directories for SKILL.md files and provides access by name.
    Skills in later directories override earlier ones with the same name.

    Usage:
        # Default discovery
        loader = SkillLoader()
        skill = loader.get_skill("my-skill")

        # Custom directories
        loader = SkillLoader(skill_dirs=[Path("./custom-skills")])

        # Get all user-invocable skills
        for skill in loader.list_user_invocable():
            print(f"/{skill.name} - {skill.description}")
    """

    def __init__(
        self,
        skill_dirs: list[Path] | None = None,
        auto_discover: bool = True,
    ):
        """Initialize the skill loader.

        Args:
            skill_dirs: List of directories to search for skills.
                       If None, uses DEFAULT_SKILL_DIRS.
            auto_discover: Whether to discover skills on initialization (default: True)
        """
        self._skill_dirs = skill_dirs if skill_dirs is not None else DEFAULT_SKILL_DIRS.copy()
        self._skills: dict[str, DanaSkill] = {}

        if auto_discover:
            self.discover()

    def discover(self) -> dict[str, DanaSkill]:
        """Discover skills from configured directories.

        Scans each directory for subdirectories containing SKILL.md files.
        Later directories override earlier ones with the same skill name.

        Returns:
            Dictionary mapping skill names to DanaSkill objects
        """
        self._skills.clear()

        for skill_dir in self._skill_dirs:
            if not skill_dir.exists() or not skill_dir.is_dir():
                continue

            logger.debug("Scanning for skills", directory=str(skill_dir))

            for item in skill_dir.iterdir():
                if not item.is_dir():
                    continue

                skill_md = item / "SKILL.md"
                if not skill_md.exists():
                    continue

                try:
                    skill = parse_skill_md(skill_md)
                    self._skills[skill.name] = skill
                    logger.debug("Discovered skill", name=skill.name, path=str(skill_md))
                except Exception as e:
                    logger.warning("Failed to parse skill", path=str(skill_md), error=str(e))

        logger.info("Skill discovery complete", count=len(self._skills))
        return self._skills.copy()

    def get_skill(self, name: str) -> DanaSkill | None:
        """Get a skill by name.

        Args:
            name: Skill name (case-sensitive)

        Returns:
            DanaSkill if found, None otherwise
        """
        return self._skills.get(name)

    def list_skills(self) -> list[DanaSkill]:
        """List all discovered skills.

        Returns:
            List of all DanaSkill objects
        """
        return list(self._skills.values())

    def list_user_invocable(self) -> list[DanaSkill]:
        """List skills that are user-invocable (shown in /slash menu).

        Returns:
            List of skills where user_invocable=True
        """
        return [skill for skill in self._skills.values() if skill.user_invocable]

    def list_model_invocable(self) -> list[DanaSkill]:
        """List skills that can be auto-invoked by the agent.

        Returns:
            List of skills where disable_model_invocation=False
        """
        return [skill for skill in self._skills.values() if not skill.disable_model_invocation]

    def get_prompt_descriptions(self, budget_chars: int = 15000) -> str:
        """Generate skill descriptions for inclusion in system prompt.

        Creates a formatted string listing available skills, truncated to budget.

        Args:
            budget_chars: Maximum characters to use (default: 15000)

        Returns:
            Formatted skill descriptions string
        """
        model_skills = self.list_model_invocable()
        if not model_skills:
            return "No skills available."

        lines = ["Available skills:"]
        total_chars = len(lines[0])

        for skill in sorted(model_skills, key=lambda s: s.name):
            line = f"- {skill.name}: {skill.description}"

            # Truncate description if needed
            if len(line) > 200:
                line = line[:197] + "..."

            if total_chars + len(line) + 1 > budget_chars:
                lines.append("- (additional skills truncated)")
                break

            lines.append(line)
            total_chars += len(line) + 1

        return "\n".join(lines)

    def add_skill_dir(self, path: Path) -> None:
        """Add a skill directory and re-discover.

        Args:
            path: Directory path to add
        """
        if path not in self._skill_dirs:
            self._skill_dirs.append(path)
            self.discover()

    def filter_by_names(self, names: list[str]) -> SkillLoader:
        """Create a new loader with only the specified skills.

        Useful for creating filtered loaders for nested skill access.

        Args:
            names: List of skill names to include

        Returns:
            New SkillLoader with filtered skills
        """
        filtered = SkillLoader(skill_dirs=[], auto_discover=False)
        filtered._skills = {name: skill for name, skill in self._skills.items() if name in names}
        return filtered

    def __len__(self) -> int:
        """Return number of discovered skills."""
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        """Check if a skill exists by name."""
        return name in self._skills

    def __iter__(self):
        """Iterate over skills."""
        return iter(self._skills.values())
