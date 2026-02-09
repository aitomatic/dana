"""Tests for StatusLineComponent status line formatting."""

from dana.cli.components.status_line import StatusLineComponent


class TestStatusLineInit:
    """Test constructor and defaults."""

    def test_default_values(self) -> None:
        status = StatusLineComponent()
        assert status.agent_id == ""
        assert status.model == ""
        assert status.turn == 0
        assert status.max_turns == 0

    def test_initial_render_is_empty(self) -> None:
        status = StatusLineComponent()
        assert status.render() == ""


class TestStatusLineUpdate:
    """Test update method."""

    def test_update_all_fields(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="agent-1", model="gpt-4", turn=2, max_turns=5)
        assert status.agent_id == "agent-1"
        assert status.model == "gpt-4"
        assert status.turn == 2
        assert status.max_turns == 5

    def test_update_partial_fields(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="agent-1")
        assert status.agent_id == "agent-1"
        assert status.model == ""
        assert status.turn == 0

    def test_update_replaces_previous_values(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="agent-1", model="gpt-4", turn=1, max_turns=5)
        status.update(agent_id="agent-2", model="claude", turn=3, max_turns=10)
        assert status.agent_id == "agent-2"
        assert status.model == "claude"
        assert status.turn == 3
        assert status.max_turns == 10

    def test_update_with_defaults_resets_fields(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="agent-1", model="gpt-4", turn=2, max_turns=5)
        status.update()
        assert status.agent_id == ""
        assert status.model == ""
        assert status.turn == 0
        assert status.max_turns == 0


class TestStatusLineRender:
    """Test render output format."""

    def test_full_status_with_turn(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="dana-coder", model="gpt-4", turn=3, max_turns=10)
        assert status.render() == "dana-coder | gpt-4 | turn 3/10"

    def test_agent_and_model_only(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="dana-coder", model="gpt-4")
        assert status.render() == "dana-coder | gpt-4"

    def test_agent_id_only(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="dana-coder")
        assert status.render() == "dana-coder"

    def test_model_only(self) -> None:
        status = StatusLineComponent()
        status.update(model="gpt-4")
        assert status.render() == "gpt-4"

    def test_turn_only(self) -> None:
        status = StatusLineComponent()
        status.update(turn=2, max_turns=5)
        assert status.render() == "turn 2/5"

    def test_turn_zero_not_shown(self) -> None:
        """Turn info is hidden when turn is 0."""
        status = StatusLineComponent()
        status.update(agent_id="dana-coder", model="gpt-4", turn=0, max_turns=5)
        assert status.render() == "dana-coder | gpt-4"

    def test_empty_strings_not_shown(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="", model="", turn=0, max_turns=0)
        assert status.render() == ""

    def test_turn_one_shown(self) -> None:
        """Turn 1 should be displayed."""
        status = StatusLineComponent()
        status.update(agent_id="agent", model="model", turn=1, max_turns=3)
        assert status.render() == "agent | model | turn 1/3"

    def test_render_after_multiple_updates(self) -> None:
        """Each render reflects the latest update."""
        status = StatusLineComponent()
        status.update(agent_id="a", model="m", turn=1, max_turns=3)
        assert "a" in status.render()
        status.update(agent_id="b", model="n", turn=2, max_turns=5)
        result = status.render()
        assert "b" in result
        assert "n" in result
        assert "turn 2/5" in result
        assert "a" not in result


class TestStatusLineEdgeCases:
    """Test edge cases."""

    def test_large_turn_numbers(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="agent", model="model", turn=999, max_turns=1000)
        assert status.render() == "agent | model | turn 999/1000"

    def test_agent_id_with_special_characters(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="agent/sub-agent-1", model="gpt-4o")
        assert status.render() == "agent/sub-agent-1 | gpt-4o"

    def test_long_model_name(self) -> None:
        status = StatusLineComponent()
        status.update(agent_id="a", model="claude-3-opus-20240229")
        assert status.render() == "a | claude-3-opus-20240229"


class TestStatusLineImport:
    """Test package imports."""

    def test_import_from_components_package(self) -> None:
        from dana.cli.components import StatusLineComponent as Imported

        assert Imported is StatusLineComponent
