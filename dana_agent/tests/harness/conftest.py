"""
Pytest fixtures for STARAgent robustness testing harness.

NOTE: All tests in this directory are marked with @pytest.mark.harness
and are excluded from CI by default. Run locally with:
    pytest tests/harness/ -v
Or include in full test run with:
    pytest tests/ -m "harness"
"""

from __future__ import annotations

import pytest

# Mark all tests in this directory as harness tests (excluded from CI by default)
pytestmark = pytest.mark.harness

from dana.core.resource.base_resource import BaseResource
from dana.core.workflow.base_workflow import BaseWorkflow

from .fault_injection import FaultInjector, FaultConfig, FaultScenarios
from .harness_agent import HarnessAgent
from .mocks.llm_client import MockLLMClient, LLMResponseScenario, SmallLLMScenarios
from .mocks.resources import (
    MockResource,
    AsyncMockResource,
    FailingResource,
    MockWorkflow,
    AsyncMockWorkflow,
    FailingWorkflow,
)


# ==================== Core Fixtures ====================

@pytest.fixture
def mock_llm():
    """Configurable mock LLM client."""
    return MockLLMClient()


@pytest.fixture
def fault_injector():
    """Fault injection framework."""
    return FaultInjector()


@pytest.fixture
def harness_agent(mock_llm):
    """
    Instrumented STARAgent for testing.

    Uses mock LLM by default, no auto-registration.
    """
    return HarnessAgent(
        mock_llm=mock_llm,
        agent_type="test_harness",
        auto_register=False,
    )


@pytest.fixture
def harness_agent_with_faults(mock_llm, fault_injector):
    """Instrumented STARAgent with fault injection."""
    return HarnessAgent(
        mock_llm=mock_llm,
        fault_injector=fault_injector,
        agent_type="test_harness_faults",
        auto_register=False,
    )


# ==================== Resource Fixtures ====================

@pytest.fixture
def mock_resource():
    """Simple mock resource for testing."""
    return MockResource(
        resource_id="mock-resource",
        default_response="Mock resource response",
        auto_register=False,
    )


@pytest.fixture
def async_mock_resource():
    """Async mock resource for testing."""
    return AsyncMockResource(
        resource_id="async-mock-resource",
        default_response="Async mock response",
        auto_register=False,
    )


@pytest.fixture
def failing_resource():
    """Resource that always fails."""
    return FailingResource(
        resource_id="failing-resource",
        auto_register=False,
    )


# ==================== Workflow Fixtures ====================

@pytest.fixture
def mock_workflow():
    """Simple mock workflow for testing."""
    return MockWorkflow(
        workflow_id="mock-workflow",
        auto_register=False,
    )


@pytest.fixture
def async_mock_workflow():
    """Async mock workflow for testing."""
    return AsyncMockWorkflow(
        workflow_id="async-mock-workflow",
        auto_register=False,
    )


@pytest.fixture
def failing_workflow():
    """Workflow that always fails."""
    return FailingWorkflow(
        workflow_id="failing-workflow",
        auto_register=False,
    )


# ==================== Agent with Resources Fixtures ====================

@pytest.fixture
def harness_agent_with_resource(mock_llm, mock_resource):
    """Harness agent with a mock resource attached."""
    agent = HarnessAgent(
        mock_llm=mock_llm,
        agent_type="test_with_resource",
        auto_register=False,
    )
    agent.with_resources(mock_resource)
    return agent


@pytest.fixture
def harness_agent_with_workflow(mock_llm, mock_workflow):
    """Harness agent with a mock workflow attached."""
    agent = HarnessAgent(
        mock_llm=mock_llm,
        agent_type="test_with_workflow",
        auto_register=False,
    )
    agent.with_workflows(mock_workflow)
    return agent


# ==================== LLM Response Scenario Fixtures ====================

@pytest.fixture
def empty_response():
    """Empty LLM response scenario."""
    return MockLLMClient.empty_response()


@pytest.fixture
def simple_response():
    """Simple text response."""
    return MockLLMClient.simple_response("This is a simple response.")


@pytest.fixture
def well_formed_tool_call():
    """Well-formed XML tool call."""
    return MockLLMClient.well_formed_tool_call()


@pytest.fixture
def malformed_responses():
    """Collection of malformed response scenarios."""
    return [
        MockLLMClient.malformed_xml_missing_closing(),
        MockLLMClient.malformed_xml_wrong_tag(),
        MockLLMClient.json_in_xml(),
        MockLLMClient.partial_response(),
    ]


@pytest.fixture
def small_llm_scenarios():
    """Common failure patterns from small LLMs."""
    return SmallLLMScenarios.all_scenarios()


# ==================== Fault Scenario Fixtures ====================

@pytest.fixture
def think_phase_fault():
    """Fault configuration for _think phase exception."""
    return FaultScenarios.think_phase_exception()


@pytest.fixture
def act_phase_fault():
    """Fault configuration for _act phase exception."""
    return FaultScenarios.act_phase_exception()


@pytest.fixture
def intermittent_fault():
    """Intermittent fault with 30% probability."""
    return FaultScenarios.intermittent_think_failure(probability=0.3)


@pytest.fixture
def slow_think_fault():
    """Slow _think phase for timeout testing."""
    return FaultScenarios.slow_think(delay_ms=2000)


# ==================== Composite Fixtures ====================

@pytest.fixture
def agent_with_failing_resource(mock_llm, failing_resource):
    """Agent with a resource that always fails."""
    agent = HarnessAgent(
        mock_llm=mock_llm,
        agent_type="test_failing_resource",
        auto_register=False,
    )
    agent.with_resources(failing_resource)
    return agent


@pytest.fixture
def agent_with_async_resources(mock_llm, async_mock_resource, async_mock_workflow):
    """Agent with async resources and workflows."""
    agent = HarnessAgent(
        mock_llm=mock_llm,
        agent_type="test_async",
        auto_register=False,
    )
    agent.with_resources(async_mock_resource)
    agent.with_workflows(async_mock_workflow)
    return agent


# ==================== Parametrized Fixtures ====================

@pytest.fixture(params=[
    "empty",
    "malformed_closing",
    "wrong_tag",
    "json_in_xml",
    "partial",
])
def problematic_response(request):
    """Parametrized fixture for various problematic LLM responses."""
    scenarios = {
        "empty": MockLLMClient.empty_response(),
        "malformed_closing": MockLLMClient.malformed_xml_missing_closing(),
        "wrong_tag": MockLLMClient.malformed_xml_wrong_tag(),
        "json_in_xml": MockLLMClient.json_in_xml(),
        "partial": MockLLMClient.partial_response(),
    }
    return scenarios[request.param]


@pytest.fixture(params=["see", "think", "act", "reflect"])
def fault_phase(request):
    """Parametrized fixture for each STAR phase."""
    return request.param


# ==================== Multi-turn Conversation Fixtures ====================

@pytest.fixture
def multi_turn_scenario(mock_llm):
    """
    Setup for multi-turn conversation testing.

    Returns a mock LLM with queued responses for a multi-turn interaction.
    """
    # Turn 1: Tool call
    mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
        target_id="mock-resource",
        method="query",
        message="first query",
    ))
    # Turn 2: Another tool call
    mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
        target_id="mock-resource",
        method="query",
        message="second query",
    ))
    # Turn 3: Final response (no tool calls)
    mock_llm.queue_response(MockLLMClient.simple_response(
        "Based on my research, here is the answer."
    ))
    return mock_llm


@pytest.fixture
def retry_scenario(mock_llm):
    """
    Setup for retry logic testing.

    Returns a mock LLM that fails twice then succeeds.
    """
    # First two attempts: empty responses
    mock_llm.queue_response(MockLLMClient.empty_response())
    mock_llm.queue_response(MockLLMClient.empty_response())
    # Third attempt: success
    mock_llm.queue_response(MockLLMClient.simple_response("Success after retries"))
    return mock_llm


@pytest.fixture
def max_iterations_scenario(mock_llm):
    """
    Setup for MAX_ITERATIONS testing.

    Returns a mock LLM that always returns tool calls (never exits naturally).
    """
    # Queue 15 tool call responses (more than MAX_ITERATIONS=10)
    for i in range(15):
        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource",
            method="query",
            message=f"iteration {i}",
        ))
    return mock_llm
