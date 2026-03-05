import pytest

from dana.common.llm.types import LLMMessage, LLMResponse
from dana.core.agent.star_agent import STARAgent
from dana.core.timeline.timeline import Timeline, TimelineEntry, TimelineEntryType
from dana.core.resource.base_resource import BaseResource
from dana.core.runtime import AgentRuntime, ParsedResponse, RuntimeRegistry
from dana.core.runtime.default import DefaultRuntime


def test_parsed_response_dataclass():
    parsed = ParsedResponse(
        done=True,
        reasoning="reason",
        response="answer",
        tool_calls=[{"function": "Tool:call", "arguments": {}}],
    )

    assert parsed.done is True
    assert parsed.reasoning == "reason"
    assert parsed.response == "answer"
    assert parsed.tool_calls == [{"function": "Tool:call", "arguments": {}}]


def test_default_runtime_initialization():
    runtime = DefaultRuntime()

    assert runtime.llm is None
    assert runtime._temperature == 0
    assert runtime._max_tokens is None


def test_default_runtime_initialization_custom_llm():
    class DummyLLM:
        pass

    llm = DummyLLM()
    runtime = DefaultRuntime(llm=llm)

    assert runtime.llm is llm


def test_default_runtime_build_prompt():
    class MockLLM:
        pass

    agent = STARAgent(
        agent_type="runtime-test", auto_register=False, enable_web_search=False, enable_skills=False, enable_code_execution=False
    )
    runtime = DefaultRuntime(llm=MockLLM())  # Pass mock LLM to avoid API key requirement
    timeline = Timeline(agent=agent)
    timeline.add_entry(
        TimelineEntry(
            entry_type=TimelineEntryType.USER_MESSAGE,
            content="Hello",
            is_latest_user_message=True,
        )
    )

    messages = runtime.build_prompt(agent, timeline)

    assert isinstance(messages, list)
    assert messages
    assert isinstance(messages[0], LLMMessage)


def test_default_runtime_parse_response_done_true():
    runtime = DefaultRuntime()
    response = LLMResponse(content='{"done": true, "response": "Done", "tool_calls": []}', model="test")

    parsed = runtime.parse_response(response)

    assert parsed.done is True
    assert parsed.response == "Done"
    assert parsed.tool_calls == []


def test_default_runtime_parse_response_done_false():
    runtime = DefaultRuntime()
    response = LLMResponse(
        content='{"done": false, "response": null, "tool_calls": [{"name": "Tool:run", "parameters": {}}]}',
        model="test",
    )

    parsed = runtime.parse_response(response)

    assert parsed.done is False
    assert parsed.response is None
    assert parsed.tool_calls == [{"function": "Tool:run", "arguments": {}}]


def test_default_runtime_parse_response_with_tool_calls():
    runtime = DefaultRuntime()
    response = LLMResponse(
        content='{"done": false, "response": null, "tool_calls": [{"name": "Tool:run", "parameters": {"message": "hi"}}]}',
        model="test",
    )

    parsed = runtime.parse_response(response)

    assert parsed.done is False
    assert parsed.tool_calls == [{"function": "Tool:run", "arguments": {"message": "hi"}}]


def test_default_runtime_execute_tools():
    class EchoResource(BaseResource):
        def __init__(self):
            super().__init__(resource_type="echo", resource_id="echo", auto_register=False)

        def echo(self, message: str) -> str:
            return f"echo:{message}"

    agent = STARAgent(
        agent_type="runtime-test", auto_register=False, enable_web_search=False, enable_skills=False, enable_code_execution=False
    )
    resource = EchoResource()
    agent.with_resources(resource)

    runtime = DefaultRuntime()
    results = runtime.execute_tools(agent, [{"function": "EchoResource:echo", "arguments": {"message": "hi"}}])

    assert results[0]["success"] is True
    assert results[0]["result"] == "echo:hi"


def test_star_agent_with_runtime_parameter():
    runtime = DefaultRuntime()
    agent = STARAgent(
        agent_type="runtime-test",
        runtime=runtime,
        auto_register=False,
        enable_web_search=False,
        enable_skills=False,
        enable_code_execution=False,
    )

    assert agent._runtime is runtime


def test_star_agent_default_runtime():
    agent = STARAgent(
        agent_type="runtime-test", auto_register=False, enable_web_search=False, enable_skills=False, enable_code_execution=False
    )

    # Runtime is auto-selected based on provider - should be an AgentRuntime subclass
    assert isinstance(agent._runtime, AgentRuntime)


def test_star_agent_deprecated_codec_parameter():
    from dana.core.knowledge.prompts.codecs import CSXMLCodec

    with pytest.warns(DeprecationWarning):
        STARAgent(
            agent_type="runtime-test",
            codec=CSXMLCodec,
            auto_register=False,
            enable_web_search=False,
            enable_skills=False,
            enable_code_execution=False,
        )


def test_think_uses_runtime_methods():
    class TrackingRuntime(AgentRuntime):
        def __init__(self):
            self.calls = []
            self._count = 0

        def validate_done_output(self, done, has_tool_calls, has_response):
            self.calls.append("validate_done_output")
            return done, has_tool_calls, has_response

        def build_prompt(self, agent, timeline, learned_context=None):
            self.calls.append("build_prompt")
            return [LLMMessage(role="system", content="system"), LLMMessage(role="user", content="hello")]

        def call_llm(self, messages):
            self.calls.append("call_llm")
            self._count += 1
            if self._count == 1:
                return LLMResponse(
                    content='{"done": false, "response": null, "tool_calls": [{"name": "Tool:run", "parameters": {}}]}', model="test"
                )
            return LLMResponse(content='{"done": true, "response": "ok", "tool_calls": []}', model="test")

        def parse_response(self, response):
            self.calls.append("parse_response")
            content = response.content if isinstance(response, LLMResponse) else str(response)
            if '"done": false' in content:
                return ParsedResponse(done=False, reasoning=None, response=None, tool_calls=[{"function": "Tool:run", "arguments": {}}])
            return ParsedResponse(done=True, reasoning=None, response="ok", tool_calls=[])

        def execute_tools(self, agent, tool_calls):
            self.calls.append("execute_tools")
            return []

        def get_output_instructions(self):
            return ""

        def get_system_prompt_template(self, native_tools: bool) -> str:
            return ""

    runtime = TrackingRuntime()
    agent = STARAgent(
        agent_type="runtime-test",
        runtime=runtime,
        auto_register=False,
        enable_web_search=False,
        enable_skills=False,
        enable_code_execution=False,
    )

    agent.query(message="hello")

    assert runtime.calls[:5] == ["build_prompt", "call_llm", "parse_response", "validate_done_output", "execute_tools"]
    assert "execute_tools" in runtime.calls


# RuntimeRegistry tests


def test_runtime_registry_default_returns_default_runtime():
    registry = RuntimeRegistry()
    runtime = registry.select(model="gpt-4", provider="openai")
    assert isinstance(runtime, DefaultRuntime)


def test_runtime_registry_matches_provider():
    class CustomRuntime(DefaultRuntime):
        pass

    registry = RuntimeRegistry()
    registry.register(CustomRuntime, provider="openai")

    # Should match openai
    runtime = registry.select(model="gpt-4", provider="openai")
    assert isinstance(runtime, CustomRuntime)

    # Should fallback for anthropic
    runtime = registry.select(model="claude-3", provider="anthropic")
    assert isinstance(runtime, DefaultRuntime)
    assert not isinstance(runtime, CustomRuntime)


def test_runtime_registry_matches_model_pattern():
    class ClaudeRuntime(DefaultRuntime):
        pass

    registry = RuntimeRegistry()
    registry.register(ClaudeRuntime, model_pattern="claude-*")

    # Should match claude models
    runtime = registry.select(model="claude-3-opus", provider="anthropic")
    assert isinstance(runtime, ClaudeRuntime)

    # Should fallback for gpt models
    runtime = registry.select(model="gpt-4", provider="openai")
    assert isinstance(runtime, DefaultRuntime)
    assert not isinstance(runtime, ClaudeRuntime)


def test_runtime_registry_priority():
    class LowPriorityRuntime(DefaultRuntime):
        pass

    class HighPriorityRuntime(DefaultRuntime):
        pass

    registry = RuntimeRegistry()
    registry.register(LowPriorityRuntime, priority=0)
    registry.register(HighPriorityRuntime, priority=10)

    # Higher priority should win
    runtime = registry.select(model="any", provider="any")
    assert isinstance(runtime, HighPriorityRuntime)


def test_runtime_registry_passes_kwargs():
    registry = RuntimeRegistry()
    registry.register(DefaultRuntime, priority=0)

    runtime = registry.select(model="gpt-4", provider="openai", temperature=0.5)
    assert runtime._temperature == 0.5


def test_runtime_registry_select_runtime_classmethod():
    from dana.core.runtime.anthropic import AnthropicRuntime

    runtime = RuntimeRegistry.select_runtime(model="claude-3", provider="anthropic")
    # Should return AnthropicRuntime for anthropic provider
    assert isinstance(runtime, AnthropicRuntime)
