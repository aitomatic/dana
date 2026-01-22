"""
Dana Skills - Agent-facing API for skill invocation.

Provides the invoke() tool for agents to execute Dana skills.
Supports both main mode (instruction injection) and fork mode (isolated subagent).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import structlog

from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource

from .loader import SkillLoader
from .models import DanaSkill


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent

logger = structlog.get_logger()


class DanaSkills(BaseResource):
    """Resource for invoking Dana skills from agents.

    Provides the invoke() tool that agents use to execute skills.
    Skills can run in two modes:

    - main: Injects skill instructions into current conversation context
    - fork: Creates isolated subagent to execute skill, returns summary

    Usage:
        loader = SkillLoader()
        dana_skills = DanaSkills(skill_loader=loader, agent=my_agent)
        agent.with_resources(dana_skills)

        # Agent can then call:
        result = await skills.invoke("my-skill", arguments="search for X")
    """

    def __init__(
        self,
        skill_loader: SkillLoader | None = None,
        agent: STARAgent | None = None,
        resource_id: str = "skills",
        **kwargs: Any,
    ):
        """Initialize the skill resource.

        Args:
            skill_loader: SkillLoader instance for skill discovery.
                         If None, creates default loader.
            agent: Parent agent (required for fork mode).
            resource_id: Resource identifier (default: "skills")
            **kwargs: Additional arguments passed to BaseResource.
        """
        super().__init__(resource_type="skills", resource_id=resource_id, **kwargs)

        self._skill_loader = skill_loader or SkillLoader()
        self._agent = agent
        self._executing_skills: set[str] = set()  # Prevent recursion

    @tool_use
    async def invoke(
        self,
        skill_name: str,
        arguments: str = "",
        context: str = "",
    ) -> dict[str, Any]:
        """Invoke a Dana skill by name.

        Args:
            skill_name: Name of the skill to invoke (e.g., "commit", "review-pr")
            arguments: Arguments to pass to the skill (replaces $ARGUMENTS)
            context: Additional context from the conversation

        Returns:
            Dict with:
            - success: Whether invocation succeeded
            - mode: "main" or "fork"
            - instructions: (main mode) Skill instructions with substitutions
            - result: (fork mode) Summary from subagent execution
            - agent_id: (fork mode) Subagent ID for potential resumption
            - error: Error message if failed
        """
        logger.info("Invoking skill", skill_name=skill_name, arguments=arguments[:100] if arguments else "")

        # Get the skill
        skill = self._skill_loader.get_skill(skill_name)
        if not skill:
            available = [s.name for s in self._skill_loader.list_skills()]
            return {
                "success": False,
                "mode": None,
                "error": f"Skill '{skill_name}' not found. Available: {', '.join(available[:10])}",
            }

        # Check for recursion
        if skill_name in self._executing_skills:
            return {
                "success": False,
                "mode": None,
                "error": f"Skill '{skill_name}' is already executing (recursion prevented)",
            }

        try:
            self._executing_skills.add(skill_name)

            if skill.context_mode == "fork":
                return await self._invoke_fork(skill, arguments, context)
            else:
                return self._invoke_main(skill, arguments, context)

        finally:
            self._executing_skills.discard(skill_name)

    def _invoke_main(
        self,
        skill: DanaSkill,
        arguments: str,
        context: str,
    ) -> dict[str, Any]:
        """Invoke skill in main mode (instruction injection).

        Returns skill instructions with $ARGUMENTS substituted.
        The agent will execute these instructions in the current context.

        Args:
            skill: The skill to invoke
            arguments: Value for $ARGUMENTS substitution
            context: Additional context (prepended to instructions)

        Returns:
            Dict with success, mode, and instructions
        """
        session_id = ""
        if self._agent and hasattr(self._agent, "_session_id"):
            session_id = self._agent._session_id

        instructions = skill.substitute_arguments(arguments, session_id)

        if context:
            instructions = f"Context: {context}\n\n{instructions}"

        logger.info(
            "Skill invoked (main mode)",
            skill_name=skill.name,
            instructions_length=len(instructions),
        )

        return {
            "success": True,
            "mode": "main",
            "instructions": instructions,
        }

    async def _invoke_fork(
        self,
        skill: DanaSkill,
        arguments: str,
        context: str,
    ) -> dict[str, Any]:
        """Invoke skill in fork mode (isolated subagent).

        Creates a subagent with filtered resources/skills and executes
        the skill instructions. Returns summary and agent ID.

        Args:
            skill: The skill to invoke
            arguments: Value for $ARGUMENTS substitution
            context: Additional context for the subagent

        Returns:
            Dict with success, mode, result, and agent_id
        """
        if not self._agent:
            return {
                "success": False,
                "mode": "fork",
                "error": "Fork mode requires parent agent reference",
            }

        try:
            # Import here to avoid circular imports
            from dana.core.agent.star_agent import STARAgent

            session_id = getattr(self._agent, "_session_id", "")
            instructions = skill.substitute_arguments(arguments, session_id)

            if context:
                instructions = f"Context: {context}\n\n{instructions}"

            # Determine subagent configuration
            agent_type = skill.agent or "general-purpose"
            model = skill.model or getattr(self._agent, "_llm_config", {}).get("model")
            llm_provider = getattr(self._agent, "_llm_config", {}).get("provider")

            # Create subagent
            subagent = STARAgent(
                agent_id=f"{self._agent.object_id}_skill_{skill.name}",
                agent_type=agent_type,
                auto_register=False,
                llm_provider=llm_provider,
                model=model,
                enable_skills=False,  # Don't auto-enable skills in subagent
            )

            # Add filtered resources based on allowed_tools
            if skill.allowed_tools:
                filtered_resources = self._filter_resources(skill.allowed_tools)
                for resource in filtered_resources:
                    subagent.with_resources(resource)
            else:
                # Copy all resources from parent
                for resource in self._agent._resources:
                    if resource.resource_id != self.resource_id:  # Don't copy self
                        subagent.with_resources(resource)

            # Add filtered skills if specified
            if skill.allowed_skills:
                filtered_loader = self._skill_loader.filter_by_names(skill.allowed_skills)
                skill_resource = DanaSkills(
                    skill_loader=filtered_loader,
                    agent=subagent,
                    resource_id="skills",
                    auto_register=False,
                )
                subagent.with_resources(skill_resource)

            # Execute the skill
            logger.info(
                "Executing skill in fork mode",
                skill_name=skill.name,
                subagent_id=subagent.object_id,
                agent_type=agent_type,
            )

            result = await subagent.aquery(message=instructions)
            response = result.get("response", "No response from subagent")

            logger.info(
                "Skill fork completed",
                skill_name=skill.name,
                subagent_id=subagent.object_id,
                response_length=len(response),
            )

            return {
                "success": True,
                "mode": "fork",
                "result": response,
                "agent_id": subagent.object_id,
            }

        except Exception as e:
            logger.error("Skill fork failed", skill_name=skill.name, error=str(e))
            return {
                "success": False,
                "mode": "fork",
                "error": str(e),
            }

    def _filter_resources(self, allowed_tools: list[str]) -> list:
        """Filter parent agent's resources based on allowed-tools patterns.

        Args:
            allowed_tools: List of tool patterns (e.g., ["Read", "Bash(git:*)"])

        Returns:
            List of matching resources
        """
        if not self._agent:
            return []

        filtered = []
        for resource in self._agent._resources:
            resource_id = resource.resource_id

            for pattern in allowed_tools:
                if self._match_tool_pattern(pattern, resource_id):
                    # For patterns like Bash(git:*), we'd need to wrap the resource
                    # to filter commands. For now, just include the whole resource.
                    filtered.append(resource)
                    break

        return filtered

    def _match_tool_pattern(self, pattern: str, resource_id: str) -> bool:
        """Match a tool pattern against a resource ID.

        Patterns:
        - "Read" -> matches resource_id="Read" or "read" (case-insensitive)
        - "Bash(git:*)" -> matches resource_id="bash" (command filtering TBD)
        - "file-io:read" -> matches resource_id="file-io" with method "read"

        Args:
            pattern: Tool pattern string
            resource_id: Resource ID to match

        Returns:
            True if pattern matches resource
        """
        # Extract base tool name and optional filter
        match = re.match(r"^([a-zA-Z_-]+)(?:\(([^)]+)\))?$", pattern)
        if not match:
            return pattern.lower() == resource_id.lower()

        tool_name = match.group(1)

        # Handle resource:method patterns
        if ":" in tool_name and "(" not in pattern:
            res_id, _ = tool_name.split(":", 1)
            return res_id.lower() == resource_id.lower()

        return tool_name.lower() == resource_id.lower()

    @tool_use
    def list_available(self) -> dict[str, Any]:
        """List available skills.

        Returns:
            Dict with success and list of skill summaries
        """
        skills = self._skill_loader.list_model_invocable()
        skill_list = [
            {
                "name": skill.name,
                "description": skill.description[:200],
                "mode": skill.context_mode,
                "user_invocable": skill.user_invocable,
            }
            for skill in skills
        ]

        return {
            "success": True,
            "skills": skill_list,
            "count": len(skill_list),
        }

    def get_skill_loader(self) -> SkillLoader:
        """Get the underlying skill loader.

        Returns:
            The SkillLoader instance
        """
        return self._skill_loader

    def set_agent(self, agent: STARAgent) -> None:
        """Set the parent agent reference.

        Required for fork mode execution.

        Args:
            agent: The parent agent
        """
        self._agent = agent

    def get_prompt_context(self) -> str:
        """Return skill labels for inclusion in system prompt.

        Called by runtime to build resource context section.
        Returns ONLY name and description for model-invocable skills.

        The LLM needs to know:
        - WHAT skills exist (name)
        - WHEN to use them (description)

        System metadata (context_mode, allowed-tools, hooks, etc.) is NOT included
        as the system handles that during execution.

        Returns:
            JSON-formatted string for inclusion in system prompt, or empty string
            if no model-invocable skills are available.
        """
        model_invocable = self._skill_loader.list_model_invocable()

        if not model_invocable:
            return ""  # No context to add

        skill_entries = self._format_skills_for_prompt(model_invocable)

        return f""""available_skills": {{
    "description": "Skills you can invoke using the skills:invoke tool",
    "usage": "Call skills:invoke with skill_name and arguments",
    "skills": [
{skill_entries}
    ]
  }}"""

    def _format_skills_for_prompt(self, skills: list[DanaSkill]) -> str:
        """Format skills as JSON array entries with ONLY name and description.

        Args:
            skills: List of DanaSkill objects to format.

        Returns:
            Formatted string with one skill per line in JSON format.
        """
        lines = []
        for skill in sorted(skills, key=lambda s: s.name):
            # Only include name and description - NO system metadata
            # Escape quotes in description to ensure valid JSON
            escaped_desc = skill.description.replace('"', '\\"')
            lines.append(f'      {{"name": "{skill.name}", "description": "{escaped_desc}"}}')
        return ",\n".join(lines)
