"""
Capability registry for managing available tools, strategies, and skills.
"""

from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable


@dataclass
class Tool:
    """Tool capability definition."""

    name: str
    description: str
    function: Callable | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class Strategy:
    """Strategy capability definition."""

    name: str
    description: str
    type: str  # "recursive", "iterative", "direct", etc.
    handler: Callable | None = None
    requirements: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class Skill:
    """Skill capability definition."""

    name: str
    description: str
    category: str  # "reasoning", "analysis", "generation", etc.
    proficiency: float = 0.5  # 0.0 to 1.0
    enabled: bool = True


class CapabilityRegistry:
    """Registry of available capabilities and actions."""

    def __init__(self):
        """Initialize the capability registry."""
        self.tools: dict[str, Tool] = {}
        self.strategies: dict[str, Strategy] = {}
        self.skills: dict[str, Skill] = {}

    def register_tool(self, tool: Tool) -> None:
        """Register a new tool capability.

        Args:
            tool: Tool to register
        """
        self.tools[tool.name] = tool

    def register_strategy(self, strategy: Strategy) -> None:
        """Register a new strategy capability.

        Args:
            strategy: Strategy to register
        """
        self.strategies[strategy.name] = strategy

    def register_skill(self, skill: Skill) -> None:
        """Register a new skill capability.

        Args:
            skill: Skill to register
        """
        self.skills[skill.name] = skill

    def get_available_actions(self) -> list[str]:
        """Get list of all currently available actions.

        Returns:
            List of action names
        """
        actions = []

        # Add enabled tools
        actions.extend([f"tool:{name}" for name, tool in self.tools.items() if tool.enabled])

        # Add enabled strategies
        actions.extend([f"strategy:{name}" for name, strategy in self.strategies.items() if strategy.enabled])

        # Add enabled skills
        actions.extend([f"skill:{name}" for name, skill in self.skills.items() if skill.enabled])

        return actions

    def get_available_strategies(self) -> list[str]:
        """Get list of available strategy names.

        Returns:
            List of enabled strategy names
        """
        return [name for name, strategy in self.strategies.items() if strategy.enabled]

    def get_available_tools(self) -> list[str]:
        """Get list of available tool names.

        Returns:
            List of enabled tool names
        """
        return [name for name, tool in self.tools.items() if tool.enabled]

    def can_execute(self, action: str) -> bool:
        """Check if an action can be executed.

        Args:
            action: Action name to check (format: "type:name" or just "name")

        Returns:
            True if action is available and enabled
        """
        # Parse action type if provided
        if ":" in action:
            action_type, action_name = action.split(":", 1)

            if action_type == "tool":
                return action_name in self.tools and self.tools[action_name].enabled
            elif action_type == "strategy":
                return action_name in self.strategies and self.strategies[action_name].enabled
            elif action_type == "skill":
                return action_name in self.skills and self.skills[action_name].enabled
        else:
            # Check all types
            return (
                (action in self.tools and self.tools[action].enabled)
                or (action in self.strategies and self.strategies[action].enabled)
                or (action in self.skills and self.skills[action].enabled)
            )

        return False

    def get_capability(self, name: str) -> Tool | Strategy | Skill | None:
        """Get a capability by name.

        Args:
            name: Capability name

        Returns:
            The capability object or None if not found
        """
        # Check each registry
        if name in self.tools:
            return self.tools[name]
        if name in self.strategies:
            return self.strategies[name]
        if name in self.skills:
            return self.skills[name]

        return None

    def update_from_registry(self, registry: dict[str, Any]) -> None:
        """Update capabilities from a workflow registry or similar.

        Args:
            registry: Dictionary of capability definitions
        """
        for name, definition in registry.items():
            if isinstance(definition, dict):
                # Determine type and create appropriate capability
                if "type" in definition:
                    if definition["type"] == "tool":
                        self.register_tool(
                            Tool(
                                name=name,
                                description=definition.get("description", ""),
                                function=definition.get("function"),
                                parameters=definition.get("parameters", {}),
                            )
                        )
                    elif definition["type"] == "strategy":
                        self.register_strategy(
                            Strategy(
                                name=name,
                                description=definition.get("description", ""),
                                type=definition.get("strategy_type", "general"),
                                handler=definition.get("handler"),
                                requirements=definition.get("requirements", []),
                            )
                        )

    def get_status(self) -> dict[str, Any]:
        """Get capability registry status.

        Returns:
            Dictionary with registry statistics
        """
        return {
            "total_tools": len(self.tools),
            "enabled_tools": sum(1 for t in self.tools.values() if t.enabled),
            "total_strategies": len(self.strategies),
            "enabled_strategies": sum(1 for s in self.strategies.values() if s.enabled),
            "total_skills": len(self.skills),
            "enabled_skills": sum(1 for s in self.skills.values() if s.enabled),
        }
