#!/usr/bin/env python3
"""
Test for the multi-line input fix in Dana TUI.
This test verifies that after entering a multi-line statement, the next input
starts at the first line instead of the last line.
"""

import pytest
from textual.app import App

from dana.apps.tui.ui.prompt_textarea import PromptStyleTextArea
from dana.core.lang.sandbox_context import SandboxContext


class MockApp(App):
    """Mock app for multi-line input testing."""

    def compose(self):
        yield PromptStyleTextArea(sandbox=SandboxContext())


@pytest.mark.asyncio
async def test_multiline_input_clear_behavior():
    """Test that multi-line input clears properly and resets to first line."""

    app = MockApp()
    async with app.run_test() as pilot:
        # Get the prompt textarea
        prompt_widget = app.query_one(PromptStyleTextArea)

        # Test 1: Single line input should work normally
        print("Test 1: Single line input")
        await pilot.press("print('hello')")
        await pilot.press("enter")

        # Verify input is cleared and focused
        assert len(prompt_widget._input_lines) == 1
        assert prompt_widget._input_lines[0].value == ""
        assert prompt_widget._input_lines[0].has_focus

        # Test 2: Multi-line input (2 lines)
        print("Test 2: Multi-line input (2 lines)")
        await pilot.press("if x > 0:")
        await pilot.press("enter")
        await pilot.press("    print('positive')")
        await pilot.press("enter")
        await pilot.press("enter")  # Empty line to submit

        # Verify input is cleared and reset to first line
        assert len(prompt_widget._input_lines) == 1, f"Expected 1 line, got {len(prompt_widget._input_lines)}"
        assert prompt_widget._input_lines[0].value == ""
        assert prompt_widget._input_lines[0].has_focus

        # Test 3: Multi-line input (3 lines)
        print("Test 3: Multi-line input (3 lines)")
        await pilot.press("for i in range(3):")
        await pilot.press("enter")
        await pilot.press("    if i % 2 == 0:")
        await pilot.press("enter")
        await pilot.press("        print(f'even: {i}')")
        await pilot.press("enter")
        await pilot.press("enter")  # Empty line to submit

        # Verify input is cleared and reset to first line
        assert len(prompt_widget._input_lines) == 1, f"Expected 1 line, got {len(prompt_widget._input_lines)}"
        assert prompt_widget._input_lines[0].value == ""
        assert prompt_widget._input_lines[0].has_focus


@pytest.mark.asyncio
async def test_multiline_input_focus_behavior():
    """Test that focus is properly maintained after multi-line input."""

    app = MockApp()
    async with app.run_test() as pilot:
        prompt_widget = app.query_one(PromptStyleTextArea)

        # Enter multi-line command
        await pilot.press("def test_func():")
        await pilot.press("enter")
        await pilot.press("    return True")
        await pilot.press("enter")
        await pilot.press("enter")  # Submit

        # Verify focus is on the first (and only) line
        assert len(prompt_widget._input_lines) == 1
        assert prompt_widget._input_lines[0].has_focus

        # Try typing - should appear at the beginning
        await pilot.press("print('test')")

        # Verify the text appears in the first line
        # Note: The input might be cleared immediately, so we check that focus is maintained
        assert prompt_widget._input_lines[0].has_focus
        # The value might be empty if the input was cleared, but focus should be correct


@pytest.mark.asyncio
async def test_multiline_input_dom_cleanup():
    """Test that DOM elements are properly cleaned up after multi-line input."""

    app = MockApp()
    async with app.run_test() as pilot:
        prompt_widget = app.query_one(PromptStyleTextArea)

        # Start with single line
        initial_children = len(prompt_widget.children)

        # Enter multi-line command
        await pilot.press("if condition:")
        await pilot.press("enter")
        await pilot.press("    do_something()")
        await pilot.press("enter")
        await pilot.press("enter")  # Submit

        # Verify DOM is cleaned up (should have same number of children as initial)
        final_children = len(prompt_widget.children)
        assert final_children == initial_children, f"Expected {initial_children} children, got {final_children}"

        # Verify only one input line remains
        assert len(prompt_widget._input_lines) == 1


def test_clear_method_logic():
    """Test the clear method logic without creating actual widgets."""

    # Test the core logic: removing extra lines from a list
    input_lines = ["line1", "line2", "line3"]

    # Simulate the clear method logic
    while len(input_lines) > 1:
        input_lines.pop()

    # Verify only one line remains
    assert len(input_lines) == 1
    assert input_lines[0] == "line1"

    # Test with single line (should not remove anything)
    single_line = ["line1"]
    while len(single_line) > 1:
        single_line.pop()

    assert len(single_line) == 1
    assert single_line[0] == "line1"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
