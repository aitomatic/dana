from datetime import UTC, datetime, timedelta

from python_a2a import A2AClient
from python_a2a.models import AgentCard, Message, MessageRole, Metadata, TextContent

from dana.integrations.a2a.client.message_utils import extract_text_from_response


class BaseA2AClient(A2AClient):
    """Base A2A client."""

    def __init__(
        self,
        endpoint_url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 30 * 60,
        google_a2a_compatible: bool = False,
        refresh_interval: int = 3600,
    ):
        self._refresh_interval = timedelta(seconds=refresh_interval)
        self._agent_card: AgentCard = None
        self._json_agent_card: dict = None
        self._last_refresh = datetime.now(UTC)
        super().__init__(endpoint_url, headers, timeout, google_a2a_compatible)

    @property
    def agent_card(self):
        if self._agent_card is None or datetime.now(UTC) - self._last_refresh > self._refresh_interval:
            self.refresh_agent_card()
        return self._agent_card

    @agent_card.setter
    def agent_card(self, agent_card: AgentCard):
        self._agent_card = agent_card

    @property
    def json_agent_card(self):
        if self._json_agent_card is None or datetime.now(UTC) - self._last_refresh > self._refresh_interval:
            self.refresh_agent_card()
        return self._json_agent_card

    @json_agent_card.setter
    def json_agent_card(self, json_agent_card: dict):
        self._json_agent_card = json_agent_card

    def get_json_agent_card(self):
        agent_card = self._agent_card
        skills = [{"name": skill.name, "description": skill.description, "examples": skill.examples} for skill in agent_card.skills[:3]]
        all_tags = []
        for skill in agent_card.skills[:3]:
            all_tags.extend(skill.tags)
        unique_tags = list(set(all_tags))[:5]
        return {
            "name": agent_card.name,
            "description": agent_card.description,
            "skills": skills,
            "tags": unique_tags,
        }

    def refresh_agent_card(self):
        self.agent_card = self.get_agent_card()
        self.json_agent_card = self.get_json_agent_card()
        self._last_refresh = datetime.now(UTC)

    async def ask_with_metadata(self, message_text: str, metadata: dict[str, any] | None = None) -> str:
        """Ask a question and return the response with metadata."""
        if metadata is None:
            metadata = {}
        message = Message(content=TextContent(text=message_text), role=MessageRole.USER, metadata=Metadata(custom_fields=metadata))
        response = await self.send_message_async(message)
        return extract_text_from_response(response)
