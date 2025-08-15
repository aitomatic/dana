"""
AgentSelector - Implements selection logic for choosing the most appropriate agent for a task based on skills.

This module provides the AgentSelector class that handles the logic for selecting
the most appropriate agent from a pool based on task requirements and skills.
"""

import json
from typing import TYPE_CHECKING, Any

from dana.common.mixins import Loggable
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.common.types import BaseRequest
from dana.common.utils import Misc

if TYPE_CHECKING:
    from .agent_pool import AgentPool


class AgentSelector(Loggable):
    """Handles agent selection logic."""

    def __init__(self, pool: "AgentPool", llm: LegacyLLMResource | None = None):
        """Initialize selector.

        Args:
            pool: AgentPool instance to select from
        """
        self.pool = pool
        self._skill_cache: dict[str, list[str]] = {}
        self._performance_metrics: dict[str, dict[str, float]] = {}
        self._llm = llm if llm is not None else LegacyLLMResource(name="agent_selector_llm")

    def select_agent(self, task: any, strategy: str = "llm", included_resources: list[str | Any] | None = None) -> Any:
        """Select an agent using LLM-based selection only.

        Args:
            task: Task requirements including description and skills
            strategy: Only 'llm' is supported
            included_resources: Optional list of resource names or resources to include when generating self agent card

        Returns:
            Selected A2AResource instance

        Raises:
            ValueError: If strategy is not 'llm'
        """
        if strategy != "llm":
            raise ValueError("Only 'llm' selection strategy is supported at this time.")
        return self._select_by_llm(task, included_resources=included_resources)

    def _select_by_llm(self, task: any, included_resources: list[str | Any] | None = None) -> Any:
        """Select agent using LLM-based selection.

        Args:
            task: Task requirements
            included_resources: Optional list of resource names or resources to include when generating self agent card

        Returns:
            Selected A2AResource instance

        Raises:
            ValueError: If no suitable agent found
        """
        # Get agent cards for context
        agent_cards = self.pool.get_agent_cards(included_resources=included_resources)
        self.log_debug(f"Selecting from {len(agent_cards)} agents for task: {str(task)[:60]}{'...' if len(str(task)) > 60 else ''}")

        # Create prompt for LLM
        prompt = f"""Task: {task}

Available agents:
{agent_cards}

Consider:
1. Domain expertise required
2. Agent capabilities and specializations
3. Query complexity and specificity
4. Whether the current agent can handle the query effectively

Your task is to:
1. Analyze the question and understand its requirements
2. Review each agent's capabilities from their cards
3. Select the most appropriate agent that can handle the question
4. Provide your selection with clear reasoning
Your response must be wrapped in ```json``` tags and contain a valid JSON object with the following format:
```json
{{
"selected_agents": [
    {{
    "agent_id": "id of the selected agent",
    "confidence": "high/medium/low",
    "reasoning": "Brief explanation of why this agent is suitable"
    }}
],
"reasoning": "Overall explanation of the selection process"
}}
"""
        try:
            # Use LLM to select agent
            request = BaseRequest(arguments={"messages": [{"role": "user", "content": prompt}]})
            decision = self._llm.query_sync(request)
            text = Misc.get_response_content(decision)
            decision_dict = Misc.text_to_dict(text)
            self.log_debug(f"Agent selection decision: \n{json.dumps(decision_dict, indent=4)}")
            selected_agents = decision_dict.get("selected_agents", [])

            if len(selected_agents) == 0:
                self.log_error(f"LLM selected no agents: {selected_agents}")
                return None
            selected_id = selected_agents[0]["agent_id"]

            # Validate selection
            if selected_id not in agent_cards:
                self.log_error(f"LLM selected invalid agent: {selected_id}")
                return None
            selected_agent = self.pool.agents.get(selected_id, None)
            self.log_info(
                f"Selected agent '{selected_agent.name if selected_agent else 'None'}' (confidence: {selected_agents[0].get('confidence', 'unknown')}) with reasoning: {selected_agents[0].get('reasoning', 'No reasoning provided')}"
            )
            return selected_agent
        except Exception as e:
            self.log_error(f"Error selecting agent: {e}")
            return None

    def _get_agent_skills(self, agent: Any) -> list[str]:
        """Get agent skills, using cache if available.

        Args:
            agent: A2AResource instance

        Returns:
            List of skill strings
        """
        if agent.name not in self._skill_cache:
            self._skill_cache[agent.name] = agent.agent_card.get("skills", agent.agent_card.get("capabilities", []))
        return self._skill_cache[agent.name]

    def _format_agent_cards(self, cards: dict[str, dict]) -> str:
        """Format agent cards for LLM prompt.

        Args:
            cards: Dictionary of agent cards

        Returns:
            Formatted string
        """
        formatted = []
        for name, card in cards.items():
            formatted.append(f"Agent: {name}")
            formatted.append(f"Description: {card.get('description', 'No description')}")

            # Handle skills which can be list of dicts or list of strings
            skills = card.get("skills") or card.get("capabilities") or []
            if skills:
                if isinstance(skills[0], dict):  # type: ignore
                    # Skills are dictionaries with name field
                    skill_names = [skill.get("name", str(skill)) for skill in skills]
                else:
                    # Skills are strings
                    skill_names = skills
                formatted.append(f"Skills: {', '.join(skill_names)}")
            else:
                formatted.append("Skills: ")
            formatted.append("")
        return "\n".join(formatted)

    def update_performance_metrics(self, agent_name: str, metrics: dict[str, float]) -> None:
        """Update performance metrics for an agent.

        Args:
            agent_name: Name of the agent
            metrics: Dictionary of metric name to value
        """
        if agent_name not in self._performance_metrics:
            self._performance_metrics[agent_name] = {}
        self._performance_metrics[agent_name].update(metrics)
