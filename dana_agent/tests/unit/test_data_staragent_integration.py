"""Tests for Data/RLMResource STARAgent integration.

These tests verify that RLMResources attached to STARAgent via with_resources()
are automatically queried when building context via PromptBuilder (retrieved context path).
"""

from dana.common.llm.types import LLMMessage
from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType
from dana.core.prompt.prompt_builder import PromptBuilder


class DummyTimeline:
    """Minimal timeline for prompt builder tests."""

    def __init__(self, task: str, max_context_tokens: int = 10000):
        self.max_context_tokens = max_context_tokens
        # timeline holds TimelineEntry objects (used by _get_latest_user_task)
        self.timeline = [TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content=task)]

    def set_context(self, context: dict) -> None:
        pass

    def to_llm_messages(self) -> list[LLMMessage]:
        return [LLMMessage(role="user", content=entry.content) for entry in self.timeline]


class DummyResource:
    """Queryable resource with tracking."""

    def __init__(self, resource_id: str = "docs", response: str = "resource response"):
        self.resource_id = resource_id
        self.response = response
        self.last_query = None

    def query(self, question: str) -> str:
        self.last_query = question
        return self.response


class DummyAgent:
    """Minimal agent for PromptBuilder tests."""

    def __init__(self, resources: list[DummyResource]):
        self._resources = resources
        self._agents = []
        self._workflows = []
        self._ltmemory = None
        self._learner = None
        self._reminder_manager = None
        self.object_id = "dummy-agent"
        self.agent_type = "dummy"


def _build_prompt_messages(resource: DummyResource, task: str) -> list[LLMMessage]:
    """Build messages via PromptBuilder with retrieved context enabled (non-codec path)."""
    agent = DummyAgent([resource])
    builder = PromptBuilder(
        identity_fn=lambda a: "IDENTITY",
        template_fn=lambda native: "{{identity}}",
        format_tool_fn=lambda sig: "",
        system_prompt_fn=lambda: "SYSTEM",
        skip_retrieved_context=False,  # Enable context retrieval
    )
    timeline = DummyTimeline(task)
    return builder.build_prompt(
        agent,
        timeline,
        learned_context=None,
        native_tools=None,
        runtime_context={},
    )


class TestLocalPromptAPIRLMResources:
    """Tests for RLM resource integration via PromptBuilder retrieved context."""

    def test_local_prompt_api_adds_rlm_resources(self):
        """PromptBuilder should add RLMResources to ContextBuilder and include tagged output."""
        resource = DummyResource(resource_id="docs", response="Docs content")

        messages = _build_prompt_messages(resource, task="Find auth")

        context_message = next(msg for msg in messages if msg.role == "user" and "<CONTEXT>" in msg.content)
        assert "<DOCS>" in context_message.content

    def test_rlm_resource_queried_with_task(self):
        """RLMResource should be queried with the current task."""
        resource = DummyResource(resource_id="code", response="Code content")

        _build_prompt_messages(resource, task="Find auth handlers")

        assert resource.last_query == "Find auth handlers"

    def test_rlm_resource_result_in_context(self):
        """RLMResource query result should appear in built context."""
        resource = DummyResource(resource_id="notes", response="Notes content")

        messages = _build_prompt_messages(resource, task="Summarize notes")

        context_message = next(msg for msg in messages if msg.role == "user" and "<CONTEXT>" in msg.content)
        assert "Notes content" in context_message.content
