"""Tests for keyboard navigation of result panels in RichCLIRenderer."""

from rich.console import Console

from dana.cli.components.result_panel import ResultPanelComponent
from dana.cli.rich_cli_renderer import RichCLIRenderer


class TestSelectDown:
    """Test select_down() navigation."""

    def _make_renderer_with_results(self, count: int = 3) -> RichCLIRenderer:
        renderer = RichCLIRenderer(console=Console(force_terminal=True))
        for i in range(count):
            renderer.state.current_turn_results.append(ResultPanelComponent(tool_name=f"tool_{i}", output=f"output {i}"))
        return renderer

    def test_select_down_from_default(self) -> None:
        """First select_down from default (-1) goes to index 0."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = -1
        renderer.select_down()
        assert renderer.state.selected_index == 0

    def test_select_down_increments(self) -> None:
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = 0
        renderer.select_down()
        assert renderer.state.selected_index == 1

    def test_select_down_wraps_to_start(self) -> None:
        """Wraps from last index back to 0."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = 2
        renderer.select_down()
        assert renderer.state.selected_index == 0

    def test_select_down_no_results_noop(self) -> None:
        """No-op when there are no current turn results."""
        renderer = RichCLIRenderer(console=Console(force_terminal=True))
        renderer.state.selected_index = -1
        renderer.select_down()
        assert renderer.state.selected_index == -1

    def test_select_down_single_result(self) -> None:
        """Single result wraps to itself."""
        renderer = self._make_renderer_with_results(1)
        renderer.state.selected_index = 0
        renderer.select_down()
        assert renderer.state.selected_index == 0


class TestSelectUp:
    """Test select_up() navigation."""

    def _make_renderer_with_results(self, count: int = 3) -> RichCLIRenderer:
        renderer = RichCLIRenderer(console=Console(force_terminal=True))
        for i in range(count):
            renderer.state.current_turn_results.append(ResultPanelComponent(tool_name=f"tool_{i}", output=f"output {i}"))
        return renderer

    def test_select_up_from_default(self) -> None:
        """First select_up from default (-1) goes to last index."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = -1
        renderer.select_up()
        assert renderer.state.selected_index == 2

    def test_select_up_decrements(self) -> None:
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = 2
        renderer.select_up()
        assert renderer.state.selected_index == 1

    def test_select_up_wraps_to_end(self) -> None:
        """Wraps from index 0 to last index."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = 0
        renderer.select_up()
        assert renderer.state.selected_index == 2

    def test_select_up_no_results_noop(self) -> None:
        """No-op when there are no current turn results."""
        renderer = RichCLIRenderer(console=Console(force_terminal=True))
        renderer.state.selected_index = -1
        renderer.select_up()
        assert renderer.state.selected_index == -1

    def test_select_up_single_result(self) -> None:
        """Single result wraps to itself."""
        renderer = self._make_renderer_with_results(1)
        renderer.state.selected_index = 0
        renderer.select_up()
        assert renderer.state.selected_index == 0


class TestToggleExpand:
    """Test toggle_expand() for selected result."""

    def _make_renderer_with_results(self, count: int = 3) -> RichCLIRenderer:
        renderer = RichCLIRenderer(console=Console(force_terminal=True))
        for i in range(count):
            renderer.state.current_turn_results.append(ResultPanelComponent(tool_name=f"tool_{i}", output=f"output {i}"))
        return renderer

    def test_toggle_adds_to_expanded(self) -> None:
        """Toggle on a non-expanded index adds it to expanded_indices."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = 1
        renderer.toggle_expand()
        assert 1 in renderer.state.expanded_indices

    def test_toggle_removes_from_expanded(self) -> None:
        """Toggle on an already expanded index removes it."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = 1
        renderer.state.expanded_indices.add(1)
        renderer.toggle_expand()
        assert 1 not in renderer.state.expanded_indices

    def test_toggle_double_toggle_returns_to_original(self) -> None:
        """Double toggle returns to original state."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = 0
        renderer.toggle_expand()
        assert 0 in renderer.state.expanded_indices
        renderer.toggle_expand()
        assert 0 not in renderer.state.expanded_indices

    def test_toggle_noop_when_no_selection(self) -> None:
        """No-op when selected_index is -1 (no selection)."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = -1
        renderer.toggle_expand()
        assert len(renderer.state.expanded_indices) == 0

    def test_toggle_noop_when_index_out_of_range(self) -> None:
        """No-op when selected_index is beyond results count."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = 5
        renderer.toggle_expand()
        assert len(renderer.state.expanded_indices) == 0

    def test_toggle_noop_when_no_results(self) -> None:
        """No-op when there are no current turn results."""
        renderer = RichCLIRenderer(console=Console(force_terminal=True))
        renderer.state.selected_index = 0
        renderer.toggle_expand()
        assert len(renderer.state.expanded_indices) == 0

    def test_toggle_independent_indices(self) -> None:
        """Toggling different indices are independent."""
        renderer = self._make_renderer_with_results(3)

        renderer.state.selected_index = 0
        renderer.toggle_expand()
        renderer.state.selected_index = 2
        renderer.toggle_expand()

        assert 0 in renderer.state.expanded_indices
        assert 1 not in renderer.state.expanded_indices
        assert 2 in renderer.state.expanded_indices


class TestHistoricalNotSelectable:
    """Test that historical results are not navigable."""

    def test_navigation_only_counts_current_turn(self) -> None:
        """select_down only navigates current_turn_results, not historical."""
        renderer = RichCLIRenderer(console=Console(force_terminal=True))

        # Add historical results
        renderer.state.historical_results.append(ResultPanelComponent(tool_name="old", output="old output", is_recent=False))

        # Add current turn results
        renderer.state.current_turn_results.append(ResultPanelComponent(tool_name="new_0", output="new 0"))
        renderer.state.current_turn_results.append(ResultPanelComponent(tool_name="new_1", output="new 1"))

        renderer.state.selected_index = 0
        renderer.select_down()
        # Should go to index 1 (within current_turn only), not to historical
        assert renderer.state.selected_index == 1

    def test_toggle_only_affects_current_turn(self) -> None:
        """toggle_expand only works on current_turn_results."""
        renderer = RichCLIRenderer(console=Console(force_terminal=True))

        # Add historical results
        renderer.state.historical_results.append(ResultPanelComponent(tool_name="old", output="old output", is_recent=False))

        # Add current turn result
        renderer.state.current_turn_results.append(ResultPanelComponent(tool_name="new", output="new output"))

        # Select index 0 in current turn
        renderer.state.selected_index = 0
        renderer.toggle_expand()
        assert 0 in renderer.state.expanded_indices

    def test_empty_current_turn_with_historical_noop(self) -> None:
        """Navigation is no-op even if historical results exist but current is empty."""
        renderer = RichCLIRenderer(console=Console(force_terminal=True))

        renderer.state.historical_results.append(ResultPanelComponent(tool_name="old", output="old", is_recent=False))
        # No current turn results

        renderer.state.selected_index = -1
        renderer.select_down()
        assert renderer.state.selected_index == -1

        renderer.select_up()
        assert renderer.state.selected_index == -1


class TestSelectedHighlight:
    """Test visual highlight for selected result panels."""

    def test_selected_recent_has_bold_yellow_border(self) -> None:
        """Selected recent panel renders with bold yellow border."""
        panel = ResultPanelComponent(tool_name="bash", output="hello", is_recent=True)
        result = panel.render(selected=True)
        assert result.border_style == "bold yellow"

    def test_unselected_recent_has_cyan_border(self) -> None:
        """Unselected recent panel retains cyan border."""
        panel = ResultPanelComponent(tool_name="bash", output="hello", is_recent=True)
        result = panel.render(selected=False)
        assert result.border_style == "cyan"

    def test_selected_historical_stays_dim(self) -> None:
        """Historical panels always have dim border regardless of selected."""
        panel = ResultPanelComponent(tool_name="bash", output="hello", is_recent=False)
        result = panel.render(selected=True)
        assert result.border_style == "dim"

    def test_default_selected_false(self) -> None:
        """Default selected parameter is False."""
        panel = ResultPanelComponent(tool_name="bash", output="hello", is_recent=True)
        result = panel.render()
        assert result.border_style == "cyan"


class TestNavigationWorkflow:
    """Test navigation workflows combining multiple operations."""

    def _make_renderer_with_results(self, count: int = 3) -> RichCLIRenderer:
        renderer = RichCLIRenderer(console=Console(force_terminal=True))
        for i in range(count):
            renderer.state.current_turn_results.append(ResultPanelComponent(tool_name=f"tool_{i}", output=f"output {i}"))
        return renderer

    def test_navigate_and_toggle_workflow(self) -> None:
        """Full workflow: navigate down, toggle, navigate, toggle."""
        renderer = self._make_renderer_with_results(3)

        # Start at -1, go to 0
        renderer.select_down()
        assert renderer.state.selected_index == 0

        # Toggle expand on index 0
        renderer.toggle_expand()
        assert 0 in renderer.state.expanded_indices

        # Move down to 1
        renderer.select_down()
        assert renderer.state.selected_index == 1

        # Toggle expand on index 1
        renderer.toggle_expand()
        assert 1 in renderer.state.expanded_indices

        # Index 0 still expanded
        assert 0 in renderer.state.expanded_indices

    def test_navigate_up_and_down_cycle(self) -> None:
        """Navigate down through all, then up back to start."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = 0

        # Down through all
        renderer.select_down()  # 1
        renderer.select_down()  # 2
        renderer.select_down()  # 0 (wrap)
        assert renderer.state.selected_index == 0

        # Up through all
        renderer.select_up()  # 2 (wrap)
        renderer.select_up()  # 1
        renderer.select_up()  # 0
        assert renderer.state.selected_index == 0

    def test_rendering_with_selection_state(self) -> None:
        """Panels render with correct highlight based on selection state."""
        renderer = self._make_renderer_with_results(3)
        renderer.state.selected_index = 1
        renderer.state.expanded_indices.add(1)

        results = renderer.state.current_turn_results
        for i, rp in enumerate(results):
            is_selected = i == renderer.state.selected_index
            is_expanded = i in renderer.state.expanded_indices
            panel = rp.render(expanded=is_expanded, selected=is_selected)

            if i == 1:
                assert panel.border_style == "bold yellow"
            else:
                assert panel.border_style == "cyan"
