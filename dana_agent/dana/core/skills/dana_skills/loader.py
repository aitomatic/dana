"""
Skill Loader - Discovery and registry for Dana skills.

Scans configured directories for SKILL.md files and maintains
a registry of available skills. Only metadata is loaded at startup;
full content is lazy-loaded on invocation.
"""

from pathlib import Path

from structlog import get_logger

from .models import DanaSkill, parse_skill_md


logger = get_logger()


class SkillLoader:
    """
    Discovers and manages skill registry.

    Default discovery directories:
    - ~/.dana/skills/ - User Dana skills
    - ./.dana/skills/ - Project Dana skills
    - ~/.claude/skills/ - User Claude Code skills (compatibility)
    - ./.claude/skills/ - Project Claude Code skills (compatibility)
    """

    DEFAULT_SKILL_DIRS = [
        Path.home() / ".dana" / "skills",
        Path.cwd() / ".dana" / "skills",
        Path.home() / ".claude" / "skills",
        Path.cwd() / ".claude" / "skills",
    ]

    def __init__(
        self,
        skill_dirs: list[Path] | None = None,
        auto_discover: bool = True,
    ):
        """
        Initialize the skill loader.

        Args:
            skill_dirs: Custom list of directories to scan for skills.
                        If None, uses DEFAULT_SKILL_DIRS.
            auto_discover: Whether to automatically discover skills on init.
        """
        self._skill_dirs = skill_dirs or self.DEFAULT_SKILL_DIRS
        self._skills: dict[str, DanaSkill] = {}

        if auto_discover:
            self.discover()

    def discover(self) -> dict[str, DanaSkill]:
        """
        Scan directories for SKILL.md files.

        Only parses frontmatter (name, description). Full content
        is lazy-loaded when the skill is invoked.

        Returns:
            Dictionary of skill name -> DanaSkill
        """
        for skill_dir in self._skill_dirs:
            if not skill_dir.exists():
                continue
            for skill_path in skill_dir.iterdir():
                if skill_path.is_dir():
                    skill_md = skill_path / "SKILL.md"
                    if skill_md.exists():
                        skill = parse_skill_md(skill_md)
                        if skill and skill.name not in self._skills:
                            self._skills[skill.name] = skill
                            logger.debug("discovered_skill", name=skill.name, path=str(skill_md))

        logger.info("skills_discovered", count=len(self._skills))
        return self._skills

    def get_skill(self, name: str) -> DanaSkill | None:
        """
        Get a skill by name.

        Args:
            name: Skill name (directory name containing SKILL.md)

        Returns:
            DanaSkill if found, None otherwise
        """
        return self._skills.get(name)

    def list_skills(self) -> list[DanaSkill]:
        """
        List all discovered skills.

        Returns:
            List of all DanaSkill objects
        """
        return list(self._skills.values())

    def list_model_invocable(self) -> list[DanaSkill]:
        """
        List skills that can be invoked by the LLM.

        Skills with disable_model_invocation=True are excluded.

        Returns:
            List of DanaSkill objects that can be model-invoked
        """
        return [skill for skill in self._skills.values() if not skill.disable_model_invocation]

    def get_prompt_descriptions(self, budget_chars: int = 15000) -> str:
        """
        Generate skill descriptions for system prompt (labels only).

        Creates a compact list of skill names and descriptions
        suitable for including in the system prompt. Only includes
        skills that can be model-invoked (excludes disabled skills).

        Args:
            budget_chars: Maximum character budget for descriptions

        Returns:
            Formatted string of skill descriptions
        """
        model_invocable = self.list_model_invocable()
        if not model_invocable:
            return ""

        lines = []
        total_chars = 0

        for skill in sorted(model_invocable, key=lambda s: s.name):
            line = f"- {skill.name}: {skill.description}"
            if total_chars + len(line) > budget_chars:
                lines.append(f"... and {len(model_invocable) - len(lines)} more skills")
                break
            lines.append(line)
            total_chars += len(line) + 1

        return "\n".join(lines)
