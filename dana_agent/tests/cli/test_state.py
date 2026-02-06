"""Tests for RenderState dataclass."""

from dana.cli.state import RenderState


class TestRenderState:
    """Test RenderState dataclass defaults and field types."""

    def test_default_values(self):
        """Test that all fields have correct default values."""
        state = RenderState()

        assert state.current_phase == ""
        assert state.current_agent_id == ""
        assert state.current_model == ""
        assert state.current_turn == 0
        assert state.max_turns == 0
        assert state.current_turn_results == []
        assert state.historical_results == []
        assert state.expanded_indices == set()
        assert state.selected_index == -1
        assert state.todo_items == []

    def test_field_types(self):
        """Test that fields are the correct types."""
        state = RenderState()

        assert isinstance(state.current_phase, str)
        assert isinstance(state.current_agent_id, str)
        assert isinstance(state.current_model, str)
        assert isinstance(state.current_turn, int)
        assert isinstance(state.max_turns, int)
        assert isinstance(state.current_turn_results, list)
        assert isinstance(state.historical_results, list)
        assert isinstance(state.expanded_indices, set)
        assert isinstance(state.selected_index, int)
        assert isinstance(state.todo_items, list)

    def test_custom_values(self):
        """Test construction with custom values."""
        state = RenderState(
            current_phase="THINK",
            current_agent_id="agent-1",
            current_model="claude-sonnet",
            current_turn=3,
            max_turns=10,
            current_turn_results=[{"tool": "bash", "output": "hello"}],
            historical_results=[{"tool": "search", "output": "found"}],
            expanded_indices={0, 2},
            selected_index=1,
            todo_items=[{"content": "Fix bug", "status": "in_progress"}],
        )

        assert state.current_phase == "THINK"
        assert state.current_agent_id == "agent-1"
        assert state.current_model == "claude-sonnet"
        assert state.current_turn == 3
        assert state.max_turns == 10
        assert len(state.current_turn_results) == 1
        assert len(state.historical_results) == 1
        assert state.expanded_indices == {0, 2}
        assert state.selected_index == 1
        assert len(state.todo_items) == 1

    def test_mutable_defaults_are_independent(self):
        """Test that mutable default fields are independent per instance."""
        state1 = RenderState()
        state2 = RenderState()

        state1.current_turn_results.append("result1")
        state1.expanded_indices.add(0)
        state1.todo_items.append("item1")

        # state2 should not be affected
        assert state2.current_turn_results == []
        assert state2.expanded_indices == set()
        assert state2.todo_items == []

    def test_import_from_package(self):
        """Test that RenderState can be imported from the cli package."""
        from dana.cli import RenderState as ImportedRenderState

        assert ImportedRenderState is RenderState
