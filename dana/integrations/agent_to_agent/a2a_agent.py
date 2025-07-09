from dana.agent.abstract_dana_agent import AbstractDanaAgent
from dana.common.mixins import ToolCallable
from dana.common.utils import Misc
from dana.integrations.agent_to_agent.a2a.client.a2a_client import BaseA2AClient


class A2AAgent(AbstractDanaAgent):
    """A2A Resource"""

    def __init__(
        self,
        name: str,
        description: str | None = None,
        config: dict[str, any] | None = None,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 30 * 60,
        google_a2a_compatible: bool = False,
    ):
        if url is None:
            raise ValueError("url is required")
        super().__init__(name, description, config)
        self.client = BaseA2AClient(
            endpoint_url=url,
            headers=headers,
            timeout=timeout,
            google_a2a_compatible=google_a2a_compatible,
        )
        if description is None:
            agent_card = self.agent_card
            if agent_card and isinstance(agent_card, dict):
                self.description = agent_card.get("description", self.description)

    @property
    def agent_card(self) -> dict[str, any]:
        """Get the agent card."""
        return self.client.json_agent_card

    @property
    def skills(self) -> list[dict[str, any]]:
        """Get the agent skills."""
        agent_card = self.agent_card
        if agent_card and isinstance(agent_card, dict):
            return agent_card.get("skills", [])
        return []

    async def query(self, message_text: str) -> str:
        """Ask a question and return the response with metadata."""
        return await self.client.ask_with_metadata(message_text, {})

    # NOTE: This is a main entry point for the agent.
    @ToolCallable.tool
    async def solve(self, message_text: str) -> str:
        """Solve a problem by delegating to the agent."""
        return await self.query(message_text)

    def refresh_agent_card(self):
        """Refresh the agent card."""
        self.client.refresh_agent_card()

    def __getattribute__(self, name):
        # For specific internal attributes, use the parent method directly to avoid recursion
        if name in ["_name", "_description", "_config", "client", "_agent_card", "_json_agent_card"]:
            return super().__getattribute__(name)

        method = super().__getattribute__(name)

        # Only modify the solve method's docstring
        if name == "solve" and callable(method):
            try:
                # Use direct attribute access to avoid recursion
                client = super().__getattribute__("client")
                agent_card = client.json_agent_card
                if agent_card and isinstance(agent_card, dict):
                    skills = Misc.get_field(agent_card, "skills", [])
                    skills_str = "\n".join(
                        [f"- {Misc.get_field(skill, 'name')}: {Misc.get_field(skill, 'description')}" for skill in skills[:5]]
                    )
                    if len(skills) > 5:
                        skills_str += f"\n... and {len(skills) - 5} more"
                    method.__func__.__doc__ = (
                        "@description: " + method.__func__.__doc__ + "\n\n" + f"Agent: {Misc.get_field(agent_card, 'name')}\n"
                        f"Description: {Misc.get_field(agent_card, 'description')}\n"
                        f"Available skills:\n{skills_str}"
                    )
            except (AttributeError, Exception):
                # If we can't access agent card safely, just return the method without modification
                pass

        return method


if __name__ == "__main__":
    a2a = A2AAgent(name="a2a hello", url="http://localhost:5001")
    print(a2a.list_openai_functions())
