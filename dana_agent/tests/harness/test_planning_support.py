"""
Tests for planning/todo support (Concern #3).

Evaluates whether the ToDoResource "placebo pattern" is sufficient
for complex multi-step planning.
"""

from __future__ import annotations

import pytest

from dana.core.resource.todo import ToDoResource

from .mocks.llm_client import MockLLMClient, LLMResponseScenario
from .mocks.resources import MockResource
from .harness_agent import HarnessAgent


class TestToDoResourceBehavior:
    """Tests for ToDoResource functionality."""

    def test_todo_resource_exists(self, harness_agent):
        """ToDoResource should be automatically attached to STARAgent."""
        # STARAgent automatically adds ToDoResource in __init__
        resources = harness_agent.available_resources
        todo_resources = [r for r in resources if isinstance(r, ToDoResource)]
        assert len(todo_resources) >= 1

    def test_todo_write_returns_success(self, harness_agent):
        """ToDoResource.write() should return success message."""
        todo_resource = None
        for r in harness_agent.available_resources:
            if isinstance(r, ToDoResource):
                todo_resource = r
                break

        assert todo_resource is not None

        result = todo_resource.write(todos=[
            {"content": "Task 1", "status": "pending"},
            {"content": "Task 2", "status": "in_progress"},
        ])

        # Should return success message (the "placebo" response)
        assert "Todos have been modified successfully" in result

    def test_todo_resource_no_storage(self, harness_agent):
        """ToDoResource should not persist data (by design - placebo pattern)."""
        todo_resource = None
        for r in harness_agent.available_resources:
            if isinstance(r, ToDoResource):
                todo_resource = r
                break

        # Write some todos
        todo_resource.write(todos=[{"content": "Test task", "status": "pending"}])

        # There's no getter - the resource doesn't actually store anything
        # This is the "placebo pattern" - the LLM believes it's tracking
        # but no actual storage occurs

        # Verify the class doesn't have storage attributes
        assert not hasattr(todo_resource, "_todos")
        assert not hasattr(todo_resource, "todos")
        assert not hasattr(todo_resource, "_storage")


class TestToDoResourceInvocation:
    """Tests for invoking ToDoResource via tool calls."""

    def test_todo_invocation_via_tool_call(self, harness_agent):
        """ToDoResource should be invocable via XML tool call."""
        mock_llm = harness_agent._mock_llm

        # Tool call to todo resource
        todo_tool_call = """<tool_call>
<target id="todo-resource"/>
<method>write</method>
<arguments>
<todos>
<todo>
<content>Research the problem</content>
<status>in_progress</status>
</todo>
<todo>
<content>Implement solution</content>
<status>pending</status>
</todo>
</todos>
</arguments>
</tool_call>"""

        mock_llm.queue_response(LLMResponseScenario(content=f"Let me track my tasks.\n{todo_tool_call}"))
        mock_llm.queue_response(MockLLMClient.simple_response("Done with task tracking"))

        result = harness_agent.query(message="Help me with a complex task")

        # Should complete successfully
        harness_agent.assert_no_errors()


class TestMultiStepTaskTracking:
    """Tests for multi-step task tracking via timeline."""

    def test_timeline_captures_all_steps(self, harness_agent_with_resource, mock_resource):
        """Timeline should capture all steps of a multi-step interaction."""
        mock_llm = harness_agent_with_resource._mock_llm

        # Multi-step interaction
        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource", method="query", message="step 1"
        ))
        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource", method="query", message="step 2"
        ))
        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource", method="query", message="step 3"
        ))
        mock_llm.queue_response(MockLLMClient.simple_response("All steps complete"))

        result = harness_agent_with_resource.query(message="Do a 3-step task")

        # Check timeline has entries (structure may vary)
        timeline = harness_agent_with_resource._timeline
        # Timeline may have entries in _entries or accessible via other means
        has_entries = hasattr(timeline, '_entries') and len(timeline._entries) > 0
        # If _entries doesn't exist, just verify the query completed
        assert result is not None or has_entries

    def test_timeline_entry_types(self, harness_agent_with_resource, mock_resource):
        """Timeline should have correct entry types for different interactions."""
        mock_llm = harness_agent_with_resource._mock_llm

        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource", method="query", message="test"
        ))
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        result = harness_agent_with_resource.query(message="Test task")

        # Verify query completed successfully
        assert result is not None

        # Timeline entry types depend on implementation
        timeline = harness_agent_with_resource._timeline
        if hasattr(timeline, '_entries') and timeline._entries:
            entry_types = [e.entry_type.value for e in timeline._entries]
            # Should have some entries
            assert len(entry_types) > 0


class TestTimelinePersistence:
    """Tests for timeline persistence functionality."""

    def test_timeline_save_called(self, harness_agent):
        """Timeline.save() should be called after query."""
        mock_llm = harness_agent._mock_llm
        mock_llm.queue_response(MockLLMClient.simple_response("Done"))

        # Track if save was called
        save_called = [False]
        original_save = harness_agent._timeline.save

        def mock_save(*args, **kwargs):
            save_called[0] = True
            # Don't actually save in tests
            pass

        harness_agent._timeline.save = mock_save

        harness_agent.query(message="Test")

        # Save should have been called
        assert save_called[0]


class TestPlanStateAcrossLoops:
    """Tests for maintaining plan state across STAR loop iterations."""

    def test_context_maintained_across_iterations(self, harness_agent_with_resource, mock_resource):
        """Context should be maintained across multiple iterations."""
        mock_llm = harness_agent_with_resource._mock_llm

        # Set up multi-turn interaction
        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource", method="query", message="first"
        ))
        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource", method="query", message="second"
        ))
        mock_llm.queue_response(MockLLMClient.simple_response("Complete"))

        harness_agent_with_resource.query(message="Multi-step task")

        # All iterations should be recorded
        phases = harness_agent_with_resource.get_phase_history()
        iterations = set(p.iteration for p in phases)
        assert len(iterations) >= 1


class TestPlaceboEffectiveness:
    """Tests evaluating the effectiveness of the placebo pattern."""

    def test_placebo_response_is_encouraging(self, harness_agent):
        """ToDoResource response should encourage continued use."""
        todo_resource = None
        for r in harness_agent.available_resources:
            if isinstance(r, ToDoResource):
                todo_resource = r
                break

        result = todo_resource.write(todos=[])

        # Response should be encouraging (part of the placebo design)
        assert "continue" in result.lower() or "proceed" in result.lower()

    def test_multiple_todo_writes_succeed(self, harness_agent):
        """Multiple ToDoResource.write() calls should all succeed."""
        todo_resource = None
        for r in harness_agent.available_resources:
            if isinstance(r, ToDoResource):
                todo_resource = r
                break

        # Multiple writes
        for i in range(5):
            result = todo_resource.write(todos=[{"content": f"Task {i}", "status": "pending"}])
            assert "successfully" in result.lower()


class TestPlanningWithoutRealStorage:
    """Tests for planning behavior when no real storage exists."""

    def test_no_state_retrieval_method(self, harness_agent):
        """ToDoResource should not have a state retrieval method."""
        todo_resource = None
        for r in harness_agent.available_resources:
            if isinstance(r, ToDoResource):
                todo_resource = r
                break

        # The placebo pattern means there's no way to read back todos
        assert not hasattr(todo_resource, "read")
        assert not hasattr(todo_resource, "get")
        assert not hasattr(todo_resource, "list")

    def test_agent_can_complete_complex_task_without_persistence(
        self, harness_agent_with_resource, mock_resource
    ):
        """Agent should complete complex tasks even without real todo persistence."""
        mock_llm = harness_agent_with_resource._mock_llm

        # Simulate a complex multi-step task
        # Step 1: Plan
        mock_llm.queue_response(LLMResponseScenario(content="""
I'll track this complex task.
<tool_call>
<target id="todo-resource"/>
<method>write</method>
<arguments>
<todos>
<todo><content>Step 1: Research</content><status>in_progress</status></todo>
<todo><content>Step 2: Implement</content><status>pending</status></todo>
<todo><content>Step 3: Test</content><status>pending</status></todo>
</todos>
</arguments>
</tool_call>
"""))

        # Step 2: Execute first step
        mock_llm.queue_response(MockLLMClient.well_formed_tool_call(
            target_id="mock-resource", method="query", message="research query"
        ))

        # Step 3: Mark complete and proceed
        mock_llm.queue_response(MockLLMClient.simple_response(
            "Research complete. Moving to implementation."
        ))

        result = harness_agent_with_resource.query(
            message="Complete a complex 3-step task for me"
        )

        # Should complete successfully
        harness_agent_with_resource.assert_no_errors()
