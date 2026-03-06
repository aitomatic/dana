"""Tests for inject_as_user timeline ordering.

Verifies that USER_MESSAGE entries from inject_as_user are added AFTER all
tool result entries, not interleaved. Interleaving breaks OpenAI's native
tool calling API which requires all tool results to immediately follow
the assistant's tool_calls message.

Timeline ordering must be:
  TOOL_CALL → RESOURCE_RESULT(1) → ... → RESOURCE_RESULT(N) → USER_MESSAGE(injected)

NOT:
  TOOL_CALL → RESOURCE_RESULT(1) → USER_MESSAGE(injected) → RESOURCE_RESULT(2)  ← BREAKS OPENAI
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from dana.core.agent.star_agent import STARAgent
from dana.core.timeline.timeline import TimelineEntryType


@pytest.fixture
def agent():
    """Create a STARAgent with mocked LLM and a real timeline."""
    with patch("dana.core.agent.star_agent.LLM"):
        a = STARAgent(agent_type="test-inject", auto_register=False)
    # Seed a USER_MESSAGE so the multi-step reminder logic doesn't choke
    from dana.core.timeline.timeline import TimelineEntry

    a._timeline.add_entry(
        TimelineEntry(
            entry_type=TimelineEntryType.USER_MESSAGE,
            content="do something",
            is_latest_user_message=True,
        )
    )
    return a


class TestInjectAsUserOrdering:
    """Verify inject_as_user entries come after ALL tool results in the timeline."""

    def test_single_skill_result_ordering(self, agent):
        """A single skill result with inject_as_user: RESOURCE_RESULT before USER_MESSAGE."""
        agent._runtime = Mock()
        agent._runtime.execute_tools.return_value = [
            {
                "type": "resource",
                "target": "Skill",
                "result": {
                    "success": True,
                    "mode": "main",
                    "message": "Launching skill: test",
                    "inject_as_user": "Skill instructions here",
                },
                "success": True,
                "tool_call_id": "call_1",
            }
        ]

        agent._act({"tool_calls": [{"name": "Skill"}]})

        # Get entries added after the seed USER_MESSAGE
        entries = agent._timeline.timeline[1:]  # skip seed
        types = [e.entry_type for e in entries]

        # RESOURCE_RESULT must come before the injected USER_MESSAGE
        assert TimelineEntryType.RESOURCE_RESULT in types
        assert TimelineEntryType.USER_MESSAGE in types

        last_resource = max(i for i, t in enumerate(types) if t == TimelineEntryType.RESOURCE_RESULT)
        first_user = min(i for i, t in enumerate(types) if t == TimelineEntryType.USER_MESSAGE)
        assert last_resource < first_user, f"RESOURCE_RESULT (index {last_resource}) must come before USER_MESSAGE (index {first_user})"

    def test_multiple_tool_results_with_one_inject(self, agent):
        """Multiple tool results where only one has inject_as_user.

        Simulates: assistant calls Skill + another resource in parallel.
        The injected user message must come after BOTH tool results.
        """
        agent._runtime = Mock()
        agent._runtime.execute_tools.return_value = [
            {
                "type": "resource",
                "target": "Skill",
                "result": {
                    "success": True,
                    "mode": "main",
                    "message": "Launching skill: test",
                    "inject_as_user": "Skill instructions here",
                },
                "success": True,
                "tool_call_id": "call_skill",
            },
            {
                "type": "resource",
                "target": "bash.execute",
                "result": "command output",
                "success": True,
                "tool_call_id": "call_bash",
            },
        ]

        agent._act({"tool_calls": [{"name": "Skill"}, {"name": "bash.execute"}]})

        entries = agent._timeline.timeline[1:]  # skip seed
        types = [e.entry_type for e in entries]

        # Should have 2 RESOURCE_RESULTs then 1 USER_MESSAGE
        resource_indices = [i for i, t in enumerate(types) if t == TimelineEntryType.RESOURCE_RESULT]
        user_indices = [i for i, t in enumerate(types) if t == TimelineEntryType.USER_MESSAGE]

        assert len(resource_indices) == 2
        assert len(user_indices) == 1
        assert max(resource_indices) < min(user_indices), "All RESOURCE_RESULTs must come before any injected USER_MESSAGE"

    def test_many_parallel_tools_with_inject(self, agent):
        """10 parallel tool calls (reproduces the original OpenAI error).

        The assistant makes 10 tool calls including one Skill invoke.
        All 10 tool results must precede the injected USER_MESSAGE.
        """
        agent._runtime = Mock()
        tool_results = []
        for i in range(10):
            if i == 3:  # Skill call is the 4th
                tool_results.append(
                    {
                        "type": "resource",
                        "target": "Skill",
                        "result": {
                            "success": True,
                            "mode": "main",
                            "message": "Launching skill: test",
                            "inject_as_user": "Follow these instructions",
                        },
                        "success": True,
                        "tool_call_id": f"call_{i}",
                    }
                )
            else:
                tool_results.append(
                    {
                        "type": "resource",
                        "target": f"resource_{i}.method",
                        "result": f"result_{i}",
                        "success": True,
                        "tool_call_id": f"call_{i}",
                    }
                )

        agent._runtime.execute_tools.return_value = tool_results
        agent._act({"tool_calls": [{"name": f"tool_{i}"} for i in range(10)]})

        entries = agent._timeline.timeline[1:]  # skip seed
        types = [e.entry_type for e in entries]

        resource_indices = [i for i, t in enumerate(types) if t == TimelineEntryType.RESOURCE_RESULT]
        user_indices = [i for i, t in enumerate(types) if t == TimelineEntryType.USER_MESSAGE]

        assert len(resource_indices) == 10, f"Expected 10 RESOURCE_RESULTs, got {len(resource_indices)}"
        assert len(user_indices) == 1, f"Expected 1 USER_MESSAGE, got {len(user_indices)}"
        assert max(resource_indices) < min(
            user_indices
        ), f"RESOURCE_RESULT at index {max(resource_indices)} must come before USER_MESSAGE at index {min(user_indices)}"

    def test_no_inject_leaves_no_user_message(self, agent):
        """Tool results without inject_as_user don't create spurious USER_MESSAGE entries."""
        agent._runtime = Mock()
        agent._runtime.execute_tools.return_value = [
            {
                "type": "resource",
                "target": "bash.execute",
                "result": "output",
                "success": True,
                "tool_call_id": "call_1",
            },
        ]

        agent._act({"tool_calls": [{"name": "bash.execute"}]})

        entries = agent._timeline.timeline[1:]  # skip seed
        types = [e.entry_type for e in entries]

        assert TimelineEntryType.USER_MESSAGE not in types

    def test_inject_content_matches_skill_instructions(self, agent):
        """The injected USER_MESSAGE content matches what the skill returned."""
        skill_instructions = "Base directory: /foo\n\n# Do the thing\nStep 1..."
        agent._runtime = Mock()
        agent._runtime.execute_tools.return_value = [
            {
                "type": "resource",
                "target": "Skill",
                "result": {
                    "success": True,
                    "mode": "main",
                    "message": "Launching skill: test",
                    "inject_as_user": skill_instructions,
                },
                "success": True,
                "tool_call_id": "call_1",
            },
        ]

        agent._act({"tool_calls": [{"name": "Skill"}]})

        entries = agent._timeline.timeline[1:]
        user_entries = [e for e in entries if e.entry_type == TimelineEntryType.USER_MESSAGE]
        assert len(user_entries) == 1
        assert user_entries[0].content == skill_instructions

    def test_tool_result_excludes_inject_content(self, agent):
        """The RESOURCE_RESULT entry should NOT contain inject_as_user content."""
        agent._runtime = Mock()
        agent._runtime.execute_tools.return_value = [
            {
                "type": "resource",
                "target": "Skill",
                "result": {
                    "success": True,
                    "mode": "main",
                    "message": "Launching skill: test",
                    "inject_as_user": "This should not be in the tool result",
                },
                "success": True,
                "tool_call_id": "call_1",
            },
        ]

        agent._act({"tool_calls": [{"name": "Skill"}]})

        entries = agent._timeline.timeline[1:]
        resource_entries = [e for e in entries if e.entry_type == TimelineEntryType.RESOURCE_RESULT]
        assert len(resource_entries) == 1
        assert "inject_as_user" not in resource_entries[0].content
        assert "This should not be in the tool result" not in resource_entries[0].content


class TestInjectAsUserOrderingAsync:
    """Same ordering tests for _act_async."""

    @pytest.mark.asyncio
    async def test_async_ordering_with_multiple_tools(self, agent):
        """Async: inject_as_user comes after all tool results."""
        mock_runtime = Mock()
        mock_runtime.execute_tools_async = Mock()

        async def mock_execute(*args, **kwargs):
            return [
                {
                    "type": "resource",
                    "target": "Skill",
                    "result": {
                        "success": True,
                        "mode": "main",
                        "message": "Launching skill: test",
                        "inject_as_user": "Skill instructions",
                    },
                    "success": True,
                    "tool_call_id": "call_1",
                },
                {
                    "type": "resource",
                    "target": "bash.execute",
                    "result": "output",
                    "success": True,
                    "tool_call_id": "call_2",
                },
            ]

        mock_runtime.execute_tools_async = mock_execute
        agent._runtime = mock_runtime

        await agent._act_async({"tool_calls": [{"name": "Skill"}, {"name": "bash"}]})

        entries = agent._timeline.timeline[1:]
        types = [e.entry_type for e in entries]

        resource_indices = [i for i, t in enumerate(types) if t == TimelineEntryType.RESOURCE_RESULT]
        user_indices = [i for i, t in enumerate(types) if t == TimelineEntryType.USER_MESSAGE]

        assert len(resource_indices) == 2
        assert len(user_indices) == 1
        assert max(resource_indices) < min(user_indices), "All RESOURCE_RESULTs must come before any injected USER_MESSAGE (async)"
