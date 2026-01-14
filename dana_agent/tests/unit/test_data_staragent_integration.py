"""Tests for Data/RLMResource STARAgent integration.

These tests verify that RLMResources attached to STARAgent via with_resources()
are automatically queried when building context in LocalPromptAPI (codec system).
"""

import pytest

from dana.common.llm.types import LLMMessage
from dana.core.knowledge.prompts import LocalPromptAPI
from dana.core.knowledge.prompts.codecs import CSXMLCodec


class DummyTimeline:
    """Minimal timeline for prompt engineer tests."""

    def __init__(self, messages: list[LLMMessage], max_context_tokens: int = 10000):
        self._messages = messages
        self.max_context_tokens = max_context_tokens
        self.timeline = messages

    def to_llm_messages(self, separate_latest_user: bool = True) -> list[LLMMessage]:
        return self._messages


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
    """Minimal agent for LocalPromptAPI tests."""

    def __init__(self, resources: list[DummyResource]):
        self._resources = resources
        self._agents = []
        self._workflows = []
        self._ltmemory = None
        self._learner = None
        self.object_id = "dummy-agent"
        self.agent_type = "dummy"
        self._codec = CSXMLCodec


def _build_prompt_messages(monkeypatch: pytest.MonkeyPatch, resource: DummyResource, task: str) -> list[LLMMessage]:
    agent = DummyAgent([resource])
    prompt_api = LocalPromptAPI(agent, codec=CSXMLCodec)
    monkeypatch.setattr(LocalPromptAPI, "system_prompt", property(lambda self: "SYSTEM"))
    timeline = DummyTimeline([LLMMessage(role="user", content=task)])
    return prompt_api.build_llm_request(timeline)


class TestLocalPromptAPIRLMResources:
    """Tests for LocalPromptAPI RLM resource integration."""

    def test_local_prompt_api_adds_rlm_resources(self, monkeypatch: pytest.MonkeyPatch):
        """LocalPromptAPI should add RLMResources to ContextBuilder."""
        resource = DummyResource(resource_id="docs", response="Docs content")

        messages = _build_prompt_messages(monkeypatch, resource, task="Find auth")

        context_message = next(msg for msg in messages if msg.role == "assistant" and "<CONTEXT>" in msg.content)
        assert "<DOCS>" in context_message.content

    def test_rlm_resource_queried_with_task(self, monkeypatch: pytest.MonkeyPatch):
        """RLMResource should be queried with the current task."""
        resource = DummyResource(resource_id="code", response="Code content")

        _build_prompt_messages(monkeypatch, resource, task="Find auth handlers")

        assert resource.last_query == "Find auth handlers"

    def test_rlm_resource_result_in_context(self, monkeypatch: pytest.MonkeyPatch):
        """RLMResource query result should appear in built context."""
        resource = DummyResource(resource_id="notes", response="Notes content")

        messages = _build_prompt_messages(monkeypatch, resource, task="Summarize notes")

        context_message = next(msg for msg in messages if msg.role == "assistant" and "<CONTEXT>" in msg.content)
        assert "Notes content" in context_message.content
