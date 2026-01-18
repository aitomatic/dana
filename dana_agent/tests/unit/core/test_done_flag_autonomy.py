import json
import os

import pytest

from dana.common.llm.types import LLMResponse
from dana.core.agent.star_agent import STARAgent
from dana.core.resource.base_resource import BaseResource


# Skip tests if no LLM API keys are available (CI environment)
def has_llm_api_key():
    """Check if any LLM API key is available."""
    keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY"]
    return any(os.getenv(k) for k in keys)


skip_without_api_key = pytest.mark.skipif(
    not has_llm_api_key(),
    reason="No LLM API keys available - skipping STAR agent tests in CI"
)


class MockLLM:
    """Mock LLM that mimics the real LLM interface."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.call_count = 0
        self.calls = []
        # Add attributes that DefaultRuntime checks
        self.provider = None
        self.provider_name = "mock"
        self.model = "mock-model"

    def chat_response_sync(self, messages, **kwargs):
        self.call_count += 1
        self.calls.append(messages)
        if not self._responses:
            raise AssertionError("MockLLM response queue exhausted")
        return self._responses.pop(0)

    async def chat_response(self, messages, **kwargs):
        """Async version for compatibility."""
        return self.chat_response_sync(messages, **kwargs)


class MockResource(BaseResource):
    def __init__(self, **kwargs):
        super().__init__(resource_type="mock", resource_id="mock-resource", auto_register=False, **kwargs)
        self.calls = []

    def query(self, message: str) -> str:
        self.calls.append(message)
        return "ok"


def make_response(content: str) -> LLMResponse:
    return LLMResponse(content=content, model="mock", usage={"prompt_tokens": 1, "completion_tokens": 1}, finish_reason="stop")


def make_json_response(done: bool, response: str | None = None, tool_calls: list | None = None) -> LLMResponse:
    """Create a JSON-formatted LLM response."""
    data = {
        "done": done,
        "response": response,
        "tool_calls": tool_calls or []
    }
    return make_response(json.dumps(data))


def make_agent(mock_llm: MockLLM, resources=None) -> STARAgent:
    from dana.core.runtime.default import DefaultRuntime

    # Pass mock LLM directly to runtime to avoid any provider initialization
    runtime = DefaultRuntime(llm=mock_llm)
    agent = STARAgent(
        agent_type="test",
        auto_register=False,
        enable_web_search=False,
        enable_skills=False,
        runtime=runtime,
    )
    # Also set agent's llm_client for any code paths that access it directly
    agent._llm_client = mock_llm
    if resources:
        agent.with_resources(*resources)
    return agent


@skip_without_api_key
def test_exit_when_done_true_with_response():
    mock_llm = MockLLM([
        make_json_response(done=True, response="Done")
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="finish")

    assert mock_llm.call_count == 1
    assert result.get("response") == "Done"
    assert result.get("tool_calls") == []


@skip_without_api_key
def test_continue_when_done_false_with_function_call():
    mock_llm = MockLLM([
        make_json_response(
            done=False,
            tool_calls=[{"name": "mock-resource:query", "parameters": {"message": "hello"}}]
        ),
        make_json_response(done=True, response="Finished"),
    ])
    resource = MockResource()
    agent = make_agent(mock_llm, resources=[resource])

    result = agent.query(message="run")

    assert mock_llm.call_count == 2
    assert "hello" in resource.calls
    assert resource.calls[-1] == "hello"
    assert result.get("response") == "Finished"


@skip_without_api_key
def test_retry_when_done_false_no_function_call():
    mock_llm = MockLLM([
        make_json_response(done=False, tool_calls=[]),
        make_json_response(done=True, response="Ok"),
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="retry")

    assert mock_llm.call_count == 2
    assert result.get("response") == "Ok"


@skip_without_api_key
def test_retry_when_done_true_no_response():
    mock_llm = MockLLM([
        make_json_response(done=True, response=None),
        make_json_response(done=True, response="Now complete"),
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="retry")

    assert mock_llm.call_count == 2
    assert result.get("response") == "Now complete"


@skip_without_api_key
def test_retry_on_parse_failure():
    mock_llm = MockLLM([
        make_response("Invalid format without JSON"),
        make_json_response(done=True, response="Recovered"),
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="retry")

    assert mock_llm.call_count == 2
    assert result.get("response") == "Recovered"


@skip_without_api_key
def test_max_retries_per_iteration():
    mock_llm = MockLLM([
        make_response("Invalid format"),
        make_response("Invalid format"),
        make_response("Invalid format"),
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="retry")

    assert mock_llm.call_count == 3
    assert result.get("response") == "No response generated"


@skip_without_api_key
def test_max_iterations():
    mock_llm = MockLLM([
        make_json_response(
            done=False,
            tool_calls=[{"name": "mock-resource:query", "parameters": {"message": "step"}}]
        )
        for _ in range(12)
    ])
    resource = MockResource()
    agent = make_agent(mock_llm, resources=[resource])

    agent.query(message="loop")

    assert mock_llm.call_count == 10


@skip_without_api_key
def test_simple_task_single_turn():
    mock_llm = MockLLM([
        make_json_response(done=True, response="4")
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="2+2")

    assert mock_llm.call_count == 1
    assert result.get("response") == "4"


@skip_without_api_key
def test_prompt_contains_output_format():
    agent = STARAgent(agent_type="prompt", auto_register=False, enable_web_search=False, enable_skills=False)
    system_prompt = agent.system_prompt

    assert '"done"' in system_prompt
    assert "JSON" in system_prompt
