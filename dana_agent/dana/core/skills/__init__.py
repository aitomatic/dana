"""Dana Skills - Composable task templates for agents."""

from .claude_code_skills import ClaudeCodeSkills
from .dana_skills import DanaSkill, DanaSkills, SkillLoader, parse_skill_md


# Backward compatibility alias
SkillResource = DanaSkills

__all__ = ["ClaudeCodeSkills", "DanaSkill", "parse_skill_md", "SkillLoader", "DanaSkills", "SkillResource"]
