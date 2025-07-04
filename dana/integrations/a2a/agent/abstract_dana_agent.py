from abc import ABC, abstractmethod

from dana.common.resource.base_resource import BaseResource


class AbstractDanaAgent(BaseResource, ABC):
    @property
    @abstractmethod
    def agent_card(self) -> dict[str, any]:
        """Get the agent card."""
        return {}

    @property
    @abstractmethod
    def skills(self) -> list[dict[str, any]]:
        """Get the agent skills."""
        return []

    @abstractmethod
    async def solve(self, task: str) -> str:
        """Solve a problem by delegating to the agent."""
        return ""
