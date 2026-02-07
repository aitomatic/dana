"""Unit tests for DanaSkills prompt context integration."""

from __future__ import annotations

from pathlib import Path

from dana.core.agent.star_agent import STARAgent
from dana.core.runtime.default import DefaultRuntime
from dana.core.skills.dana_skills.loader import SkillLoader
from dana.core.skills.dana_skills.skills import DanaSkillResource


class TestDanaSkillsPromptContext:
    """Tests for DanaSkills.get_prompt_context() method."""

    def test_get_prompt_context_with_skills(self, tmp_path: Path):
        """Test that get_prompt_context returns skill labels in correct format."""
        # Create test skill
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            """---
name: test-skill
description: A test skill for unit testing
---
This is the skill content.
"""
        )

        # Create loader and skills resource
        loader = SkillLoader(skill_dirs=[tmp_path])
        skills = DanaSkillResource(skill_loader=loader, auto_register=False)

        # Get prompt context
        context = skills.get_prompt_context()

        # Verify format
        assert '"available_skills"' in context
        assert '"name": "test-skill"' in context
        assert '"description": "A test skill for unit testing"' in context
        assert "skills:invoke" in context

    def test_get_prompt_context_empty_when_no_skills(self, tmp_path: Path):
        """Test that get_prompt_context returns empty string when no skills available."""
        # Create loader with empty directory
        loader = SkillLoader(skill_dirs=[tmp_path])
        skills = DanaSkillResource(skill_loader=loader, auto_register=False)

        context = skills.get_prompt_context()

        assert context == ""

    def test_get_prompt_context_excludes_disabled_model_invocation(self, tmp_path: Path):
        """Test that skills with disable-model-invocation=true are excluded."""
        # Create skill with model invocation disabled
        skill_dir = tmp_path / "disabled-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            """---
name: disabled-skill
description: A skill that should not be model-invocable
disable-model-invocation: true
---
This skill should be excluded.
"""
        )

        # Create enabled skill
        enabled_dir = tmp_path / "enabled-skill"
        enabled_dir.mkdir()
        (enabled_dir / "SKILL.md").write_text(
            """---
name: enabled-skill
description: A skill that should be model-invocable
---
This skill should be included.
"""
        )

        loader = SkillLoader(skill_dirs=[tmp_path])
        skills = DanaSkillResource(skill_loader=loader, auto_register=False)

        context = skills.get_prompt_context()

        # Should include enabled skill
        assert '"name": "enabled-skill"' in context
        # Should exclude disabled skill
        assert '"name": "disabled-skill"' not in context

    def test_get_prompt_context_excludes_system_metadata(self, tmp_path: Path):
        """Test that system metadata is NOT included in prompt context."""
        # Create skill with system metadata
        skill_dir = tmp_path / "fork-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            """---
name: fork-skill
description: A fork mode skill
context: fork
agent: Explore
allowed-tools: Read, Grep
---
Fork mode skill content.
"""
        )

        loader = SkillLoader(skill_dirs=[tmp_path])
        skills = DanaSkillResource(skill_loader=loader, auto_register=False)

        context = skills.get_prompt_context()

        # Should include name and description
        assert '"name": "fork-skill"' in context
        assert '"description": "A fork mode skill"' in context

        # Should NOT include system metadata
        assert '"context":' not in context
        assert '"agent":' not in context
        assert '"allowed-tools":' not in context
        assert '"allowed_tools":' not in context
        assert "fork" not in context.lower() or '"fork-skill"' in context  # Only in name is OK

    def test_get_prompt_context_escapes_quotes(self, tmp_path: Path):
        """Test that quotes in descriptions are properly escaped."""
        skill_dir = tmp_path / "quote-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            """---
name: quote-skill
description: A skill with "quotes" in description
---
Skill content.
"""
        )

        loader = SkillLoader(skill_dirs=[tmp_path])
        skills = DanaSkillResource(skill_loader=loader, auto_register=False)

        context = skills.get_prompt_context()

        # Should have escaped quotes
        assert '\\"quotes\\"' in context or '"quotes"' not in context.replace('\\"', "")

    def test_format_skills_for_prompt(self, tmp_path: Path):
        """Test the _format_skills_for_prompt helper method."""
        # Create skills
        for _, name in enumerate(["zeta-skill", "alpha-skill"]):
            skill_dir = tmp_path / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                f"""---
name: {name}
description: Description for {name}
---
Content.
"""
            )

        loader = SkillLoader(skill_dirs=[tmp_path])
        skills = DanaSkillResource(skill_loader=loader, auto_register=False)

        # Get model invocable skills and format
        model_invocable = loader.list_model_invocable()
        formatted = skills._format_skills_for_prompt(model_invocable)

        # Should be sorted alphabetically
        alpha_pos = formatted.find("alpha-skill")
        zeta_pos = formatted.find("zeta-skill")
        assert alpha_pos < zeta_pos, "Skills should be sorted alphabetically"


class TestRuntimeResourceContextIntegration:
    """Tests for runtime integration with resource context."""

    def test_build_resource_context_collects_from_resources(self, tmp_path: Path):
        """Test that _build_resource_context collects context from resources."""
        # Create test skill
        skill_dir = tmp_path / "integration-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            """---
name: integration-skill
description: Test integration
---
Content.
"""
        )

        # Create agent with DanaSkills resource
        loader = SkillLoader(skill_dirs=[tmp_path])
        skills_resource = DanaSkillResource(skill_loader=loader, auto_register=False)

        agent = STARAgent(
            agent_type="test-agent",
            auto_register=False,
            enable_web_search=False,
            enable_skills=False,  # Don't auto-add skills
            enable_code_execution=False,
        )
        agent.with_resources(skills_resource)

        # Build resource context using runtime
        runtime = DefaultRuntime()
        context = runtime._build_resource_context(agent)

        # Should include skill context
        assert '"available_skills"' in context
        assert '"name": "integration-skill"' in context

    def test_build_resource_context_empty_without_resources(self):
        """Test that _build_resource_context returns empty string with no resources."""
        agent = STARAgent(
            agent_type="test-agent",
            auto_register=False,
            enable_web_search=False,
            enable_skills=False,
            enable_code_execution=False,
        )

        runtime = DefaultRuntime()
        context = runtime._build_resource_context(agent)

        assert context == ""

    def test_system_prompt_includes_resource_context(self, tmp_path: Path):
        """Test that system prompt includes resource context when skills are present."""
        # Create test skill
        skill_dir = tmp_path / "prompt-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            """---
name: prompt-skill
description: Skill for prompt testing
---
Content.
"""
        )

        # Create agent with DanaSkills resource
        loader = SkillLoader(skill_dirs=[tmp_path])
        skills_resource = DanaSkillResource(skill_loader=loader, auto_register=False)

        agent = STARAgent(
            agent_type="test-agent",
            auto_register=False,
            enable_web_search=False,
            enable_skills=False,
            enable_code_execution=False,
        )
        agent.with_resources(skills_resource)

        # Build system prompt
        runtime = DefaultRuntime()
        prompt = runtime._build_system_prompt(agent)

        # Should include skill context in prompt
        assert "prompt-skill" in prompt
        assert "Skill for prompt testing" in prompt


class TestSubstituteArguments:
    """Tests for $ARGUMENTS inline substitution (Claude Code compatible)."""

    def _make_resource(self, tmp_path: Path, content: str) -> tuple[DanaSkillResource, str]:
        """Helper: create a single-skill resource and return (resource, skill_name)."""
        skill_dir = tmp_path / "arg-skill"
        skill_dir.mkdir(exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content)
        loader = SkillLoader(skill_dirs=[tmp_path])
        resource = DanaSkillResource(skill_loader=loader, auto_register=False)
        return resource, "arg-skill"

    def test_substitute_arguments_replaces_inline(self, tmp_path: Path):
        """$ARGUMENTS in skill content is replaced with the args string."""
        resource, name = self._make_resource(
            tmp_path,
            "---\nname: arg-skill\ndescription: test\n---\nAnalyze module: $ARGUMENTS",
        )
        result = resource._execute_main(
            resource._skill_loader.get_skill(name),
            context="",
            args="src/auth",
        )
        assert "Analyze module: src/auth" in result["instructions"]
        assert "$ARGUMENTS" not in result["instructions"]

    def test_substitute_arguments_empty_when_no_args(self, tmp_path: Path):
        """$ARGUMENTS becomes empty string when args is empty."""
        resource, name = self._make_resource(
            tmp_path,
            "---\nname: arg-skill\ndescription: test\n---\nTarget: $ARGUMENTS done",
        )
        result = resource._execute_main(
            resource._skill_loader.get_skill(name),
            context="",
            args="",
        )
        assert "Target:  done" in result["instructions"]
        assert "$ARGUMENTS" not in result["instructions"]

    def test_substitute_arguments_no_placeholder_untouched(self, tmp_path: Path):
        """Content without $ARGUMENTS is not modified."""
        resource, name = self._make_resource(
            tmp_path,
            "---\nname: arg-skill\ndescription: test\n---\nPlain instructions here.",
        )
        result = resource._execute_main(
            resource._skill_loader.get_skill(name),
            context="",
            args="should-not-appear-inline",
        )
        assert "Plain instructions here." in result["instructions"]

    def test_substitute_arguments_with_special_chars(self, tmp_path: Path):
        """Args with special characters are substituted verbatim."""
        resource, name = self._make_resource(
            tmp_path,
            "---\nname: arg-skill\ndescription: test\n---\nRun: $ARGUMENTS",
        )
        result = resource._execute_main(
            resource._skill_loader.get_skill(name),
            context="",
            args="-m 'Fix bug' --no-verify",
        )
        assert "Run: -m 'Fix bug' --no-verify" in result["instructions"]
        assert "$ARGUMENTS" not in result["instructions"]


class TestBaseDirectoryPrefix:
    """Tests for base directory prefix in skill output."""

    def test_execute_main_includes_base_directory(self, tmp_path: Path):
        """Main mode output includes 'Base directory for this skill:' prefix."""
        skill_dir = tmp_path / "dir-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: dir-skill\ndescription: test\n---\nDo something.")
        loader = SkillLoader(skill_dirs=[tmp_path])
        resource = DanaSkillResource(skill_loader=loader, auto_register=False)
        skill = loader.get_skill("dir-skill")

        result = resource._execute_main(skill, context="", args="")

        assert f"Base directory for this skill: {skill_dir}" in result["instructions"]

    def test_fork_task_message_includes_base_directory(self, tmp_path: Path):
        """Fork task message includes 'Base directory for this skill:' prefix."""
        skill_dir = tmp_path / "dir-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: dir-skill\ndescription: test\n---\nDo something.")
        loader = SkillLoader(skill_dirs=[tmp_path])
        resource = DanaSkillResource(skill_loader=loader, auto_register=False)
        skill = loader.get_skill("dir-skill")

        msg = resource._build_fork_task_message(skill, context="", args="")

        assert f"Base directory for this skill: {skill_dir}" in msg


class TestForkTaskMessageContent:
    """Tests for skill content inclusion in fork task message."""

    def test_fork_task_message_includes_skill_content(self, tmp_path: Path):
        """Fork task message includes <skill> block with content."""
        skill_dir = tmp_path / "fork-content-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: fork-content-skill\ndescription: test\n---\nThese are the instructions.")
        loader = SkillLoader(skill_dirs=[tmp_path])
        resource = DanaSkillResource(skill_loader=loader, auto_register=False)
        skill = loader.get_skill("fork-content-skill")

        msg = resource._build_fork_task_message(skill, context="user context", args="")

        assert '<skill name="fork-content-skill">' in msg
        assert "These are the instructions." in msg
        assert "</skill>" in msg

    def test_fork_task_message_substitutes_arguments(self, tmp_path: Path):
        """Fork task message applies $ARGUMENTS substitution."""
        skill_dir = tmp_path / "fork-args-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: fork-args-skill\ndescription: test\n---\nTarget: $ARGUMENTS")
        loader = SkillLoader(skill_dirs=[tmp_path])
        resource = DanaSkillResource(skill_loader=loader, auto_register=False)
        skill = loader.get_skill("fork-args-skill")

        msg = resource._build_fork_task_message(skill, context="", args="mymodule")

        assert "Target: mymodule" in msg
        assert "$ARGUMENTS" not in msg
