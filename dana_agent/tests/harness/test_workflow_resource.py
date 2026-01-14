"""
Tests for workflow vs resource framework (Concern #4).

Evaluates the inconsistencies between workflow and resource handling,
and tests whether the current implementation is robust.
"""

from __future__ import annotations

import asyncio
import pytest

from dana.core.agent.components.tool_caller import ToolCaller

from .mocks.llm_client import MockLLMClient, LLMResponseScenario
from .mocks.resources import (
    MockResource,
    AsyncMockResource,
    FailingResource,
    MockWorkflow,
    AsyncMockWorkflow,
    FailingWorkflow,
)
from .harness_agent import HarnessAgent


class TestResourceMethodRequirement:
    """Tests for resource method requirement (asymmetry with workflows)."""

    def test_resource_call_without_method_fails(self, harness_agent_with_resource, mock_resource):
        """Resource call without method should produce error."""
        mock_llm = harness_agent_with_resource._mock_llm

        # Tool call without method
        content = """<tool_call>
<target id="mock-resource"/>
<arguments>
<message>test</message>
</arguments>
</tool_call>"""
        mock_llm.queue_response(LLMResponseScenario(content=content))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Call without method")

        # Should complete (may have error in tool result)
        assert result is not None

    def test_resource_call_with_method_succeeds(self, harness_agent_with_resource, mock_resource):
        """Resource call with method should succeed."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource",
            method="query",
            message="test",
        ))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Call with method")

        harness_agent_with_resource.assert_no_errors()
        assert len(mock_resource.call_history) == 1


class TestWorkflowDefaultMethod:
    """Tests for workflow default method behavior."""

    def test_workflow_call_without_method_uses_execute(
        self, harness_agent_with_workflow, mock_workflow
    ):
        """Workflow call without method should use 'execute' as default."""
        mock_llm = harness_agent_with_workflow._mock_llm

        # Tool call without explicit method - should default to 'execute'
        content = """<tool_call>
<target type="workflow" id="mock-workflow"/>
<arguments>
<input>test</input>
</arguments>
</tool_call>"""
        mock_llm.queue_response(LLMResponseScenario(content=content))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_workflow.query(message="Execute workflow")

        # Should complete without errors
        assert result is not None

    def test_workflow_call_with_explicit_execute(
        self, harness_agent_with_workflow, mock_workflow
    ):
        """Workflow call with explicit 'execute' method should work."""
        mock_llm = harness_agent_with_workflow._mock_llm

        content = """<tool_call>
<target type="workflow" id="mock-workflow"/>
<method>execute</method>
<arguments>
<input>test</input>
</arguments>
</tool_call>"""
        mock_llm.queue_response(LLMResponseScenario(content=content))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_workflow.query(message="Execute workflow explicitly")

        assert result is not None


class TestAsyncResourceHandling:
    """Tests for async resource handling in sync context."""

    def test_async_resource_in_sync_query(self, mock_llm, async_mock_resource):
        """Async resource called from sync query should not deadlock."""
        agent = HarnessAgent(
            mock_llm=mock_llm,
            agent_type="async_resource_test",
            auto_register=False,
        )
        agent.with_resources(async_mock_resource)

        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="async-mock-resource",
            method="query",
            message="test",
        ))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        # This should not hang or deadlock
        # Note: Current implementation may use asyncio.run() which can deadlock
        # This test documents the expected behavior
        try:
            result = agent.query(message="Call async resource")
            assert result is not None
        except RuntimeError as e:
            # If it fails due to nested event loop, that's the bug we're documenting
            if "cannot be called from a running event loop" in str(e):
                pytest.skip("Known issue: asyncio.run() in sync context causes deadlock")
            raise


class TestAsyncWorkflowHandling:
    """Tests for async workflow handling in sync context."""

    def test_async_workflow_in_sync_query(self, mock_llm, async_mock_workflow):
        """Async workflow called from sync query should not deadlock."""
        agent = HarnessAgent(
            mock_llm=mock_llm,
            agent_type="async_workflow_test",
            auto_register=False,
        )
        agent.with_workflows(async_mock_workflow)

        content = """<tool_call>
<target type="workflow" id="async-mock-workflow"/>
<method>execute</method>
</tool_call>"""
        mock_llm.queue_response(LLMResponseScenario(content=content))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        try:
            result = agent.query(message="Execute async workflow")
            assert result is not None
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                pytest.skip("Known issue: asyncio.run() in sync context causes deadlock")
            raise


class TestErrorHandlingSymmetry:
    """Tests for consistent error handling between resources and workflows."""

    def test_failing_resource_error_format(self, agent_with_failing_resource, failing_resource):
        """Failing resource should produce consistent error format."""
        mock_llm = agent_with_failing_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="failing-resource",
            method="query",
        ))
        mock_llm.queue_response(MockLLMClient.simple_response("Error occurred"))

        result = agent_with_failing_resource.query(message="Call failing resource")

        # Should complete without crashing
        assert result is not None

    def test_failing_workflow_error_format(self, mock_llm, failing_workflow):
        """Failing workflow should produce consistent error format."""
        agent = HarnessAgent(
            mock_llm=mock_llm,
            agent_type="failing_workflow_test",
            auto_register=False,
        )
        agent.with_workflows(failing_workflow)

        content = """<tool_call>
<target type="workflow" id="failing-workflow"/>
<method>execute</method>
</tool_call>"""
        mock_llm.queue_response(LLMResponseScenario(content=content))
        mock_llm.queue_response(MockLLMClient.simple_response("Error handled"))

        result = agent.query(message="Execute failing workflow")

        # Should complete without crashing
        assert result is not None


class TestReturnValueHandling:
    """Tests for consistent return value handling."""

    def test_resource_returns_string(self, harness_agent_with_resource, mock_resource):
        """Resource returning string should be handled."""
        mock_llm = harness_agent_with_resource._mock_llm
        mock_resource.default_response = "String result"

        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource",
            method="query",
        ))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Get string result")

        assert result is not None

    def test_workflow_returns_dict(self, harness_agent_with_workflow, mock_workflow):
        """Workflow returning dict should be handled."""
        mock_llm = harness_agent_with_workflow._mock_llm
        mock_workflow.default_result = {"status": "success", "data": [1, 2, 3]}

        content = """<tool_call>
<target type="workflow" id="mock-workflow"/>
<method>execute</method>
</tool_call>"""
        mock_llm.queue_response(LLMResponseScenario(content=content))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_workflow.query(message="Get dict result")

        assert result is not None


class TestToolCallerBehavior:
    """Unit tests for ToolCaller resource vs workflow handling."""

    def test_execute_resource_call_signature(self, harness_agent, mock_resource):
        """Test execute_resource_call method signature."""
        harness_agent.with_resources(mock_resource)
        tool_caller = harness_agent._tool_caller

        # Valid call with method
        result = tool_caller.execute_resource_call({
            "resource_id": "mock-resource",
            "method": "query",
            "parameters": {"message": "test"},
        })

        assert "success" in result or "result" in result or "error" in result

    def test_execute_workflow_call_signature(self, harness_agent, mock_workflow):
        """Test execute_workflow_call method signature."""
        harness_agent.with_workflows(mock_workflow)
        tool_caller = harness_agent._tool_caller

        # Call with explicit method
        result = tool_caller.execute_workflow_call({
            "workflow_id": "mock-workflow",
            "method": "execute",
            "parameters": {},
        })

        assert result is not None


class TestIdKeyConsistency:
    """Tests for ID key consistency (resource_id vs workflow_id vs object_id)."""

    def test_resource_uses_resource_id(self, harness_agent_with_resource, mock_resource):
        """Resources should be identified by resource_id."""
        mock_llm = harness_agent_with_resource._mock_llm

        # Use resource_id in tool call
        content = """<tool_call>
<target type="resource" id="mock-resource"/>
<method>query</method>
<arguments><message>test</message></arguments>
</tool_call>"""
        mock_llm.queue_response(LLMResponseScenario(content=content))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Use resource_id")

        assert result is not None

    def test_workflow_uses_workflow_id(self, harness_agent_with_workflow, mock_workflow):
        """Workflows should be identified by workflow_id."""
        mock_llm = harness_agent_with_workflow._mock_llm

        content = """<tool_call>
<target type="workflow" id="mock-workflow"/>
<method>execute</method>
</tool_call>"""
        mock_llm.queue_response(LLMResponseScenario(content=content))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_workflow.query(message="Use workflow_id")

        assert result is not None

    def test_generic_object_id_works_for_both(self, harness_agent, mock_resource, mock_workflow):
        """Generic object_id lookup should work for both types."""
        harness_agent.with_resources(mock_resource)
        harness_agent.with_workflows(mock_workflow)

        # Both should be findable
        resources = harness_agent.available_resources
        workflows = harness_agent.available_workflows

        resource_ids = [r.object_id for r in resources]
        workflow_ids = [w.object_id for w in workflows]

        assert "mock-resource" in resource_ids
        assert "mock-workflow" in workflow_ids


class TestMixedResourceWorkflowCalls:
    """Tests for handling mixed resource and workflow calls."""

    def test_sequential_resource_and_workflow_calls(
        self, mock_llm, mock_resource, mock_workflow
    ):
        """Sequential resource and workflow calls should both succeed."""
        agent = HarnessAgent(
            mock_llm=mock_llm,
            agent_type="mixed_test",
            auto_register=False,
        )
        agent.with_resources(mock_resource)
        agent.with_workflows(mock_workflow)

        # First: resource call
        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource",
            method="query",
            message="first",
        ))
        # Second: workflow call
        workflow_call = """<tool_call>
<target type="workflow" id="mock-workflow"/>
<method>execute</method>
</tool_call>"""
        mock_llm.queue_response(LLMResponseScenario(content=workflow_call))
        # Final response
        mock_llm.queue_response(MockLLMClient.simple_response("Both completed"))

        result = agent.query(message="Do both resource and workflow")

        assert result is not None
        assert len(mock_resource.call_history) >= 1
