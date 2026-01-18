from dana.common.llm.types import LLMResponse
from dana.core.agent.star_agent import STARAgent
from dana.core.resource.base_resource import BaseResource


class MockLLM:
    def __init__(self, responses):
        self._responses = list(responses)
        self.call_count = 0
        self.calls = []

    def chat_response_sync(self, messages, **kwargs):
        self.call_count += 1
        self.calls.append(messages)
        if not self._responses:
            raise AssertionError("MockLLM response queue exhausted")
        return self._responses.pop(0)


class MockResource(BaseResource):
    def __init__(self, **kwargs):
        super().__init__(resource_type="mock", resource_id="mock-resource", auto_register=False, **kwargs)
        self.calls = []

    def query(self, message: str) -> str:
        self.calls.append(message)
        return "ok"


def make_response(content: str) -> LLMResponse:
    return LLMResponse(content=content, model="mock", usage={"prompt_tokens": 1, "completion_tokens": 1}, finish_reason="stop")


def make_agent(mock_llm: MockLLM, resources=None) -> STARAgent:
    agent = STARAgent(
        agent_type="test",
        auto_register=False,
        enable_web_search=False,
        enable_skills=False,
    )
    agent.llm_client = mock_llm
    if resources:
        agent.with_resources(*resources)
    return agent


def test_exit_when_done_true_with_response():
    mock_llm = MockLLM([
        make_response(
            "<done>true</done>"
            "<function_call></function_call>"
            "<response>Done</response>"
        )
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="finish")

    assert mock_llm.call_count == 1
    assert result.get("response") == "Done"
    assert result.get("tool_calls") == []


def test_continue_when_done_false_with_function_call():
    mock_llm = MockLLM([
        make_response(
            "<done>false</done>"
            "<function_call>"
            "<invoke name=\"mock-resource:query\">"
            "<parameter name=\"message\">hello</parameter>"
            "</invoke>"
            "</function_call>"
            "<response></response>"
        ),
        make_response(
            "<done>true</done>"
            "<function_call></function_call>"
            "<response>Finished</response>"
        ),
    ])
    resource = MockResource()
    agent = make_agent(mock_llm, resources=[resource])

    result = agent.query(message="run")

    assert mock_llm.call_count == 2
    assert "hello" in resource.calls
    assert resource.calls[-1] == "hello"
    assert result.get("response") == "Finished"


def test_retry_when_done_false_no_function_call():
    mock_llm = MockLLM([
        make_response(
            "<done>false</done>"
            "<function_call></function_call>"
            "<response></response>"
        ),
        make_response(
            "<done>true</done>"
            "<function_call></function_call>"
            "<response>Ok</response>"
        ),
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="retry")

    assert mock_llm.call_count == 2
    assert result.get("response") == "Ok"


def test_retry_when_done_true_no_response():
    mock_llm = MockLLM([
        make_response(
            "<done>true</done>"
            "<function_call></function_call>"
            "<response></response>"
        ),
        make_response(
            "<done>true</done>"
            "<function_call></function_call>"
            "<response>Now complete</response>"
        ),
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="retry")

    assert mock_llm.call_count == 2
    assert result.get("response") == "Now complete"


def test_retry_on_parse_failure():
    mock_llm = MockLLM([
        make_response("<response>Missing done</response>"),
        make_response(
            "<done>true</done>"
            "<function_call></function_call>"
            "<response>Recovered</response>"
        ),
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="retry")

    assert mock_llm.call_count == 2
    assert result.get("response") == "Recovered"


def test_max_retries_per_iteration():
    mock_llm = MockLLM([
        make_response("<response>Missing done</response>"),
        make_response("<response>Missing done</response>"),
        make_response("<response>Missing done</response>"),
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="retry")

    assert mock_llm.call_count == 3
    assert result.get("response") == "No response generated"


def test_max_iterations():
    mock_llm = MockLLM([
        make_response(
            "<done>false</done>"
            "<function_call>"
            "<invoke name=\"mock-resource:query\">"
            "<parameter name=\"message\">step</parameter>"
            "</invoke>"
            "</function_call>"
            "<response></response>"
        )
        for _ in range(12)
    ])
    resource = MockResource()
    agent = make_agent(mock_llm, resources=[resource])

    agent.query(message="loop")

    assert mock_llm.call_count == 10


def test_simple_task_single_turn():
    mock_llm = MockLLM([
        make_response(
            "<done>true</done>"
            "<function_call></function_call>"
            "<response>4</response>"
        )
    ])
    agent = make_agent(mock_llm)

    result = agent.query(message="2+2")

    assert mock_llm.call_count == 1
    assert result.get("response") == "4"


def test_prompt_contains_output_format():
    agent = STARAgent(agent_type="prompt", auto_register=False, enable_web_search=False, enable_skills=False)
    system_prompt = agent.system_prompt

    assert "<output_format>" in system_prompt
    assert "<done>" in system_prompt
