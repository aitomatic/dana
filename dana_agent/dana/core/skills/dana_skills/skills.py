"""
Skill Resource - @tool_use interface for invoking skills.

Provides the agent-facing API for skill invocation. Skills can run in:
- Main mode: Instructions returned to current context (recipe stays on counter)
- Fork mode: Isolated execution via subagent, only summary returns (context discarded after)

Fork Mode Architecture:
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Main Agent   │──────│ Skill Tool   │──────│ Subagent     │
│              │      │              │      │              │
│ "I'm just    │      │ Sees fork,   │      │ Same type,   │
│  using a     │      │ creates      │      │ restricted   │
│  skill"      │      │ subagent     │      │ tools        │
└──────────────┘      └──────────────┘      └──────────────┘
    UNAWARE              AUTOMATIC           ISOLATED
"""

import fnmatch
from typing import TYPE_CHECKING, Any

from structlog import get_logger

from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource

from .loader import SkillLoader
from .models import DanaSkill


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent

logger = get_logger()


class DanaSkillResource(BaseResource):
    """
    Execute skills - composable task templates that extend agent capabilities.

    Skills are discovered at startup from ~/.dana/skills/, ./.dana/skills/,
    ~/.claude/skills/, and ./.claude/skills/. Available skills and their
    descriptions are shown in the system prompt.

    Use invoke() to execute a skill by name.
    """

    def __init__(
        self,
        skill_loader: SkillLoader | None = None,
        agent: "STARAgent | None" = None,
        resource_id: str = "skills",
        **kwargs: Any,
    ):
        """
        Initialize the skill resource.

        Args:
            skill_loader: Custom SkillLoader instance. If None, creates default.
            agent: Parent agent (for subagent creation in fork mode).
                   Required for fork mode to work - without it, fork falls back to main.
            resource_id: Resource identifier.
            **kwargs: Additional arguments passed to BaseResource.
        """
        super().__init__(resource_type="skill", resource_id=resource_id, **kwargs)
        self._skill_loader = skill_loader or SkillLoader()
        self._agent = agent

    @tool_use
    async def invoke(
        self,
        skill_name: str,
        context: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Invoke a skill by name.

        Args:
            skill_name: Name of the skill to invoke (e.g., "commit-message")
            context: Relevant context from the conversation that the skill needs
            parameters: Optional parameters to pass to the skill (accessible as $ARGUMENTS in scripts)

        Returns:
            For non-fork skills: Returns skill instructions to follow in your response
            For fork skills: Returns summary of completed work
        """
        skill = self._skill_loader.get_skill(skill_name)
        if not skill:
            available = ", ".join(s.name for s in self._skill_loader.list_skills()[:10])
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found. Available: {available}",
            }

        logger.info("invoking_skill", name=skill_name, context_mode=skill.context_mode)

        if skill.context_mode == "fork":
            return await self._execute_fork(skill, context, parameters or {})
        else:
            # Main mode doesn't need await (just returns instructions)
            return self._execute_main(skill, context, parameters or {})

    def _execute_main(
        self,
        skill: DanaSkill,
        context: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute skill in main context (non-fork).

        The skill content is returned to the agent. The agent should follow
        the instructions in its response. Content stays in conversation history.

        Args:
            skill: The skill to execute
            context: Context from the conversation
            parameters: Skill parameters

        Returns:
            Dictionary with skill instructions
        """
        skill_content = skill.content

        # Build tool restriction note if applicable
        tools_note = ""
        if skill.allowed_tools:
            tools_note = f"\n\n**Tool Restrictions:** You may only use: {', '.join(skill.allowed_tools)}"

        # Build scripts note if applicable
        scripts_note = ""
        if skill.scripts_dir:
            scripts_note = f"\n\n**Scripts Available:** Run scripts from {skill.scripts_dir}/ - execute them, do not read the code."

        return {
            "success": True,
            "mode": "main",
            "instructions": f"""<skill name="{skill.name}">
{skill_content}
</skill>

<context>
{context if context else "No additional context provided."}
</context>

<parameters>
{parameters if parameters else "No parameters provided."}
</parameters>{tools_note}{scripts_note}

Follow the skill instructions above. The skill content will remain in your context for follow-up questions.""",
        }

    async def _execute_fork(
        self,
        skill: DanaSkill,
        context: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute skill in forked context (isolated subagent).

        Creates a subagent with:
        - Same agent type and system prompt as parent
        - Restricted tools based on allowed-tools in SKILL.md
        - Skill content + context + parameters as the task

        Only returns a summary - the subagent context is discarded after execution.

        Architecture:
        ┌─────────────────────────────────────────────────────────────┐
        │ SKILL TOOL (Internal Logic)                                 │
        │                                                             │
        │   1. Loads SKILL.md                                         │
        │   2. Reads frontmatter (context: fork, allowed-tools)       │
        │   3. Creates subagent (same type, restricted tools)         │
        │   4. Passes SKILL.md + context + parameters to subagent     │
        │   5. Waits for subagent to complete                         │
        │   6. Returns summary to main agent (context discarded)      │
        │                                                             │
        └─────────────────────────────────────────────────────────────┘

        Args:
            skill: The skill to execute
            context: Context from the conversation
            parameters: Skill parameters

        Returns:
            Dictionary with execution result/summary
        """
        # Check if we have a parent agent for forking
        if self._agent is None:
            logger.warning(
                "fork_mode_no_agent",
                skill=skill.name,
                message="No parent agent available for fork mode, falling back to main mode",
            )
            return self._execute_main(skill, context, parameters)

        try:
            # Create subagent with restricted resources
            subagent = self._create_fork_subagent(skill)

            # Build the task message for the subagent
            task_message = self._build_fork_task_message(skill, context, parameters)

            logger.info(
                "fork_executing",
                skill=skill.name,
                subagent_id=subagent.object_id,
                allowed_tools=skill.allowed_tools,
            )

            # Use async query for non-blocking execution
            result = await subagent.aquery(message=task_message)

            # Extract the response from the subagent
            response = result.get("response", "Skill execution completed.")

            logger.info(
                "fork_completed",
                skill=skill.name,
                subagent_id=subagent.object_id,
            )

            return {
                "success": True,
                "mode": "fork",
                "result": response,
            }

        except Exception as e:
            logger.error(
                "fork_execution_error",
                skill=skill.name,
                error=str(e),
            )
            return {
                "success": False,
                "mode": "fork",
                "error": f"Fork execution failed: {e}",
            }

    def _create_fork_subagent(self, skill: DanaSkill) -> "STARAgent":
        """
        Create a subagent for fork execution.

        The subagent:
        - Is the same type as the parent agent
        - Has the same LLM configuration
        - Has restricted resources based on allowed-tools
        - Uses a unique agent_id to avoid inheriting parent's persisted prompts
        - Overrides identity with skill content

        Args:
            skill: The skill being executed (contains allowed-tools)

        Returns:
            Configured subagent ready for execution
        """

        from dana.core.agent.star_agent import STARAgent

        # Create subagent with unique ID to avoid inheriting parent's persisted prompts
        # The identity_override ensures the skill content becomes the fork's identity
        subagent = STARAgent(
            agent_type=f"{self._agent.agent_type}",
            agent_id=f"fork-{skill.name}",
            llm_provider=self._agent._llm_config.get("provider"),
            model=self._agent._llm_config.get("model"),
            codec=self._agent._codec,
            auto_register=False,  # Don't register fork agents
            max_context_tokens=self._agent._timeline.max_context_tokens,
            enable_assistant=False,
            identity_override=skill.content,  # Skill content becomes the fork's identity
        )

        subagent.set_session_id(f"{self._agent._session_id}-{skill.name}")
        # Filter and add resources based on allowed-tools
        if skill.allowed_tools:
            filtered_resources = self._filter_resources(skill.allowed_tools)
            if filtered_resources:
                subagent.with_resources(*filtered_resources)
        else:
            # No restrictions - copy all resources from parent (except SkillResource to prevent recursion)
            for resource in self._agent._resources:
                if not isinstance(resource, DanaSkillResource):
                    subagent.with_resources(resource)

        # Handle nested skills if skill declares allowed_skills
        if skill.allowed_skills:
            # Prevent self-recursion: exclude the current skill from allowed_skills
            safe_allowed_skills = [s for s in skill.allowed_skills if s != skill.name]

            if safe_allowed_skills:
                filtered_skill_loader = self._create_filtered_skill_loader(safe_allowed_skills)
                nested_skill_resource = DanaSkillResource(
                    skill_loader=filtered_skill_loader,
                    agent=subagent,  # Enable further nesting
                    resource_id="skills",
                )
                subagent.with_resources(nested_skill_resource)
                logger.info(
                    "fork_with_nested_skills",
                    skill=skill.name,
                    nested_skills=safe_allowed_skills,
                )
            elif skill.name in skill.allowed_skills:
                # Log when self-recursion was prevented
                logger.info(
                    "fork_self_recursion_prevented",
                    skill=skill.name,
                    message="Skill declared itself in allowed_skills - removed to prevent infinite loop",
                )

        return subagent

    def _filter_resources(self, allowed_tools: list[str]) -> list[Any]:
        """
        Filter parent resources based on allowed-tools patterns.

        Pattern format: "resource_id:method" or "resource_id:*"
        Examples:
        - "bash:execute" - only bash.execute method
        - "bash:*" - all bash methods
        - "*:read" - read method on any resource

        Args:
            allowed_tools: List of tool patterns from SKILL.md

        Returns:
            List of resources that match the patterns
        """
        if not self._agent:
            return []

        filtered = []
        for resource in self._agent._resources:
            # Skip SkillResource to prevent recursion
            if isinstance(resource, DanaSkillResource):
                continue

            resource_id = resource.resource_id

            # Check if this resource matches any allowed pattern
            for pattern in allowed_tools:
                if ":" in pattern:
                    pattern_resource, _ = pattern.split(":", 1)
                else:
                    pattern_resource = pattern

                # Match resource_id using fnmatch for glob-style patterns
                if fnmatch.fnmatch(resource_id, pattern_resource):
                    # TODO: Could add method-level filtering if needed
                    # For now, include the whole resource if resource_id matches
                    if resource not in filtered:
                        filtered.append(resource)
                    break

        return filtered

    def _create_filtered_skill_loader(self, allowed_skills: list[str]) -> SkillLoader:
        """
        Create a SkillLoader with only the specified skills.

        This enables nested skill invocation with controlled access:
        - Parent skill declares which skills it can invoke via skills: [...]
        - Subagent gets a SkillLoader containing only those skills
        - Prevents arbitrary skill access from forked contexts

        Args:
            allowed_skills: List of skill names this skill can invoke

        Returns:
            SkillLoader containing only the allowed skills
        """
        # Get all skills from parent loader
        all_skills = self._skill_loader._skills

        # Filter to only allowed skills
        filtered_skills = {name: skill for name, skill in all_skills.items() if name in allowed_skills}

        # Create new loader with filtered skills (no auto-discover)
        loader = SkillLoader(skill_dirs=[], auto_discover=False)
        loader._skills = filtered_skills

        logger.debug(
            "created_filtered_skill_loader",
            allowed=allowed_skills,
            available=list(filtered_skills.keys()),
        )

        return loader

    def _build_fork_task_message(
        self,
        skill: DanaSkill,
        context: str,
        parameters: dict[str, Any],
    ) -> str:
        """
        Build the task message for the forked subagent.

        Args:
            skill: The skill to execute
            context: Context from the conversation
            parameters: Skill parameters

        Returns:
            Formatted task message for the subagent
        """
        skill_content = skill.content

        scripts_note = ""
        if skill.scripts_dir:
            scripts_note = f"\n\n**Scripts Available:** Run scripts from {skill.scripts_dir}/ - execute them, do not read the code."

        return f"""You are executing a forked skill in an isolated context.

CRITICAL: Your entire conversation history will be DISCARDED after execution.
ONLY your FINAL RESPONSE will be returned to the caller.

This means:
- Do NOT provide status updates or partial progress
- Do NOT explain what you're about to do next
- Complete ALL instructions FIRST, then provide your final response
- Your final response must be actionable/usable, not internal reasoning

<skill name="{skill.name}">
{skill_content}
</skill>

<context>
{context if context else "No additional context provided."}
</context>

<parameters>
{parameters if parameters else "No parameters provided."}
</parameters>{scripts_note}

Execute ALL skill instructions above completely. Your final response is the ONLY output that will be seen - make it count."""

    def list_skills(self) -> list[DanaSkill]:
        """
        List all available skills (for programmatic use, not @tool_use).

        Returns:
            List of all discovered DanaSkill objects
        """
        return self._skill_loader.list_skills()

    def list_model_invocable(self) -> list[DanaSkill]:
        """
        List skills that can be invoked by the LLM.

        Skills with disable_model_invocation=True are excluded.

        Returns:
            List of DanaSkill objects that can be model-invoked
        """
        return self._skill_loader.list_model_invocable()

    def get_prompt_descriptions(self, budget_chars: int = 15000) -> str:
        """
        Generate skill descriptions for system prompt (markdown format).

        Creates a compact list of skill names and descriptions
        suitable for including in the system prompt. Only includes
        skills that can be model-invoked (excludes disabled skills).

        Args:
            budget_chars: Maximum character budget for descriptions

        Returns:
            Formatted string of skill descriptions (markdown list)
        """
        return self._skill_loader.get_prompt_descriptions(budget_chars)

    def get_prompt_context(self) -> str:
        """
        Get skill context for inclusion in the system prompt.

        Returns available skills in a JSON format suitable for the system prompt,
        excluding skills with disable_model_invocation=True and system metadata.

        Returns:
            JSON-formatted string with skill labels, or empty string if no skills
        """
        model_invocable = self._skill_loader.list_model_invocable()
        if not model_invocable:
            return ""

        return self._format_skills_for_prompt(model_invocable)

    def _format_skills_for_prompt(self, skills: list[DanaSkill]) -> str:
        """
        Format skills for inclusion in the system prompt.

        Args:
            skills: List of DanaSkill objects to format

        Returns:
            JSON-formatted string with skill names and descriptions
        """
        if not skills:
            return ""

        # Sort alphabetically by name
        sorted_skills = sorted(skills, key=lambda s: s.name)

        # Build skill entries with only name and description (no system metadata)
        skill_entries = []
        for skill in sorted_skills:
            # Escape quotes in description
            escaped_desc = skill.description.replace('"', '\\"')
            skill_entries.append(f'{{"name": "{skill.name}", "description": "{escaped_desc}"}}')

        skills_json = ", ".join(skill_entries)

        return f'"available_skills": [{skills_json}], "skill_usage": "Use skills:invoke to execute a skill by name"'
