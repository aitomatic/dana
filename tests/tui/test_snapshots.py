"""
Snapshot Tests for Dana TUI.

Visual regression testing using pytest-textual-snapshot.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""


def test_dana_tui_initial_state(snap_compare):
    """Test initial TUI state with snapshot."""
    assert snap_compare("dana/tui/app.py")


def test_dana_tui_with_agents(snap_compare):
    """Test TUI with agents created."""

    async def setup_agents(pilot):
        await pilot.type("agent research")
        await pilot.press("enter")
        await pilot.type("agent coder")
        await pilot.press("enter")

    assert snap_compare("dana/tui/app.py", run_before=setup_agents)


def test_dana_tui_terminal_focus(snap_compare):
    """Test TUI with terminal focused."""

    async def focus_terminal(pilot):
        await pilot.click("#terminal")

    assert snap_compare("dana/tui/app.py", run_before=focus_terminal)


def test_dana_tui_agents_list_focus(snap_compare):
    """Test TUI with agents list focused."""

    async def focus_agents_list(pilot):
        await pilot.click("#agents-list")

    assert snap_compare("dana/tui/app.py", run_before=focus_agents_list)


def test_dana_tui_with_command_input(snap_compare):
    """Test TUI with command input."""

    async def input_command(pilot):
        await pilot.type("agent test")
        await pilot.press("enter")
        await pilot.type("hello world")

    assert snap_compare("dana/tui/app.py", run_before=input_command)


def test_dana_tui_different_sizes(snap_compare):
    """Test TUI at different terminal sizes."""
    assert snap_compare("dana/tui/app.py", terminal_size=(80, 24))
    assert snap_compare("dana/tui/app.py", terminal_size=(120, 40))


def test_dana_tui_with_agent_selection(snap_compare):
    """Test TUI with agent selected."""

    async def select_agent(pilot):
        await pilot.type("agent research")
        await pilot.press("enter")
        await pilot.type("agent coder")
        await pilot.press("enter")
        await pilot.press("tab")  # Switch to second agent

    assert snap_compare("dana/tui/app.py", run_before=select_agent)


def test_dana_tui_with_error_state(snap_compare):
    """Test TUI with error state."""

    async def trigger_error(pilot):
        await pilot.type("invalid command")
        await pilot.press("enter")

    assert snap_compare("dana/tui/app.py", run_before=trigger_error)


def test_dana_tui_with_long_content(snap_compare):
    """Test TUI with long content in terminal."""

    async def add_long_content(pilot):
        for i in range(10):
            await pilot.type(f"agent agent{i}")
            await pilot.press("enter")

    assert snap_compare("dana/tui/app.py", run_before=add_long_content)


def test_dana_tui_help_screen(snap_compare):
    """Test TUI help screen."""

    async def show_help(pilot):
        await pilot.press("f1")

    assert snap_compare("dana/tui/app.py", run_before=show_help)


def test_dana_tui_with_key_presses(snap_compare):
    """Test TUI with various key presses."""

    async def press_keys(pilot):
        await pilot.press("tab")
        await pilot.press("shift+tab")
        await pilot.press("escape")

    assert snap_compare("dana/tui/app.py", run_before=press_keys)
